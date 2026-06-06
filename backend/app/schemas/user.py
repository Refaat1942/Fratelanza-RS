from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.users import SystemRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name_ar: str = Field(min_length=2)
    full_name_en: str = Field(min_length=2)
    system_role: SystemRole = SystemRole.SALES_AGENT
    company_id: Optional[int] = None
    phone: Optional[str] = None


class ClientOnboard(BaseModel):
    full_name_ar: str = Field(min_length=2)
    full_name_en: str = Field(min_length=2)
    mobile: str = Field(min_length=8)
    email: Optional[EmailStr] = None
    whatsapp: Optional[str] = None
    city: Optional[str] = None
    national_id: Optional[str] = None
    source: str = "walk_in"
    create_lead: bool = True
    notes: Optional[str] = None
