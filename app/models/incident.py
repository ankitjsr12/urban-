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
    from app.models.incident_evidence import IncidentEvidence
    from app.models.route import Route
    from app.models.user import User
    from app.models.vehicle import Vehicle


class IncidentType(str, enum.Enum):
    """Classification of critical urban transit incidents."""
    ACCIDENT = "ACCIDENT"
    MEDICAL = "MEDICAL"
    FIRE = "FIRE"
    ROAD_HAZARD = "ROAD_HAZARD"
    WATERLOGGING = "WATERLOGGING"
    TRAFFIC = "TRAFFIC"
    SECURITY = "SECURITY"
    # Backward compatibility
    POSSIBLE_HIT_AND_RUN = "POSSIBLE_HIT_AND_RUN"
    DANGEROUS_DRIVING = "DANGEROUS_DRIVING"
    COLLISION_LIKE_EVENT = "COLLISION_LIKE_EVENT"
    PEDESTRIAN_RISK = "PEDESTRIAN_RISK"
    OTHER = "OTHER"


class IncidentSeverity(str, enum.Enum):
    """Severity and urgency rating of an incident."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Backward compatibility alias
Priority = IncidentSeverity


class IncidentStatus(str, enum.Enum):
    """Dispatch and resolution lifecycle of an incident."""
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    FALSE_ALARM = "FALSE_ALARM"
    # Backward compatibility
    NEW = "NEW"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    ASSIGNED = "ASSIGNED"
    REJECTED = "REJECTED"


class Incident(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Critical safety or operational incident logged from buses, AI alerts, or dispatchers."""
    __tablename__ = "incidents"
    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)",
            name="chk_incident_confidence_range",
        ),
    )

    incident_type: Mapped[IncidentType] = mapped_column(
        Enum(IncidentType, name="incident_type_enum", native_enum=False),
        index=True,
        nullable=False,
    )
    severity: Mapped[IncidentSeverity] = mapped_column(
        Enum(IncidentSeverity, name="incident_severity_enum", native_enum=False),
        default=IncidentSeverity.MEDIUM,
        index=True,
        nullable=False,
    )
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus, name="incident_status_enum", native_enum=False),
        default=IncidentStatus.OPEN,
        index=True,
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
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
    route_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("routes.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    reported_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
        nullable=False,
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
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

    # Backward compatibility aliases
    @property
    def priority(self) -> IncidentSeverity:
        return self.severity

    @priority.setter
    def priority(self, val: IncidentSeverity) -> None:
        self.severity = val

    @property
    def created_by(self) -> uuid.UUID | None:
        return self.reported_by

    @created_by.setter
    def created_by(self, val: uuid.UUID | None) -> None:
        self.reported_by = val

    @property
    def timestamp(self) -> datetime:
        return self.detected_at

    @timestamp.setter
    def timestamp(self, val: datetime) -> None:
        self.detected_at = val

    def __init__(self, *args, **kwargs):
        if "priority" in kwargs and "severity" not in kwargs:
            kwargs["severity"] = kwargs.pop("priority")
        if "created_by" in kwargs and "reported_by" not in kwargs:
            kwargs["reported_by"] = kwargs.pop("created_by")
        if "timestamp" in kwargs and "detected_at" not in kwargs:
            kwargs["detected_at"] = kwargs.pop("timestamp")
        if "metadata" in kwargs and "metadata_json" not in kwargs:
            kwargs["metadata_json"] = kwargs.pop("metadata")
        kwargs.setdefault("severity", IncidentSeverity.MEDIUM)
        kwargs.setdefault("status", IncidentStatus.OPEN)
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
        back_populates="incidents",
        foreign_keys=[bus_id],
    )
    route: Mapped[Optional["Route"]] = relationship(
        "Route",
        back_populates="incidents",
        foreign_keys=[route_id],
    )
    reporter: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="reported_incidents",
        foreign_keys=[reported_by],
    )
    vehicle: Mapped[Optional["Vehicle"]] = relationship(
        "Vehicle",
        foreign_keys=[vehicle_id],
    )
    evidence: Mapped[list["IncidentEvidence"]] = relationship(
        "IncidentEvidence",
        back_populates="incident",
        cascade="all, delete-orphan",
        foreign_keys="IncidentEvidence.incident_id",
    )
