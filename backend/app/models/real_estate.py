import enum
from decimal import Decimal
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class ProjectStatus(str, enum.Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"


class UnitType(str, enum.Enum):
    APARTMENT = "apartment"
    VILLA = "villa"
    TWIN_HOUSE = "twin_house"
    TOWN_HOUSE = "town_house"
    CHALET = "chalet"
    PENTHOUSE = "penthouse"
    DUPLEX = "duplex"
    OFFICE = "office"
    RETAIL = "retail"
    CLINIC = "clinic"
    WAREHOUSE = "warehouse"


class UnitStatus(str, enum.Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    CONTRACTED = "contracted"
    SOLD = "sold"
    DELIVERED = "delivered"
    BLOCKED = "blocked"


class Project(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    branch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("branches.id"))
    name_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description_ar: Mapped[Optional[str]] = mapped_column(Text)
    description_en: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100), default="Egypt")
    address: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus), default=ProjectStatus.PLANNING)
    total_units: Mapped[int] = mapped_column(Integer, default=0)
    available_units: Mapped[int] = mapped_column(Integer, default=0)
    cover_image_url: Mapped[Optional[str]] = mapped_column(String(500))

    buildings: Mapped[list["Building"]] = relationship(back_populates="project", lazy="selectin")


class Building(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    name_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    total_floors: Mapped[int] = mapped_column(Integer, default=0)

    project: Mapped["Project"] = relationship(back_populates="buildings")
    floors: Mapped[list["Floor"]] = relationship(back_populates="building", lazy="selectin")


class Floor(Base, TimestampMixin):
    __tablename__ = "floors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    building_id: Mapped[int] = mapped_column(ForeignKey("buildings.id"), nullable=False, index=True)
    floor_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name_ar: Mapped[Optional[str]] = mapped_column(String(100))
    name_en: Mapped[Optional[str]] = mapped_column(String(100))

    building: Mapped["Building"] = relationship(back_populates="floors")
    units: Mapped[list["Unit"]] = relationship(back_populates="floor", lazy="selectin")


class Unit(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    floor_id: Mapped[int] = mapped_column(ForeignKey("floors.id"), nullable=False, index=True)
    unit_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    unit_number: Mapped[str] = mapped_column(String(50), nullable=False)
    unit_type: Mapped[UnitType] = mapped_column(Enum(UnitType), nullable=False)
    area_sqm: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    garden_area_sqm: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    roof_area_sqm: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    bedrooms: Mapped[int] = mapped_column(Integer, default=0)
    bathrooms: Mapped[int] = mapped_column(Integer, default=0)
    base_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    maintenance_fee: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    delivery_date: Mapped[Optional[str]] = mapped_column(String(20))
    status: Mapped[UnitStatus] = mapped_column(Enum(UnitStatus), default=UnitStatus.AVAILABLE)
    images: Mapped[Optional[str]] = mapped_column(Text)
    attachments: Mapped[Optional[str]] = mapped_column(Text)
    is_locked: Mapped[bool] = mapped_column(default=False)

    floor: Mapped["Floor"] = relationship(back_populates="units")
