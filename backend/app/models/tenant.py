import enum
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class CompanyStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    EXPIRED = "expired"


class Company(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    address: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100), default="Egypt")
    tax_number: Mapped[Optional[str]] = mapped_column(String(100))
    commercial_register: Mapped[Optional[str]] = mapped_column(String(100))
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[CompanyStatus] = mapped_column(Enum(CompanyStatus), default=CompanyStatus.TRIAL)
    storage_limit_mb: Mapped[int] = mapped_column(Integer, default=5120)
    storage_used_mb: Mapped[int] = mapped_column(Integer, default=0)
    default_language: Mapped[str] = mapped_column(String(5), default="ar")
    theme: Mapped[str] = mapped_column(String(50), default="default")

    branches: Mapped[list["Branch"]] = relationship(back_populates="company", lazy="selectin")
    subscription: Mapped[Optional["CompanySubscription"]] = relationship(
        back_populates="company", uselist=False, lazy="selectin"
    )


class Branch(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    name_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    company: Mapped["Company"] = relationship(back_populates="branches")


class SubscriptionPlan(Base, TimestampMixin):
    __tablename__ = "subscription_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    price_monthly: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    price_yearly: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    max_users: Mapped[int] = mapped_column(Integer, default=10)
    max_projects: Mapped[int] = mapped_column(Integer, default=5)
    max_storage_mb: Mapped[int] = mapped_column(Integer, default=5120)
    features: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class CompanySubscription(Base, TimestampMixin):
    __tablename__ = "company_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), unique=True, nullable=False)
    plan_id: Mapped[int] = mapped_column(ForeignKey("subscription_plans.id"), nullable=False)
    start_date: Mapped[Optional[str]] = mapped_column(String(20))
    end_date: Mapped[Optional[str]] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    company: Mapped["Company"] = relationship(back_populates="subscription")
    plan: Mapped["SubscriptionPlan"] = relationship(lazy="selectin")
