from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class CompanyBillingSummary(BaseModel):
    plan_id: Optional[int] = None
    plan_name_ar: Optional[str] = None
    plan_name_en: Optional[str] = None
    plan_code: Optional[str] = None
    billing_cycle: str = "monthly"
    payment_terms_days: int = 30
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    next_billing_date: Optional[str] = None
    payment_status: str = "pending"
    amount_due: Optional[Decimal] = None
    last_payment_date: Optional[str] = None
    last_reminder_sent_at: Optional[str] = None


class CompanyWithBillingResponse(BaseModel):
    id: int
    name_ar: str
    name_en: str
    code: str
    status: str
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    country: str = "Egypt"
    billing: Optional[CompanyBillingSummary] = None


class SubscriptionBillingUpdate(BaseModel):
    plan_id: Optional[int] = None
    billing_cycle: Optional[str] = None
    payment_terms_days: Optional[int] = Field(None, ge=0, le=90)
    next_billing_date: Optional[str] = None
    payment_status: Optional[str] = None
    amount_due: Optional[Decimal] = None


class RecordSubscriptionPayment(BaseModel):
    amount: Decimal = Field(gt=0)
    payment_date: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
