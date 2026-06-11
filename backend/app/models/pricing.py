import enum
from decimal import Decimal
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class PricingTriggerType(str, enum.Enum):
    SALES_VOLUME = "sales_volume"
    CONSTRUCTION_PROGRESS = "construction_progress"


class PricingRule(Base, TimestampMixin):
    """Tier rule: when metric >= threshold_percent, apply adjustment_percent to available units."""

    __tablename__ = "pricing_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), index=True)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    trigger_type: Mapped[PricingTriggerType] = mapped_column(Enum(PricingTriggerType), nullable=False)
    threshold_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    adjustment_percent: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=Decimal("0"))
    is_active: Mapped[bool] = mapped_column(default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
