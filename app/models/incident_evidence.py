import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.user import User


class StorageProvider(str, enum.Enum):
    """Supported cloud and local object storage providers."""
    MINIO = "MINIO"
    AWS_S3 = "AWS_S3"
    CLOUDINARY = "CLOUDINARY"
    LOCAL = "LOCAL"


class EvidenceType(str, enum.Enum):
    """Classification of digital evidence artifact."""
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    FRAME = "FRAME"
    OCR_RESULT = "OCR_RESULT"
    AI_RESULT = "AI_RESULT"


class IncidentEvidence(UUIDPrimaryKeyMixin, Base):
    """Digital evidence object references (images/video snippets) linked to incidents.
    
    Binary video and image data must never be stored in the database.
    Only object storage pointers and cryptographic hashes are persisted.
    """
    __tablename__ = "incident_evidence"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    storage_provider: Mapped[StorageProvider] = mapped_column(
        Enum(StorageProvider, name="storage_provider_enum", native_enum=False),
        default=StorageProvider.MINIO,
        nullable=False,
    )
    object_key: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    object_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    mime_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    checksum: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    duration_seconds: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    captured_at: Mapped[datetime | None] = mapped_column(
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
    def file_url(self) -> str:
        return self.object_url

    @file_url.setter
    def file_url(self, val: str) -> None:
        self.object_url = val

    def __init__(self, *args, **kwargs):
        if "file_url" in kwargs and "object_url" not in kwargs:
            kwargs["object_url"] = kwargs.pop("file_url")
        if "metadata" in kwargs and "metadata_json" not in kwargs:
            kwargs["metadata_json"] = kwargs.pop("metadata")
        kwargs.setdefault("storage_provider", StorageProvider.MINIO)
        kwargs.setdefault("metadata_json", {})
        kwargs.setdefault("created_at", utc_now())
        super().__init__(*args, **kwargs)

    # Relationships
    incident: Mapped["Incident"] = relationship(
        "Incident",
        back_populates="evidence",
        foreign_keys=[incident_id],
    )
    uploader: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[uploaded_by],
    )
