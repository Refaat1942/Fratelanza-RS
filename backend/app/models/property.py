from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class MaintenanceRequest(Base, TimestampMixin):
    __tablename__ = "maintenance_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), nullable=False, index=True)
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customers.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(50), default="open")
    assigned_to_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))


class HandoverRecord(Base, TimestampMixin):
    __tablename__ = "handover_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    handover_date: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="scheduled")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    completed_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
