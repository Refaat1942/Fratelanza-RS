import enum
from decimal import Decimal
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class CommissionStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    PAID = "paid"
    REJECTED = "rejected"


class Broker(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "brokers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    name_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    mobile: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    license_number: Mapped[Optional[str]] = mapped_column(String(100))
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=2.5)
    total_sales: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    rank_score: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(default=True)


class BrokerCommission(Base, TimestampMixin):
    __tablename__ = "broker_commissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    broker_id: Mapped[int] = mapped_column(ForeignKey("brokers.id"), nullable=False, index=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[CommissionStatus] = mapped_column(Enum(CommissionStatus), default=CommissionStatus.PENDING)
    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    paid_at: Mapped[Optional[str]] = mapped_column(String(30))
    notes: Mapped[Optional[str]] = mapped_column(Text)
