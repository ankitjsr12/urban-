from typing import Annotated
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
