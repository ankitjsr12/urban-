from typing import TYPE_CHECKING, Any

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.bus import Bus
    from app.models.incident import Incident


class Route(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Transit route with geospatial path representation."""
    __tablename__ = "routes"

    route_number: Mapped[str] = mapped_column(
        String(40),
        unique=True,
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    origin: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
    )
    destination: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
    )
    geometry: Mapped[Any | None] = mapped_column(
        Geometry(
            geometry_type="LINESTRING",
            srid=4326,
            spatial_index=True,
            from_text="ST_GeomFromEWKT",
            name="geometry",
        ),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Backward compatibility alias for existing code referencing route.code
    @property
    def code(self) -> str:
        return self.route_number

    @code.setter
    def code(self, val: str) -> None:
        self.route_number = val

    def __init__(self, *args, **kwargs):
        if "code" in kwargs and "route_number" not in kwargs:
            kwargs["route_number"] = kwargs.pop("code")
        if "geometry_wkt" in kwargs and "geometry" not in kwargs:
            from geoalchemy2.elements import WKTElement
            wkt = kwargs.pop("geometry_wkt")
            kwargs["geometry"] = WKTElement(wkt, srid=4326) if wkt else None
        kwargs.setdefault("is_active", True)
        super().__init__(*args, **kwargs)

    # Relationships
    buses: Mapped[list["Bus"]] = relationship(
        "Bus",
        back_populates="route",
        foreign_keys="Bus.assigned_route_id",
    )
    incidents: Mapped[list["Incident"]] = relationship(
        "Incident",
        back_populates="route",
        foreign_keys="Incident.route_id",
    )
