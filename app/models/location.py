import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from geoalchemy2 import Geography
from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from app.models.bus import Bus


class BusLocation(UUIDPrimaryKeyMixin, Base):
    """High-frequency GPS and telemetry stream records for transit buses."""
    __tablename__ = "bus_locations"
    __table_args__ = (
        Index("ix_bus_locations_bus_id_recorded_at", "bus_id", "recorded_at"),
        CheckConstraint("speed IS NULL OR speed >= 0", name="chk_bus_locations_speed_positive"),
        CheckConstraint(
            "heading IS NULL OR (heading >= 0 AND heading <= 360)",
            name="chk_bus_locations_heading_valid",
        ),
        CheckConstraint("accuracy IS NULL OR accuracy >= 0", name="chk_bus_locations_accuracy_positive"),
        CheckConstraint("latitude >= -90.0 AND latitude <= 90.0", name="chk_bus_locations_latitude_range"),
        CheckConstraint("longitude >= -180.0 AND longitude <= 180.0", name="chk_bus_locations_longitude_range"),
    )

    bus_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("buses.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
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
    speed: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    heading: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    accuracy: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    altitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
        nullable=False,
    )
    source: Mapped[str | None] = mapped_column(
        String(50),
        default="GPS",
        nullable=True,
    )
    client_event_id: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=True,
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
        return self.recorded_at

    @timestamp.setter
    def timestamp(self, val: datetime) -> None:
        self.recorded_at = val

    def __init__(self, *args, **kwargs):
        if "timestamp" in kwargs and "recorded_at" not in kwargs:
            kwargs["recorded_at"] = kwargs.pop("timestamp")
        kwargs.setdefault("recorded_at", utc_now())
        kwargs.setdefault("source", "GPS")
        lat = kwargs.get("latitude")
        lon = kwargs.get("longitude")
        if lat is not None and lon is not None and "location" not in kwargs:
            kwargs["location"] = f"SRID=4326;POINT({lon} {lat})"
        super().__init__(*args, **kwargs)

    # Relationship
    bus: Mapped["Bus"] = relationship(
        "Bus",
        back_populates="locations",
        foreign_keys=[bus_id],
    )


class SyncEvent(UUIDPrimaryKeyMixin, Base):
    """Idempotency tracking for offline telemetry batch sync."""
    __tablename__ = "sync_events"

    client_event_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("received_at", utc_now())
        super().__init__(*args, **kwargs)
