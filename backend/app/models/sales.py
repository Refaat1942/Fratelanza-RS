import enum
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class ReservationStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    CONVERTED = "converted_to_contract"


class ContractStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentPlanType(str, enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"
    CUSTOM = "custom"


class InstallmentStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    DUE = "due"
    OVERDUE = "overdue"
    PAID = "paid"
    PARTIAL = "partial"


class Reservation(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    reservation_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), nullable=False)
    deposit_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    reservation_date: Mapped[str] = mapped_column(String(20), nullable=False)
    expiry_date: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus), default=ReservationStatus.DRAFT
    )
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    notes: Mapped[Optional[str]] = mapped_column(Text)


class Contract(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    contract_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), nullable=False)
    reservation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reservations.id"))
    total_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    contract_date: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[ContractStatus] = mapped_column(Enum(ContractStatus), default=ContractStatus.DRAFT)
    contract_ar: Mapped[Optional[str]] = mapped_column(Text)
    contract_en: Mapped[Optional[str]] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_signed: Mapped[bool] = mapped_column(Boolean, default=False)
    signed_at: Mapped[Optional[str]] = mapped_column(String(30))
    pdf_file_path: Mapped[Optional[str]] = mapped_column(String(500))
    pdf_generated_at: Mapped[Optional[str]] = mapped_column(String(30))
    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    payment_plan: Mapped[Optional["PaymentPlan"]] = relationship(
        back_populates="contract", uselist=False, lazy="selectin"
    )


class PaymentPlan(Base, TimestampMixin):
    __tablename__ = "payment_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"), unique=True, nullable=False)
    plan_type: Mapped[PaymentPlanType] = mapped_column(Enum(PaymentPlanType), nullable=False)
    down_payment: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    number_of_installments: Mapped[int] = mapped_column(Integer, default=0)
    start_date: Mapped[str] = mapped_column(String(20), nullable=False)

    contract: Mapped["Contract"] = relationship(back_populates="payment_plan")
    installments: Mapped[list["Installment"]] = relationship(back_populates="payment_plan", lazy="selectin")


class Installment(Base, TimestampMixin):
    __tablename__ = "installments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_plan_id: Mapped[int] = mapped_column(ForeignKey("payment_plans.id"), nullable=False, index=True)
    installment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[str] = mapped_column(String(20), nullable=False)
    due_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    remaining_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[InstallmentStatus] = mapped_column(
        Enum(InstallmentStatus), default=InstallmentStatus.UPCOMING
    )

    payment_plan: Mapped["PaymentPlan"] = relationship(back_populates="installments")
    payments: Mapped[list["Payment"]] = relationship(back_populates="installment", lazy="selectin")


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    installment_id: Mapped[int] = mapped_column(ForeignKey("installments.id"), nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    payment_date: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), default="cash")
    reference_number: Mapped[Optional[str]] = mapped_column(String(100))
    received_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    installment: Mapped["Installment"] = relationship(back_populates="payments")
