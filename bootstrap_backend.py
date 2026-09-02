from pathlib import Path

root = Path('/home/ubuntu/backend')
files = {
'app/core/security.py': r'''from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from app.core.config import settings

ALGORITHM = "HS256"
ph = PasswordHasher()

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    try:
        return ph.verify(hashed, password)
    except VerifyMismatchError:
        return False

def create_token(subject: str, role: str, kind: str, expires: timedelta) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": subject, "role": role, "kind": kind, "iat": now, "exp": now + expires}, settings.jwt_secret_key, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
''',
'app/models/models.py': r'''import enum, uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Float, Integer, ForeignKey, Text, JSON, Enum, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base

def uid(): return uuid.uuid4()
def now(): return datetime.now(timezone.utc)
class Role(str, enum.Enum): ADMIN="ADMIN"; AUTHORITY="AUTHORITY"; DRIVER="DRIVER"; CITIZEN="CITIZEN"
class BusStatus(str, enum.Enum): ACTIVE="ACTIVE"; INACTIVE="INACTIVE"; MAINTENANCE="MAINTENANCE"; OFFLINE="OFFLINE"
class Density(str, enum.Enum): LOW="LOW"; MEDIUM="MEDIUM"; HIGH="HIGH"; CRITICAL="CRITICAL"
class IncidentStatus(str, enum.Enum): NEW="NEW"; UNDER_REVIEW="UNDER_REVIEW"; VERIFIED="VERIFIED"; ASSIGNED="ASSIGNED"; RESOLVED="RESOLVED"; REJECTED="REJECTED"
class Priority(str, enum.Enum): LOW="LOW"; MEDIUM="MEDIUM"; HIGH="HIGH"; CRITICAL="CRITICAL"
class DefectStatus(str, enum.Enum): DETECTED="DETECTED"; VERIFIED="VERIFIED"; ASSIGNED="ASSIGNED"; IN_PROGRESS="IN_PROGRESS"; RESOLVED="RESOLVED"; REJECTED="REJECTED"
class DetectionType(str, enum.Enum): POTHOLE="POTHOLE"; DAMAGED_ROAD="DAMAGED_ROAD"; WATERLOGGING="WATERLOGGING"; TRAFFIC_SIGN="TRAFFIC_SIGN"; ZEBRA_CROSSING="ZEBRA_CROSSING"; ROAD_DIVIDER="ROAD_DIVIDER"; VEHICLE="VEHICLE"; PEDESTRIAN="PEDESTRIAN"; CHILD_RISK="CHILD_RISK"; TRAFFIC_HAZARD="TRAFFIC_HAZARD"
class VehicleType(str, enum.Enum): CAR="CAR"; BUS="BUS"; TRUCK="TRUCK"; MOTORCYCLE="MOTORCYCLE"; AUTO="AUTO"; BICYCLE="BICYCLE"; OTHER="OTHER"
class EvidenceType(str, enum.Enum): IMAGE="IMAGE"; VIDEO="VIDEO"; FRAME="FRAME"; OCR_RESULT="OCR_RESULT"; AI_RESULT="AI_RESULT"
class IncidentType(str, enum.Enum): POSSIBLE_HIT_AND_RUN="POSSIBLE_HIT_AND_RUN"; DANGEROUS_DRIVING="DANGEROUS_DRIVING"; COLLISION_LIKE_EVENT="COLLISION_LIKE_EVENT"; PEDESTRIAN_RISK="PEDESTRIAN_RISK"; ROAD_HAZARD="ROAD_HAZARD"; OTHER="OTHER"
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
class User(TimestampMixin, Base):
    __tablename__='users'; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), primary_key=True, default=uid); name: Mapped[str]=mapped_column(String(160)); email: Mapped[str]=mapped_column(String(255), unique=True, index=True); phone: Mapped[str|None]=mapped_column(String(40)); password_hash: Mapped[str]=mapped_column(Text()); role: Mapped[Role]=mapped_column(Enum(Role), default=Role.CITIZEN); is_active: Mapped[bool]=mapped_column(Boolean, default=True)
class Route(TimestampMixin, Base):
    __tablename__='routes'; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), primary_key=True, default=uid); name: Mapped[str]=mapped_column(String(160)); code: Mapped[str]=mapped_column(String(40), unique=True); origin: Mapped[str|None]=mapped_column(String(160)); destination: Mapped[str|None]=mapped_column(String(160))
class Driver(TimestampMixin, Base):
    __tablename__='drivers'; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), primary_key=True, default=uid); user_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), unique=True); license_number: Mapped[str]=mapped_column(String(80), unique=True)
class Bus(TimestampMixin, Base):
    __tablename__='buses'; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), primary_key=True, default=uid); bus_number: Mapped[str]=mapped_column(String(40), unique=True); registration_number: Mapped[str]=mapped_column(String(40), unique=True); route_id: Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True), ForeignKey('routes.id'), index=True); driver_id: Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True), ForeignKey('drivers.id'), index=True); status: Mapped[BusStatus]=mapped_column(Enum(BusStatus), default=BusStatus.INACTIVE, index=True)
class BusLocation(Base):
    __tablename__='bus_locations'; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), primary_key=True, default=uid); bus_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), ForeignKey('buses.id'), index=True); latitude: Mapped[float]=mapped_column(Float); longitude: Mapped[float]=mapped_column(Float); speed: Mapped[float|None]=mapped_column(Float); heading: Mapped[float|None]=mapped_column(Float); accuracy: Mapped[float|None]=mapped_column(Float); timestamp: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now, index=True); client_event_id: Mapped[str|None]=mapped_column(String(100), unique=True)
class Detection(TimestampMixin, Base):
    __tablename__='detections'; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), primary_key=True, default=uid); bus_id: Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True), ForeignKey('buses.id'), index=True); detection_type: Mapped[DetectionType]=mapped_column(Enum(DetectionType), index=True); confidence: Mapped[float]=mapped_column(Float); latitude: Mapped[float|None]=mapped_column(Float); longitude: Mapped[float|None]=mapped_column(Float); timestamp: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now, index=True); frame_number: Mapped[int|None]=mapped_column(Integer); evidence_id: Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True)); model_name: Mapped[str]=mapped_column(String(120)); model_version: Mapped[str]=mapped_column(String(80)); metadata_json: Mapped[dict]=mapped_column('metadata', JSON, default=dict)
class RoadDefect(TimestampMixin, Base):
    __tablename__='road_defects'; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), primary_key=True, default=uid); defect_type: Mapped[str]=mapped_column(String(50), index=True); severity: Mapped[str]=mapped_column(String(30)); confidence: Mapped[float]=mapped_column(Float); latitude: Mapped[float]; longitude: Mapped[float]; bus_id: Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True), ForeignKey('buses.id'), index=True); evidence_id: Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True)); status: Mapped[DefectStatus]=mapped_column(Enum(DefectStatus), default=DefectStatus.DETECTED, index=True); detected_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now, index=True)
class Vehicle(Base):
    __tablename__='vehicles'; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), primary_key=True, default=uid); vehicle_type: Mapped[VehicleType]=mapped_column(Enum(VehicleType)); tracking_id: Mapped[str|None]=mapped_column(String(100), index=True); plate_number: Mapped[str|None]=mapped_column(String(40), index=True); ocr_confidence: Mapped[float|None]=mapped_column(Float); ocr_status: Mapped[str|None]=mapped_column(String(30))
class VehicleDetection(Base):
    __tablename__='vehicle_detections'; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), primary_key=True, default=uid); vehicle_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), ForeignKey('vehicles.id'), index=True); bus_id: Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True), ForeignKey('buses.id'), index=True); confidence: Mapped[float]=mapped_column(Float); latitude: Mapped[float|None]=mapped_column(Float); longitude: Mapped[float|None]=mapped_column(Float); timestamp: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now, index=True)
class TrafficEvent(Base):
    __tablename__='traffic_events'; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), primary_key=True, default=uid); cars: Mapped[int]=mapped_column(Integer, default=0); bikes: Mapped[int]=mapped_column(Integer, default=0); buses: Mapped[int]=mapped_column(Integer, default=0); trucks: Mapped[int]=mapped_column(Integer, default=0); autos: Mapped[int]=mapped_column(Integer, default=0); total_vehicles: Mapped[int]=mapped_column(Integer, default=0); traffic_density: Mapped[Density]=mapped_column(Enum(Density)); average_speed: Mapped[float|None]=mapped_column(Float); latitude: Mapped[float]; longitude: Mapped[float]; timestamp: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now, index=True)
class Incident(TimestampMixin, Base):
    __tablename__='incidents'; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), primary_key=True, default=uid); bus_id: Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True), ForeignKey('buses.id'), index=True); incident_type: Mapped[IncidentType]=mapped_column(Enum(IncidentType)); priority: Mapped[Priority]=mapped_column(Enum(Priority), index=True); description: Mapped[str|None]=mapped_column(Text()); latitude: Mapped[float]; longitude: Mapped[float]; timestamp: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now, index=True); vehicle_id: Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True)); confidence: Mapped[float|None]=mapped_column(Float); status: Mapped[IncidentStatus]=mapped_column(Enum(IncidentStatus), default=IncidentStatus.NEW, index=True); created_by: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), ForeignKey('users.id'))
class IncidentEvidence(Base):
    __tablename__='incident_evidence'; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), primary_key=True, default=uid); incident_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), ForeignKey('incidents.id'), index=True); file_url: Mapped[str]=mapped_column(Text()); file_type: Mapped[EvidenceType]; file_size: Mapped[int]; checksum: Mapped[str|None]=mapped_column(String(128)); captured_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
class CitizenReport(TimestampMixin, Base):
    __tablename__='citizen_reports'; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), primary_key=True, default=uid); citizen_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), index=True); problem_type: Mapped[str]=mapped_column(String(80)); description: Mapped[str|None]=mapped_column(Text()); latitude: Mapped[float]; longitude: Mapped[float]; status: Mapped[str]=mapped_column(String(30), default='SUBMITTED', index=True); image_url: Mapped[str|None]=mapped_column(Text())
class Notification(Base):
    __tablename__='notifications'; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), primary_key=True, default=uid); user_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), index=True); title: Mapped[str]=mapped_column(String(200)); body: Mapped[str]=mapped_column(Text()); is_read: Mapped[bool]=mapped_column(Boolean, default=False); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
class AuditLog(Base):
    __tablename__='audit_logs'; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), primary_key=True, default=uid); user_id: Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True), index=True); action: Mapped[str]=mapped_column(String(100)); resource_type: Mapped[str|None]=mapped_column(String(80)); resource_id: Mapped[str|None]=mapped_column(String(100)); ip_address: Mapped[str|None]=mapped_column(String(64)); timestamp: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now, index=True); metadata_json: Mapped[dict]=mapped_column('metadata', JSON, default=dict)
class RefreshToken(Base):
    __tablename__='refresh_tokens'; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), primary_key=True, default=uid); user_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), index=True); token_hash: Mapped[str]=mapped_column(String(128), unique=True); expires_at: Mapped[datetime]=mapped_column(DateTime(timezone=True)); revoked: Mapped[bool]=mapped_column(Boolean, default=False)
class SyncEvent(Base):
    __tablename__='sync_events'; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True), primary_key=True, default=uid); client_event_id: Mapped[str]=mapped_column(String(100), unique=True); event_type: Mapped[str]=mapped_column(String(60)); received_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now); user_id: Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True))
''',
'app/models/__init__.py': 'from app.models.models import *\n',
'app/schemas/common.py': r'''from datetime import datetime
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field, field_validator
T=TypeVar('T')
class Envelope(BaseModel, Generic[T]): success: bool=True; data: T|None=None; message: str='Operation successful'
class ErrorDetail(BaseModel): code: str; message: str
class ErrorEnvelope(BaseModel): success: bool=False; error: ErrorDetail
class Page(BaseModel, Generic[T]): items: list[T]; total: int; limit: int; offset: int
class Coordinates(BaseModel): latitude: float=Field(ge=-90, le=90); longitude: float=Field(ge=-180, le=180)
class ORMBase(BaseModel): model_config=ConfigDict(from_attributes=True)
''',
'app/schemas/auth.py': r'''from pydantic import BaseModel, EmailStr, Field
from app.models.models import Role
class RegisterIn(BaseModel): name: str=Field(min_length=2,max_length=160); email: EmailStr; password: str=Field(min_length=8); phone: str|None=None; role: Role=Role.CITIZEN
class LoginIn(BaseModel): email: EmailStr; password: str
class RefreshIn(BaseModel): refresh_token: str
class UserOut(BaseModel): id: str; name: str; email: str; role: Role; is_active: bool
class TokenOut(BaseModel): access_token: str; refresh_token: str; token_type: str='bearer'
''',
'app/schemas/domain.py': r'''from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from app.models.models import *
class LocationIn(BaseModel): bus_id: UUID; latitude: float=Field(ge=-90,le=90); longitude: float=Field(ge=-180,le=180); speed: float|None=Field(default=None,ge=0); heading: float|None=None; accuracy: float|None=Field(default=None,ge=0); timestamp: datetime|None=None; client_event_id: str|None=None
class DetectionIn(BaseModel): bus_id: UUID|None=None; detection_type: DetectionType; confidence: float=Field(ge=0,le=1); latitude: float|None=Field(default=None,ge=-90,le=90); longitude: float|None=Field(default=None,ge=-180,le=180); timestamp: datetime|None=None; frame_number: int|None=None; evidence_id: UUID|None=None; model_name: str; model_version: str; metadata: dict={}
class DefectIn(BaseModel): defect_type: str; severity: str; confidence: float=Field(ge=0,le=1); latitude: float=Field(ge=-90,le=90); longitude: float=Field(ge=-180,le=180); bus_id: UUID|None=None; evidence_id: UUID|None=None
class TrafficIn(BaseModel): cars:int=0; bikes:int=0; buses:int=0; trucks:int=0; autos:int=0; average_speed:float|None=None; latitude:float=Field(ge=-90,le=90); longitude:float=Field(ge=-180,le=180); traffic_density: Density
class IncidentIn(BaseModel): incident_type: IncidentType; priority: Priority; description: str|None=None; latitude:float=Field(ge=-90,le=90); longitude:float=Field(ge=-180,le=180); bus_id:UUID|None=None; vehicle_id:UUID|None=None; confidence:float|None=Field(default=None,ge=0,le=1)
class StatusIn(BaseModel): status: str
class ReportIn(BaseModel): problem_type:str; description:str|None=None; latitude:float=Field(ge=-90,le=90); longitude:float=Field(ge=-180,le=180); image_url:str|None=None
''',
'app/api/deps.py': r'''from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.models import User, Role
from app.core.security import decode_token
oauth2=OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login')
async def current_user(token: Annotated[str, Depends(oauth2)], db: Annotated[AsyncSession, Depends(get_db)]):
    try: payload=decode_token(token)
    except Exception: raise HTTPException(status_code=401, detail='Invalid or expired token')
    if payload.get('kind')!='access': raise HTTPException(status_code=401, detail='Access token required')
    user=await db.get(User, payload.get('sub'))
    if not user or not user.is_active: raise HTTPException(status_code=401, detail='Inactive user')
    return user
def require_roles(*roles):
    async def dep(user=Depends(current_user)):
        if user.role not in roles: raise HTTPException(status_code=403, detail='Insufficient permissions')
        return user
    return dep
''',
'app/api/v1/auth.py': r'''from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.models import User, Role
from app.schemas.auth import *
from app.core.security import *
from app.api.deps import current_user
router=APIRouter(prefix='/auth', tags=['Authentication'])
@router.post('/register', response_model=Envelope[UserOut])
async def register(data:RegisterIn, db:AsyncSession=Depends(get_db)):
    if (await db.execute(select(User).where(User.email==data.email))).scalar_one_or_none(): raise HTTPException(409,'Email already registered')
    user=User(name=data.name,email=data.email,phone=data.phone,password_hash=hash_password(data.password),role=data.role); db.add(user); await db.commit(); await db.refresh(user)
    return {'data': {'id':str(user.id),'name':user.name,'email':user.email,'role':user.role,'is_active':user.is_active}}
@router.post('/login', response_model=Envelope[TokenOut])
async def login(data:LoginIn, db:AsyncSession=Depends(get_db)):
    user=(await db.execute(select(User).where(User.email==data.email))).scalar_one_or_none()
    if not user or not verify_password(data.password,user.password_hash): raise HTTPException(401,'Invalid credentials')
    access=create_token(str(user.id),user.role.value,'access',timedelta(minutes=settings.jwt_access_token_expire_minutes)); refresh=create_token(str(user.id),user.role.value,'refresh',timedelta(days=settings.jwt_refresh_token_expire_days))
    return {'data': {'access_token':access,'refresh_token':refresh}}
@router.get('/me', response_model=Envelope[UserOut])
async def me(user=Depends(current_user)): return {'data': {'id':str(user.id),'name':user.name,'email':user.email,'role':user.role,'is_active':user.is_active}}
''',
'app/api/v1/crud.py': r'''from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
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
''',
'app/api/v1/analytics.py': r'''from fastapi import APIRouter, Depends, Query
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
''',
'app/main.py': r'''from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.api.v1.auth import router as auth_router
from app.api.v1.crud import router as crud_router
from app.api.v1.analytics import router as analytics_router
app=FastAPI(title=settings.app_name,version='1.0.0',description='Secure urban intelligence backend for public transport fleets')
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins,allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
limiter=Limiter(key_func=get_remote_address,default_limits=[f'{settings.rate_limit_per_minute}/minute'])
app.state.limiter=limiter
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc): return JSONResponse(status_code=429,content={'success':False,'error':{'code':'RATE_LIMITED','message':'Too many requests'}})
@app.get('/health')
async def health(): return {'status':'ok','service':'urbansense-api'}
@app.get('/ready')
async def ready(): return {'status':'ready'}
app.include_router(auth_router,prefix='/api/v1'); app.include_router(crud_router,prefix='/api/v1'); app.include_router(analytics_router,prefix='/api/v1')
''',
'ai_service/models/interfaces.py': r'''from dataclasses import dataclass
from typing import Protocol
@dataclass
class AIResult: label:str; confidence:float; model_name:str; model_version:str; metadata:dict
class Detector(Protocol):
    def detect(self, image: bytes) -> list[AIResult]: ...
class OCRProvider(Protocol):
    def recognize(self, image: bytes) -> tuple[str,float]: ...
class StubDetector:
    def detect(self,image:bytes): return []
class StubOCR:
    def recognize(self,image:bytes): return '',0.0
''',
'ai_service/main.py': r'''from fastapi import FastAPI, UploadFile, File
from ai_service.models.interfaces import StubDetector, StubOCR
app=FastAPI(title='UrbanSense AI Worker')
detector=StubDetector(); ocr=StubOCR()
@app.get('/health')
async def health(): return {'status':'ok','models':'adapter-ready'}
@app.post('/detect')
async def detect(file:UploadFile=File(...)): return {'results':[r.__dict__ for r in detector.detect(await file.read())]}
@app.post('/ocr')
async def process_ocr(file:UploadFile=File(...)):
    plate,confidence=ocr.recognize(await file.read()); return {'plate_number':plate,'ocr_confidence':confidence,'verification_status':'VERIFIED' if confidence>=0.85 else 'NEEDS_VERIFICATION'}
''',
'alembic/env.py': r'''from logging.config import fileConfig
from sqlalchemy import engine_from_config,pool
from alembic import context
from app.db.session import Base
from app.models import models
config=context.config
target_metadata=Base.metadata
if config.config_file_name: fileConfig(config.config_file_name)
def run_migrations_offline(): context.configure(url=config.get_main_option('sqlalchemy.url'),target_metadata=target_metadata,literal_binds=True,dialect_opts={'paramstyle':'named'}); 
with context.begin_transaction(): context.run_migrations()
def run_migrations_online():
    connectable=engine_from_config(config.get_section(config.config_ini_section,{}),prefix='sqlalchemy.',poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection,target_metadata=target_metadata)
        with context.begin_transaction(): context.run_migrations()
if context.is_offline_mode(): run_migrations_offline()
else: run_migrations_online()
''',
'Dockerfile': r'''FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
''',
'pytest.ini': '[pytest]\nasyncio_mode = auto\n',
'README.md': r'''# AI UrbanSense Central Backend

A FastAPI backend and modular AI-service foundation for public-transport urban intelligence. It provides JWT/RBAC authentication, fleet and GPS ingestion, AI detections, road defects, traffic and vehicle records, incidents, citizen reports, analytics, GeoJSON heatmaps, and an adapter boundary for YOLO/OCR/tracking.

## Run locally

```bash
cp .env.example .env
docker compose up --build
```

The API is available at `http://localhost:8000`, Swagger at `/docs`, ReDoc at `/redoc`, MinIO at `http://localhost:9001`, and the AI worker is available with `docker compose --profile worker up --build`.

## Database and seed data

```bash
alembic upgrade head
python -m app.seed
```

The local Compose database is PostGIS-enabled. The current service keeps geographic coordinates in validated latitude/longitude columns and exposes GeoJSON heatmap output; a production migration can add native `geometry(Point,4326)` columns and GiST indexes without changing client contracts.

## Authentication

Register at `POST /api/v1/auth/register`, log in at `POST /api/v1/auth/login`, and send `Authorization: Bearer <access_token>` to protected endpoints. Roles are `ADMIN`, `AUTHORITY`, `DRIVER`, and `CITIZEN`; privileged endpoints enforce role and ownership checks.

## Configuration and production notes

All secrets and provider settings are environment variables. MinIO is the local storage target; an S3-compatible storage adapter should be enabled for production evidence. AI weights are intentionally not committed: implement a YOLO/OpenCV/ByteTrack/PaddleOCR provider behind `ai_service/models/interfaces.py` and configure model name/version in every result. Low-confidence OCR is returned as `NEEDS_VERIFICATION`. Large media belongs in object storage, not PostgreSQL. Use a reverse proxy with TLS, managed PostgreSQL/PostGIS, Redis, object storage, and a long-lived WebSocket-capable deployment for production.

## API scope

All routes are versioned under `/api/v1`. The backend deliberately does not implement the Flutter mobile application or React admin dashboard; their integration contract is the generated OpenAPI document.
''',
'app/seed.py': r'''import asyncio
from app.db.session import AsyncSessionLocal, engine, Base
from app.models.models import User,Route,Bus,BusStatus,Role
from app.core.security import hash_password
async def main():
    async with engine.begin() as conn: await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        admin=User(name='System Admin',email='admin@urbansense.local',password_hash=hash_password('ChangeMe123!'),role=Role.ADMIN); db.add(admin)
        routes=[Route(name=f'Route {i}',code=f'R{i:02d}',origin=f'Origin {i}',destination=f'Destination {i}') for i in range(1,6)]; db.add_all(routes); await db.flush()
        db.add_all([Bus(bus_number=f'BUS-{i:03d}',registration_number=f'WB{i:02d}AB{i:04d}',route_id=routes[(i-1)%5].id,status=BusStatus.ACTIVE if i<8 else BusStatus.INACTIVE) for i in range(1,11)]); await db.commit()
    print('Seeded admin, 5 routes, and 10 buses. Login: admin@urbansense.local / ChangeMe123!')
if __name__=='__main__': asyncio.run(main())
''',
}
for rel, text in files.items():
    p=root/rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)
(root/'alembic/versions/0001_initial.py').write_text("from alembic import op\nimport sqlalchemy as sa\n\ndef upgrade():\n    # The canonical schema is created from SQLAlchemy metadata for local bootstrapping.\n    from app.db.session import Base\n    from app.models import models\n    bind=op.get_bind(); Base.metadata.create_all(bind=bind)\n\ndef downgrade():\n    from app.db.session import Base\n    from app.models import models\n    bind=op.get_bind(); Base.metadata.drop_all(bind=bind)\n")
(root/'app/models/__init__.py').write_text('from app.models.models import *\n')
print(f'Wrote {len(files)+1} backend files')
