import enum
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models.user import Role
from app.models.bus import BusStatus
from app.models.driver import DriverStatus
from app.models.detection import DetectionType
from app.models.road_defect import RoadDefectType, DefectSeverity, DefectStatus
from app.models.vehicle import VehicleType
from app.models.traffic_event import TrafficEventType, TrafficSeverity, Density
from app.models.incident import IncidentType, IncidentSeverity, IncidentStatus, Priority
from app.models.incident_evidence import StorageProvider, EvidenceType
from app.models.citizen_report import CitizenReportType, CitizenReportStatus, ReportPriority
from app.models.notification import NotificationType
from app.models.model_version import AIModelType


# Location Schemas
class LocationIn(BaseModel):
    bus_id: UUID
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    speed: float | None = Field(default=None, ge=0)
    heading: float | None = Field(default=None, ge=0, le=360)
    accuracy: float | None = Field(default=None, ge=0)
    altitude: float | None = None
    source: str | None = 'GPS'
    timestamp: datetime | None = None
    client_event_id: str | None = None


# Bus Schemas
class BusIn(BaseModel):
    registration_number: str = Field(min_length=2, max_length=40)
    fleet_number: str | None = None
    bus_number: str | None = None
    operator_name: str | None = None
    model: str | None = None
    manufacturer: str | None = None
    year: int | None = None
    capacity: int | None = Field(default=None, gt=0)
    status: BusStatus = BusStatus.INACTIVE
    assigned_driver_id: UUID | None = None
    assigned_route_id: UUID | None = None
    driver_id: UUID | None = None
    route_id: UUID | None = None


class BusUpdate(BaseModel):
    registration_number: str | None = None
    fleet_number: str | None = None
    operator_name: str | None = None
    model: str | None = None
    manufacturer: str | None = None
    year: int | None = None
    capacity: int | None = Field(default=None, gt=0)
    status: BusStatus | None = None
    assigned_driver_id: UUID | None = None
    assigned_route_id: UUID | None = None
    is_active: bool | None = None


# Driver Schemas
class DriverIn(BaseModel):
    user_id: UUID
    employee_id: str = Field(min_length=2, max_length=80)
    license_number: str = Field(min_length=2, max_length=80)
    license_expiry: datetime | None = None
    phone: str | None = None
    status: DriverStatus = DriverStatus.ACTIVE


class DriverUpdate(BaseModel):
    employee_id: str | None = None
    license_number: str | None = None
    license_expiry: datetime | None = None
    phone: str | None = None
    status: DriverStatus | None = None


class DriverAssignIn(BaseModel):
    bus_id: UUID | None = None


# Route Schemas
class RouteIn(BaseModel):
    route_number: str | None = None
    code: str | None = None
    name: str = Field(min_length=2, max_length=160)
    description: str | None = None
    origin: str | None = None
    destination: str | None = None
    geometry_wkt: str | None = None
    is_active: bool = True


class RouteUpdate(BaseModel):
    route_number: str | None = None
    name: str | None = None
    description: str | None = None
    origin: str | None = None
    destination: str | None = None
    geometry_wkt: str | None = None
    is_active: bool | None = None


# Detection Schemas
class DetectionIn(BaseModel):
    bus_id: UUID | None = None
    detection_type: DetectionType
    class_name: str | None = None
    confidence: float = Field(ge=0, le=1)
    bounding_box: dict | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    timestamp: datetime | None = None
    detected_at: datetime | None = None
    model_name: str = "urbansense-detector"
    model_version: str = "1.0.0"
    tracking_id: str | None = None
    frame_number: int | None = None
    frame_id: int | None = None
    evidence_id: UUID | None = None
    metadata: dict = {}


# Road Defect Schemas
class DefectIn(BaseModel):
    defect_type: str = "POTHOLE"
    severity: str = "MEDIUM"
    status: str = "OPEN"
    description: str | None = None
    confidence: float = Field(default=0.8, ge=0, le=1)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    bus_id: UUID | None = None
    detected_by_bus_id: UUID | None = None
    evidence_id: UUID | None = None
    model_name: str | None = None
    model_version: str | None = None
    metadata: dict = {}


class DefectUpdate(BaseModel):
    severity: str | None = None
    status: str | None = None
    description: str | None = None
    resolved_at: datetime | None = None
    resolved_by: UUID | None = None


# Traffic Schemas
class TrafficIn(BaseModel):
    event_type: TrafficEventType = TrafficEventType.CONGESTION
    severity: TrafficSeverity | None = None
    traffic_density: Density = Density.MEDIUM
    description: str | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    bus_id: UUID | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    cars: int = 0
    bikes: int = 0
    buses: int = 0
    trucks: int = 0
    autos: int = 0
    average_speed: float | None = None
    model_name: str | None = None
    model_version: str | None = None
    metadata: dict = {}


# Incident Schemas
class IncidentIn(BaseModel):
    incident_type: IncidentType = IncidentType.ROAD_HAZARD
    severity: IncidentSeverity | None = None
    priority: Priority = Priority.MEDIUM
    status: IncidentStatus = IncidentStatus.OPEN
    title: str | None = None
    description: str | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    bus_id: UUID | None = None
    route_id: UUID | None = None
    vehicle_id: UUID | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    detected_at: datetime | None = None
    metadata: dict = {}


class IncidentStatusIn(BaseModel):
    status: str


class StatusIn(BaseModel):
    status: str


# Citizen Report Schemas
class ReportIn(BaseModel):
    problem_type: str | None = None
    report_type: str = "OTHER"
    title: str | None = None
    description: str | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    priority: ReportPriority = ReportPriority.MEDIUM
    image_url: str | None = None
    metadata: dict = {}


class ReportUpdate(BaseModel):
    status: str | None = None
    priority: ReportPriority | None = None
    description: str | None = None
    resolved_at: datetime | None = None


# Notification Schemas
class NotificationIn(BaseModel):
    user_id: UUID
    notification_type: NotificationType = NotificationType.ALERT
    title: str = Field(min_length=1, max_length=200)
    message: str | None = None
    body: str | None = None
    metadata: dict = {}


# Vehicle Schemas
class VehicleIn(BaseModel):
    plate_number: str | None = None
    vehicle_type: VehicleType = VehicleType.CAR
    make: str | None = None
    model: str | None = None
    color: str | None = None
    tracking_id: str | None = None
    ocr_confidence: float | None = Field(default=None, ge=0, le=1)
    ocr_status: str | None = None
    metadata: dict = {}


class VehicleDetectionIn(BaseModel):
    vehicle_id: UUID
    bus_id: UUID | None = None
    detection_type: str | None = None
    vehicle_type: VehicleType | None = None
    confidence: float = Field(ge=0, le=1)
    tracking_id: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    model_name: str | None = None
    model_version: str | None = None
    metadata: dict = {}


# Model Version Registry Schema
class ModelVersionIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    version: str = Field(min_length=1, max_length=80)
    model_type: AIModelType = AIModelType.OBJECT_DETECTION
    framework: str | None = None
    file_reference: str | None = None
    is_active: bool = True
    metadata: dict = {}


# Proximity Geospatial Query
class ProximityQuery(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    radius_meters: float = Field(default=5000.0, gt=0, le=100000.0)
    limit: int = Field(default=100, ge=1, le=1000)
