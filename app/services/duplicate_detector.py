"""Duplicate Detection Service for UrbanSense.

Provides spatial and temporal deduplication for road defects, incidents,
and traffic events to prevent redundant fleet reports and alert fatigue.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.road_defect import DefectStatus, RoadDefect, RoadDefectType
from app.models.incident import Incident, IncidentStatus, IncidentType
from app.models.traffic_event import TrafficEvent, TrafficEventType


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in meters using Haversine formula."""
    r = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


class DuplicateDetector:
    """Geospatial and temporal duplicate detector for urban infrastructure anomalies."""

    @staticmethod
    def _bounding_box(latitude: float, longitude: float, distance_meters: float) -> tuple[float, float, float, float]:
        """Compute bounding box (min_lat, max_lat, min_lon, max_lon) for quick DB filtering."""
        # 1 deg latitude ~ 111,320 meters
        delta_lat = distance_meters / 111320.0
        # 1 deg longitude ~ 111,320 * cos(lat) meters
        cos_lat = math.cos(math.radians(latitude))
        delta_lon = distance_meters / (111320.0 * max(cos_lat, 0.01))
        return (
            latitude - delta_lat,
            latitude + delta_lat,
            longitude - delta_lon,
            longitude + delta_lon,
        )

    @classmethod
    async def find_duplicate_defect(
        cls,
        db: AsyncSession,
        latitude: float,
        longitude: float,
        defect_type: RoadDefectType,
        distance_meters: float = 50.0,
        time_window_hours: int = 48,
        active_only: bool = True,
    ) -> Optional[RoadDefect]:
        """Find an existing road defect near the specified location of the same defect type."""
        min_lat, max_lat, min_lon, max_lon = cls._bounding_box(latitude, longitude, distance_meters)

        stmt = select(RoadDefect).where(
            RoadDefect.defect_type == defect_type,
            RoadDefect.latitude >= min_lat,
            RoadDefect.latitude <= max_lat,
            RoadDefect.longitude >= min_lon,
            RoadDefect.longitude <= max_lon,
        )

        if active_only:
            # Active or unresolved defects
            stmt = stmt.where(
                RoadDefect.status.in_([
                    DefectStatus.OPEN,
                    DefectStatus.VERIFIED,
                    DefectStatus.IN_PROGRESS,
                    DefectStatus.DETECTED,
                    DefectStatus.ASSIGNED,
                ])
            )

        if time_window_hours > 0:
            since = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
            stmt = stmt.where(RoadDefect.detected_at >= since)

        result = await db.execute(stmt)
        candidates = result.scalars().all()

        closest: Optional[RoadDefect] = None
        min_dist = float("inf")

        for candidate in candidates:
            dist = haversine_distance_meters(latitude, longitude, candidate.latitude, candidate.longitude)
            if dist <= distance_meters and dist < min_dist:
                min_dist = dist
                closest = candidate

        return closest

    @classmethod
    async def find_duplicate_incident(
        cls,
        db: AsyncSession,
        latitude: float,
        longitude: float,
        incident_type: IncidentType,
        distance_meters: float = 100.0,
        time_window_hours: int = 24,
        active_only: bool = True,
    ) -> Optional[Incident]:
        """Find an existing incident near the specified location of the same incident type."""
        min_lat, max_lat, min_lon, max_lon = cls._bounding_box(latitude, longitude, distance_meters)

        stmt = select(Incident).where(
            Incident.incident_type == incident_type,
            Incident.latitude >= min_lat,
            Incident.latitude <= max_lat,
            Incident.longitude >= min_lon,
            Incident.longitude <= max_lon,
        )

        if active_only:
            stmt = stmt.where(
                Incident.status.in_([
                    IncidentStatus.OPEN,
                    IncidentStatus.ACKNOWLEDGED,
                    IncidentStatus.IN_PROGRESS,
                    IncidentStatus.NEW,
                    IncidentStatus.UNDER_REVIEW,
                    IncidentStatus.VERIFIED,
                    IncidentStatus.ASSIGNED,
                ])
            )

        if time_window_hours > 0:
            since = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
            stmt = stmt.where(Incident.detected_at >= since)

        result = await db.execute(stmt)
        candidates = result.scalars().all()

        closest: Optional[Incident] = None
        min_dist = float("inf")

        for candidate in candidates:
            dist = haversine_distance_meters(latitude, longitude, candidate.latitude, candidate.longitude)
            if dist <= distance_meters and dist < min_dist:
                min_dist = dist
                closest = candidate

        return closest

    @classmethod
    async def find_duplicate_traffic_event(
        cls,
        db: AsyncSession,
        latitude: float,
        longitude: float,
        event_type: TrafficEventType,
        distance_meters: float = 200.0,
        time_window_minutes: int = 60,
    ) -> Optional[TrafficEvent]:
        """Find active traffic event near the location within the time window."""
        min_lat, max_lat, min_lon, max_lon = cls._bounding_box(latitude, longitude, distance_meters)
        since = datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)

        stmt = select(TrafficEvent).where(
            TrafficEvent.event_type == event_type,
            TrafficEvent.latitude >= min_lat,
            TrafficEvent.latitude <= max_lat,
            TrafficEvent.longitude >= min_lon,
            TrafficEvent.longitude <= max_lon,
            TrafficEvent.ended_at.is_(None),
            TrafficEvent.started_at >= since,
        )

        result = await db.execute(stmt)
        candidates = result.scalars().all()

        closest: Optional[TrafficEvent] = None
        min_dist = float("inf")

        for candidate in candidates:
            dist = haversine_distance_meters(latitude, longitude, candidate.latitude, candidate.longitude)
            if dist <= distance_meters and dist < min_dist:
                min_dist = dist
                closest = candidate

        return closest
