import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from geoalchemy2 import Geography
from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from app.models.user import User


class CitizenReportType(str, enum.Enum):
    """Categories of public citizen civic reports."""
    POTHOLE = "POTHOLE"
    WATERLOGGING = "WATERLOGGING"
    TRAFFIC = "TRAFFIC"
    ACCIDENT = "ACCIDENT"
    ROAD_DAMAGE = "ROAD_DAMAGE"
    OBSTRUCTION = "OBSTRUCTION"
    OTHER = "OTHER"


class CitizenReportStatus(str, enum.Enum):
    """Lifecycle stages of a citizen report."""
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"


class ReportPriority(str, enum.Enum):
    """Priority level for civic response."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CitizenReport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Crowdsourced issue report submitted by citizens with geolocation and photo references."""
    __tablename__ = "citizen_reports"

    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    report_type: Mapped[str] = mapped_column(
        String(80),
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
    status: Mapped[str] = mapped_column(
        String(30),
        default=CitizenReportStatus.SUBMITTED.value,
        index=True,
        nullable=False,
    )
    priority: Mapped[ReportPriority] = mapped_column(
        Enum(ReportPriority, name="citizen_report_priority_enum", native_enum=False),
        default=ReportPriority.MEDIUM,
        index=True,
        nullable=False,
    )
    image_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    metadata_json: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        server_default="{}",
        nullable=False,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Backward compatibility alias
    @property
    def problem_type(self) -> str:
        return self.report_type

    @problem_type.setter
    def problem_type(self, val: str) -> None:
        self.report_type = val

    def __init__(self, *args, **kwargs):
        if "problem_type" in kwargs and "report_type" not in kwargs:
            kwargs["report_type"] = kwargs.pop("problem_type")
        if "metadata" in kwargs and "metadata_json" not in kwargs:
            kwargs["metadata_json"] = kwargs.pop("metadata")
        kwargs.setdefault("status", CitizenReportStatus.SUBMITTED.value)
        kwargs.setdefault("priority", ReportPriority.MEDIUM)
        kwargs.setdefault("metadata_json", {})
        lat = kwargs.get("latitude")
        lon = kwargs.get("longitude")
        if lat is not None and lon is not None and "location" not in kwargs:
            kwargs["location"] = f"SRID=4326;POINT({lon} {lat})"
        super().__init__(*args, **kwargs)

    # Relationships
    citizen: Mapped["User"] = relationship(
        "User",
        back_populates="citizen_reports",
        foreign_keys=[citizen_id],
    )
