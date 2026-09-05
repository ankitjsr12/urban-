import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.bus import Bus
    from app.models.user import User


class DriverStatus(str, enum.Enum):
    """Driver duty status."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ON_LEAVE = "ON_LEAVE"
    SUSPENDED = "SUSPENDED"


class Driver(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Public transport bus driver profile."""
    __tablename__ = "drivers"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    employee_id: Mapped[str] = mapped_column(
        String(80),
        unique=True,
        index=True,
        nullable=False,
    )
    license_number: Mapped[str] = mapped_column(
        String(80),
        unique=True,
        index=True,
        nullable=False,
    )
    license_expiry: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    phone: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )
    status: Mapped[DriverStatus] = mapped_column(
        Enum(DriverStatus, name="driver_status_enum", native_enum=False),
        default=DriverStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("status", DriverStatus.ACTIVE)
        super().__init__(*args, **kwargs)

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="driver",
        foreign_keys=[user_id],
    )
    assigned_buses: Mapped[list["Bus"]] = relationship(
        "Bus",
        back_populates="driver",
        foreign_keys="Bus.assigned_driver_id",
    )
