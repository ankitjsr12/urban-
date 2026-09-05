import enum
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, CheckConstraint, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.detection import Detection
    from app.models.driver import Driver
    from app.models.incident import Incident
    from app.models.location import BusLocation
    from app.models.road_defect import RoadDefect
    from app.models.route import Route
    from app.models.traffic_event import TrafficEvent
    from app.models.vehicle import VehicleDetection


class BusStatus(str, enum.Enum):
    """Operational status of a bus in the fleet."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    OFFLINE = "OFFLINE"


class Bus(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Fleet vehicle entity representing transit buses."""
    __tablename__ = "buses"
    __table_args__ = (
        CheckConstraint("capacity IS NULL OR capacity > 0", name="chk_bus_capacity_positive"),
    )

    registration_number: Mapped[str] = mapped_column(
        String(40),
        unique=True,
        index=True,
        nullable=False,
    )
    fleet_number: Mapped[str] = mapped_column(
        String(40),
        unique=True,
        index=True,
        nullable=False,
    )
    operator_name: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )
    model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    manufacturer: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    capacity: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    status: Mapped[BusStatus] = mapped_column(
        Enum(BusStatus, name="bus_status_enum", native_enum=False),
        default=BusStatus.INACTIVE,
        index=True,
        nullable=False,
    )
    assigned_driver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("drivers.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    assigned_route_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("routes.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Backward compatibility aliases
    @property
    def bus_number(self) -> str:
        return self.fleet_number

    @bus_number.setter
    def bus_number(self, val: str) -> None:
        self.fleet_number = val

    @property
    def route_id(self) -> uuid.UUID | None:
        return self.assigned_route_id

    @route_id.setter
    def route_id(self, val: uuid.UUID | None) -> None:
        self.assigned_route_id = val

    @property
    def driver_id(self) -> uuid.UUID | None:
        return self.assigned_driver_id

    @driver_id.setter
    def driver_id(self, val: uuid.UUID | None) -> None:
        self.assigned_driver_id = val

    def __init__(self, *args, **kwargs):
        if "bus_number" in kwargs and "fleet_number" not in kwargs:
            kwargs["fleet_number"] = kwargs.pop("bus_number")
        if "route_id" in kwargs and "assigned_route_id" not in kwargs:
            kwargs["assigned_route_id"] = kwargs.pop("route_id")
        if "driver_id" in kwargs and "assigned_driver_id" not in kwargs:
            kwargs["assigned_driver_id"] = kwargs.pop("driver_id")
        kwargs.setdefault("status", BusStatus.INACTIVE)
        kwargs.setdefault("is_active", True)
        super().__init__(*args, **kwargs)

    # Relationships
    driver: Mapped[Optional["Driver"]] = relationship(
        "Driver",
        back_populates="assigned_buses",
        foreign_keys=[assigned_driver_id],
    )
    route: Mapped[Optional["Route"]] = relationship(
        "Route",
        back_populates="buses",
        foreign_keys=[assigned_route_id],
    )
    locations: Mapped[list["BusLocation"]] = relationship(
        "BusLocation",
        back_populates="bus",
        cascade="all, delete-orphan",
        foreign_keys="BusLocation.bus_id",
    )
    detections: Mapped[list["Detection"]] = relationship(
        "Detection",
        back_populates="bus",
        foreign_keys="Detection.bus_id",
    )
    vehicle_detections: Mapped[list["VehicleDetection"]] = relationship(
        "VehicleDetection",
        back_populates="bus",
        foreign_keys="VehicleDetection.bus_id",
    )
    traffic_events: Mapped[list["TrafficEvent"]] = relationship(
        "TrafficEvent",
        back_populates="bus",
        foreign_keys="TrafficEvent.bus_id",
    )
    road_defects: Mapped[list["RoadDefect"]] = relationship(
        "RoadDefect",
        back_populates="bus",
        foreign_keys="RoadDefect.detected_by_bus_id",
    )
    incidents: Mapped[list["Incident"]] = relationship(
        "Incident",
        back_populates="bus",
        foreign_keys="Incident.bus_id",
    )
