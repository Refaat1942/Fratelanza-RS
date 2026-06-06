from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class Vendor(Base, TimestampMixin):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    name_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_person: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    rating: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(default=True)


class RFQ(Base, TimestampMixin):
    __tablename__ = "rfqs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    rfq_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    due_date: Mapped[Optional[str]] = mapped_column(String(20))


class PurchaseOrder(Base, TimestampMixin):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    po_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), nullable=False)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
