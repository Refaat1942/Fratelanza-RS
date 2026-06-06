import enum
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class ActivityType(str, enum.Enum):
    CALL = "call"
    MEETING = "meeting"
    VISIT = "visit"
    RESERVATION = "reservation"
    CONTRACT = "contract"
    INSTALLMENT = "installment"
    PAYMENT = "payment"
    COMPLAINT = "complaint"
    NOTE = "note"


class Customer(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    full_name_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    mobile: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    whatsapp: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    national_id: Mapped[Optional[str]] = mapped_column(String(50))
    passport_number: Mapped[Optional[str]] = mapped_column(String(50))
    address: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100), default="Egypt")
    occupation: Mapped[Optional[str]] = mapped_column(String(255))
    employer: Mapped[Optional[str]] = mapped_column(String(255))
    income_range: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    assigned_to_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    documents: Mapped[list["CustomerDocument"]] = relationship(back_populates="customer", lazy="selectin")
    activities: Mapped[list["CustomerActivity"]] = relationship(back_populates="customer", lazy="selectin")


class CustomerDocument(Base, TimestampMixin):
    __tablename__ = "customer_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[Optional[str]] = mapped_column(String(50))
    uploaded_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    customer: Mapped["Customer"] = relationship(back_populates="documents")


class CustomerActivity(Base, TimestampMixin):
    __tablename__ = "customer_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)
    activity_type: Mapped[ActivityType] = mapped_column(Enum(ActivityType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    reference_type: Mapped[Optional[str]] = mapped_column(String(50))
    reference_id: Mapped[Optional[int]] = mapped_column(Integer)

    customer: Mapped["Customer"] = relationship(back_populates="activities")
