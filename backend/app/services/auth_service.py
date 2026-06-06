from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_totp,
    verify_token,
)
from app.models.users import SystemRole, User, UserStatus
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse


class AuthService:
    @staticmethod
    async def login(db: AsyncSession, data: LoginRequest) -> tuple[TokenResponse, User]:
        result = await db.execute(select(User).where(User.email == data.email, User.is_deleted == False))
        user = result.scalar_one_or_none()
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if user.status == UserStatus.SUSPENDED:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account suspended")
        if user.is_2fa_enabled:
            if not data.totp_code or not user.totp_secret:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="2FA code required")
            if not verify_totp(user.totp_secret, data.totp_code):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid 2FA code")
        user.last_login_at = datetime.now(timezone.utc).isoformat()
        access = create_access_token(
            user.id,
            {
                "role": user.system_role.value,
                "company_id": user.company_id,
                "is_super_admin": user.is_super_admin,
            },
        )
        refresh = create_refresh_token(user.id)
        return TokenResponse(access_token=access, refresh_token=refresh), user

    @staticmethod
    async def refresh(db: AsyncSession, refresh_token: str) -> TokenResponse:
        payload = verify_token(refresh_token, "refresh")
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        user_id = int(payload["sub"])
        result = await db.execute(select(User).where(User.id == user_id, User.is_deleted == False))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        access = create_access_token(
            user.id,
            {
                "role": user.system_role.value,
                "company_id": user.company_id,
                "is_super_admin": user.is_super_admin,
            },
        )
        return TokenResponse(access_token=access, refresh_token=refresh_token)

    @staticmethod
    def to_user_response(user: User) -> UserResponse:
        return UserResponse.model_validate(user)

    @staticmethod
    async def create_user(
        db: AsyncSession,
        email: str,
        password: str,
        full_name_ar: str,
        full_name_en: str,
        system_role: SystemRole,
        company_id: int | None = None,
        is_super_admin: bool = False,
    ) -> User:
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        user = User(
            email=email,
            password_hash=get_password_hash(password),
            full_name_ar=full_name_ar,
            full_name_en=full_name_en,
            system_role=system_role,
            company_id=company_id,
            is_super_admin=is_super_admin,
            status=UserStatus.ACTIVE,
        )
        db.add(user)
        await db.flush()
        return user
