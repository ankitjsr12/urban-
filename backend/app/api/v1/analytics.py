from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import current_user, require_roles
from app.models import (
    Bus,
    BusStatus,
    CitizenReport,
    DefectSeverity,
    DefectStatus,
    Detection,
    DetectionType,
    Incident,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
    Priority,
    RoadDefect,
    RoadDefectType,
    Role,
    Route,
    TrafficEvent,
    TrafficSeverity,
    User,
)
from app.schemas.common import Envelope

router = APIRouter(prefix='/analytics', tags=['Analytics'])


@router.get('/overview', response_model=Envelope[dict])
async def get_overview(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUTHORITY)),
):
    async def count_rows(model, where=None):
        q = select(func.count()).select_from(model)
        if where is not None:
            q = q.where(where)
        return (await db.execute(q)).scalar_one()

    total_buses = await count_rows(Bus)
    active_buses = await count_rows(Bus, Bus.status == BusStatus.ACTIVE)
    total_detections = await count_rows(Detection)
    total_road_defects = await count_rows(RoadDefect)
    open_defects = await count_rows(RoadDefect, RoadDefect.status == DefectStatus.OPEN)
    total_incidents = await count_rows(Incident)
    high_priority_incidents = await count_rows(
        Incident,
        Incident.severity.in_([IncidentSeverity.HIGH, IncidentSeverity.CRITICAL]),
    )
    total_traffic_events = await count_rows(TrafficEvent)
    total_citizen_reports = await count_rows(CitizenReport)

    return {
        'data': {
            'total_buses': total_buses,
            'active_buses': active_buses,
            'total_detections': total_detections,
            'total_road_defects': total_road_defects,
            'open_road_defects': open_defects,
            'total_incidents': total_incidents,
            'high_priority_incidents': high_priority_incidents,
            'total_traffic_events': total_traffic_events,
            'total_citizen_reports': total_citizen_reports,
        }
    }


@router.get('/traffic', response_model=Envelope[dict])
async def get_traffic_analytics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUTHORITY)),
):
    # Aggregated vehicle totals and average speeds
    totals_q = select(
        func.coalesce(func.sum(TrafficEvent.cars), 0).label('total_cars'),
        func.coalesce(func.sum(TrafficEvent.bikes), 0).label('total_bikes'),
        func.coalesce(func.sum(TrafficEvent.buses_count), 0).label('total_buses'),
        func.coalesce(func.sum(TrafficEvent.trucks), 0).label('total_trucks'),
        func.coalesce(func.sum(TrafficEvent.autos), 0).label('total_autos'),
        func.coalesce(func.sum(TrafficEvent.total_vehicles), 0).label('grand_total_vehicles'),
        func.coalesce(func.avg(TrafficEvent.average_speed), 0.0).label('system_avg_speed'),
    )
    row = (await db.execute(totals_q)).one()

    # Severity distribution
    sev_q = select(TrafficEvent.severity, func.count(TrafficEvent.id)).group_by(TrafficEvent.severity)
    sev_rows = (await db.execute(sev_q)).all()
    severity_distribution = {s.value: c for s, c in sev_rows}

    return {
        'data': {
            'vehicle_totals': {
                'cars': row.total_cars,
                'bikes': row.total_bikes,
                'buses': row.total_buses,
                'trucks': row.total_trucks,
                'autos': row.total_autos,
                'grand_total': row.grand_total_vehicles,
            },
            'system_average_speed_kmh': round(float(row.system_avg_speed), 2),
            'severity_distribution': severity_distribution,
        }
    }


@router.get('/road-defects', response_model=Envelope[dict])
async def get_road_defects_analytics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUTHORITY)),
):
    # Group by defect type
    type_q = select(RoadDefect.defect_type, func.count(RoadDefect.id)).group_by(RoadDefect.defect_type)
    type_rows = (await db.execute(type_q)).all()

    # Group by severity
    sev_q = select(RoadDefect.severity, func.count(RoadDefect.id)).group_by(RoadDefect.severity)
    sev_rows = (await db.execute(sev_q)).all()

    # Group by status
    status_q = select(RoadDefect.status, func.count(RoadDefect.id)).group_by(RoadDefect.status)
    status_rows = (await db.execute(status_q)).all()

    total = sum(c for _, c in type_rows)
    resolved = sum(c for s, c in status_rows if s == DefectStatus.RESOLVED)
    resolution_rate = round((resolved / total * 100), 2) if total > 0 else 0.0

    return {
        'data': {
            'by_type': {t.value: c for t, c in type_rows},
            'by_severity': {s.value: c for s, c in sev_rows},
            'by_status': {st.value: c for st, c in status_rows},
            'total_defects': total,
            'resolved_defects': resolved,
            'resolution_rate_percent': resolution_rate,
        }
    }


@router.get('/incidents', response_model=Envelope[dict])
async def get_incidents_analytics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUTHORITY)),
):
    # Group by incident type
    type_q = select(Incident.incident_type, func.count(Incident.id)).group_by(Incident.incident_type)
    type_rows = (await db.execute(type_q)).all()

    # Group by severity
    sev_q = select(Incident.severity, func.count(Incident.id)).group_by(Incident.severity)
    sev_rows = (await db.execute(sev_q)).all()

    # Group by status
    status_q = select(Incident.status, func.count(Incident.id)).group_by(Incident.status)
    status_rows = (await db.execute(status_q)).all()

    return {
        'data': {
            'by_type': {t.value: c for t, c in type_rows},
            'by_severity': {s.value: c for s, c in sev_rows},
            'by_status': {st.value: c for st, c in status_rows},
            'total_incidents': sum(c for _, c in type_rows),
        }
    }


@router.get('/routes', response_model=Envelope[dict])
async def get_routes_analytics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUTHORITY)),
):
    # Active buses per route
    routes_q = (
        select(
            Route.id,
            Route.route_number,
            Route.name,
            func.count(Bus.id).label('assigned_buses'),
        )
        .outerjoin(Bus, (Bus.assigned_route_id == Route.id) & (Bus.status == BusStatus.ACTIVE))
        .group_by(Route.id, Route.route_number, Route.name)
    )
    rows = (await db.execute(routes_q)).all()

    return {
        'data': {
            'routes': [
                {
                    'route_id': str(r.id),
                    'route_number': r.route_number,
                    'name': r.name,
                    'active_buses': r.assigned_buses,
                }
                for r in rows
            ]
        }
    }


@router.get('/heatmap', response_model=Envelope[dict])
async def get_heatmap_geojson(
    kind: str = Query('incidents'),
    limit: int = Query(5000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    model_map = {
        'incidents': Incident,
        'road_defects': RoadDefect,
        'traffic': TrafficEvent,
        'potholes': RoadDefect,
        'waterlogging': RoadDefect,
    }
    model = model_map.get(kind, Incident)

    where = None
    if kind == 'potholes':
        where = (RoadDefect.defect_type == RoadDefectType.POTHOLE)
    elif kind == 'waterlogging':
        where = (RoadDefect.defect_type == RoadDefectType.WATERLOGGING)

    q = select(model.latitude, model.longitude)
    if where is not None:
        q = q.where(where)

    rows = (await db.execute(q.limit(limit))).all()

    features = [
        {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [lon, lat]},
            'properties': {'kind': kind},
        }
        for lat, lon in rows
        if lat is not None and lon is not None
    ]

    return {
        'data': {
            'type': 'FeatureCollection',
            'features': features,
            'total_points': len(features),
        }
    }
