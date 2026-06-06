from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.users import SystemRole, UserStatus


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    totp_code: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name_ar: str
    full_name_en: str
    system_role: SystemRole
    status: UserStatus
    is_super_admin: bool
    company_id: Optional[int] = None
    company_name_ar: Optional[str] = None
    company_name_en: Optional[str] = None
    company_code: Optional[str] = None
    branch_id: Optional[int] = None
    preferred_language: str = "ar"
    is_2fa_enabled: bool = False

    model_config = {"from_attributes": True}


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)
