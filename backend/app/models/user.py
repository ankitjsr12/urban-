import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, generate_uuid, utc_now

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.citizen_report import CitizenReport
    from app.models.driver import Driver
    from app.models.incident import Incident
    from app.models.notification import Notification


class Role(str, enum.Enum):
    """System user roles."""
    ADMIN = "ADMIN"
    AUTHORITY = "AUTHORITY"
    DRIVER = "DRIVER"
    CITIZEN = "CITIZEN"


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """User accounts across all roles (Admin, Authority, Driver, Citizen)."""
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    phone: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )
    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )
    role: Mapped[Role] = mapped_column(
        Enum(Role, name="user_role_enum", native_enum=False),
        default=Role.CITIZEN,
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Backward compatibility alias for existing code referencing user.name
    @property
    def name(self) -> str:
        return self.full_name

    @name.setter
    def name(self, val: str) -> None:
        self.full_name = val

    def __init__(self, *args, **kwargs):
        if "name" in kwargs and "full_name" not in kwargs:
            kwargs["full_name"] = kwargs.pop("name")
        kwargs.setdefault("role", Role.CITIZEN)
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("is_verified", False)
        super().__init__(*args, **kwargs)

    # Relationships
    driver: Mapped[Optional["Driver"]] = relationship(
        "Driver",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    citizen_reports: Mapped[list["CitizenReport"]] = relationship(
        "CitizenReport",
        back_populates="citizen",
        cascade="all, delete-orphan",
        foreign_keys="CitizenReport.citizen_id",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="Notification.user_id",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        foreign_keys="AuditLog.user_id",
    )
    reported_incidents: Mapped[list["Incident"]] = relationship(
        "Incident",
        back_populates="reporter",
        foreign_keys="Incident.reported_by",
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="RefreshToken.user_id",
    )


class RefreshToken(UUIDPrimaryKeyMixin, Base):
    """Refresh token records for JWT rotation and revocation."""
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("revoked", False)
        kwargs.setdefault("created_at", utc_now())
        super().__init__(*args, **kwargs)

    user: Mapped["User"] = relationship(
        "User",
        back_populates="refresh_tokens",
    )
