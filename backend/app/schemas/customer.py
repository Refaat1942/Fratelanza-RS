from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class CustomerCreate(BaseModel):
    full_name_ar: str = Field(min_length=2)
    full_name_en: str = Field(min_length=2)
    mobile: str = Field(min_length=8)
    whatsapp: Optional[str] = None
    email: Optional[EmailStr] = None
    national_id: Optional[str] = None
    passport_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: str = "Egypt"
    occupation: Optional[str] = None
    employer: Optional[str] = None
    income_range: Optional[str] = None
    notes: Optional[str] = None
    assigned_to_id: Optional[int] = None


class CustomerUpdate(BaseModel):
    full_name_ar: Optional[str] = None
    full_name_en: Optional[str] = None
    mobile: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[EmailStr] = None
    national_id: Optional[str] = None
    passport_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    occupation: Optional[str] = None
    employer: Optional[str] = None
    income_range: Optional[str] = None
    notes: Optional[str] = None
    assigned_to_id: Optional[int] = None


class CustomerResponse(CustomerCreate):
    id: int
    company_id: int

    model_config = {"from_attributes": True}
