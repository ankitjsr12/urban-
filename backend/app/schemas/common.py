from datetime import datetime
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field, field_validator
T=TypeVar('T')
class Envelope(BaseModel, Generic[T]): success: bool=True; data: T|None=None; message: str='Operation successful'
class ErrorDetail(BaseModel): code: str; message: str
class ErrorEnvelope(BaseModel): success: bool=False; error: ErrorDetail
class Page(BaseModel, Generic[T]): items: list[T]; total: int; limit: int; offset: int
class Coordinates(BaseModel): latitude: float=Field(ge=-90, le=90); longitude: float=Field(ge=-180, le=180)
class ORMBase(BaseModel): model_config=ConfigDict(from_attributes=True)
