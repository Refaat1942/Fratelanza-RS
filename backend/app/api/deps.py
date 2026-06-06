from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import verify_token
from app.models.tenant import Company
from app.models.users import SystemRole, User, UserStatus
from app.services.platform_billing_service import PlatformBillingService

security = HTTPBearer(auto_error=False)


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = verify_token(credentials.credentials, "access")
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id, User.is_deleted == False))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account suspended")
    if user.company_id and not user.is_super_admin:
        company_result = await db.execute(
            select(Company)
            .options(selectinload(Company.subscription))
            .where(Company.id == user.company_id, Company.is_deleted == False)
        )
        company = company_result.scalar_one_or_none()
        if company:
            await PlatformBillingService.ensure_company_accessible(db, company)
    return user


async def get_super_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin access required")
    return current_user


async def get_company_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.is_super_admin:
        return current_user
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company access required")
    return current_user


def require_roles(*roles: SystemRole):
    async def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.is_super_admin:
            return current_user
        if current_user.system_role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return role_checker


async def log_audit(
    db: AsyncSession,
    request: Request,
    user: Optional[User],
    action: str,
    module: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    details: Optional[str] = None,
) -> None:
    from app.models.system import AuditLog

    log = AuditLog(
        company_id=user.company_id if user else None,
        user_id=user.id if user else None,
        action=action,
        module=module,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details=details,
    )
    db.add(log)
