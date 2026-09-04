import asyncio
from datetime import datetime, timezone, timedelta
import random
from app.db.session import AsyncSessionLocal, engine, Base
from app.models import (
    AIModelType,
    AuditLog,
    Bus,
    BusLocation,
    BusStatus,
    CitizenReport,
    CitizenReportStatus,
    CitizenReportType,
    DefectSeverity,
    DefectStatus,
    Detection,
    DetectionType,
    Driver,
    DriverStatus,
    Incident,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
    ModelVersion,
    Notification,
    NotificationType,
    ReportPriority,
    RoadDefect,
    RoadDefectType,
    Role,
    Route,
    TrafficEvent,
    TrafficEventType,
    TrafficSeverity,
    User,
    Vehicle,
    VehicleDetection,
    VehicleType,
    utc_now,
)
from app.core.security import hash_password


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # 1. Demo Users
        password_hash = hash_password('ChangeMe123!')
        admin = User(
            name='System Administrator',
            email='admin@urbansense.local',
            password_hash=password_hash,
            role=Role.ADMIN,
            phone='+15550000001',
            is_active=True,
            is_verified=True,
        )
        authority = User(
            name='Transit Authority Officer',
            email='authority@urbansense.local',
            password_hash=password_hash,
            role=Role.AUTHORITY,
            phone='+15550000002',
            is_active=True,
            is_verified=True,
        )
        driver_user = User(
            name='Fleet Lead Driver',
            email='driver@urbansense.local',
            password_hash=password_hash,
            role=Role.DRIVER,
            phone='+15550000003',
            is_active=True,
            is_verified=True,
        )
        citizen = User(
            name='Jane Citizen',
            email='citizen@urbansense.local',
            password_hash=password_hash,
            role=Role.CITIZEN,
            phone='+15550000004',
            is_active=True,
            is_verified=True,
        )
        db.add_all([admin, authority, driver_user, citizen])
        await db.flush()

        # 2. Driver profile
        driver = Driver(
            user_id=driver_user.id,
            employee_id='EMP-9001',
            license_number='DL-9988776655',
            status=DriverStatus.ACTIVE,
            phone='+15550000003',
        )
        db.add(driver)
        await db.flush()

        # 3. 5 Routes
        routes = []
        for i in range(1, 6):
            route = Route(
                route_number=f'R{i:02d}',
                name=f'Metropolitan Corridor Route {i}',
                origin=f'Terminal {chr(64+i)} North',
                destination=f'Station {chr(64+i)} South',
                description=f'High density rapid bus line {i}',
                geometry_wkt=f'LINESTRING(-122.41{i} 37.77{i}, -122.42{i} 37.78{i})',
                is_active=True,
            )
            routes.append(route)
            db.add(route)
        await db.flush()

        # 4. 10 Buses
        buses = []
        for i in range(1, 11):
            bus = Bus(
                fleet_number=f'BUS-{i:03d}',
                registration_number=f'WB{i:02d}AB{1000+i}',
                operator_name='Metro Urban Transport',
                model='Volvo 7900 Hybrid',
                manufacturer='Volvo Buses',
                year=2024,
                capacity=65,
                assigned_route_id=routes[(i - 1) % 5].id,
                assigned_driver_id=driver.id if i == 1 else None,
                status=BusStatus.ACTIVE if i <= 8 else BusStatus.INACTIVE,
                is_active=True,
            )
            buses.append(bus)
            db.add(bus)
        await db.flush()

        # 5. 100 Bus GPS Locations
        base_lat, base_lon = 37.7749, -122.4194
        now_time = utc_now()
        locations = []
        for i in range(100):
            bus = buses[i % len(buses)]
            time_offset = now_time - timedelta(minutes=100 - i)
            lat = base_lat + (random.random() - 0.5) * 0.08
            lon = base_lon + (random.random() - 0.5) * 0.08
            locations.append(
                BusLocation(
                    bus_id=bus.id,
                    latitude=lat,
                    longitude=lon,
                    speed=round(random.uniform(10.0, 45.0), 1),
                    heading=round(random.uniform(0.0, 360.0), 1),
                    accuracy=round(random.uniform(1.0, 5.0), 1),
                    altitude=round(random.uniform(10.0, 60.0), 1),
                    recorded_at=time_offset,
                    source='GPS',
                )
            )
        db.add_all(locations)

        # 6. 20 Road Defects
        defect_types = list(RoadDefectType)
        severities = list(DefectSeverity)
        defect_statuses = [DefectStatus.OPEN, DefectStatus.VERIFIED, DefectStatus.IN_PROGRESS, DefectStatus.RESOLVED]
        defects = []
        for i in range(20):
            dtype = defect_types[i % len(defect_types)]
            sev = severities[i % len(severities)]
            st = defect_statuses[i % len(defect_statuses)]
            d_lat = base_lat + (random.random() - 0.5) * 0.09
            d_lon = base_lon + (random.random() - 0.5) * 0.09
            defects.append(
                RoadDefect(
                    defect_type=dtype,
                    severity=sev,
                    status=st,
                    description=f'Identified {dtype.value.lower()} anomaly at intersection {i+1}',
                    latitude=d_lat,
                    longitude=d_lon,
                    confidence=round(random.uniform(0.75, 0.98), 2),
                    detected_by_bus_id=buses[i % len(buses)].id,
                    model_name='yolov8-road-inspector',
                    model_version='v2.1.0',
                    detected_at=now_time - timedelta(hours=20 - i),
                )
            )
        db.add_all(defects)

        # 7. 50 Traffic Events
        event_types = list(TrafficEventType)
        traffic_events = []
        for i in range(50):
            etype = event_types[i % len(event_types)]
            t_sev = severities[i % len(severities)]
            cars_c = random.randint(10, 60)
            bikes_c = random.randint(5, 25)
            buses_c = random.randint(1, 8)
            trucks_c = random.randint(1, 12)
            autos_c = random.randint(2, 15)
            traffic_events.append(
                TrafficEvent(
                    event_type=etype,
                    severity=t_sev,
                    description=f'Traffic congestion flow report {i+1}',
                    latitude=base_lat + (random.random() - 0.5) * 0.1,
                    longitude=base_lon + (random.random() - 0.5) * 0.1,
                    bus_id=buses[i % len(buses)].id,
                    confidence=round(random.uniform(0.8, 0.99), 2),
                    cars=cars_c,
                    bikes=bikes_c,
                    buses_count=buses_c,
                    trucks=trucks_c,
                    autos=autos_c,
                    total_vehicles=cars_c + bikes_c + buses_c + trucks_c + autos_c,
                    average_speed=round(random.uniform(5.0, 35.0), 1),
                    model_name='bytetrack-traffic-analyzer',
                    model_version='v1.4.0',
                    detected_at=now_time - timedelta(minutes=(50 - i) * 10),
                )
            )
        db.add_all(traffic_events)

        # 8. 10 Incidents
        incident_types = [
            IncidentType.ACCIDENT,
            IncidentType.ROAD_HAZARD,
            IncidentType.WATERLOGGING,
            IncidentType.TRAFFIC,
            IncidentType.MEDICAL,
            IncidentType.FIRE,
            IncidentType.SECURITY,
        ]
        incidents = []
        for i in range(10):
            itype = incident_types[i % len(incident_types)]
            isev = severities[i % len(severities)]
            incidents.append(
                Incident(
                    incident_type=itype,
                    severity=isev,
                    status=IncidentStatus.OPEN if i < 6 else IncidentStatus.RESOLVED,
                    title=f'Urgent {itype.value.replace("_", " ").title()} Event #{i+1}',
                    description=f'Live incident alert triggered from vehicle sensors in corridor {i+1}',
                    latitude=base_lat + (random.random() - 0.5) * 0.06,
                    longitude=base_lon + (random.random() - 0.5) * 0.06,
                    bus_id=buses[i % len(buses)].id,
                    route_id=routes[i % len(routes)].id,
                    reported_by=admin.id,
                    confidence=round(random.uniform(0.85, 0.99), 2),
                    detected_at=now_time - timedelta(hours=10 - i),
                )
            )
        db.add_all(incidents)

        # 9. AI Model Versions
        model_versions = [
            ModelVersion(
                name='yolov8-urban-detector',
                version='v1.0.0',
                model_type=AIModelType.OBJECT_DETECTION,
                framework='PyTorch',
                file_reference='s3://urbansense-models/yolov8_urban_v1.0.0.onnx',
                is_active=True,
            ),
            ModelVersion(
                name='paddleocr-anpr',
                version='v2.2.0',
                model_type=AIModelType.ANPR,
                framework='PaddleOCR',
                file_reference='s3://urbansense-models/paddleocr_anpr_v2.2.0.tar',
                is_active=True,
            ),
        ]
        db.add_all(model_versions)

        await db.commit()

    print("""
================================================================================
AI UrbanSense Database Seeded Successfully!
--------------------------------------------------------------------------------
Demo Accounts:
* Admin:     admin@urbansense.local     / ChangeMe123!
* Authority: authority@urbansense.local / ChangeMe123!
* Driver:    driver@urbansense.local    / ChangeMe123!
* Citizen:   citizen@urbansense.local   / ChangeMe123!

Seeded Data:
* 4 Demo Users + 1 Driver Profile
* 5 Transit Routes with PostGIS Geometries
* 10 Buses (8 Active, 2 Inactive)
* 100 Bus GPS Telemetry Points
* 20 Road Defects (Potholes, Waterlogging, Cracks)
* 50 Traffic Events with Vehicle Aggregations
* 10 Critical Transit Incidents
* 2 AI Model Version Registries
================================================================================
""")


if __name__ == '__main__':
    asyncio.run(seed())
