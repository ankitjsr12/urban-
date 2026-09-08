"""Severity Scoring Engine for UrbanSense.

Calculates multi-factor AI severity ratings for road defects and incidents
based on computer vision confidence, spatial dimensions, fleet dynamics,
recurrence patterns, and ambient traffic conditions.
"""

from __future__ import annotations

from typing import Any, Optional

from app.models.road_defect import DefectSeverity, RoadDefectType
from app.models.incident import IncidentSeverity, IncidentType


class SeverityEngine:
    """Intelligent severity scoring engine."""

    DEFECT_BASE_SCORES: dict[str, float] = {
        RoadDefectType.POTHOLE.value: 45.0,
        RoadDefectType.ROAD_DAMAGE.value: 55.0,
        RoadDefectType.WATERLOGGING.value: 50.0,
        RoadDefectType.OBSTRUCTION.value: 65.0,
        RoadDefectType.CRACK.value: 25.0,
        RoadDefectType.OTHER.value: 20.0,
    }

    INCIDENT_BASE_SCORES: dict[str, float] = {
        IncidentType.ACCIDENT.value: 80.0,
        IncidentType.MEDICAL.value: 90.0,
        IncidentType.FIRE.value: 95.0,
        IncidentType.ROAD_HAZARD.value: 70.0,
        IncidentType.WATERLOGGING.value: 60.0,
        IncidentType.SECURITY.value: 75.0,
        IncidentType.POSSIBLE_HIT_AND_RUN.value: 85.0,
        IncidentType.COLLISION_LIKE_EVENT.value: 75.0,
        IncidentType.DANGEROUS_DRIVING.value: 55.0,
        IncidentType.PEDESTRIAN_RISK.value: 80.0,
        IncidentType.TRAFFIC.value: 40.0,
        IncidentType.OTHER.value: 30.0,
    }

    @classmethod
    def calculate_defect_severity(
        cls,
        defect_type: RoadDefectType | str,
        confidence: float,
        bounding_box: Any | None = None,
        speed_kmh: float | None = None,
        recurrence_count: int = 1,
        traffic_density: str | None = None,
    ) -> tuple[DefectSeverity, float, dict[str, Any]]:
        """Calculate road defect severity, returning (DefectSeverity, score, explanation_factors)."""
        type_key = defect_type.value if hasattr(defect_type, "value") else str(defect_type).upper()
        base_score = cls.DEFECT_BASE_SCORES.get(type_key, 30.0)

        # Confidence weight: low confidence dampens, high confidence reinforces
        conf = max(0.1, min(1.0, float(confidence or 0.5)))
        score = base_score * (0.6 + 0.4 * conf)

        factors: dict[str, Any] = {
            "base_score": base_score,
            "confidence": conf,
            "recurrence_count": recurrence_count,
        }

        # Bounding box sizing modifier (if bbox area is significant in frame)
        if bounding_box and isinstance(bounding_box, (list, tuple)) and len(bounding_box) >= 4:
            try:
                x1, y1, x2, y2 = [float(v) for v in bounding_box[:4]]
                w = abs(x2 - x1)
                h = abs(y2 - y1)
                area = w * h
                # Normal normalized bounding box area: 0.0 - 1.0
                if area > 0.08:
                    score += 20.0
                    factors["bbox_size"] = "large"
                elif area > 0.03:
                    score += 10.0
                    factors["bbox_size"] = "medium"
            except Exception:
                pass

        # Speed factor: road anomalies at higher vehicle speeds present greater hazard
        if speed_kmh is not None:
            factors["speed_kmh"] = speed_kmh
            if speed_kmh >= 60.0:
                score += 15.0
            elif speed_kmh >= 40.0:
                score += 8.0

        # Recurrence factor: repeatedly detected by multiple fleet passes
        if recurrence_count >= 5:
            score += 18.0
            factors["recurrence_level"] = "high"
        elif recurrence_count >= 2:
            score += 8.0
            factors["recurrence_level"] = "repeat"

        # Traffic density factor
        if traffic_density and traffic_density.upper() in ("HIGH", "CONGESTED"):
            score += 10.0
            factors["traffic_density"] = traffic_density

        score = max(0.0, min(100.0, score))

        if score >= 75.0:
            sev = DefectSeverity.CRITICAL
        elif score >= 50.0:
            sev = DefectSeverity.HIGH
        elif score >= 30.0:
            sev = DefectSeverity.MEDIUM
        else:
            sev = DefectSeverity.LOW

        return sev, round(score, 1), factors

    @classmethod
    def calculate_incident_severity(
        cls,
        incident_type: IncidentType | str,
        confidence: float = 1.0,
        recurrence_count: int = 1,
        traffic_density: str | None = None,
        speed_kmh: float | None = None,
    ) -> tuple[IncidentSeverity, float, dict[str, Any]]:
        """Calculate incident severity, returning (IncidentSeverity, score, factors)."""
        type_key = incident_type.value if hasattr(incident_type, "value") else str(incident_type).upper()
        base_score = cls.INCIDENT_BASE_SCORES.get(type_key, 40.0)

        conf = max(0.1, min(1.0, float(confidence or 0.8)))
        score = base_score * (0.7 + 0.3 * conf)

        factors: dict[str, Any] = {
            "base_score": base_score,
            "confidence": conf,
        }

        if speed_kmh and speed_kmh > 70.0:
            score += 15.0
            factors["speed_kmh"] = speed_kmh

        if traffic_density and traffic_density.upper() in ("HIGH", "CONGESTED"):
            score += 12.0
            factors["traffic_density"] = traffic_density

        score = max(0.0, min(100.0, score))

        if score >= 75.0:
            sev = IncidentSeverity.CRITICAL
        elif score >= 50.0:
            sev = IncidentSeverity.HIGH
        elif score >= 30.0:
            sev = IncidentSeverity.MEDIUM
        else:
            sev = IncidentSeverity.LOW

        return sev, round(score, 1), factors
