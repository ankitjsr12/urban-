import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from app.models.user import User


class NotificationType(str, enum.Enum):
    """Notification dispatch categories."""
    ALERT = "ALERT"
    INCIDENT = "INCIDENT"
    SYSTEM = "SYSTEM"
    DEFECT = "DEFECT"
    DISPATCH = "DISPATCH"
    SMS = "SMS"
    EMAIL = "EMAIL"
    PUSH = "PUSH"


class Notification(UUIDPrimaryKeyMixin, Base):
    """Multi-channel notifications targeted to users and drivers."""
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type_enum", native_enum=False),
        default=NotificationType.ALERT,
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        nullable=False,
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    metadata_json: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        server_default="{}",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )

    # Backward compatibility alias
    @property
    def body(self) -> str:
        return self.message

    @body.setter
    def body(self, val: str) -> None:
        self.message = val

    def __init__(self, *args, **kwargs):
        if "body" in kwargs and "message" not in kwargs:
            kwargs["message"] = kwargs.pop("body")
        if "metadata" in kwargs and "metadata_json" not in kwargs:
            kwargs["metadata_json"] = kwargs.pop("metadata")
        kwargs.setdefault("notification_type", NotificationType.ALERT)
        kwargs.setdefault("is_read", False)
        kwargs.setdefault("metadata_json", {})
        kwargs.setdefault("created_at", utc_now())
        super().__init__(*args, **kwargs)

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="notifications",
        foreign_keys=[user_id],
    )
