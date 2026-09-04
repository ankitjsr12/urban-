import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import CheckConstraint, UniqueConstraint, inspect
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models import (
    AIModelType,
    AuditLog,
    Base,
    Bus,
    BusLocation,
    BusStatus,
    CitizenReport,
    CitizenReportStatus,
    CitizenReportType,
    DefectSeverity,
    DefectStatus,
    Density,
    Detection,
    DetectionType,
    Driver,
    DriverStatus,
    EvidenceType,
    Incident,
    IncidentEvidence,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
    ModelVersion,
    Notification,
    NotificationType,
    Priority,
    RefreshToken,
    RoadDefect,
    RoadDefectType,
    Role,
    Route,
    SoftDeleteMixin,
    StorageProvider,
    SyncEvent,
    TimestampMixin,
    TrafficEvent,
    TrafficEventType,
    TrafficSeverity,
    UUIDPrimaryKeyMixin,
    User,
    Vehicle,
    VehicleDetection,
    VehicleType,
    generate_uuid,
    utc_now,
)


def test_base_mixins():
    now_dt = utc_now()
    assert now_dt.tzinfo is not None
    assert now_dt.tzinfo == timezone.utc

    new_id = generate_uuid()
    assert isinstance(new_id, uuid.UUID)


def test_user_model_instantiation_and_properties():
    user = User(
        name="Transit Authority Admin",
        email="admin@citytransit.gov",
        password_hash="$argon2id$v=19$m=65536,t=3,p=4$fakehash",
        role=Role.AUTHORITY,
        phone="+15551234567",
    )
    assert user.full_name == "Transit Authority Admin"
    assert user.name == "Transit Authority Admin"
    assert user.email == "admin@citytransit.gov"
    assert user.role == Role.AUTHORITY
    assert user.is_active is True
    assert user.is_verified is False
    assert user.password_hash.startswith("$argon2id$")

    # Name property setter
    user.name = "Updated Admin Name"
    assert user.full_name == "Updated Admin Name"


def test_user_table_metadata():
    table = User.__table__
    assert table.name == "users"
    assert "email" in table.c
    assert table.c.email.unique is True or any(
        isinstance(i, UniqueConstraint) and "email" in [c.name for c in i.columns]
        for i in table.constraints
    )
    assert "password_hash" in table.c
    assert "full_name" in table.c
    assert "role" in table.c


def test_driver_model():
    user_id = uuid.uuid4()
    driver = Driver(
        user_id=user_id,
        employee_id="DRV-90210",
        license_number="DL-NY-987654321",
        status=DriverStatus.ACTIVE,
        phone="+15559876543",
    )
    assert driver.user_id == user_id
    assert driver.employee_id == "DRV-90210"
    assert driver.license_number == "DL-NY-987654321"
    assert driver.status == DriverStatus.ACTIVE

    table = Driver.__table__
    assert table.name == "drivers"
    assert table.c.user_id.unique is True


def test_bus_model_and_backward_compatibility():
    bus = Bus(
        bus_number="BUS-501",
        registration_number="CA-BUS-501",
        capacity=60,
        status=BusStatus.ACTIVE,
        operator_name="Metro Transit",
    )
    assert bus.fleet_number == "BUS-501"
    assert bus.bus_number == "BUS-501"
    assert bus.registration_number == "CA-BUS-501"
    assert bus.capacity == 60
    assert bus.status == BusStatus.ACTIVE

    table = Bus.__table__
    check_constraints = [c for c in table.constraints if isinstance(c, CheckConstraint)]
    assert any("chk_bus_capacity_positive" in c.name for c in check_constraints)


def test_route_model_and_geometry():
    route = Route(
        code="R-101",
        name="Downtown Express",
        origin="Central Terminal",
        destination="Tech Campus",
        description="High frequency rapid transit route",
    )
    assert route.route_number == "R-101"
    assert route.code == "R-101"
    assert route.name == "Downtown Express"

    table = Route.__table__
    assert "geometry" in table.c
    assert str(table.c.geometry.type).lower().startswith("geometry")
    assert table.c.geometry.type.geometry_type == "LINESTRING"
    assert table.c.geometry.type.srid == 4326


def test_bus_location_model():
    bus_id = uuid.uuid4()
    loc = BusLocation(
        bus_id=bus_id,
        latitude=37.7749,
        longitude=-122.4194,
        speed=14.5,
        heading=180.0,
        accuracy=2.5,
        source="GPS_TELEMETRY",
    )
    assert loc.bus_id == bus_id
    assert loc.latitude == 37.7749
    assert loc.longitude == -122.4194
    assert loc.speed == 14.5
    assert loc.heading == 180.0
    assert loc.timestamp is not None

    table = BusLocation.__table__
    assert "location" in table.c
    assert str(table.c.location.type).lower().startswith("geography")
    assert table.c.location.type.geometry_type == "POINT"
    assert table.c.location.type.srid == 4326
    index_names = [i.name for i in table.indexes]
    assert "ix_bus_locations_bus_id_recorded_at" in index_names


def test_detection_model():
    bus_id = uuid.uuid4()
    det = Detection(
        bus_id=bus_id,
        detection_type=DetectionType.POTHOLE,
        confidence=0.94,
        latitude=37.7749,
        longitude=-122.4194,
        model_name="yolov8-road-inspector",
        model_version="v2.1.0",
        frame_number=1420,
        metadata={"area_sqm": 0.45, "depth_est_cm": 6.2},
    )
    assert det.bus_id == bus_id
    assert det.detection_type == DetectionType.POTHOLE
    assert det.confidence == 0.94
    assert det.model_name == "yolov8-road-inspector"
    assert det.frame_id == 1420
    assert det.frame_number == 1420
    assert det.metadata_json["depth_est_cm"] == 6.2

    table = Detection.__table__
    check_constraints = [c for c in table.constraints if isinstance(c, CheckConstraint)]
    assert any("chk_detection_confidence_range" in c.name for c in check_constraints)
    index_names = [i.name for i in table.indexes]
    assert "ix_detections_bus_id_detected_at" in index_names
    assert "ix_detections_type_detected_at" in index_names


def test_road_defect_model():
    bus_id = uuid.uuid4()
    defect = RoadDefect(
        defect_type=RoadDefectType.WATERLOGGING,
        severity=DefectSeverity.HIGH,
        status=DefectStatus.OPEN,
        description="Deep standing water across 2 lanes",
        latitude=37.7749,
        longitude=-122.4194,
        confidence=0.88,
        bus_id=bus_id,
        model_name="flood-detector",
        model_version="v1.0",
    )
    assert defect.defect_type == RoadDefectType.WATERLOGGING
    assert defect.severity == DefectSeverity.HIGH
    assert defect.status == DefectStatus.OPEN
    assert defect.detected_by_bus_id == bus_id
    assert defect.bus_id == bus_id

    table = RoadDefect.__table__
    check_constraints = [c for c in table.constraints if isinstance(c, CheckConstraint)]
    assert any("chk_road_defect_confidence_range" in c.name for c in check_constraints)


def test_vehicle_and_vehicle_detection_models():
    vehicle = Vehicle(
        plate_number="7XYZ123",
        vehicle_type=VehicleType.CAR,
        make="Toyota",
        model="Prius",
        color="Silver",
        ocr_confidence=0.96,
        ocr_status="VERIFIED",
    )
    assert vehicle.plate_number == "7XYZ123"
    assert vehicle.vehicle_type == VehicleType.CAR
    assert vehicle.ocr_confidence == 0.96

    veh_id = uuid.uuid4()
    vd = VehicleDetection(
        vehicle_id=veh_id,
        vehicle_type=VehicleType.CAR,
        confidence=0.92,
        tracking_id="TRK-8802",
        latitude=37.7749,
        longitude=-122.4194,
        model_name="bytetrack-anpr",
        model_version="v3.0",
    )
    assert vd.vehicle_id == veh_id
    assert vd.confidence == 0.92
    assert vd.tracking_id == "TRK-8802"

    table = VehicleDetection.__table__
    check_constraints = [c for c in table.constraints if isinstance(c, CheckConstraint)]
    assert any("chk_vehicle_detection_confidence_range" in c.name for c in check_constraints)


def test_traffic_event_model():
    event = TrafficEvent(
        event_type=TrafficEventType.CONGESTION,
        traffic_density=Density.CRITICAL,
        description="Severe bottleneck at junction 4",
        latitude=37.7749,
        longitude=-122.4194,
        cars=45,
        bikes=12,
        buses=4,
        trucks=8,
        autos=10,
        total_vehicles=79,
        average_speed=8.2,
    )
    assert event.event_type == TrafficEventType.CONGESTION
    assert event.severity == TrafficSeverity.CRITICAL
    assert event.traffic_density == TrafficSeverity.CRITICAL
    assert event.cars == 45
    assert event.buses == 4
    assert event.buses_count == 4
    assert event.total_vehicles == 79


def test_incident_and_evidence_models():
    user_id = uuid.uuid4()
    bus_id = uuid.uuid4()
    incident = Incident(
        incident_type=IncidentType.ACCIDENT,
        priority=Priority.CRITICAL,
        status=IncidentStatus.OPEN,
        title="Bus-Car Minor Collision",
        description="Collision occurred near bus stop 14",
        latitude=37.7749,
        longitude=-122.4194,
        created_by=user_id,
        bus_id=bus_id,
        confidence=0.91,
    )
    assert incident.incident_type == IncidentType.ACCIDENT
    assert incident.severity == IncidentSeverity.CRITICAL
    assert incident.priority == IncidentSeverity.CRITICAL
    assert incident.reported_by == user_id
    assert incident.created_by == user_id
    assert incident.bus_id == bus_id

    inc_id = uuid.uuid4()
    evidence = IncidentEvidence(
        incident_id=inc_id,
        storage_provider=StorageProvider.MINIO,
        object_key="incidents/2026/09/02/evidence_001.mp4",
        file_url="http://localhost:9000/urbansense-evidence/incidents/2026/09/02/evidence_001.mp4",
        file_type="video/mp4",
        mime_type="video/mp4",
        file_size=15420000,
        checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        duration_seconds=12.5,
    )
    assert evidence.incident_id == inc_id
    assert evidence.storage_provider == StorageProvider.MINIO
    assert evidence.object_url.startswith("http://localhost:9000")
    assert evidence.file_url == evidence.object_url
    assert evidence.file_size == 15420000


def test_citizen_report_model():
    citizen_id = uuid.uuid4()
    report = CitizenReport(
        citizen_id=citizen_id,
        problem_type="POTHOLE",
        title="Deep pothole on 5th Ave",
        description="Hazardous pothole causing traffic swerving",
        latitude=37.7749,
        longitude=-122.4194,
        status=CitizenReportStatus.SUBMITTED.value,
        image_url="http://localhost:9000/reports/img_123.jpg",
    )
    assert report.citizen_id == citizen_id
    assert report.report_type == "POTHOLE"
    assert report.problem_type == "POTHOLE"
    assert report.status == "SUBMITTED"


def test_notification_model():
    user_id = uuid.uuid4()
    notif = Notification(
        user_id=user_id,
        notification_type=NotificationType.ALERT,
        title="Critical Weather Alert",
        body="Flash flood warning issued for Sector 7 route",
    )
    assert notif.user_id == user_id
    assert notif.notification_type == NotificationType.ALERT
    assert notif.message == "Flash flood warning issued for Sector 7 route"
    assert notif.body == "Flash flood warning issued for Sector 7 route"
    assert notif.is_read is False


def test_audit_log_model():
    user_id = uuid.uuid4()
    log = AuditLog(
        user_id=user_id,
        action="ROUTE_MODIFIED",
        resource_type="Route",
        resource_id="R-101",
        ip_address="192.168.1.100",
        metadata={"changes": ["origin changed"]},
    )
    assert log.user_id == user_id
    assert log.action == "ROUTE_MODIFIED"
    assert log.metadata_json["changes"] == ["origin changed"]


def test_model_version_model():
    mv = ModelVersion(
        name="yolov8-urban-defect",
        version="v1.4.2",
        model_type=AIModelType.ROAD_DEFECT,
        framework="PyTorch",
        file_reference="s3://models/yolov8_defect_v1.4.2.pt",
        is_active=True,
    )
    assert mv.name == "yolov8-urban-defect"
    assert mv.version == "v1.4.2"
    assert mv.model_type == AIModelType.ROAD_DEFECT

    table = ModelVersion.__table__
    unique_constraints = [c for c in table.constraints if isinstance(c, UniqueConstraint)]
    assert any("uq_model_versions_name_version" in c.name for c in unique_constraints)


def test_all_models_registered_in_metadata():
    expected_tables = {
        "users",
        "refresh_tokens",
        "drivers",
        "buses",
        "routes",
        "bus_locations",
        "sync_events",
        "detections",
        "road_defects",
        "vehicles",
        "vehicle_detections",
        "traffic_events",
        "incidents",
        "incident_evidence",
        "citizen_reports",
        "notifications",
        "audit_logs",
        "model_versions",
    }
    actual_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(actual_tables), f"Missing tables: {expected_tables - actual_tables}"
