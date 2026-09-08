"""User Management API for UrbanSense.

Provides administrative controls for listing, inspecting, updating roles,
and managing activation status of platform accounts.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user
from app.db.session import get_db
from app.models.user import Role, User
from app.schemas.auth import UserOut
from app.schemas.common import Envelope
from app.services.audit import AuditService

router = APIRouter(prefix="/users", tags=["Users"])


class UserUpdateIn(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=160)
    phone: Optional[str] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


@router.get("", response_model=Envelope[dict])
async def list_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    role: Optional[Role] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(current_user),
):
    """List platform users (Admin only)."""
    if admin.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")

    stmt = select(User)
    count_stmt = select(func.count(User.id))

    if role is not None:
        stmt = stmt.where(User.role == role)
        count_stmt = count_stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
        count_stmt = count_stmt.where(User.is_active == is_active)
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(User.email.ilike(pattern) | User.full_name.ilike(pattern))
        count_stmt = count_stmt.where(User.email.ilike(pattern) | User.full_name.ilike(pattern))

    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)
    users = (await db.execute(stmt)).scalars().all()

    items = [
        {
            "id": str(u.id),
            "name": u.full_name,
            "email": u.email,
            "role": u.role.value if hasattr(u.role, "value") else str(u.role),
            "is_active": u.is_active,
            "phone": u.phone,
            "is_verified": u.is_verified,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        }
        for u in users
    ]

    return {
        "data": {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    }


@router.get("/{user_id}", response_model=Envelope[dict])
async def get_user_detail(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    caller: User = Depends(current_user),
):
    """Get user profile details (Admin or self)."""
    if caller.role != Role.ADMIN and caller.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {
        "data": {
            "id": str(user.id),
            "name": user.full_name,
            "email": user.email,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
            "is_active": user.is_active,
            "phone": user.phone,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        }
    }


@router.patch("/{user_id}", response_model=Envelope[dict])
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdateIn,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(current_user),
):
    """Update user attributes or roles (Admin only)."""
    if admin.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.name is not None:
        user.full_name = payload.name
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.is_verified is not None:
        user.is_verified = payload.is_verified

    await db.commit()
    await db.refresh(user)

    await AuditService.log_action(
        db=db,
        action="USER_UPDATED",
        user_id=admin.id,
        resource_type="User",
        resource_id=str(user.id),
        metadata={"updated_fields": payload.model_dump(exclude_unset=True)},
    )

    return {
        "data": {
            "id": str(user.id),
            "name": user.full_name,
            "email": user.email,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
            "is_active": user.is_active,
            "phone": user.phone,
            "is_verified": user.is_verified,
        }
    }


@router.delete("/{user_id}", response_model=Envelope[dict])
async def deactivate_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(current_user),
):
    """Deactivate a user account (Admin only)."""
    if admin.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")

    if admin.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate own account")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = False
    await db.commit()

    await AuditService.log_action(
        db=db,
        action="USER_DEACTIVATED",
        user_id=admin.id,
        resource_type="User",
        resource_id=str(user.id),
    )

    return {"data": {"id": str(user.id), "is_active": False}, "message": "User successfully deactivated"}
