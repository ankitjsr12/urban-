import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from geoalchemy2 import Geography
from sqlalchemy import CheckConstraint, DateTime, Enum, Float, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from app.models.bus import Bus


class DetectionType(str, enum.Enum):
    """Types of objects, hazards, and infrastructure detected by edge AI."""
    PERSON = "PERSON"
    VEHICLE = "VEHICLE"
    POTHOLE = "POTHOLE"
    WATERLOGGING = "WATERLOGGING"
    ROAD_DAMAGE = "ROAD_DAMAGE"
    TRAFFIC_SIGN = "TRAFFIC_SIGN"
    ZEBRA_CROSSING = "ZEBRA_CROSSING"
    OBSTRUCTION = "OBSTRUCTION"
    PEDESTRIAN = "PEDESTRIAN"
    DAMAGED_ROAD = "DAMAGED_ROAD"
    ROAD_DIVIDER = "ROAD_DIVIDER"
    CHILD_RISK = "CHILD_RISK"
    TRAFFIC_HAZARD = "TRAFFIC_HAZARD"
    OTHER = "OTHER"


class Detection(UUIDPrimaryKeyMixin, Base):
    """Raw computer vision detection output from vehicle-mounted edge camera units."""
    __tablename__ = "detections"
    __table_args__ = (
        Index("ix_detections_bus_id_detected_at", "bus_id", "detected_at"),
        Index("ix_detections_type_detected_at", "detection_type", "detected_at"),
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="chk_detection_confidence_range"),
    )

    bus_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("buses.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    detection_type: Mapped[DetectionType] = mapped_column(
        Enum(DetectionType, name="detection_type_enum", native_enum=False),
        index=True,
        nullable=False,
    )
    class_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    bounding_box: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
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
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    model_version: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )
    tracking_id: Mapped[str | None] = mapped_column(
        String(100),
        index=True,
        nullable=True,
    )
    frame_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    evidence_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
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

    # Backward compatibility aliases
    @property
    def timestamp(self) -> datetime:
        return self.detected_at

    @timestamp.setter
    def timestamp(self, val: datetime) -> None:
        self.detected_at = val

    @property
    def frame_number(self) -> int | None:
        return self.frame_id

    @frame_number.setter
    def frame_number(self, val: int | None) -> None:
        self.frame_id = val

    def __init__(self, *args, **kwargs):
        if "timestamp" in kwargs and "detected_at" not in kwargs:
            kwargs["detected_at"] = kwargs.pop("timestamp")
        if "frame_number" in kwargs and "frame_id" not in kwargs:
            kwargs["frame_id"] = kwargs.pop("frame_number")
        if "metadata" in kwargs and "metadata_json" not in kwargs:
            kwargs["metadata_json"] = kwargs.pop("metadata")
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
        back_populates="detections",
        foreign_keys=[bus_id],
    )
