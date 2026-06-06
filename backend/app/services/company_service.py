from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_password_hash
from app.models.tenant import BillingCycle, Company, CompanyStatus, CompanySubscription
from app.services.platform_billing_service import PlatformBillingService
from app.models.users import SystemRole, User, UserStatus
from app.schemas.company import CompanyCreate, CompanyUpdate
from app.services.module_service import ModuleService


class CompanyService:
    @staticmethod
    async def list_companies(db: AsyncSession, page: int = 1, page_size: int = 20) -> tuple[list[Company], int]:
        query = (
            select(Company)
            .options(selectinload(Company.subscription).selectinload(CompanySubscription.plan))
            .where(Company.is_deleted == False)
            .order_by(Company.id.desc())
        )
        total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
        result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
        return list(result.scalars().all()), total

    @staticmethod
    async def get_company(db: AsyncSession, company_id: int) -> Company:
        result = await db.execute(
            select(Company)
            .options(selectinload(Company.subscription).selectinload(CompanySubscription.plan))
            .where(Company.id == company_id, Company.is_deleted == False)
        )
        company = result.scalar_one_or_none()
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        return company

    @staticmethod
    async def create_company(db: AsyncSession, data: CompanyCreate) -> Company:
        existing = await db.execute(select(Company).where(Company.code == data.code))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company code already exists")
        company = Company(
            name_ar=data.name_ar,
            name_en=data.name_en,
            code=data.code,
            email=data.email,
            phone=data.phone,
            address=data.address,
            city=data.city,
            country=data.country,
            tax_number=data.tax_number,
            commercial_register=data.commercial_register,
            default_language=data.default_language,
            theme=data.theme,
            currency=getattr(data, "currency", "EGP") or "EGP",
            storage_limit_mb=data.storage_limit_mb,
            status=CompanyStatus.TRIAL if data.start_trial else CompanyStatus.ACTIVE,
        )
        db.add(company)
        await db.flush()

        plan = None
        if data.start_trial and not data.plan_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscription plan required to start a trial",
            )
        if data.plan_id:
            from app.models.tenant import SubscriptionPlan
            plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == data.plan_id))
            plan = plan_result.scalar_one_or_none()
            if not plan:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription plan not found")
            subscription = CompanySubscription(
                company_id=company.id,
                plan_id=data.plan_id,
                is_active=True,
                billing_cycle=BillingCycle.MONTHLY.value,
                payment_terms_days=30,
            )
            db.add(subscription)
            await db.flush()
            subscription.plan = plan
            await PlatformBillingService.ensure_subscription_defaults(
                db,
                company,
                plan,
                trial=data.start_trial,
            )

        if data.enabled_modules:
            await ModuleService.set_company_modules(db, company, data.enabled_modules)
        elif plan:
            await ModuleService.set_company_modules(db, company, ModuleService.defaults_for_plan(plan.code))

        if data.admin_email and data.admin_password:
            admin_username = data.admin_email.split("@")[0].lower().replace(".", "_")
            admin = User(
                username=admin_username,
                email=data.admin_email,
                password_hash=get_password_hash(data.admin_password),
                full_name_ar=data.admin_name_ar or data.name_ar,
                full_name_en=data.admin_name_en or data.name_en,
                system_role=SystemRole.COMPANY_ADMIN,
                company_id=company.id,
                status=UserStatus.ACTIVE,
            )
            db.add(admin)

        await db.flush()
        return company

    @staticmethod
    async def update_company(db: AsyncSession, company_id: int, data: CompanyUpdate) -> Company:
        company = await CompanyService.get_company(db, company_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(company, field, value)
        await db.flush()
        return company

    @staticmethod
    async def suspend_company(db: AsyncSession, company_id: int) -> Company:
        company = await CompanyService.get_company(db, company_id)
        company.status = CompanyStatus.SUSPENDED
        await db.flush()
        return company

    @staticmethod
    async def activate_company(db: AsyncSession, company_id: int) -> Company:
        company = await CompanyService.get_company(db, company_id)
        company.status = CompanyStatus.ACTIVE
        await db.flush()
        return company
