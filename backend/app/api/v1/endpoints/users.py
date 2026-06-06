from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user, get_super_admin
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.tenant import Company, CompanySubscription
from app.services.platform_billing_service import PlatformBillingService
from app.models.users import SystemRole, User, UserStatus
from app.schemas.auth import UserResponse
from app.schemas.common import PaginatedResponse
from app.schemas.user import AdminPasswordReset, UserCreate, UserUpdate
from app.services.auth_service import AuthService

router = APIRouter()


def _user_with_company(
    user: User,
    company: Company | None = None,
    subscription: CompanySubscription | None = None,
) -> UserResponse:
    resp = UserResponse.model_validate(user)
    if not company:
        return resp
    billing = PlatformBillingService.subscription_to_summary(subscription)
    update = {
        "company_name_ar": company.name_ar,
        "company_name_en": company.name_en,
        "company_code": company.code,
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
            }
        )
    return resp.model_copy(update=update)


async def _enrich_users(db: AsyncSession, users: list[User]) -> list[UserResponse]:
    company_ids = {u.company_id for u in users if u.company_id}
    companies: dict[int, Company] = {}
    subscriptions: dict[int, CompanySubscription] = {}
    if company_ids:
        from sqlalchemy.orm import selectinload

        result = await db.execute(
            select(Company)
            .options(selectinload(Company.subscription).selectinload(CompanySubscription.plan))
            .where(Company.id.in_(company_ids))
        )
        for company in result.scalars().all():
            companies[company.id] = company
            if company.subscription:
                subscriptions[company.id] = company.subscription
    return [
        _user_with_company(
            u,
            companies.get(u.company_id) if u.company_id else None,
            subscriptions.get(u.company_id) if u.company_id else None,
        )
        for u in users
    ]


async def _enrich_user(db: AsyncSession, user: User) -> UserResponse:
    company = None
    subscription = None
    if user.company_id:
        from sqlalchemy.orm import selectinload

        result = await db.execute(
            select(Company)
            .options(selectinload(Company.subscription).selectinload(CompanySubscription.plan))
            .where(Company.id == user.company_id)
        )
        company = result.scalar_one_or_none()
        if company and company.subscription:
            subscription = company.subscription
    return _user_with_company(user, company, subscription)


@router.post("", response_model=UserResponse)
async def create_user(
    data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    company_id = data.company_id if current_user.is_super_admin else current_user.company_id
    if not company_id and not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    user = await AuthService.create_user(
        db,
        username=data.username,
        email=data.email,
        password=data.password,
        full_name_ar=data.full_name_ar,
        full_name_en=data.full_name_en,
        system_role=data.system_role,
        company_id=company_id,
    )
    if data.phone:
        user.phone = data.phone
    await db.flush()
    return UserResponse.model_validate(user)


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    company_id: Optional[int] = None,
):
    query = select(User).where(User.is_deleted == False)
    if current_user.is_super_admin:
        if company_id:
            query = query.where(User.company_id == company_id)
    else:
        query = query.where(User.company_id == current_user.company_id)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    users = result.scalars().all()
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=await _enrich_users(db, users),
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("/{user_id}/suspend")
async def suspend_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(User).where(User.id == user_id, User.is_deleted == False))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not current_user.is_super_admin and user.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    user.status = UserStatus.SUSPENDED
    await db.flush()
    return {"message": "User suspended", "success": True}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(User).where(User.id == user_id, User.is_deleted == False))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete super admin")
    if not current_user.is_super_admin and user.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    user.soft_delete()
    await db.flush()
    return {"message": "User deleted", "success": True}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(User).where(User.id == user_id, User.is_deleted == False))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not current_user.is_super_admin and user.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    user.status = UserStatus.ACTIVE
    await db.flush()
    return {"message": "User activated", "success": True}


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(User).where(User.id == user_id, User.is_deleted == False))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not current_user.is_super_admin and user.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return await _enrich_user(db, user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(User).where(User.id == user_id, User.is_deleted == False))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not current_user.is_super_admin and user.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if user.is_super_admin and not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot edit super admin")
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "company_id" and not current_user.is_super_admin:
            continue
        setattr(user, field, value)
    await db.flush()
    return await _enrich_user(db, user)


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    data: AdminPasswordReset,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(User).where(User.id == user_id, User.is_deleted == False))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not current_user.is_super_admin and user.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if user.is_super_admin and not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot reset super admin password")
    user.password_hash = get_password_hash(data.new_password)
    await db.flush()
    return {"message": "Password reset successfully", "success": True}
