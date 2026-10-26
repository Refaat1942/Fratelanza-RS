from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_totp,
    verify_token,
)
from app.models.tenant import Company
from app.models.users import SystemRole, User, UserStatus
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.middleware.security import clear_login_attempts, is_login_blocked, record_login_failure
from app.services.platform_billing_service import PlatformBillingService


class AuthService:
    @staticmethod
    async def _max_login_attempts(db: AsyncSession) -> int:
        from app.models.system import SystemSetting
        from sqlalchemy import select

        result = await db.execute(select(SystemSetting).where(SystemSetting.key == "max_login_attempts"))
        setting = result.scalar_one_or_none()
        if setting and str(setting.value).isdigit():
            return max(3, int(setting.value))
        return 5

    @staticmethod
    async def login(db: AsyncSession, data: LoginRequest) -> tuple[TokenResponse, User]:
        # Login is by username only and is case-sensitive ("Ahmed" ≠ "ahmed"); e-mail is not a login.
        login = data.username.strip()
        client_key = f"user:{login.lower()}"
        max_attempts = await AuthService._max_login_attempts(db)
        if is_login_blocked(client_key, max_attempts):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Please try again later.",
            )
        result = await db.execute(
            select(User).where(User.username == login, User.is_deleted == False)
        )
        user = result.scalar_one_or_none()
        if not user or not verify_password(data.password, user.password_hash):
            record_login_failure(client_key)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        clear_login_attempts(client_key)
        if user.status == UserStatus.SUSPENDED:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account suspended")
        if user.company_id and not user.is_super_admin:
            company_result = await db.execute(
                select(Company)
                .options(selectinload(Company.subscription))
                .where(Company.id == user.company_id, Company.is_deleted == False)
            )
            company = company_result.scalar_one_or_none()
            if not company:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company not found")
            await PlatformBillingService.ensure_company_accessible(db, company)
            if company.is_demo:
                from app.services.access_service import AccessService

                AccessService.ensure_demo_usable(await AccessService.load_demo(db, company.id))
            await db.commit()
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
        if user.company_id and not user.is_super_admin:
            company_result = await db.execute(
                select(Company)
                .options(selectinload(Company.subscription))
                .where(Company.id == user.company_id, Company.is_deleted == False)
            )
            company = company_result.scalar_one_or_none()
            if not company:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Company not found")
            await PlatformBillingService.ensure_company_accessible(db, company)
            if company.is_demo:
                from app.services.access_service import AccessService

                AccessService.ensure_demo_usable(await AccessService.load_demo(db, company.id))
            await db.commit()
        if user.status == UserStatus.SUSPENDED:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account suspended")
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
    async def to_user_response_enriched(db: AsyncSession, user: User) -> UserResponse:
        from app.services.company_service import CompanyService

        if user.is_super_admin or not user.company_id:
            return AuthService.to_user_response(user)
        company = await CompanyService.get_company(db, user.company_id)
        sub = company.subscription
        if sub:
            PlatformBillingService.sync_trial_expiry(sub, company)
            await db.flush()
        resp = UserResponse.model_validate(user)
        billing = PlatformBillingService.subscription_to_summary(sub, company)
        update: dict = {
            "company_name_ar": company.name_ar,
            "company_name_en": company.name_en,
            "company_code": company.code,
            "company_status": company.status.value,
        }
        if billing:
            update.update(
                {
                    "plan_name_ar": billing.plan_name_ar,
                    "plan_name_en": billing.plan_name_en,
                    "payment_terms_days": billing.payment_terms_days,
                    "next_billing_date": billing.next_billing_date,
                    "payment_status": billing.payment_status,
                    "amount_due": float(billing.amount_due) if billing.amount_due is not None else None,
                    "trial_end_date": billing.end_date,
                }
            )
        if sub:
            update["trial_days_remaining"] = PlatformBillingService.trial_days_remaining(sub)
        return resp.model_copy(update=update)

    @staticmethod
    async def create_user(
        db: AsyncSession,
        username: str,
        email: str | None,
        password: str,
        full_name_ar: str,
        full_name_en: str,
        system_role: SystemRole,
        company_id: int | None = None,
        is_super_admin: bool = False,
    ) -> User:
        username_norm = username.strip()  # case-sensitive, kept exactly as typed
        clauses = [User.username == username_norm]
        if email:
            clauses.append(User.email == email)
        existing = await db.execute(select(User).where(or_(*clauses)))
        if existing.scalars().first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already registered")
        user = User(
            username=username_norm,
            email=email or None,
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
