from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.tenant import CompanyStatus


class CompanyBase(BaseModel):
    name_ar: str = Field(min_length=2, max_length=255)
    name_en: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: str = "Egypt"
    tax_number: Optional[str] = None
    commercial_register: Optional[str] = None
    default_language: str = "ar"
    theme: str = "default"
    storage_limit_mb: int = 5120


class CompanyCreate(CompanyBase):
    plan_id: Optional[int] = None
    admin_email: Optional[EmailStr] = None
    admin_password: Optional[str] = None
    admin_name_ar: Optional[str] = None
    admin_name_en: Optional[str] = None


class CompanyUpdate(BaseModel):
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    status: Optional[CompanyStatus] = None
    storage_limit_mb: Optional[int] = None
    default_language: Optional[str] = None
    theme: Optional[str] = None


class CompanyResponse(CompanyBase):
    id: int
    status: CompanyStatus
    storage_used_mb: int
    logo_url: Optional[str] = None

    model_config = {"from_attributes": True}


class BranchCreate(BaseModel):
    name_ar: str
    name_en: str
    code: str
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None


class BranchResponse(BranchCreate):
    id: int
    company_id: int
    is_active: bool

    model_config = {"from_attributes": True}
