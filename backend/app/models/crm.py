import enum
from decimal import Decimal
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class LeadSource(str, enum.Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    GOOGLE_ADS = "google_ads"
    WEBSITE = "website"
    REFERRAL = "referral"
    BROKER = "broker"
    CALL_CENTER = "call_center"
    WALK_IN = "walk_in"


class LeadStage(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    INTERESTED = "interested"
    SITE_VISIT = "site_visit"
    NEGOTIATION = "negotiation"
    RESERVATION = "reservation"
    CONTRACT_SIGNED = "contract_signed"
    LOST = "lost"


class Lead(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customers.id"))
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"))
    assigned_to_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    broker_id: Mapped[Optional[int]] = mapped_column(ForeignKey("brokers.id"))
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mobile: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    source: Mapped[LeadSource] = mapped_column(Enum(LeadSource), default=LeadSource.WEBSITE)
    stage: Mapped[LeadStage] = mapped_column(Enum(LeadStage), default=LeadStage.NEW)
    score: Mapped[int] = mapped_column(Integer, default=0)
    ai_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    ai_qualification: Mapped[Optional[str]] = mapped_column(Text)
    budget_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    budget_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    next_follow_up: Mapped[Optional[str]] = mapped_column(String(30))

    activities: Mapped[list["LeadActivity"]] = relationship(back_populates="lead", lazy="selectin")


class LeadActivity(Base, TimestampMixin):
    __tablename__ = "lead_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), nullable=False, index=True)
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    lead: Mapped["Lead"] = relationship(back_populates="activities")
