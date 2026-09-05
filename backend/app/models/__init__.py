"""AI UrbanSense Backend Database Models.

Central model registry exposing all SQLAlchemy declarative models,
mixins, and enumeration types for production execution and Alembic discovery.
"""

from app.models.audit_log import AuditLog
from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, generate_uuid, utc_now
from app.models.bus import Bus, BusStatus
from app.models.citizen_report import CitizenReport, CitizenReportStatus, CitizenReportType, ReportPriority
from app.models.detection import Detection, DetectionType
from app.models.driver import Driver, DriverStatus
from app.models.incident import Incident, IncidentSeverity, IncidentStatus, IncidentType, Priority
from app.models.incident_evidence import EvidenceType, IncidentEvidence, StorageProvider
from app.models.location import BusLocation, SyncEvent
from app.models.model_version import AIModelType, ModelVersion
from app.models.notification import Notification, NotificationType
from app.models.road_defect import DefectSeverity, DefectStatus, RoadDefect, RoadDefectType
from app.models.route import Route
from app.models.traffic_event import Density, TrafficEvent, TrafficEventType, TrafficSeverity
from app.models.user import RefreshToken, Role, User
from app.models.vehicle import Vehicle, VehicleDetection, VehicleType

# Legacy alias helpers
def uid():
    return generate_uuid()

def now():
    return utc_now()

__all__ = [
    # Base and Mixins
    "Base",
    "UUIDPrimaryKeyMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
    "generate_uuid",
    "utc_now",
    "uid",
    "now",
    # User & Auth
    "User",
    "Role",
    "RefreshToken",
    # Fleet & Operations
    "Bus",
    "BusStatus",
    "Driver",
    "DriverStatus",
    "Route",
    # Telemetry & Location
    "BusLocation",
    "SyncEvent",
    # AI Computer Vision Detections
    "Detection",
    "DetectionType",
    # Infrastructure & Road Quality
    "RoadDefect",
    "RoadDefectType",
    "DefectSeverity",
    "DefectStatus",
    # Vehicle Intelligence & ANPR
    "Vehicle",
    "VehicleDetection",
    "VehicleType",
    # Traffic Intelligence
    "TrafficEvent",
    "TrafficEventType",
    "TrafficSeverity",
    "Density",
    # Safety & Incident Management
    "Incident",
    "IncidentType",
    "IncidentSeverity",
    "IncidentStatus",
    "Priority",
    "IncidentEvidence",
    "EvidenceType",
    "StorageProvider",
    # Citizen Engagement
    "CitizenReport",
    "CitizenReportType",
    "CitizenReportStatus",
    "ReportPriority",
    # Platform Core
    "Notification",
    "NotificationType",
    "AuditLog",
    "ModelVersion",
    "AIModelType",
]
