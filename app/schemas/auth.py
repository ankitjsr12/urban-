from pydantic import BaseModel, EmailStr, Field
from app.models.models import Role
class RegisterIn(BaseModel): name: str=Field(min_length=2,max_length=160); email: EmailStr; password: str=Field(min_length=8); phone: str|None=None; role: Role=Role.CITIZEN
class LoginIn(BaseModel): email: EmailStr; password: str
class RefreshIn(BaseModel): refresh_token: str
class UserOut(BaseModel): id: str; name: str; email: str; role: Role; is_active: bool
class TokenOut(BaseModel): access_token: str; refresh_token: str; token_type: str='bearer'
