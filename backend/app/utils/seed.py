from decimal import Decimal

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.tenant import Company, CompanyStatus, CompanySubscription, SubscriptionPlan
from app.models.users import SystemRole, User, UserStatus


async def seed_database() -> None:
    async with AsyncSessionLocal() as db:
        # Subscription plans
        result = await db.execute(select(SubscriptionPlan).limit(1))
        if not result.scalar_one_or_none():
            plans = [
                SubscriptionPlan(
                    name_ar="أساسي",
                    name_en="Basic",
                    code="basic",
                    price_monthly=Decimal("999"),
                    price_yearly=Decimal("9999"),
                    max_users=10,
                    max_projects=3,
                    max_storage_mb=2048,
                ),
                SubscriptionPlan(
                    name_ar="احترافي",
                    name_en="Professional",
                    code="professional",
                    price_monthly=Decimal("2499"),
                    price_yearly=Decimal("24999"),
                    max_users=50,
                    max_projects=15,
                    max_storage_mb=10240,
                ),
                SubscriptionPlan(
                    name_ar="مؤسسي",
                    name_en="Enterprise",
                    code="enterprise",
                    price_monthly=Decimal("4999"),
                    price_yearly=Decimal("49999"),
                    max_users=500,
                    max_projects=100,
                    max_storage_mb=51200,
                ),
            ]
            db.add_all(plans)

        # Super Admin
        result = await db.execute(select(User).where(User.is_super_admin == True))
        if not result.scalar_one_or_none():
            super_admin = User(
                email=settings.SUPER_ADMIN_EMAIL,
                password_hash=get_password_hash(settings.SUPER_ADMIN_PASSWORD),
                full_name_ar="مدير النظام",
                full_name_en="Super Administrator",
                system_role=SystemRole.SUPER_ADMIN,
                is_super_admin=True,
                status=UserStatus.ACTIVE,
                preferred_language="ar",
            )
            db.add(super_admin)

        # Demo company
        result = await db.execute(select(Company).where(Company.code == "DEMO"))
        if not result.scalar_one_or_none():
            plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.code == "professional"))
            plan = plan_result.scalar_one_or_none()
            company = Company(
                name_ar="شركة فراتيلانزا للتطوير العقاري",
                name_en="Fratelanza Real Estate Development",
                code="DEMO",
                email="info@fratelanza-demo.com",
                phone="+201000000000",
                city="القاهرة",
                country="Egypt",
                status=CompanyStatus.ACTIVE,
            )
            db.add(company)
            await db.flush()
            if plan:
                db.add(CompanySubscription(company_id=company.id, plan_id=plan.id, is_active=True))
            admin = User(
                email="admin@demo.fratelanza.com",
                password_hash=get_password_hash("Demo@123456"),
                full_name_ar="مدير الشركة",
                full_name_en="Company Administrator",
                system_role=SystemRole.COMPANY_ADMIN,
                company_id=company.id,
                status=UserStatus.ACTIVE,
            )
            db.add(admin)

        await db.commit()
