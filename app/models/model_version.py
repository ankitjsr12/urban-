import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AIModelType(str, enum.Enum):
    """Computer vision and deep learning model categories deployed at the edge/cloud."""
    OBJECT_DETECTION = "OBJECT_DETECTION"
    ROAD_DEFECT = "ROAD_DEFECT"
    VEHICLE_DETECTION = "VEHICLE_DETECTION"
    OCR = "OCR"
    ANPR = "ANPR"
    TRAFFIC = "TRAFFIC"


class ModelVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Registry and deployment tracker for edge and cloud AI model artifacts."""
    __tablename__ = "model_versions"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_model_versions_name_version"),
    )

    name: Mapped[str] = mapped_column(
        String(120),
        index=True,
        nullable=False,
    )
    version: Mapped[str] = mapped_column(
        String(80),
        index=True,
        nullable=False,
    )
    model_type: Mapped[AIModelType] = mapped_column(
        Enum(AIModelType, name="ai_model_type_enum", native_enum=False),
        default=AIModelType.OBJECT_DETECTION,
        index=True,
        nullable=False,
    )
    framework: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )
    file_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
        nullable=False,
    )
    deployed_at: Mapped[datetime | None] = mapped_column(
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

    def __init__(self, *args, **kwargs):
        if "metadata" in kwargs and "metadata_json" not in kwargs:
            kwargs["metadata_json"] = kwargs.pop("metadata")
        kwargs.setdefault("model_type", AIModelType.OBJECT_DETECTION)
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("metadata_json", {})
        super().__init__(*args, **kwargs)
