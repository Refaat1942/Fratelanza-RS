from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class SubscriptionPlanUpdate(BaseModel):
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    price_monthly: Optional[Decimal] = None
    price_yearly: Optional[Decimal] = None
    max_users: Optional[int] = None
    max_projects: Optional[int] = None
    max_storage_mb: Optional[int] = None
    enabled_modules: Optional[list[str]] = None
    is_active: Optional[bool] = None


class SubscriptionPlanResponse(BaseModel):
    id: int
    name_ar: str
    name_en: str
    code: str
    price_monthly: Decimal
    price_yearly: Decimal
    max_users: int
    max_projects: int
    max_storage_mb: int
    enabled_modules: list[str]
    is_active: bool

    model_config = {"from_attributes": True}
