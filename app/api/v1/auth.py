from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.models import User, Role
from app.schemas.auth import *
from app.schemas.common import Envelope
from app.core.config import settings
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
