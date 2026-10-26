from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.users import SystemRole


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_.-]+$")
    email: Optional[EmailStr] = None
    password: str = Field(min_length=6)
    full_name_ar: str = Field(min_length=2)
    full_name_en: str = Field(min_length=2)
    system_role: SystemRole = SystemRole.SALES_AGENT
    company_id: Optional[int] = None
    phone: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_.-]+$")
    email: Optional[EmailStr] = None
    full_name_ar: Optional[str] = None
    full_name_en: Optional[str] = None
    phone: Optional[str] = None
    system_role: Optional[SystemRole] = None
    company_id: Optional[int] = None
    preferred_language: Optional[str] = None


class AdminPasswordReset(BaseModel):
    new_password: str = Field(min_length=6)


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
