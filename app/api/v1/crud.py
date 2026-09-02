from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
import hashlib
from app.core.config import settings
from app.services.storage import get_storage
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.deps import current_user, require_roles
from app.models.models import *
from app.schemas.common import Envelope, Page
from app.schemas.domain import *
router=APIRouter(tags=['Urban Intelligence'])
def out(x):
    d={k:v for k,v in x.__dict__.items() if not k.startswith('_')};
    for k,v in list(d.items()):
        if isinstance(v,UUID): d[k]=str(v)
        elif isinstance(v,datetime): d[k]=v.isoformat()
        elif isinstance(v,enum.Enum): d[k]=v.value
    return d
async def list_rows(model, db, limit, offset, where=None):
    q=select(model); q=q.where(where) if where is not None else q; total=(await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one(); rows=(await db.execute(q.order_by(model.__table__.c.created_at.desc() if 'created_at' in model.__table__.c else model.__table__.c.timestamp.desc()).limit(limit).offset(offset))).scalars().all(); return {'items':[out(x) for x in rows],'total':total,'limit':limit,'offset':offset}
@router.post('/locations', response_model=Envelope[dict])
async def location(data:LocationIn, db=Depends(get_db), user=Depends(current_user)):
    if data.client_event_id and (await db.execute(select(BusLocation).where(BusLocation.client_event_id==data.client_event_id))).scalar_one_or_none(): return {'data':{'duplicate':True}}
    x=BusLocation(**data.model_dump(exclude_none=True)); x.timestamp=x.timestamp or datetime.now(timezone.utc); db.add(x); await db.commit(); await db.refresh(x); return {'data':out(x)}
@router.get('/buses/{bus_id}/location', response_model=Envelope[dict])
async def latest(bus_id:UUID,db=Depends(get_db),user=Depends(current_user)):
    x=(await db.execute(select(BusLocation).where(BusLocation.bus_id==bus_id).order_by(BusLocation.timestamp.desc()).limit(1))).scalar_one_or_none(); return {'data':out(x) if x else None}
@router.get('/buses/{bus_id}/location-history', response_model=Envelope[dict])
async def history(bus_id:UUID,limit:int=Query(100,le=1000),db=Depends(get_db),user=Depends(current_user)): return {'data':await list_rows(BusLocation,db,limit,0,BusLocation.bus_id==bus_id)}
@router.post('/detections', response_model=Envelope[dict])
async def detection(data:DetectionIn,db=Depends(get_db),user=Depends(current_user)):
    x=Detection(**data.model_dump(exclude={'metadata'}),metadata_json=data.metadata); x.timestamp=x.timestamp or datetime.now(timezone.utc); db.add(x); await db.commit(); await db.refresh(x); return {'data':out(x)}
@router.get('/detections', response_model=Envelope[dict])
async def detections(limit:int=Query(100,le=1000),offset:int=0,db=Depends(get_db),user=Depends(current_user)): return {'data':await list_rows(Detection,db,limit,offset)}
@router.post('/road-defects', response_model=Envelope[dict])
async def defect(data:DefectIn,db=Depends(get_db),user=Depends(current_user)): x=RoadDefect(**data.model_dump()); db.add(x); await db.commit(); await db.refresh(x); return {'data':out(x)}
@router.get('/road-defects', response_model=Envelope[dict])
async def defects(limit:int=Query(100,le=1000),offset:int=0,db=Depends(get_db),user=Depends(current_user)): return {'data':await list_rows(RoadDefect,db,limit,offset)}
@router.post('/traffic/events', response_model=Envelope[dict])
async def traffic(data:TrafficIn,db=Depends(get_db),user=Depends(current_user)): x=TrafficEvent(**data.model_dump()); x.total_vehicles=sum([x.cars,x.bikes,x.buses,x.trucks,x.autos]); db.add(x); await db.commit(); await db.refresh(x); return {'data':out(x)}
@router.get('/traffic', response_model=Envelope[dict])
async def traffic_list(limit:int=Query(100,le=1000),offset:int=0,db=Depends(get_db),user=Depends(current_user)): return {'data':await list_rows(TrafficEvent,db,limit,offset)}
@router.post('/incidents', response_model=Envelope[dict])
async def incident(data:IncidentIn,db=Depends(get_db),user=Depends(current_user)): x=Incident(**data.model_dump(),created_by=user.id); db.add(x); await db.commit(); await db.refresh(x); return {'data':out(x)}
@router.get('/incidents', response_model=Envelope[dict])
async def incidents(limit:int=Query(100,le=1000),offset:int=0,db=Depends(get_db),user=Depends(require_roles(Role.ADMIN,Role.AUTHORITY))): return {'data':await list_rows(Incident,db,limit,offset)}
@router.patch('/incidents/{incident_id}/status', response_model=Envelope[dict])
async def incident_status(incident_id:UUID,data:StatusIn,db=Depends(get_db),user=Depends(require_roles(Role.ADMIN,Role.AUTHORITY))):
    x=await db.get(Incident,incident_id)
    if not x: raise HTTPException(404,'Incident not found')
    try: x.status=IncidentStatus(data.status)
    except ValueError: raise HTTPException(422,'Invalid incident status')
    await db.commit(); await db.refresh(x); return {'data':out(x)}
@router.post('/reports', response_model=Envelope[dict])
async def report(data:ReportIn,db=Depends(get_db),user=Depends(current_user)): x=CitizenReport(**data.model_dump(),citizen_id=user.id); db.add(x); await db.commit(); await db.refresh(x); return {'data':out(x)}
@router.get('/reports/my', response_model=Envelope[dict])
async def my_reports(db=Depends(get_db),user=Depends(current_user)): return {'data':await list_rows(CitizenReport,db,100,0,CitizenReport.citizen_id==user.id)}
@router.post('/evidence/upload', response_model=Envelope[dict])
async def upload_evidence(file: UploadFile=File(...), user=Depends(current_user)):
    allowed={'image/jpeg','image/png','image/webp','video/mp4','video/webm'}
    if file.content_type not in allowed: raise HTTPException(415,'Unsupported evidence file type')
    data=await file.read()
    if len(data)>settings.max_upload_bytes: raise HTTPException(413,'Evidence file exceeds configured size limit')
    checksum=hashlib.sha256(data).hexdigest(); url=await get_storage().put(data,file.content_type,file.filename or 'evidence')
    return {'data':{'file_url':url,'file_type':file.content_type,'file_size':len(data),'checksum':checksum}}
@router.get('/buses', response_model=Envelope[dict])
async def buses(limit:int=Query(100,le=1000),offset:int=0,db=Depends(get_db),user=Depends(current_user)): return {'data':await list_rows(Bus,db,limit,offset)}
@router.get('/routes', response_model=Envelope[dict])
async def routes(limit:int=Query(100,le=1000),offset:int=0,db=Depends(get_db),user=Depends(current_user)): return {'data':await list_rows(Route,db,limit,offset)}
@router.get('/vehicles', response_model=Envelope[dict])
async def vehicles(limit:int=Query(100,le=1000),offset:int=0,db=Depends(get_db),user=Depends(current_user)): return {'data':await list_rows(Vehicle,db,limit,offset)}
@router.post('/sync', response_model=Envelope[dict])
async def sync(events:list[dict],db=Depends(get_db),user=Depends(current_user)):
    results=[]
    for event in events:
        client_id=event.get('client_event_id')
        if not client_id: results.append({'accepted':False,'error':'client_event_id is required'}); continue
        duplicate=(await db.execute(select(SyncEvent).where(SyncEvent.client_event_id==client_id))).scalar_one_or_none()
        if duplicate: results.append({'client_event_id':client_id,'accepted':True,'duplicate':True}); continue
        db.add(SyncEvent(client_event_id=client_id,event_type=event.get('event_type','unknown'),user_id=user.id)); results.append({'client_event_id':client_id,'accepted':True,'duplicate':False})
    await db.commit(); return {'data':{'results':results}}
