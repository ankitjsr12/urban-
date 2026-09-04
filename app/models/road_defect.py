import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from geoalchemy2 import Geography
from sqlalchemy import CheckConstraint, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from app.models.bus import Bus
    from app.models.user import User


class RoadDefectType(str, enum.Enum):
    """Classification of road surface and infrastructure anomalies."""
    POTHOLE = "POTHOLE"
    WATERLOGGING = "WATERLOGGING"
    CRACK = "CRACK"
    ROAD_DAMAGE = "ROAD_DAMAGE"
    OBSTRUCTION = "OBSTRUCTION"
    OTHER = "OTHER"


class DefectSeverity(str, enum.Enum):
    """Urgency level of a road defect."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DefectStatus(str, enum.Enum):
    """Lifecycle status of a reported or detected road defect."""
    OPEN = "OPEN"
    VERIFIED = "VERIFIED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"
    # Backward compatibility
    DETECTED = "DETECTED"
    ASSIGNED = "ASSIGNED"


class RoadDefect(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Aggregated or verified road surface defect requiring municipal action."""
    __tablename__ = "road_defects"
    __table_args__ = (
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="chk_road_defect_confidence_range"),
    )

    defect_type: Mapped[RoadDefectType] = mapped_column(
        Enum(RoadDefectType, name="road_defect_type_enum", native_enum=False),
        index=True,
        nullable=False,
    )
    severity: Mapped[DefectSeverity] = mapped_column(
        Enum(DefectSeverity, name="defect_severity_enum", native_enum=False),
        default=DefectSeverity.MEDIUM,
        index=True,
        nullable=False,
    )
    status: Mapped[DefectStatus] = mapped_column(
        Enum(DefectStatus, name="defect_status_enum", native_enum=False),
        default=DefectStatus.OPEN,
        index=True,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    location: Mapped[Any | None] = mapped_column(
        Geography(
            geometry_type="POINT",
            srid=4326,
            spatial_index=True,
            from_text="ST_GeogFromText",
            name="geography",
        ),
        nullable=True,
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    detected_by_bus_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("buses.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    model_name: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )
    model_version: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )
    evidence_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
        nullable=False,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_json: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        server_default="{}",
        nullable=False,
    )

    # Backward compatibility alias
    @property
    def bus_id(self) -> uuid.UUID | None:
        return self.detected_by_bus_id

    @bus_id.setter
    def bus_id(self, val: uuid.UUID | None) -> None:
        self.detected_by_bus_id = val

    def __init__(self, *args, **kwargs):
        if "bus_id" in kwargs and "detected_by_bus_id" not in kwargs:
            kwargs["detected_by_bus_id"] = kwargs.pop("bus_id")
        if "metadata" in kwargs and "metadata_json" not in kwargs:
            kwargs["metadata_json"] = kwargs.pop("metadata")
        kwargs.setdefault("severity", DefectSeverity.MEDIUM)
        kwargs.setdefault("status", DefectStatus.OPEN)
        kwargs.setdefault("detected_at", utc_now())
        kwargs.setdefault("metadata_json", {})
        lat = kwargs.get("latitude")
        lon = kwargs.get("longitude")
        if lat is not None and lon is not None and "location" not in kwargs:
            kwargs["location"] = f"SRID=4326;POINT({lon} {lat})"
        super().__init__(*args, **kwargs)

    # Relationships
    bus: Mapped[Optional["Bus"]] = relationship(
        "Bus",
        back_populates="road_defects",
        foreign_keys=[detected_by_bus_id],
    )
    resolver: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[resolved_by],
    )
