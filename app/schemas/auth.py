from pydantic import BaseModel, Field
from app.models.user import Role


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8)
    phone: str | None = None
    role: Role = Role.CITIZEN


class LoginIn(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class LogoutIn(BaseModel):
    refresh_token: str | None = None


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: Role
    is_active: bool
    phone: str | None = None
    is_verified: bool = False


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'
