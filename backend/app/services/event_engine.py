"""AI Event Engine for UrbanSense.

Bridges raw computer vision detections into standardized urban infrastructure events,
automating defect creation, incident alerts, deduplication, and real-time fleet notifications.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.detection import Detection, DetectionType
from app.models.incident import Incident, IncidentSeverity, IncidentStatus, IncidentType, Priority
from app.models.road_defect import DefectSeverity, DefectStatus, RoadDefect, RoadDefectType
from app.models.traffic_event import Density, TrafficEvent, TrafficEventType, TrafficSeverity
from app.services.duplicate_detector import DuplicateDetector
from app.services.severity_engine import SeverityEngine
from app.websocket.manager import manager

logger = logging.getLogger("urbansense.event_engine")

# Mapping from DetectionType or class_name to RoadDefectType
DEFECT_TYPE_MAP: dict[str, RoadDefectType] = {
    "POTHOLE": RoadDefectType.POTHOLE,
    "WATERLOGGING": RoadDefectType.WATERLOGGING,
    "CRACK": RoadDefectType.CRACK,
    "ROAD_DAMAGE": RoadDefectType.ROAD_DAMAGE,
    "OBSTRUCTION": RoadDefectType.OBSTRUCTION,
    "ROAD_DEFECT": RoadDefectType.ROAD_DAMAGE,
}

# Mapping to IncidentType
INCIDENT_TYPE_MAP: dict[str, IncidentType] = {
    "ACCIDENT": IncidentType.ACCIDENT,
    "CRASH": IncidentType.ACCIDENT,
    "MEDICAL": IncidentType.MEDICAL,
    "MEDICAL_EMERGENCY": IncidentType.MEDICAL,
    "FIRE": IncidentType.FIRE,
    "ROAD_HAZARD": IncidentType.ROAD_HAZARD,
    "ROAD_BLOCK": IncidentType.ROAD_HAZARD,
    "SECURITY": IncidentType.SECURITY,
    "SUSPICIOUS_ACTIVITY": IncidentType.SECURITY,
    "POSSIBLE_HIT_AND_RUN": IncidentType.POSSIBLE_HIT_AND_RUN,
    "DANGEROUS_DRIVING": IncidentType.DANGEROUS_DRIVING,
    "COLLISION_LIKE_EVENT": IncidentType.COLLISION_LIKE_EVENT,
    "PEDESTRIAN_RISK": IncidentType.PEDESTRIAN_RISK,
}


class AIEventEngine:
    """Central processing engine for AI detections to generate urban intelligence events."""

    @classmethod
    async def process_detection(
        cls,
        db: AsyncSession,
        detection: Detection,
        auto_commit: bool = True,
    ) -> dict[str, Any]:
        """Process an ingested detection through deduplication and automated event generation."""
        try:
            class_key = (detection.class_name or "").upper()
            det_type_key = detection.detection_type.value.upper() if hasattr(detection.detection_type, "value") else str(detection.detection_type).upper()

            # Check if detection represents a Road Defect
            defect_type = DEFECT_TYPE_MAP.get(class_key) or DEFECT_TYPE_MAP.get(det_type_key)
            if defect_type:
                return await cls._handle_road_defect(db, detection, defect_type, auto_commit)

            # Check if detection represents an Incident
            incident_type = INCIDENT_TYPE_MAP.get(class_key) or INCIDENT_TYPE_MAP.get(det_type_key)
            if incident_type:
                return await cls._handle_incident(db, detection, incident_type, auto_commit)

            return {
                "status": "acknowledged",
                "action": "none",
                "detection_id": str(detection.id),
                "detection_type": det_type_key,
            }

        except Exception as err:
            logger.error("Error processing detection %s through event engine: %s", detection.id, err, exc_info=True)
            return {
                "status": "error",
                "error": str(err),
                "detection_id": str(detection.id),
            }

    @classmethod
    async def _handle_road_defect(
        cls,
        db: AsyncSession,
        detection: Detection,
        defect_type: RoadDefectType,
        auto_commit: bool,
    ) -> dict[str, Any]:
        """Handle deduplication or creation of a road defect."""
        duplicate = await DuplicateDetector.find_duplicate_defect(
            db=db,
            latitude=detection.latitude,
            longitude=detection.longitude,
            defect_type=defect_type,
            distance_meters=50.0,
            time_window_hours=72,
        )

        if duplicate:
            # Merge into existing defect
            meta = dict(duplicate.metadata_json or {})
            rec_count = int(meta.get("recurrence_count", 1)) + 1
            meta["recurrence_count"] = rec_count
            meta["last_detected_at"] = (detection.detected_at or detection.created_at).isoformat()
            
            # Recalculate severity with new recurrence
            sev, score, factors = SeverityEngine.calculate_defect_severity(
                defect_type=defect_type,
                confidence=max(duplicate.confidence, detection.confidence),
                bounding_box=detection.bounding_box,
                recurrence_count=rec_count,
            )
            duplicate.severity = sev
            meta["severity_score"] = score
            meta["severity_factors"] = factors
            duplicate.metadata_json = meta

            if detection.confidence > duplicate.confidence:
                duplicate.confidence = detection.confidence

            if auto_commit:
                await db.commit()
                await db.refresh(duplicate)

            await manager.broadcast("detections", {
                "event": "ROAD_DEFECT_UPDATED",
                "data": {
                    "id": str(duplicate.id),
                    "defect_type": duplicate.defect_type.value,
                    "severity": duplicate.severity.value,
                    "recurrence_count": rec_count,
                    "latitude": duplicate.latitude,
                    "longitude": duplicate.longitude,
                    "is_duplicate": True,
                },
            })

            return {
                "status": "success",
                "action": "merged",
                "entity_type": "RoadDefect",
                "entity_id": str(duplicate.id),
                "recurrence_count": rec_count,
                "severity": duplicate.severity.value,
                "is_duplicate": True,
            }

        # New defect
        sev, score, factors = SeverityEngine.calculate_defect_severity(
            defect_type=defect_type,
            confidence=detection.confidence,
            bounding_box=detection.bounding_box,
            recurrence_count=1,
        )

        new_defect = RoadDefect(
            defect_type=defect_type,
            severity=sev,
            status=DefectStatus.OPEN,
            description=f"Auto-detected {defect_type.value} from fleet camera",
            latitude=detection.latitude,
            longitude=detection.longitude,
            confidence=detection.confidence,
            detected_by_bus_id=detection.bus_id,
            evidence_id=detection.evidence_id,
            model_name=detection.model_name,
            model_version=detection.model_version,
            metadata_json={
                "severity_score": score,
                "severity_factors": factors,
                "source_detection_id": str(detection.id),
                "recurrence_count": 1,
            },
        )
        db.add(new_defect)
        if auto_commit:
            await db.commit()
            await db.refresh(new_defect)

        await manager.broadcast("detections", {
            "event": "ROAD_DEFECT_CREATED",
            "data": {
                "id": str(new_defect.id),
                "defect_type": new_defect.defect_type.value,
                "severity": new_defect.severity.value,
                "latitude": new_defect.latitude,
                "longitude": new_defect.longitude,
                "confidence": new_defect.confidence,
                "is_duplicate": False,
            },
        })

        return {
            "status": "success",
            "action": "created",
            "entity_type": "RoadDefect",
            "entity_id": str(new_defect.id),
            "severity": new_defect.severity.value,
            "is_duplicate": False,
        }

    @classmethod
    async def _handle_incident(
        cls,
        db: AsyncSession,
        detection: Detection,
        incident_type: IncidentType,
        auto_commit: bool,
    ) -> dict[str, Any]:
        """Handle deduplication or creation of an incident."""
        duplicate = await DuplicateDetector.find_duplicate_incident(
            db=db,
            latitude=detection.latitude,
            longitude=detection.longitude,
            incident_type=incident_type,
            distance_meters=100.0,
            time_window_hours=24,
        )

        if duplicate:
            meta = dict(duplicate.metadata_json or {})
            rec_count = int(meta.get("recurrence_count", 1)) + 1
            meta["recurrence_count"] = rec_count
            duplicate.metadata_json = meta

            if auto_commit:
                await db.commit()
                await db.refresh(duplicate)

            return {
                "status": "success",
                "action": "merged",
                "entity_type": "Incident",
                "entity_id": str(duplicate.id),
                "recurrence_count": rec_count,
                "is_duplicate": True,
            }

        sev, score, factors = SeverityEngine.calculate_incident_severity(
            incident_type=incident_type,
            confidence=detection.confidence,
        )

        priority_map = {
            IncidentSeverity.CRITICAL: Priority.CRITICAL,
            IncidentSeverity.HIGH: Priority.HIGH,
            IncidentSeverity.MEDIUM: Priority.MEDIUM,
            IncidentSeverity.LOW: Priority.LOW,
        }

        new_incident = Incident(
            incident_type=incident_type,
            severity=sev,
            priority=priority_map.get(sev, Priority.MEDIUM),
            status=IncidentStatus.OPEN,
            title=f"Fleet Alert: {incident_type.value}",
            description=f"Automated incident alert detected by fleet camera (confidence: {detection.confidence:.2f})",
            latitude=detection.latitude,
            longitude=detection.longitude,
            bus_id=detection.bus_id,
            metadata_json={
                "severity_score": score,
                "severity_factors": factors,
                "source_detection_id": str(detection.id),
                "recurrence_count": 1,
            },
        )
        db.add(new_incident)
        if auto_commit:
            await db.commit()
            await db.refresh(new_incident)

        await manager.broadcast("incidents", {
            "event": "INCIDENT_CREATED",
            "data": {
                "id": str(new_incident.id),
                "incident_type": new_incident.incident_type.value,
                "severity": new_incident.severity.value,
                "latitude": new_incident.latitude,
                "longitude": new_incident.longitude,
                "title": new_incident.title,
            },
        })

        return {
            "status": "success",
            "action": "created",
            "entity_type": "Incident",
            "entity_id": str(new_incident.id),
            "severity": new_incident.severity.value,
            "is_duplicate": False,
        }
