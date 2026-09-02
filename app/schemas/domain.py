from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from app.models.models import *
from uuid import UUID
class LocationIn(BaseModel): bus_id: UUID; latitude: float=Field(ge=-90,le=90); longitude: float=Field(ge=-180,le=180); speed: float|None=Field(default=None,ge=0); heading: float|None=None; accuracy: float|None=Field(default=None,ge=0); timestamp: datetime|None=None; client_event_id: str|None=None
class DetectionIn(BaseModel): bus_id: UUID|None=None; detection_type: DetectionType; confidence: float=Field(ge=0,le=1); latitude: float|None=Field(default=None,ge=-90,le=90); longitude: float|None=Field(default=None,ge=-180,le=180); timestamp: datetime|None=None; frame_number: int|None=None; evidence_id: UUID|None=None; model_name: str; model_version: str; metadata: dict={}
class DefectIn(BaseModel): defect_type: str; severity: str; confidence: float=Field(ge=0,le=1); latitude: float=Field(ge=-90,le=90); longitude: float=Field(ge=-180,le=180); bus_id: UUID|None=None; evidence_id: UUID|None=None
class TrafficIn(BaseModel): cars:int=0; bikes:int=0; buses:int=0; trucks:int=0; autos:int=0; average_speed:float|None=None; latitude:float=Field(ge=-90,le=90); longitude:float=Field(ge=-180,le=180); traffic_density: Density
class IncidentIn(BaseModel): incident_type: IncidentType; priority: Priority; description: str|None=None; latitude:float=Field(ge=-90,le=90); longitude:float=Field(ge=-180,le=180); bus_id:UUID|None=None; vehicle_id:UUID|None=None; confidence:float|None=Field(default=None,ge=0,le=1)
class StatusIn(BaseModel): status: str
class ReportIn(BaseModel): problem_type:str; description:str|None=None; latitude:float=Field(ge=-90,le=90); longitude:float=Field(ge=-180,le=180); image_url:str|None=None
