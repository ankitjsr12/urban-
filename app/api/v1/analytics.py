from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from app.db.session import get_db
from app.api.deps import current_user, require_roles
from app.models.models import *
from app.schemas.common import Envelope
router=APIRouter(prefix='/analytics',tags=['Analytics'])
@router.get('/overview', response_model=Envelope[dict])
async def overview(db=Depends(get_db),user=Depends(require_roles(Role.ADMIN,Role.AUTHORITY))):
    async def c(m,where=None): return (await db.execute(select(func.count()).select_from(m).where(where) if where is not None else select(func.count()).select_from(m))).scalar_one()
    return {'data':{'total_buses':await c(Bus),'active_buses':await c(Bus,Bus.status==BusStatus.ACTIVE),'total_detections':await c(Detection),'total_road_defects':await c(RoadDefect),'total_incidents':await c(Incident),'high_priority_incidents':await c(Incident,Incident.priority.in_([Priority.HIGH,Priority.CRITICAL])),'total_traffic_events':await c(TrafficEvent)}}
@router.get('/heatmap', response_model=Envelope[dict])
async def heatmap(kind:str=Query('incidents'),db=Depends(get_db),user=Depends(current_user)):
    model={'incidents':Incident,'road_defects':RoadDefect,'traffic':TrafficEvent,'potholes':RoadDefect,'waterlogging':RoadDefect}.get(kind,Incident); rows=(await db.execute(select(model.latitude,model.longitude).limit(5000))).all(); return {'data':{'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'Point','coordinates':[lon,lat]},'properties':{'kind':kind}} for lat,lon in rows]}}
