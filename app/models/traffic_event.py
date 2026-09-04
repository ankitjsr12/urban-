import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from geoalchemy2 import Geography
from sqlalchemy import CheckConstraint, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from app.models.bus import Bus


class TrafficEventType(str, enum.Enum):
    """Types of urban traffic occurrences and flow impediments."""
    CONGESTION = "CONGESTION"
    ACCIDENT = "ACCIDENT"
    ROAD_BLOCK = "ROAD_BLOCK"
    SLOW_TRAFFIC = "SLOW_TRAFFIC"
    HEAVY_TRAFFIC = "HEAVY_TRAFFIC"
    SIGNAL_FAILURE = "SIGNAL_FAILURE"
    OTHER = "OTHER"


class TrafficSeverity(str, enum.Enum):
    """Traffic congestion severity rating."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Backward compatibility alias
Density = TrafficSeverity


class TrafficEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Aggregated traffic condition event detected from road fleet telemetry."""
    __tablename__ = "traffic_events"
    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)",
            name="chk_traffic_event_confidence_range",
        ),
    )

    event_type: Mapped[TrafficEventType] = mapped_column(
        Enum(TrafficEventType, name="traffic_event_type_enum", native_enum=False),
        default=TrafficEventType.CONGESTION,
        index=True,
        nullable=False,
    )
    severity: Mapped[TrafficSeverity] = mapped_column(
        Enum(TrafficSeverity, name="traffic_severity_enum", native_enum=False),
        default=TrafficSeverity.MEDIUM,
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
    bus_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("buses.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    confidence: Mapped[float | None] = mapped_column(
        Float,
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
    cars: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    bikes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    buses_count: Mapped[int] = mapped_column(
        "buses",
        Integer,
        default=0,
        nullable=False,
    )
    trucks: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    autos: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    total_vehicles: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    average_speed: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    metadata_json: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        server_default="{}",
        nullable=False,
    )

    # Backward compatibility aliases
    @property
    def traffic_density(self) -> TrafficSeverity:
        return self.severity

    @traffic_density.setter
    def traffic_density(self, val: TrafficSeverity) -> None:
        self.severity = val

    @property
    def timestamp(self) -> datetime:
        return self.detected_at

    @timestamp.setter
    def timestamp(self, val: datetime) -> None:
        self.detected_at = val

    @property
    def buses(self) -> int:
        return self.buses_count

    @buses.setter
    def buses(self, val: int) -> None:
        self.buses_count = val

    def __init__(self, *args, **kwargs):
        if "traffic_density" in kwargs and "severity" not in kwargs:
            kwargs["severity"] = kwargs.pop("traffic_density")
        if "timestamp" in kwargs and "detected_at" not in kwargs:
            kwargs["detected_at"] = kwargs.pop("timestamp")
        if "buses" in kwargs and "buses_count" not in kwargs:
            kwargs["buses_count"] = kwargs.pop("buses")
        if "metadata" in kwargs and "metadata_json" not in kwargs:
            kwargs["metadata_json"] = kwargs.pop("metadata")
        kwargs.setdefault("event_type", TrafficEventType.CONGESTION)
        kwargs.setdefault("severity", TrafficSeverity.MEDIUM)
        kwargs.setdefault("detected_at", utc_now())
        kwargs.setdefault("cars", 0)
        kwargs.setdefault("bikes", 0)
        kwargs.setdefault("buses_count", 0)
        kwargs.setdefault("trucks", 0)
        kwargs.setdefault("autos", 0)
        kwargs.setdefault("total_vehicles", 0)
        kwargs.setdefault("metadata_json", {})
        lat = kwargs.get("latitude")
        lon = kwargs.get("longitude")
        if lat is not None and lon is not None and "location" not in kwargs:
            kwargs["location"] = f"SRID=4326;POINT({lon} {lat})"
        super().__init__(*args, **kwargs)

    # Relationships
    bus: Mapped[Optional["Bus"]] = relationship(
        "Bus",
        back_populates="traffic_events",
        foreign_keys=[bus_id],
    )
