import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from geoalchemy2 import Geography
from sqlalchemy import CheckConstraint, DateTime, Enum, Float, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from app.models.bus import Bus


class VehicleType(str, enum.Enum):
    """Types of tracked vehicles on urban road networks."""
    CAR = "CAR"
    BUS = "BUS"
    TRUCK = "TRUCK"
    MOTORCYCLE = "MOTORCYCLE"
    AUTO = "AUTO"
    BICYCLE = "BICYCLE"
    OTHER = "OTHER"


class Vehicle(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tracked vehicle identity across observation frames with ANPR/license plate indexing."""
    __tablename__ = "vehicles"

    plate_number: Mapped[str | None] = mapped_column(
        String(40),
        index=True,
        nullable=True,
    )
    vehicle_type: Mapped[VehicleType] = mapped_column(
        Enum(VehicleType, name="vehicle_type_enum", native_enum=False),
        default=VehicleType.CAR,
        index=True,
        nullable=False,
    )
    make: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )
    model: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )
    color: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )
    tracking_id: Mapped[str | None] = mapped_column(
        String(100),
        index=True,
        nullable=True,
    )
    ocr_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    ocr_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )
    first_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=True,
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
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
        kwargs.setdefault("vehicle_type", VehicleType.CAR)
        kwargs.setdefault("first_seen_at", utc_now())
        kwargs.setdefault("last_seen_at", utc_now())
        kwargs.setdefault("metadata_json", {})
        super().__init__(*args, **kwargs)

    # Relationships
    vehicle_detections: Mapped[list["VehicleDetection"]] = relationship(
        "VehicleDetection",
        back_populates="vehicle",
        cascade="all, delete-orphan",
        foreign_keys="VehicleDetection.vehicle_id",
    )


class VehicleDetection(UUIDPrimaryKeyMixin, Base):
    """Observation instance of a vehicle detected by on-bus edge cameras."""
    __tablename__ = "vehicle_detections"
    __table_args__ = (
        Index("ix_vehicle_detections_bus_id_detected_at", "bus_id", "detected_at"),
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="chk_vehicle_detection_confidence_range"),
    )

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    bus_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("buses.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    detection_type: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )
    vehicle_type: Mapped[VehicleType | None] = mapped_column(
        Enum(VehicleType, name="vd_vehicle_type_enum", native_enum=False),
        nullable=True,
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    tracking_id: Mapped[str | None] = mapped_column(
        String(100),
        index=True,
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
    model_name: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )
    model_version: Mapped[str | None] = mapped_column(
        String(80),
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
    def timestamp(self) -> datetime:
        return self.detected_at

    @timestamp.setter
    def timestamp(self, val: datetime) -> None:
        self.detected_at = val

    def __init__(self, *args, **kwargs):
        if "timestamp" in kwargs and "detected_at" not in kwargs:
            kwargs["detected_at"] = kwargs.pop("timestamp")
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
    vehicle: Mapped["Vehicle"] = relationship(
        "Vehicle",
        back_populates="vehicle_detections",
        foreign_keys=[vehicle_id],
    )
    bus: Mapped[Optional["Bus"]] = relationship(
        "Bus",
        back_populates="vehicle_detections",
        foreign_keys=[bus_id],
    )
