from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class SubscriptionPlanCreate(BaseModel):
    name_ar: str = Field(min_length=2)
    name_en: str = Field(min_length=2)
    code: str = Field(min_length=2, max_length=50, pattern=r"^[a-z][a-z0-9_]*$")
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    billing_type: str = Field(default="recurring", pattern=r"^(recurring|one_time)$")
    price_monthly: Decimal = Field(ge=0, default=0)
    price_yearly: Decimal = Field(ge=0, default=0)
    price_one_time: Decimal = Field(ge=0, default=0)
    hosting_fee_monthly: Decimal = Field(ge=0, default=0)
    max_users: int = Field(ge=0, default=10, description="0 = unlimited")
    max_projects: int = Field(ge=0, default=5, description="0 = unlimited")
    max_storage_mb: int = Field(ge=0, default=5120, description="0 = unlimited")
    support_months: int = Field(ge=0, default=0)
    includes_hosting: bool = False
    enabled_modules: Optional[list[str]] = None
    sort_order: int = Field(ge=0, default=0)
    is_active: bool = True


class SubscriptionPlanUpdate(BaseModel):
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    billing_type: Optional[str] = Field(default=None, pattern=r"^(recurring|one_time)$")
    price_monthly: Optional[Decimal] = Field(default=None, ge=0)
    price_yearly: Optional[Decimal] = Field(default=None, ge=0)
    price_one_time: Optional[Decimal] = Field(default=None, ge=0)
    hosting_fee_monthly: Optional[Decimal] = Field(default=None, ge=0)
    max_users: Optional[int] = Field(default=None, ge=0)
    max_projects: Optional[int] = Field(default=None, ge=0)
    max_storage_mb: Optional[int] = Field(default=None, ge=0)
    support_months: Optional[int] = Field(default=None, ge=0)
    includes_hosting: Optional[bool] = None
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
    billing_type: str
    price_monthly: Decimal
    price_yearly: Decimal
    price_one_time: Decimal
    hosting_fee_monthly: Decimal
    max_users: int
    max_projects: int
    max_storage_mb: int
    support_months: int
    includes_hosting: bool
    enabled_modules: list[str]
    sort_order: int
    is_active: bool

    model_config = {"from_attributes": True}
