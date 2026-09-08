"""Report Generation & Export API for UrbanSense.

Supports automated aggregation and CSV/JSON export for municipal authorities,
transit departments, and urban infrastructure engineers.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user
from app.db.session import get_db
from app.models.incident import Incident
from app.models.road_defect import RoadDefect
from app.models.user import User
from app.schemas.common import Envelope

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/generate")
async def generate_report(
    report_type: str = Query("road_defects"),
    time_window: str = Query("7d"),
    format: str = Query("json"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """Generate and export platform intelligence report in JSON or CSV format."""
    now = datetime.now(timezone.utc)
    since = None
    if time_window == "24h":
        since = now - timedelta(hours=24)
    elif time_window == "7d":
        since = now - timedelta(days=7)
    elif time_window == "30d":
        since = now - timedelta(days=30)

    if report_type == "road_defects":
        stmt = select(RoadDefect).order_by(RoadDefect.detected_at.desc()).limit(1000)
        if since:
            stmt = stmt.where(RoadDefect.detected_at >= since)
        defects = (await db.execute(stmt)).scalars().all()

        rows = [
            {
                "id": str(d.id),
                "defect_type": d.defect_type.value if hasattr(d.defect_type, "value") else str(d.defect_type),
                "severity": d.severity.value if hasattr(d.severity, "value") else str(d.severity),
                "status": d.status.value if hasattr(d.status, "value") else str(d.status),
                "latitude": d.latitude,
                "longitude": d.longitude,
                "confidence": round(d.confidence, 4),
                "detected_at": d.detected_at.isoformat() if d.detected_at else "",
                "description": d.description or "",
            }
            for d in defects
        ]

        if format == "csv":
            buf = io.StringIO()
            writer = csv.DictWriter(
                buf,
                fieldnames=["id", "defect_type", "severity", "status", "latitude", "longitude", "confidence", "detected_at", "description"],
            )
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
            filename = f"urbansense_defects_{time_window}_{now.strftime('%Y%m%d')}.csv"
            return Response(
                content=buf.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        return {
            "success": True,
            "data": {
                "report_type": report_type,
                "time_window": time_window,
                "generated_at": now.isoformat(),
                "total_records": len(rows),
                "records": rows,
            },
        }

    elif report_type == "incidents":
        stmt = select(Incident).order_by(Incident.detected_at.desc()).limit(1000)
        if since:
            stmt = stmt.where(Incident.detected_at >= since)
        incidents = (await db.execute(stmt)).scalars().all()

        rows = [
            {
                "id": str(i.id),
                "incident_type": i.incident_type.value if hasattr(i.incident_type, "value") else str(i.incident_type),
                "severity": i.severity.value if hasattr(i.severity, "value") else str(i.severity),
                "status": i.status.value if hasattr(i.status, "value") else str(i.status),
                "title": i.title or "",
                "latitude": i.latitude,
                "longitude": i.longitude,
                "detected_at": i.detected_at.isoformat() if i.detected_at else "",
            }
            for i in incidents
        ]

        if format == "csv":
            buf = io.StringIO()
            writer = csv.DictWriter(
                buf,
                fieldnames=["id", "incident_type", "severity", "status", "title", "latitude", "longitude", "detected_at"],
            )
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
            filename = f"urbansense_incidents_{time_window}_{now.strftime('%Y%m%d')}.csv"
            return Response(
                content=buf.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        return {
            "success": True,
            "data": {
                "report_type": report_type,
                "time_window": time_window,
                "generated_at": now.isoformat(),
                "total_records": len(rows),
                "records": rows,
            },
        }

    # Summary
    stmt_def = select(RoadDefect)
    stmt_inc = select(Incident)
    if since:
        stmt_def = stmt_def.where(RoadDefect.detected_at >= since)
        stmt_inc = stmt_inc.where(Incident.detected_at >= since)

    def_count = len((await db.execute(stmt_def)).scalars().all())
    inc_count = len((await db.execute(stmt_inc)).scalars().all())

    summary_data = {
        "report_type": "summary",
        "time_window": time_window,
        "generated_at": now.isoformat(),
        "total_defects": def_count,
        "total_incidents": inc_count,
    }

    if format == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["metric", "value"])
        for k, v in summary_data.items():
            writer.writerow([k, v])
        filename = f"urbansense_summary_{time_window}_{now.strftime('%Y%m%d')}.csv"
        return Response(
            content=buf.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    return {"success": True, "data": summary_data}
