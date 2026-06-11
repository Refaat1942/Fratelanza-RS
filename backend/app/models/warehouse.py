from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class Warehouse(Base, TimestampMixin):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    name_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255))
    warehouse_type: Mapped[str] = mapped_column(String(30), default="central")
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), index=True)
    is_active: Mapped[bool] = mapped_column(default=True)


class InventoryItem(Base, TimestampMixin):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    barcode: Mapped[Optional[str]] = mapped_column(String(100))
    name_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    item_type: Mapped[str] = mapped_column(String(30), default="raw_material")
    category: Mapped[Optional[str]] = mapped_column(String(100))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    min_stock_level: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    unit: Mapped[str] = mapped_column(String(20), default="pcs")
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)


class StockMovement(Base, TimestampMixin):
    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"), nullable=False, index=True)
    movement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    from_warehouse_id: Mapped[Optional[int]] = mapped_column(ForeignKey("warehouses.id"))
    to_warehouse_id: Mapped[Optional[int]] = mapped_column(ForeignKey("warehouses.id"))
    reference: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))


class HeavyEquipment(Base, TimestampMixin):
    __tablename__ = "heavy_equipment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    asset_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    equipment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    serial_number: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default="available")
    current_warehouse_id: Mapped[Optional[int]] = mapped_column(ForeignKey("warehouses.id"), index=True)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)


class EquipmentTransfer(Base, TimestampMixin):
    __tablename__ = "equipment_transfers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("heavy_equipment.id"), nullable=False, index=True)
    from_warehouse_id: Mapped[Optional[int]] = mapped_column(ForeignKey("warehouses.id"))
    to_warehouse_id: Mapped[Optional[int]] = mapped_column(ForeignKey("warehouses.id"))
    from_project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"))
    to_project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"))
    reference: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
