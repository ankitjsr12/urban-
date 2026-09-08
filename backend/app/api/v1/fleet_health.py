"""Fleet Health Monitoring API for UrbanSense.

Provides real-time operational health checks for public transport fleet,
tracking GPS telemetry continuity, edge camera status, and AI ingestion latency.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user
from app.db.session import get_db
from app.models.bus import Bus, BusStatus
from app.models.detection import Detection
from app.models.location import BusLocation
from app.models.user import User
from app.schemas.common import Envelope

router = APIRouter(prefix="/fleet/health", tags=["Fleet Health"])


@router.get("", response_model=Envelope[dict])
async def get_fleet_health(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """Retrieve operational telemetry and AI edge sensor health for all fleet vehicles."""
    now = datetime.now(timezone.utc)
    ten_min_ago = now - timedelta(minutes=10)
    one_hour_ago = now - timedelta(hours=1)
    one_day_ago = now - timedelta(days=1)

    # 1. Fetch all buses
    buses = (await db.execute(select(Bus).order_by(Bus.registration_number))).scalars().all()

    # 2. Get latest location per bus
    # Subquery for max recorded_at per bus
    subq = (
        select(BusLocation.bus_id, func.max(BusLocation.recorded_at).label("max_recorded"))
        .group_by(BusLocation.bus_id)
        .subquery()
    )
    loc_stmt = (
        select(BusLocation)
        .join(subq, (BusLocation.bus_id == subq.c.bus_id) & (BusLocation.recorded_at == subq.c.max_recorded))
    )
    latest_locs = {loc.bus_id: loc for loc in (await db.execute(loc_stmt)).scalars().all()}

    # 3. Get detection counts in past 24h per bus
    det_stmt = (
        select(Detection.bus_id, func.count(Detection.id), func.max(Detection.detected_at))
        .where(Detection.detected_at >= one_day_ago)
        .group_by(Detection.bus_id)
    )
    det_stats = {
        row[0]: {"count_24h": row[1], "last_detection": row[2]}
        for row in (await db.execute(det_stmt)).all()
    }

    online_count = 0
    idle_count = 0
    offline_count = 0
    ai_active_count = 0
    fleet_records: list[dict[str, Any]] = []

    for bus in buses:
        loc = latest_locs.get(bus.id)
        det = det_stats.get(bus.id, {"count_24h": 0, "last_detection": None})

        # Calculate GPS state
        last_seen = loc.recorded_at if loc else (bus.updated_at or bus.created_at)
        if last_seen and last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)

        sec_since_gps = (now - last_seen).total_seconds() if last_seen else 999999

        if sec_since_gps <= 300:  # < 5 minutes
            gps_status = "ONLINE"
            online_count += 1
        elif sec_since_gps <= 1800:  # < 30 minutes
            gps_status = "IDLE"
            idle_count += 1
        else:
            gps_status = "OFFLINE"
            offline_count += 1

        # Calculate Camera / AI Edge state
        last_det = det["last_detection"]
        if last_det and last_det.tzinfo is None:
            last_det = last_det.replace(tzinfo=timezone.utc)
        sec_since_det = (now - last_det).total_seconds() if last_det else 999999

        camera_status = "ACTIVE" if sec_since_det <= 1800 else "STANDBY"
        if camera_status == "ACTIVE":
            ai_active_count += 1

        # Sensor health score (0 - 100)
        health_score = 100
        if gps_status == "OFFLINE":
            health_score -= 50
        elif gps_status == "IDLE":
            health_score -= 20
        if camera_status == "STANDBY" and gps_status == "ONLINE":
            health_score -= 15

        fleet_records.append({
            "bus_id": str(bus.id),
            "registration_number": bus.registration_number,
            "status": bus.status.value if hasattr(bus.status, "value") else str(bus.status),
            "gps_status": gps_status,
            "camera_status": camera_status,
            "health_score": max(0, health_score),
            "last_location": {
                "latitude": loc.latitude if loc else None,
                "longitude": loc.longitude if loc else None,
                "speed_kmh": loc.speed if loc else 0.0,
                "recorded_at": loc.recorded_at.isoformat() if loc and loc.recorded_at else None,
            } if loc else None,
            "ai_telemetry": {
                "detections_today": det["count_24h"],
                "last_detection_at": last_det.isoformat() if last_det else None,
            },
        })

    return {
        "data": {
            "summary": {
                "total_buses": len(buses),
                "online": online_count,
                "idle": idle_count,
                "offline": offline_count,
                "ai_cameras_active": ai_active_count,
                "fleet_health_avg": (
                    round(sum(b["health_score"] for b in fleet_records) / len(fleet_records), 1)
                    if fleet_records
                    else 100.0
                ),
            },
            "vehicles": fleet_records,
            "timestamp": now.isoformat(),
        }
    }
