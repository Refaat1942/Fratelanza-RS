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

            from app.models.customers import Customer
            from app.models.crm import Lead, LeadSource, LeadStage
            from app.models.real_estate import Building, Floor, Project, ProjectStatus, Unit, UnitStatus, UnitType
            from app.models.finance import ChartOfAccount

            project = Project(
                company_id=company.id,
                name_ar="مشروع فراتيلانزا ريزيدنس",
                name_en="Fratelanza Residence",
                code="FR-001",
                city="القاهرة الجديدة",
                country="Egypt",
                status=ProjectStatus.ACTIVE,
                total_units=10,
                available_units=8,
            )
            db.add(project)
            await db.flush()

            building = Building(project_id=project.id, name_ar="المبنى أ", name_en="Building A", code="A", total_floors=5)
            db.add(building)
            await db.flush()

            floor = Floor(building_id=building.id, floor_number=1, name_ar="الدور الأول", name_en="First Floor")
            db.add(floor)
            await db.flush()

            for i in range(1, 6):
                db.add(
                    Unit(
                        floor_id=floor.id,
                        unit_code=f"A1-{i:02d}",
                        unit_number=str(i),
                        unit_type=UnitType.APARTMENT,
                        area_sqm=Decimal("120"),
                        bedrooms=2,
                        bathrooms=2,
                        price=Decimal("2500000"),
                        status=UnitStatus.AVAILABLE,
                    )
                )

            db.add(
                Customer(
                    company_id=company.id,
                    full_name_ar="أحمد محمد",
                    full_name_en="Ahmed Mohamed",
                    mobile="+201012345678",
                    email="ahmed@example.com",
                    city="القاهرة",
                )
            )
            db.add(
                Lead(
                    company_id=company.id,
                    full_name="سارة علي",
                    mobile="+201098765432",
                    source=LeadSource.FACEBOOK,
                    stage=LeadStage.INTERESTED,
                    project_id=project.id,
                    score=45,
                )
            )
            for code, name_ar, name_en, acc_type in [
                ("1000", "الأصول", "Assets", "asset"),
                ("2000", "الخصوم", "Liabilities", "liability"),
                ("3000", "حقوق الملكية", "Equity", "equity"),
                ("4000", "الإيرادات", "Revenue", "revenue"),
                ("5000", "المصروفات", "Expenses", "expense"),
            ]:
                db.add(
                    ChartOfAccount(
                        company_id=company.id,
                        code=code,
                        name_ar=name_ar,
                        name_en=name_en,
                        account_type=acc_type,
                    )
                )

        await db.commit()
