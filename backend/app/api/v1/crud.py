import enum
import math
import hashlib
from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy import select, func, update, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.api.deps import current_user, require_roles
from app.models import (
    AuditLog,
    Base,
    Bus,
    BusLocation,
    BusStatus,
    CitizenReport,
    CitizenReportStatus,
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
    RoadDefect,
    RoadDefectType,
    Role,
    Route,
    StorageProvider,
    SyncEvent,
    TrafficEvent,
    TrafficEventType,
    TrafficSeverity,
    User,
    Vehicle,
    VehicleDetection,
    VehicleType,
    utc_now,
)
from app.schemas.common import Envelope, Page
from app.schemas.domain import (
    BusIn,
    BusUpdate,
    CitizenReportType,
    DefectIn,
    DefectUpdate,
    DetectionIn,
    DriverAssignIn,
    DriverIn,
    DriverUpdate,
    IncidentIn,
    LocationIn,
    ModelVersionIn,
    NotificationIn,
    ReportIn,
    ReportPriority,
    ReportUpdate,
    RouteIn,
    RouteUpdate,
    StatusIn,
    TrafficIn,
    VehicleDetectionIn,
    VehicleIn,
)
from app.services.storage import get_storage
from app.services.audit import AuditService
from app.services.notifications import NotificationService
from app.websocket.manager import manager

router = APIRouter(tags=['Urban Intelligence'])


def out(x):
    """Serialize SQLAlchemy model attributes safely."""
    if x is None:
        return None
    d = {k: v for k, v in x.__dict__.items() if not k.startswith('_')}
    for k, v in list(d.items()):
        if isinstance(v, UUID):
            d[k] = str(v)
        elif isinstance(v, datetime):
            d[k] = v.isoformat()
        elif isinstance(v, enum.Enum):
            d[k] = v.value
        elif hasattr(v, 'data') or 'WKBElement' in type(v).__name__:
            d[k] = f"POINT({d.get('longitude')} {d.get('latitude')})" if 'longitude' in d and 'latitude' in d else str(v)
    # Add backward compatible aliases
    if 'fleet_number' in d and 'bus_number' not in d:
        d['bus_number'] = d['fleet_number']
    if 'route_number' in d and 'code' not in d:
        d['code'] = d['route_number']
    if 'recorded_at' in d and 'timestamp' not in d:
        d['timestamp'] = d['recorded_at']
    if 'detected_at' in d and 'timestamp' not in d:
        d['timestamp'] = d['detected_at']
    if 'detected_by_bus_id' in d and 'bus_id' not in d:
        d['bus_id'] = d['detected_by_bus_id']
    if 'buses_count' in d and 'buses' not in d:
        d['buses'] = d['buses_count']
    if 'object_url' in d and 'file_url' not in d:
        d['file_url'] = d['object_url']
    if 'report_type' in d and 'problem_type' not in d:
        d['problem_type'] = d['report_type']
    if 'message' in d and 'body' not in d:
        d['body'] = d['message']
    if 'severity' in d and 'priority' not in d:
        d['priority'] = d['severity']
    if 'severity' in d and 'traffic_density' not in d:
        d['traffic_density'] = d['severity']
    if 'full_name' in d and 'name' not in d:
        d['name'] = d['full_name']
    if 'metadata_json' in d and 'metadata' not in d:
        d['metadata'] = d['metadata_json']
    return d


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance between two GPS coordinates in km."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


async def list_rows(model, db: AsyncSession, limit: int, offset: int, where=None, order_by=None):
    q = select(model)
    if where is not None:
        q = q.where(where)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()

    if order_by is None:
        if hasattr(model, 'created_at'):
            order_by = model.created_at.desc()
        elif hasattr(model, 'detected_at'):
            order_by = model.detected_at.desc()
        elif hasattr(model, 'recorded_at'):
            order_by = model.recorded_at.desc()
        elif hasattr(model, 'timestamp'):
            order_by = model.timestamp.desc()
        else:
            order_by = model.id.desc()

    rows = (await db.execute(q.order_by(order_by).limit(limit).offset(offset))).scalars().all()
    return {'items': [out(x) for x in rows], 'total': total, 'limit': limit, 'offset': offset}


# ============================================================================
# FLEET MANAGEMENT: BUSES
# ============================================================================

@router.post('/buses', response_model=Envelope[dict], status_code=status.HTTP_201_CREATED)
async def create_bus(
    data: BusIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUTHORITY)),
):
    fleet_num = data.fleet_number or data.bus_number or f"BUS-{data.registration_number[-4:]}"
    existing = (
        await db.execute(
            select(Bus).where(
                or_(
                    Bus.registration_number == data.registration_number,
                    Bus.fleet_number == fleet_num,
                )
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Bus registration or fleet number already exists')

    driver_id = data.assigned_driver_id or data.driver_id
    route_id = data.assigned_route_id or data.route_id

    bus = Bus(
        registration_number=data.registration_number,
        fleet_number=fleet_num,
        operator_name=data.operator_name,
        model=data.model,
        manufacturer=data.manufacturer,
        year=data.year,
        capacity=data.capacity,
        status=data.status,
        assigned_driver_id=driver_id,
        assigned_route_id=route_id,
    )
    db.add(bus)
    await db.commit()
    await db.refresh(bus)
    return {'data': out(bus)}


@router.get('/buses', response_model=Envelope[dict])
async def list_buses(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status_filter: BusStatus | None = Query(None, alias='status'),
    route_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    where = None
    if status_filter is not None:
        where = (Bus.status == status_filter)
    if route_id is not None:
        where = (where & (Bus.assigned_route_id == route_id)) if where is not None else (Bus.assigned_route_id == route_id)
    return {'data': await list_rows(Bus, db, limit, offset, where=where)}


@router.get('/locations/nearby', response_model=Envelope[dict])
@router.get('/buses/nearby', response_model=Envelope[dict])
async def get_nearby_buses(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(5.0, gt=0, le=100.0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """Calculates nearby active buses using geographic coordinate distance."""
    # Subquery latest location per bus
    subq = (
        select(
            BusLocation.bus_id,
            func.max(BusLocation.recorded_at).label('max_time'),
        )
        .group_by(BusLocation.bus_id)
        .subquery()
    )
    q = (
        select(BusLocation)
        .join(subq, (BusLocation.bus_id == subq.c.bus_id) & (BusLocation.recorded_at == subq.c.max_time))
    )
    rows = (await db.execute(q)).scalars().all()

    nearby_results = []
    for loc in rows:
        dist = haversine_distance_km(latitude, longitude, loc.latitude, loc.longitude)
        if dist <= radius_km:
            loc_dict = out(loc)
            loc_dict['distance_km'] = round(dist, 3)
            nearby_results.append(loc_dict)

    nearby_results.sort(key=lambda item: item['distance_km'])
    return {'data': {'items': nearby_results[:limit], 'total': len(nearby_results), 'radius_km': radius_km}}


@router.get('/buses/{bus_id}', response_model=Envelope[dict])
async def get_bus(bus_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    bus = await db.get(Bus, bus_id)
    if not bus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Bus not found')
    return {'data': out(bus)}


@router.patch('/buses/{bus_id}', response_model=Envelope[dict])
async def update_bus(
    bus_id: UUID,
    data: BusUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUTHORITY)),
):
    bus = await db.get(Bus, bus_id)
    if not bus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Bus not found')

    update_dict = data.model_dump(exclude_unset=True, exclude_none=True)
    for k, v in update_dict.items():
        setattr(bus, k, v)

    await db.commit()
    await db.refresh(bus)
    return {'data': out(bus)}


@router.delete('/buses/{bus_id}', response_model=Envelope[dict])
async def delete_bus(
    bus_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN)),
):
    bus = await db.get(Bus, bus_id)
    if not bus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Bus not found')
    bus.is_active = False
    bus.status = BusStatus.INACTIVE
    await db.commit()
    return {'data': {'id': str(bus_id), 'is_active': False}, 'message': 'Bus deactivated successfully'}


@router.get('/buses/{bus_id}/status', response_model=Envelope[dict])
async def get_bus_status(bus_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    bus = await db.get(Bus, bus_id)
    if not bus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Bus not found')
    latest_loc = (
        await db.execute(
            select(BusLocation).where(BusLocation.bus_id == bus_id).order_by(BusLocation.recorded_at.desc()).limit(1)
        )
    ).scalar_one_or_none()

    return {
        'data': {
            'bus_id': str(bus.id),
            'fleet_number': bus.fleet_number,
            'status': bus.status.value,
            'is_active': bus.is_active,
            'last_location': out(latest_loc) if latest_loc else None,
        }
    }


# ============================================================================
# FLEET MANAGEMENT: DRIVERS
# ============================================================================

@router.post('/drivers', response_model=Envelope[dict], status_code=status.HTTP_201_CREATED)
async def create_driver(
    data: DriverIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUTHORITY)),
):
    existing = (
        await db.execute(
            select(Driver).where(
                or_(
                    Driver.user_id == data.user_id,
                    Driver.employee_id == data.employee_id,
                    Driver.license_number == data.license_number,
                )
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Driver with given user, employee ID or license already exists')

    driver = Driver(**data.model_dump())
    db.add(driver)
    await db.commit()
    await db.refresh(driver)
    return {'data': out(driver)}


@router.get('/drivers', response_model=Envelope[dict])
async def list_drivers(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status_filter: DriverStatus | None = Query(None, alias='status'),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUTHORITY)),
):
    where = (Driver.status == status_filter) if status_filter else None
    return {'data': await list_rows(Driver, db, limit, offset, where=where)}


@router.get('/drivers/{driver_id}', response_model=Envelope[dict])
async def get_driver(driver_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN, Role.AUTHORITY))):
    driver = await db.get(Driver, driver_id)
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Driver not found')
    return {'data': out(driver)}


@router.patch('/drivers/{driver_id}', response_model=Envelope[dict])
async def update_driver(
    driver_id: UUID,
    data: DriverUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUTHORITY)),
):
    driver = await db.get(Driver, driver_id)
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Driver not found')

    update_dict = data.model_dump(exclude_unset=True, exclude_none=True)
    for k, v in update_dict.items():
        setattr(driver, k, v)
    await db.commit()
    await db.refresh(driver)
    return {'data': out(driver)}


@router.post('/drivers/{driver_id}/assign', response_model=Envelope[dict])
async def assign_driver(
    driver_id: UUID,
    data: DriverAssignIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUTHORITY)),
):
    driver = await db.get(Driver, driver_id)
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Driver not found')

    if data.bus_id:
        bus = await db.get(Bus, data.bus_id)
        if not bus:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Bus not found')
        bus.assigned_driver_id = driver.id
        await db.commit()
        await db.refresh(bus)
        return {'data': {'driver_id': str(driver_id), 'assigned_bus_id': str(bus.id)}, 'message': 'Driver assigned to bus'}
    else:
        # Unassign driver from any assigned buses
        await db.execute(update(Bus).where(Bus.assigned_driver_id == driver_id).values(assigned_driver_id=None))
        await db.commit()
        return {'data': {'driver_id': str(driver_id), 'assigned_bus_id': None}, 'message': 'Driver unassigned from all buses'}


# ============================================================================
# FLEET MANAGEMENT: ROUTES
# ============================================================================

@router.post('/routes', response_model=Envelope[dict], status_code=status.HTTP_201_CREATED)
async def create_route(
    data: RouteIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUTHORITY)),
):
    route_num = data.route_number or data.code or f"R-{uuid.uuid4().hex[:4].upper()}"
    existing = (await db.execute(select(Route).where(Route.route_number == route_num))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Route number already exists')

    geom = f"SRID=4326;{data.geometry_wkt}" if data.geometry_wkt else None
    route = Route(
        route_number=route_num,
        name=data.name,
        description=data.description,
        origin=data.origin,
        destination=data.destination,
        geometry=geom,
        is_active=data.is_active,
    )
    db.add(route)
    await db.commit()
    await db.refresh(route)
    return {'data': out(route)}


@router.get('/routes', response_model=Envelope[dict])
async def list_routes(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    where = (Route.is_active == is_active) if is_active is not None else None
    return {'data': await list_rows(Route, db, limit, offset, where=where)}


@router.get('/routes/{route_id}', response_model=Envelope[dict])
async def get_route(route_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    route = await db.get(Route, route_id)
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Route not found')
    return {'data': out(route)}


@router.patch('/routes/{route_id}', response_model=Envelope[dict])
async def update_route(
    route_id: UUID,
    data: RouteUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUTHORITY)),
):
    route = await db.get(Route, route_id)
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Route not found')

    update_dict = data.model_dump(exclude_unset=True, exclude_none=True)
    if 'geometry_wkt' in update_dict:
        wkt = update_dict.pop('geometry_wkt')
        route.geometry = f"SRID=4326;{wkt}" if wkt else None

    for k, v in update_dict.items():
        setattr(route, k, v)

    await db.commit()
    await db.refresh(route)
    return {'data': out(route)}


@router.delete('/routes/{route_id}', response_model=Envelope[dict])
async def delete_route(
    route_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN)),
):
    route = await db.get(Route, route_id)
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Route not found')
    route.is_active = False
    await db.commit()
    return {'data': {'id': str(route_id), 'is_active': False}, 'message': 'Route deactivated'}


# ============================================================================
# GPS & TELEMETRY
# ============================================================================

@router.post('/locations', response_model=Envelope[dict])
async def record_location(data: LocationIn, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    if data.client_event_id:
        duplicate = (
            await db.execute(select(BusLocation).where(BusLocation.client_event_id == data.client_event_id))
        ).scalar_one_or_none()
        if duplicate:
            return {'data': {'duplicate': True, 'id': str(duplicate.id)}}

    x = BusLocation(
        bus_id=data.bus_id,
        latitude=data.latitude,
        longitude=data.longitude,
        speed=data.speed,
        heading=data.heading,
        accuracy=data.accuracy,
        altitude=data.altitude,
        source=data.source or 'GPS',
        recorded_at=data.timestamp or utc_now(),
        client_event_id=data.client_event_id,
    )
    db.add(x)
    await db.commit()
    await db.refresh(x)

    # Real-time WebSocket broadcast to live buses channel
    await manager.broadcast('buses', {'event': 'BUS_LOCATION_UPDATE', 'data': out(x)})
    return {'data': out(x)}


@router.get('/buses/{bus_id}/location', response_model=Envelope[dict])
async def get_latest_location(bus_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    x = (
        await db.execute(
            select(BusLocation).where(BusLocation.bus_id == bus_id).order_by(BusLocation.recorded_at.desc()).limit(1)
        )
    ).scalar_one_or_none()
    return {'data': out(x) if x else None}


@router.get('/buses/{bus_id}/location-history', response_model=Envelope[dict])
async def get_location_history(
    bus_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    return {'data': await list_rows(BusLocation, db, limit, offset, where=(BusLocation.bus_id == bus_id))}





# ============================================================================
# AI DETECTIONS & TRACKING
# ============================================================================

@router.post('/detections', response_model=Envelope[dict], status_code=status.HTTP_201_CREATED)
async def create_detection(data: DetectionIn, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    det_at = data.detected_at or data.timestamp or utc_now()
    frame_id = data.frame_id if data.frame_id is not None else data.frame_number
    x = Detection(
        bus_id=data.bus_id,
        detection_type=data.detection_type,
        class_name=data.class_name,
        confidence=data.confidence,
        bounding_box=data.bounding_box,
        latitude=data.latitude,
        longitude=data.longitude,
        detected_at=det_at,
        model_name=data.model_name,
        model_version=data.model_version,
        tracking_id=data.tracking_id,
        frame_id=frame_id,
        evidence_id=data.evidence_id,
        metadata_json=data.metadata or {},
    )
    db.add(x)
    await db.commit()
    await db.refresh(x)

    await manager.broadcast('detections', {'event': 'DETECTION_RECORDED', 'data': out(x)})
    return {'data': out(x)}


@router.get('/detections', response_model=Envelope[dict])
async def list_detections(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    detection_type: DetectionType | None = None,
    bus_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    where = None
    if detection_type is not None:
        where = (Detection.detection_type == detection_type)
    if bus_id is not None:
        where = (where & (Detection.bus_id == bus_id)) if where is not None else (Detection.bus_id == bus_id)
    return {'data': await list_rows(Detection, db, limit, offset, where=where)}


@router.get('/detections/{detection_id}', response_model=Envelope[dict])
async def get_detection(detection_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    x = await db.get(Detection, detection_id)
    if not x:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Detection not found')
    return {'data': out(x)}


# ============================================================================
# ROAD DEFECTS
# ============================================================================

@router.post('/road-defects', response_model=Envelope[dict], status_code=status.HTTP_201_CREATED)
async def create_road_defect(data: DefectIn, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    bus_id = data.detected_by_bus_id or data.bus_id
    try:
        dtype = RoadDefectType(data.defect_type.upper())
    except ValueError:
        dtype = RoadDefectType.OTHER

    try:
        sev = DefectSeverity(data.severity.upper())
    except ValueError:
        sev = DefectSeverity.MEDIUM

    try:
        stat = DefectStatus(data.status.upper())
    except ValueError:
        stat = DefectStatus.OPEN

    x = RoadDefect(
        defect_type=dtype,
        severity=sev,
        status=stat,
        description=data.description,
        latitude=data.latitude,
        longitude=data.longitude,
        confidence=data.confidence,
        detected_by_bus_id=bus_id,
        evidence_id=data.evidence_id,
        model_name=data.model_name,
        model_version=data.model_version,
        metadata_json=data.metadata or {},
    )
    db.add(x)
    await db.commit()
    await db.refresh(x)
    return {'data': out(x)}


@router.get('/road-defects', response_model=Envelope[dict])
async def list_road_defects(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    defect_type: str | None = None,
    severity: str | None = None,
    status_filter: str | None = Query(None, alias='status'),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    where = None
    if defect_type:
        try:
            where = (RoadDefect.defect_type == RoadDefectType(defect_type.upper()))
        except ValueError:
            pass
    if severity:
        try:
            sev_cond = (RoadDefect.severity == DefectSeverity(severity.upper()))
            where = (where & sev_cond) if where is not None else sev_cond
        except ValueError:
            pass
    if status_filter:
        try:
            st_cond = (RoadDefect.status == DefectStatus(status_filter.upper()))
            where = (where & st_cond) if where is not None else st_cond
        except ValueError:
            pass

    return {'data': await list_rows(RoadDefect, db, limit, offset, where=where)}


@router.get('/road-defects/nearby', response_model=Envelope[dict])
async def get_nearby_road_defects(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(5.0, gt=0, le=100.0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    try:
        from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_GeogFromText
        pt = ST_GeogFromText(f'SRID=4326;POINT({longitude} {latitude})')
        dist_expr = ST_Distance(RoadDefect.location, pt)
        stmt = (
            select(RoadDefect, dist_expr.label('distance_meters'))
            .where(
                RoadDefect.location.isnot(None),
                ST_DWithin(RoadDefect.location, pt, radius_km * 1000.0),
            )
            .order_by(dist_expr.asc())
            .limit(limit)
        )
        res = await db.execute(stmt)
        rows = res.all()
        nearby = []
        for defect, dist_m in rows:
            d = out(defect)
            d['distance_km'] = round(dist_m / 1000.0, 3)
            nearby.append(d)
        return {'data': {'items': nearby, 'total': len(nearby), 'radius_km': radius_km}}
    except Exception:
        rows = (await db.execute(select(RoadDefect))).scalars().all()
        nearby = []
        for defect in rows:
            dist = haversine_distance_km(latitude, longitude, defect.latitude, defect.longitude)
            if dist <= radius_km:
                d = out(defect)
                d['distance_km'] = round(dist, 3)
                nearby.append(d)
        nearby.sort(key=lambda i: i['distance_km'])
        return {'data': {'items': nearby[:limit], 'total': len(nearby), 'radius_km': radius_km}}


@router.get('/road-defects/{defect_id}', response_model=Envelope[dict])
async def get_road_defect(defect_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    defect = await db.get(RoadDefect, defect_id)
    if not defect:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Road defect not found')
    return {'data': out(defect)}


@router.patch('/road-defects/{defect_id}/status', response_model=Envelope[dict])
async def update_road_defect_status(
    defect_id: UUID,
    data: StatusIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUTHORITY)),
):
    defect = await db.get(RoadDefect, defect_id)
    if not defect:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Road defect not found')
    try:
        defect.status = DefectStatus(data.status.upper())
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='Invalid defect status')

    if defect.status == DefectStatus.RESOLVED:
        defect.resolved_at = utc_now()
        defect.resolved_by = user.id

    await db.commit()
    await db.refresh(defect)
    return {'data': out(defect)}


# ============================================================================
# VEHICLES & TRAFFIC
# ============================================================================

@router.post('/vehicles', response_model=Envelope[dict], status_code=status.HTTP_201_CREATED)
async def create_vehicle(data: VehicleIn, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    v = Vehicle(**data.model_dump())
    db.add(v)
    await db.commit()
    await db.refresh(v)
    return {'data': out(v)}


@router.get('/vehicles', response_model=Envelope[dict])
async def list_vehicles(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    plate_number: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    where = (Vehicle.plate_number == plate_number) if plate_number else None
    return {'data': await list_rows(Vehicle, db, limit, offset, where=where)}


@router.get('/vehicles/{vehicle_id}', response_model=Envelope[dict])
async def get_vehicle(vehicle_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    v = await db.get(Vehicle, vehicle_id)
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Vehicle not found')
    return {'data': out(v)}


@router.post('/vehicle-detections', response_model=Envelope[dict], status_code=status.HTTP_201_CREATED)
async def create_vehicle_detection(
    data: VehicleDetectionIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    vd = VehicleDetection(**data.model_dump())
    db.add(vd)
    await db.commit()
    await db.refresh(vd)
    return {'data': out(vd)}


@router.get('/vehicle-detections', response_model=Envelope[dict])
async def list_vehicle_detections(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    vehicle_id: UUID | None = None,
    bus_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    where = None
    if vehicle_id:
        where = (VehicleDetection.vehicle_id == vehicle_id)
    if bus_id:
        where = (where & (VehicleDetection.bus_id == bus_id)) if where is not None else (VehicleDetection.bus_id == bus_id)
    return {'data': await list_rows(VehicleDetection, db, limit, offset, where=where)}


@router.post('/traffic/events', response_model=Envelope[dict], status_code=status.HTTP_201_CREATED)
async def create_traffic_event(data: TrafficIn, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    sev = data.severity or data.traffic_density
    total = sum([data.cars, data.bikes, data.buses, data.trucks, data.autos])
    x = TrafficEvent(
        event_type=data.event_type,
        severity=sev,
        description=data.description,
        latitude=data.latitude,
        longitude=data.longitude,
        bus_id=data.bus_id,
        confidence=data.confidence,
        cars=data.cars,
        bikes=data.bikes,
        buses_count=data.buses,
        trucks=data.trucks,
        autos=data.autos,
        total_vehicles=total,
        average_speed=data.average_speed,
        model_name=data.model_name,
        model_version=data.model_version,
        metadata_json=data.metadata or {},
    )
    db.add(x)
    await db.commit()
    await db.refresh(x)

    await manager.broadcast('traffic', {'event': 'TRAFFIC_EVENT', 'data': out(x)})
    return {'data': out(x)}


@router.get('/traffic', response_model=Envelope[dict])
async def list_traffic_events(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    return {'data': await list_rows(TrafficEvent, db, limit, offset)}


@router.get('/traffic/nearby', response_model=Envelope[dict])
async def get_nearby_traffic(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(5.0, gt=0, le=100.0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    rows = (await db.execute(select(TrafficEvent))).scalars().all()
    nearby = []
    for event in rows:
        dist = haversine_distance_km(latitude, longitude, event.latitude, event.longitude)
        if dist <= radius_km:
            e = out(event)
            e['distance_km'] = round(dist, 3)
            nearby.append(e)
    nearby.sort(key=lambda i: i['distance_km'])
    return {'data': {'items': nearby[:limit], 'total': len(nearby), 'radius_km': radius_km}}


# ============================================================================
# INCIDENT MANAGEMENT & EVIDENCE
# ============================================================================

@router.post('/incidents', response_model=Envelope[dict], status_code=status.HTTP_201_CREATED)
async def create_incident(data: IncidentIn, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    sev = data.severity or data.priority
    x = Incident(
        incident_type=data.incident_type,
        severity=sev,
        status=data.status,
        title=data.title or f"{data.incident_type.value} Incident",
        description=data.description,
        latitude=data.latitude,
        longitude=data.longitude,
        bus_id=data.bus_id,
        route_id=data.route_id,
        vehicle_id=data.vehicle_id,
        reported_by=user.id,
        confidence=data.confidence,
        detected_at=data.detected_at or utc_now(),
        metadata_json=data.metadata or {},
    )
    db.add(x)
    await db.commit()
    await db.refresh(x)

    await manager.broadcast('incidents', {'event': 'INCIDENT_CREATED', 'data': out(x)})
    return {'data': out(x)}


@router.get('/incidents', response_model=Envelope[dict])
async def list_incidents(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    incident_type: IncidentType | None = None,
    status_filter: IncidentStatus | None = Query(None, alias='status'),
    severity: IncidentSeverity | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUTHORITY)),
):
    where = None
    if incident_type is not None:
        where = (Incident.incident_type == incident_type)
    if status_filter is not None:
        where = (where & (Incident.status == status_filter)) if where is not None else (Incident.status == status_filter)
    if severity is not None:
        where = (where & (Incident.severity == severity)) if where is not None else (Incident.severity == severity)
    return {'data': await list_rows(Incident, db, limit, offset, where=where)}


@router.get('/incidents/nearby', response_model=Envelope[dict])
async def get_nearby_incidents(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(5.0, gt=0, le=100.0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    try:
        from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_GeogFromText
        pt = ST_GeogFromText(f'SRID=4326;POINT({longitude} {latitude})')
        dist_expr = ST_Distance(Incident.location, pt)
        stmt = (
            select(Incident, dist_expr.label('distance_meters'))
            .where(
                Incident.location.isnot(None),
                ST_DWithin(Incident.location, pt, radius_km * 1000.0),
            )
            .order_by(dist_expr.asc())
            .limit(limit)
        )
        res = await db.execute(stmt)
        rows = res.all()
        nearby = []
        for inc, dist_m in rows:
            d = out(inc)
            d['distance_km'] = round(dist_m / 1000.0, 3)
            nearby.append(d)
        return {'data': {'items': nearby, 'total': len(nearby), 'radius_km': radius_km}}
    except Exception:
        rows = (await db.execute(select(Incident))).scalars().all()
        nearby = []
        for inc in rows:
            dist = haversine_distance_km(latitude, longitude, inc.latitude, inc.longitude)
            if dist <= radius_km:
                d = out(inc)
                d['distance_km'] = round(dist, 3)
                nearby.append(d)
        nearby.sort(key=lambda i: i['distance_km'])
        return {'data': {'items': nearby[:limit], 'total': len(nearby), 'radius_km': radius_km}}


@router.get('/incidents/{incident_id}', response_model=Envelope[dict])
async def get_incident(
    incident_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUTHORITY)),
):
    incident = await db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Incident not found')

    # Load associated evidence
    evidence_rows = (
        await db.execute(select(IncidentEvidence).where(IncidentEvidence.incident_id == incident_id))
    ).scalars().all()

    inc_dict = out(incident)
    inc_dict['evidence'] = [out(e) for e in evidence_rows]
    return {'data': inc_dict}


@router.patch('/incidents/{incident_id}/status', response_model=Envelope[dict])
async def update_incident_status(
    incident_id: UUID,
    data: StatusIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUTHORITY)),
):
    incident = await db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Incident not found')

    try:
        incident.status = IncidentStatus(data.status.upper())
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='Invalid incident status')

    if incident.status == IncidentStatus.ACKNOWLEDGED and not incident.acknowledged_at:
        incident.acknowledged_at = utc_now()
    elif incident.status in (IncidentStatus.RESOLVED, IncidentStatus.CLOSED):
        incident.resolved_at = utc_now()

    await db.commit()
    await db.refresh(incident)

    await manager.broadcast('incidents', {'event': 'INCIDENT_STATUS_UPDATED', 'data': out(incident)})
    return {'data': out(incident)}


@router.post('/evidence/upload', response_model=Envelope[dict])
async def upload_evidence(
    file: UploadFile = File(...),
    incident_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    allowed = {'image/jpeg', 'image/png', 'image/webp', 'video/mp4', 'video/webm'}
    if file.content_type not in allowed:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail='Unsupported evidence file type')

    data = await file.read()
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail='Evidence file exceeds configured size limit')

    checksum = hashlib.sha256(data).hexdigest()
    url, object_key = await get_storage().put(data, file.content_type, file.filename or 'evidence')

    evidence_record = None
    if incident_id:
        incident = await db.get(Incident, incident_id)
        if incident:
            storage_prov = (
                StorageProvider.AWS_S3
                if settings.storage_provider in ('s3', 'aws_s3')
                else StorageProvider.MINIO
                if settings.storage_provider == 'minio'
                else StorageProvider.LOCAL
            )
            evidence_record = IncidentEvidence(
                incident_id=incident_id,
                uploaded_by=user.id,
                storage_provider=storage_prov,
                object_key=object_key,
                object_url=url,
                file_type=file.content_type,
                mime_type=file.content_type,
                file_size=len(data),
                checksum=checksum,
            )
            db.add(evidence_record)
            await db.commit()
            await db.refresh(evidence_record)

    return {
        'data': {
            'id': str(evidence_record.id) if evidence_record else None,
            'file_url': url,
            'object_url': url,
            'object_key': object_key,
            'file_type': file.content_type,
            'file_size': len(data),
            'checksum': checksum,
        }
    }


# ============================================================================
# CITIZEN REPORTS
# ============================================================================

@router.post('/reports', response_model=Envelope[dict], status_code=status.HTTP_201_CREATED)
async def submit_citizen_report(
    data: ReportIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    rtype = data.report_type or data.problem_type or 'OTHER'
    x = CitizenReport(
        citizen_id=user.id,
        report_type=rtype,
        title=data.title,
        description=data.description,
        latitude=data.latitude,
        longitude=data.longitude,
        status=CitizenReportStatus.SUBMITTED.value,
        priority=data.priority,
        image_url=data.image_url,
        metadata_json=data.metadata or {},
    )
    db.add(x)
    await db.commit()
    await db.refresh(x)
    return {'data': out(x)}


@router.get('/reports', response_model=Envelope[dict])
async def list_citizen_reports(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status_filter: str | None = Query(None, alias='status'),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUTHORITY)),
):
    where = (CitizenReport.status == status_filter.upper()) if status_filter else None
    return {'data': await list_rows(CitizenReport, db, limit, offset, where=where)}


@router.get('/reports/my', response_model=Envelope[dict])
async def my_reports(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    return {'data': await list_rows(CitizenReport, db, limit, offset, where=(CitizenReport.citizen_id == user.id))}


@router.get('/reports/{report_id}', response_model=Envelope[dict])
async def get_citizen_report(report_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    report = await db.get(CitizenReport, report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Citizen report not found')
    if user.role not in (Role.ADMIN, Role.AUTHORITY) and report.citizen_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Forbidden')
    return {'data': out(report)}


@router.patch('/reports/{report_id}/status', response_model=Envelope[dict])
async def update_citizen_report_status(
    report_id: UUID,
    data: StatusIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUTHORITY)),
):
    report = await db.get(CitizenReport, report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Citizen report not found')

    report.status = data.status.upper()
    if report.status == CitizenReportStatus.RESOLVED.value:
        report.resolved_at = utc_now()

    await db.commit()
    await db.refresh(report)
    return {'data': out(report)}


# ============================================================================
# NOTIFICATIONS
# ============================================================================

@router.post('/notifications', response_model=Envelope[dict], status_code=status.HTTP_201_CREATED)
async def create_notification(
    data: NotificationIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUTHORITY)),
):
    msg = data.message or data.body or data.title
    notif = await NotificationService.send_notification(
        db=db,
        user_id=data.user_id,
        title=data.title,
        message=msg,
        notification_type=data.notification_type,
        metadata=data.metadata,
    )
    return {'data': out(notif)}


@router.get('/notifications/my', response_model=Envelope[dict])
async def get_my_notifications(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    where = (Notification.user_id == user.id)
    if unread_only:
        where = where & (Notification.is_read == False)
    return {'data': await list_rows(Notification, db, limit, offset, where=where)}


@router.patch('/notifications/{notification_id}/read', response_model=Envelope[dict])
async def mark_notification_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    notif = await db.get(Notification, notification_id)
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Notification not found')
    if notif.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Forbidden')

    notif.is_read = True
    notif.read_at = utc_now()
    await db.commit()
    await db.refresh(notif)
    return {'data': out(notif)}


# ============================================================================
# AUDIT LOGS & MODEL REGISTRY
# ============================================================================

@router.get('/audit-logs', response_model=Envelope[dict])
async def list_audit_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    action: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN)),
):
    where = (AuditLog.action == action) if action else None
    return {'data': await list_rows(AuditLog, db, limit, offset, where=where)}


@router.post('/model-versions', response_model=Envelope[dict], status_code=status.HTTP_201_CREATED)
async def register_model_version(
    data: ModelVersionIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN)),
):
    existing = (
        await db.execute(
            select(ModelVersion).where(
                ModelVersion.name == data.name,
                ModelVersion.version == data.version,
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Model version already registered')

    mv = ModelVersion(
        name=data.name,
        version=data.version,
        model_type=data.model_type,
        framework=data.framework,
        file_reference=data.file_reference,
        is_active=data.is_active,
        metadata_json=data.metadata or {},
        deployed_at=utc_now(),
    )
    db.add(mv)
    await db.commit()
    await db.refresh(mv)
    return {'data': out(mv)}


@router.get('/model-versions', response_model=Envelope[dict])
async def list_model_versions(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    return {'data': await list_rows(ModelVersion, db, limit, offset)}


# ============================================================================
# OFFLINE MOBILE SYNCHRONIZATION
# ============================================================================

@router.post('/sync', response_model=Envelope[dict])
async def sync_offline_events(
    events: list[dict],
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """Idempotent batch offline sync endpoint."""
    results = []
    for event in events:
        client_id = event.get('client_event_id')
        if not client_id:
            results.append({'accepted': False, 'error': 'client_event_id is required'})
            continue

        duplicate = (
            await db.execute(select(SyncEvent).where(SyncEvent.client_event_id == client_id))
        ).scalar_one_or_none()

        if duplicate:
            results.append({'client_event_id': client_id, 'accepted': True, 'duplicate': True})
            continue

        # Ingest event according to type
        event_type = event.get('event_type', 'telemetry')
        payload = event.get('payload', {})

        if event_type == 'location' and 'latitude' in payload and 'longitude' in payload:
            bus_id_val = payload.get('bus_id')
            if bus_id_val:
                db.add(
                    BusLocation(
                        bus_id=UUID(bus_id_val),
                        latitude=payload['latitude'],
                        longitude=payload['longitude'],
                        speed=payload.get('speed'),
                        heading=payload.get('heading'),
                        client_event_id=client_id,
                    )
                )

        db.add(
            SyncEvent(
                client_event_id=client_id,
                event_type=event_type,
                user_id=user.id,
            )
        )
        results.append({'client_event_id': client_id, 'accepted': True, 'duplicate': False})

    await db.commit()
    return {'data': {'results': results, 'processed_count': len(results)}}
