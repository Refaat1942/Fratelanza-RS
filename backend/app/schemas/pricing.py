from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.models.pricing import PricingTriggerType


class PricingRuleCreate(BaseModel):
    project_id: Optional[int] = None
    name_en: str = Field(min_length=2)
    name_ar: str = Field(min_length=2)
    trigger_type: PricingTriggerType
    threshold_percent: int = Field(ge=0, le=100)
    adjustment_percent: Decimal = Field(ge=0, le=100)
    is_active: bool = True
    sort_order: int = 0


class PricingRuleUpdate(BaseModel):
    project_id: Optional[int] = None
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    trigger_type: Optional[PricingTriggerType] = None
    threshold_percent: Optional[int] = Field(default=None, ge=0, le=100)
    adjustment_percent: Optional[Decimal] = Field(default=None, ge=0, le=100)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class PricingRuleResponse(PricingRuleCreate):
    id: int
    company_id: int

    model_config = {"from_attributes": True}
