from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class SubscriptionPlanCreate(BaseModel):
    name_ar: str = Field(min_length=2)
    name_en: str = Field(min_length=2)
    code: str = Field(min_length=2, max_length=50, pattern=r"^[a-z][a-z0-9_]*$")
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    price_monthly: Decimal = Field(ge=0)
    price_yearly: Decimal = Field(ge=0)
    max_users: int = Field(ge=1, default=10)
    max_projects: int = Field(ge=1, default=5)
    max_storage_mb: int = Field(ge=100, default=5120)
    enabled_modules: Optional[list[str]] = None
    sort_order: int = Field(ge=0, default=0)
    is_active: bool = True


class SubscriptionPlanUpdate(BaseModel):
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    price_monthly: Optional[Decimal] = None
    price_yearly: Optional[Decimal] = None
    max_users: Optional[int] = None
    max_projects: Optional[int] = None
    max_storage_mb: Optional[int] = None
    enabled_modules: Optional[list[str]] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class SubscriptionPlanResponse(BaseModel):
    id: int
    name_ar: str
    name_en: str
    code: str
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    price_monthly: Decimal
    price_yearly: Decimal
    max_users: int
    max_projects: int
    max_storage_mb: int
    enabled_modules: list[str]
    sort_order: int
    is_active: bool

    model_config = {"from_attributes": True}
