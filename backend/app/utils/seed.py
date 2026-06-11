from decimal import Decimal

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.tenant import Company, CompanyStatus, CompanySubscription, SubscriptionPlan
from app.models.users import SystemRole, User, UserStatus


DEFAULT_SUBSCRIPTION_PLANS = [
    {
        "name_ar": "أساسي",
        "name_en": "Basic",
        "code": "basic",
        "description_ar": "باقة أساسية للشركات الصغيرة — CRM ومبيعات وتقارير.",
        "description_en": "Starter plan for small teams — CRM, sales pipeline, and reports.",
        "price_monthly": Decimal("999"),
        "price_yearly": Decimal("9999"),
        "max_users": 10,
        "max_projects": 3,
        "max_storage_mb": 2048,
        "sort_order": 1,
    },
    {
        "name_ar": "احترافي",
        "name_en": "Professional",
        "code": "professional",
        "description_ar": "باقة متكاملة — مالية، موارد بشرية، مقاولات، ومشتريات.",
        "description_en": "Full operations — finance, HR, construction, and procurement.",
        "price_monthly": Decimal("2499"),
        "price_yearly": Decimal("24999"),
        "max_users": 50,
        "max_projects": 15,
        "max_storage_mb": 10240,
        "sort_order": 2,
    },
    {
        "name_ar": "مؤسسي",
        "name_en": "Enterprise",
        "code": "enterprise",
        "description_ar": "كل الميزات بما فيها المساعد الذكي — للشركات الكبيرة.",
        "description_en": "All features including AI assistant — for large developers.",
        "price_monthly": Decimal("4999"),
        "price_yearly": Decimal("49999"),
        "max_users": 500,
        "max_projects": 100,
        "max_storage_mb": 51200,
        "sort_order": 3,
    },
    {
        "name_ar": "الباقة الكاملة",
        "name_en": "Full Plan",
        "code": "full",
        "description_ar": (
            "باقة كاملة بدون حدود — مستخدمون ومشاريع غير محدودة، جميع الميزات، "
            "ودعم فني مجاني لمدة 12 شهراً (بدون استضافة سيرفر)."
        ),
        "description_en": (
            "Unlimited users and projects, every platform feature, "
            "plus 12 months of free premium support. One-time payment — no monthly fees "
            "(software only, you host on your own server)."
        ),
        "billing_type": "one_time",
        "price_monthly": Decimal("0"),
        "price_yearly": Decimal("0"),
        "price_one_time": Decimal("149999"),
        "hosting_fee_monthly": Decimal("0"),
        "max_users": 0,
        "max_projects": 0,
        "max_storage_mb": 0,
        "support_months": 12,
        "includes_hosting": False,
        "sort_order": 4,
    },
    {
        "name_ar": "الباقة الكاملة + استضافة",
        "name_en": "Full Plan + Hosting",
        "code": "full_hosted",
        "description_ar": (
            "كل مزايا الباقة الكاملة — دفع مرة واحدة للبرنامج، ورسوم استضافة شهرية للسيرفر "
            "المُدار، نسخ احتياطي، ومراقبة. مستخدمون ومشاريع غير محدودة، دعم مجاني 12 شهراً."
        ),
        "description_en": (
            "Full platform paid once. Managed VPS hosting billed monthly (server, backups, monitoring). "
            "Unlimited users and projects, all features, 12 months free premium support."
        ),
        "billing_type": "one_time",
        "price_monthly": Decimal("0"),
        "price_yearly": Decimal("0"),
        "price_one_time": Decimal("149999"),
        "hosting_fee_monthly": Decimal("2499"),
        "max_users": 0,
        "max_projects": 0,
        "max_storage_mb": 0,
        "support_months": 12,
        "includes_hosting": True,
        "sort_order": 5,
    },
]


def _apply_plan_spec(plan: SubscriptionPlan, spec: dict) -> None:
    from app.services.module_service import ModuleService

    plan.name_ar = spec["name_ar"]
    plan.name_en = spec["name_en"]
    plan.description_ar = spec.get("description_ar")
    plan.description_en = spec.get("description_en")
    plan.billing_type = spec.get("billing_type", "recurring")
    plan.price_monthly = spec["price_monthly"]
    plan.price_yearly = spec["price_yearly"]
    plan.price_one_time = spec.get("price_one_time", 0)
    plan.hosting_fee_monthly = spec.get("hosting_fee_monthly", 0)
    plan.max_users = spec["max_users"]
    plan.max_projects = spec["max_projects"]
    plan.max_storage_mb = spec["max_storage_mb"]
    plan.support_months = spec.get("support_months", 0)
    plan.includes_hosting = spec.get("includes_hosting", False)
    plan.sort_order = spec.get("sort_order", 0)
    plan.features = ModuleService.serialize_plan_features(ModuleService.defaults_for_plan(spec["code"]))
    plan.is_active = True


async def ensure_default_subscription_plans(db) -> int:
    """Create or refresh default plans. Returns count added."""
    added = 0
    for spec in DEFAULT_SUBSCRIPTION_PLANS:
        existing = (
            await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.code == spec["code"]))
        ).scalar_one_or_none()
        if existing:
            if spec["code"] in ("full", "full_hosted"):
                _apply_plan_spec(existing, spec)
            continue
        plan = SubscriptionPlan(code=spec["code"])
        _apply_plan_spec(plan, spec)
        db.add(plan)
        added += 1
    await db.flush()
    return added


async def seed_database() -> None:
    async with AsyncSessionLocal() as db:
        try:
            from sqlalchemy import text
            await db.execute(text(
                "ALTER TABLE companies ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'EGP'"
            ))
            await db.execute(text(
                "ALTER TABLE companies ADD COLUMN IF NOT EXISTS enabled_modules TEXT"
            ))
            await db.execute(text(
                "ALTER TABLE company_subscriptions ADD COLUMN IF NOT EXISTS billing_cycle VARCHAR(20) DEFAULT 'monthly'"
            ))
            await db.execute(text(
                "ALTER TABLE company_subscriptions ADD COLUMN IF NOT EXISTS payment_terms_days INTEGER DEFAULT 30"
            ))
            await db.execute(text(
                "ALTER TABLE company_subscriptions ADD COLUMN IF NOT EXISTS next_billing_date VARCHAR(20)"
            ))
            await db.execute(text(
                "ALTER TABLE company_subscriptions ADD COLUMN IF NOT EXISTS payment_status VARCHAR(20) DEFAULT 'pending'"
            ))
            await db.execute(text(
                "ALTER TABLE company_subscriptions ADD COLUMN IF NOT EXISTS amount_due NUMERIC(12,2)"
            ))
            await db.execute(text(
                "ALTER TABLE company_subscriptions ADD COLUMN IF NOT EXISTS last_payment_date VARCHAR(20)"
            ))
            await db.execute(text(
                "ALTER TABLE company_subscriptions ADD COLUMN IF NOT EXISTS last_reminder_sent_at VARCHAR(50)"
            ))
            await db.execute(text(
                "CREATE TABLE IF NOT EXISTS customer_reminders ("
                "id SERIAL PRIMARY KEY, company_id INTEGER NOT NULL, customer_id INTEGER, "
                "lead_id INTEGER, title VARCHAR(255) NOT NULL, reminder_type VARCHAR(50), "
                "due_date VARCHAR(20) NOT NULL, due_time VARCHAR(10), status VARCHAR(50), "
                "notes TEXT, call_outcome VARCHAR(50), outcome_notes TEXT, completed_at TIMESTAMP, "
                "assigned_to_id INTEGER, created_at TIMESTAMP DEFAULT NOW(), "
                "updated_at TIMESTAMP DEFAULT NOW())"
            ))
            await db.execute(text(
                "ALTER TABLE customer_reminders ADD COLUMN IF NOT EXISTS call_outcome VARCHAR(50)"
            ))
            await db.execute(text(
                "ALTER TABLE customer_reminders ADD COLUMN IF NOT EXISTS outcome_notes TEXT"
            ))
            await db.execute(text(
                "ALTER TABLE customer_reminders ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP"
            ))
            await db.execute(text(
                "CREATE TABLE IF NOT EXISTS payroll_runs ("
                "id SERIAL PRIMARY KEY, company_id INTEGER NOT NULL, period_month VARCHAR(7) NOT NULL, "
                "status VARCHAR(50), total_gross NUMERIC(14,2), total_deductions NUMERIC(14,2), "
                "total_net NUMERIC(14,2), created_by_id INTEGER, created_at TIMESTAMP DEFAULT NOW(), "
                "updated_at TIMESTAMP DEFAULT NOW())"
            ))
            await db.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(100)"
            ))
            await db.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS allowed_modules TEXT"
            ))
            await db.execute(text(
                "ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS description_ar TEXT"
            ))
            await db.execute(text(
                "ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS description_en TEXT"
            ))
            await db.execute(text(
                "ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0"
            ))
            await db.execute(text(
                "ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS support_months INTEGER DEFAULT 0"
            ))
            await db.execute(text(
                "ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS includes_hosting BOOLEAN DEFAULT FALSE"
            ))
            await db.execute(text(
                "ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS billing_type VARCHAR(20) DEFAULT 'recurring'"
            ))
            await db.execute(text(
                "ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS price_one_time NUMERIC(12,2) DEFAULT 0"
            ))
            await db.execute(text(
                "ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS hosting_fee_monthly NUMERIC(12,2) DEFAULT 0"
            ))
            await db.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username) WHERE username IS NOT NULL"
            ))
            await db.execute(text(
                "CREATE TABLE IF NOT EXISTS payslips ("
                "id SERIAL PRIMARY KEY, payroll_run_id INTEGER NOT NULL, employee_id INTEGER NOT NULL, "
                "basic_salary NUMERIC(12,2), allowances NUMERIC(12,2), deductions NUMERIC(12,2), "
                "social_insurance NUMERIC(12,2), net_salary NUMERIC(12,2), status VARCHAR(50), "
                "created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW())"
            ))
            await db.execute(text(
                "ALTER TABLE installments ADD COLUMN IF NOT EXISTS is_manual BOOLEAN DEFAULT FALSE"
            ))
            await db.execute(text(
                "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS pdf_file_path VARCHAR(500)"
            ))
            await db.execute(text(
                "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS pdf_generated_at VARCHAR(30)"
            ))
        except Exception:
            pass
        await ensure_default_subscription_plans(db)

        from app.models.system import SystemSetting
        settings_seed = [
            ("platform_name", "Fratelanza Real Estate", "اسم المنصة", "Platform display name"),
            ("support_email", "support@fratelanza.com", "بريد الدعم", "Support contact email"),
            ("default_currency", "EGP", "العملة الافتراضية", "Default currency for new companies"),
            ("trial_days", "14", "أيام التجربة", "Trial period in days"),
            ("max_login_attempts", "5", "محاولات الدخول", "Max failed login attempts"),
        ]
        for key, value, desc_ar, desc_en in settings_seed:
            existing = (await db.execute(select(SystemSetting).where(SystemSetting.key == key))).scalar_one_or_none()
            if not existing:
                db.add(SystemSetting(key=key, value=value, description_ar=desc_ar, description_en=desc_en))

        # Backfill usernames for existing users
        all_users = (await db.execute(select(User))).scalars().all()
        seen_usernames: set[str] = set()
        for u in all_users:
            if not getattr(u, "username", None):
                base = (u.email.split("@")[0] if u.email else f"user{u.id}").lower().replace(".", "_")
                candidate = base
                n = 1
                while candidate in seen_usernames:
                    candidate = f"{base}{n}"
                    n += 1
                u.username = candidate
                seen_usernames.add(candidate)
            else:
                seen_usernames.add(u.username)

        # Super Admin — create only if missing (do not overwrite password on restart)
        result = await db.execute(select(User).where(User.is_super_admin == True))
        super_admin = result.scalar_one_or_none()
        if not super_admin:
            super_admin = User(
                username="superadmin",
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

        # Backfill subscription billing columns for existing rows
        try:
            from datetime import date, timedelta
            from app.models.tenant import CompanySubscription as CoSub
            subs = (await db.execute(select(CoSub))).scalars().all()
            for sub in subs:
                if not sub.billing_cycle:
                    sub.billing_cycle = "monthly"
                if sub.payment_terms_days is None:
                    sub.payment_terms_days = 30
                if not sub.next_billing_date:
                    sub.next_billing_date = (date.today() + timedelta(days=30)).isoformat()
                if not sub.payment_status:
                    sub.payment_status = "pending"
                if sub.amount_due is None:
                    plan_row = (
                        await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == sub.plan_id))
                    ).scalar_one_or_none()
                    if plan_row:
                        sub.amount_due = plan_row.price_monthly
        except Exception:
            pass

        # Demo company
        result = await db.execute(select(Company).where(Company.code == "DEMO"))
        company = result.scalar_one_or_none()
        if not company:
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
                from datetime import date, timedelta
                db.add(
                    CompanySubscription(
                        company_id=company.id,
                        plan_id=plan.id,
                        is_active=True,
                        billing_cycle="monthly",
                        payment_terms_days=30,
                        next_billing_date=(date.today() + timedelta(days=14)).isoformat(),
                        payment_status="paid",
                        amount_due=plan.price_monthly,
                        last_payment_date=date.today().isoformat(),
                    )
                )

        # Demo admin — always ensure exists with known password
        demo_email = "admin@demo.fratelanza.com"
        demo_password = "Demo123456"
        demo_result = await db.execute(select(User).where(User.email == demo_email))
        demo_admin = demo_result.scalar_one_or_none()
        if not demo_admin:
            demo_admin = User(
                username="demo_admin",
                email=demo_email,
                password_hash=get_password_hash(demo_password),
                full_name_ar="مدير الشركة",
                full_name_en="Company Administrator",
                system_role=SystemRole.COMPANY_ADMIN,
                company_id=company.id if company else None,
                status=UserStatus.ACTIVE,
            )
            db.add(demo_admin)
        else:
            demo_admin.status = UserStatus.ACTIVE
            demo_admin.is_deleted = False
            if not demo_admin.username:
                demo_admin.username = "demo_admin"
            if company and not demo_admin.company_id:
                demo_admin.company_id = company.id

        # Demo data (only if no project yet)
        if company and company.id:
            from app.models.customers import Customer
            from app.models.crm import Lead, LeadSource, LeadStage
            from app.models.real_estate import Building, Floor, Project, ProjectStatus, Unit, UnitStatus, UnitType
            from app.models.finance import ChartOfAccount

            pe = await db.execute(select(Project).where(Project.company_id == company.id).limit(1))
            project = pe.scalar_one_or_none()
            if not project:
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

            if not (await db.execute(select(Building).where(Building.project_id == project.id).limit(1))).scalar_one_or_none():
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

            cust_result = await db.execute(
                select(Customer).where(Customer.company_id == company.id, Customer.mobile == "+201012345678")
            )
            customer = cust_result.scalar_one_or_none()
            if not customer:
                customer = Customer(
                    company_id=company.id,
                    full_name_ar="أحمد محمد",
                    full_name_en="Ahmed Mohamed",
                    mobile="+201012345678",
                    email="ahmed@example.com",
                    city="القاهرة",
                )
                db.add(customer)
                await db.flush()

            if not (await db.execute(select(Lead).where(Lead.company_id == company.id).limit(1))).scalar_one_or_none():
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
                exists = await db.execute(
                    select(ChartOfAccount).where(ChartOfAccount.company_id == company.id, ChartOfAccount.code == code)
                )
                if not exists.scalar_one_or_none():
                    db.add(
                        ChartOfAccount(
                            company_id=company.id,
                            code=code,
                            name_ar=name_ar,
                            name_en=name_en,
                            account_type=acc_type,
                        )
                    )

            from app.models.hr import Employee, Attendance, LeaveRequest, PayrollRun, Payslip
            from app.models.crm import CustomerReminder, ReminderType
            from app.models.finance import BankAccount, JournalEntry, JournalLine
            from app.models.sales import Contract, ContractStatus, Payment, PaymentPlan, Installment, InstallmentStatus, PaymentPlanType
            from datetime import date, timedelta

            employees_created = []
            for code, name_ar, name_en, dept, pos, sal in [
                ("EMP-001", "محمود حسن", "Mahmoud Hassan", "Sales", "Sales Agent", "15000"),
                ("EMP-002", "نورا أحمد", "Noura Ahmed", "Finance", "Accountant", "18000"),
                ("EMP-003", "كريم سامي", "Karim Samy", "HR", "HR Officer", "12000"),
            ]:
                er = await db.execute(
                    select(Employee).where(Employee.company_id == company.id, Employee.employee_code == code)
                )
                emp = er.scalar_one_or_none()
                if not emp:
                    emp = Employee(
                        company_id=company.id,
                        employee_code=code,
                        full_name_ar=name_ar,
                        full_name_en=name_en,
                        department=dept,
                        position=pos,
                        salary=Decimal(sal),
                        hire_date="2024-01-01",
                    )
                    db.add(emp)
                    await db.flush()
                employees_created.append(emp)

            if employees_created and not (
                await db.execute(
                    select(Attendance).join(Employee).where(Employee.company_id == company.id).limit(1)
                )
            ).scalar_one_or_none():
                today = date.today().isoformat()
                for emp in employees_created[:2]:
                    db.add(Attendance(employee_id=emp.id, date=today, check_in="09:00", check_out="17:00", status="present"))

            if employees_created and not (
                await db.execute(
                    select(LeaveRequest).join(Employee).where(Employee.company_id == company.id).limit(1)
                )
            ).scalar_one_or_none():
                db.add(
                    LeaveRequest(
                        employee_id=employees_created[0].id,
                        leave_type="annual",
                        start_date=(date.today() + timedelta(days=14)).isoformat(),
                        end_date=(date.today() + timedelta(days=16)).isoformat(),
                        reason="Family vacation",
                        status="pending",
                    )
                )

            if not (await db.execute(select(CustomerReminder).where(CustomerReminder.company_id == company.id).limit(1))).scalar_one_or_none():
                db.add(
                    CustomerReminder(
                        company_id=company.id,
                        customer_id=customer.id if customer else None,
                        title="Call Ahmed Mohamed about unit A1-02",
                        reminder_type=ReminderType.CALL,
                        due_date=date.today().isoformat(),
                        due_time="11:00",
                        notes="Interested in 2.5M EGP apartment — follow up on payment plan",
                    )
                )
                db.add(
                    CustomerReminder(
                        company_id=company.id,
                        title="Site visit with Sara Ali",
                        reminder_type=ReminderType.VISIT,
                        due_date=(date.today() + timedelta(days=2)).isoformat(),
                        due_time="14:00",
                        notes="Facebook lead — show Fratelanza Residence",
                    )
                )

            if not (await db.execute(select(BankAccount).where(BankAccount.company_id == company.id).limit(1))).scalar_one_or_none():
                db.add(
                    BankAccount(
                        company_id=company.id,
                        bank_name="CIB",
                        account_number="1234567890",
                        currency="EGP",
                        balance=Decimal("850000"),
                    )
                )

            from app.models.brokers import Broker
            from app.models.warehouse import Warehouse, InventoryItem
            from app.models.procurement import Vendor
            from app.models.construction import ConstructionPhase
            from app.models.sales import Reservation, ReservationStatus

            if not (await db.execute(select(Broker).where(Broker.company_id == company.id).limit(1))).scalar_one_or_none():
                db.add(
                    Broker(
                        company_id=company.id,
                        name_ar="محمد الوسيط",
                        name_en="Mohamed Broker",
                        mobile="+201055566677",
                        email="broker@example.com",
                        commission_rate=Decimal("3.0"),
                        rank_score=85,
                    )
                )

            wh = (await db.execute(select(Warehouse).where(Warehouse.company_id == company.id).limit(1))).scalar_one_or_none()
            if not wh:
                wh = Warehouse(
                    company_id=company.id,
                    name_ar="المخزن الرئيسي",
                    name_en="Main Warehouse",
                    code="WH-001",
                    location="New Cairo Site",
                )
                db.add(wh)
                await db.flush()
                db.add(
                    InventoryItem(
                        warehouse_id=wh.id,
                        sku="CEM-001",
                        name_ar="أسمنت",
                        name_en="Cement",
                        quantity=Decimal("500"),
                        min_stock_level=Decimal("100"),
                        unit="bags",
                    )
                )
                db.add(
                    InventoryItem(
                        warehouse_id=wh.id,
                        sku="STL-001",
                        name_ar="حديد تسليح",
                        name_en="Steel Rebar",
                        quantity=Decimal("50"),
                        min_stock_level=Decimal("80"),
                        unit="tons",
                    )
                )

            if not (await db.execute(select(Vendor).where(Vendor.company_id == company.id).limit(1))).scalar_one_or_none():
                db.add(
                    Vendor(
                        company_id=company.id,
                        name_ar="شركة مواد البناء",
                        name_en="Building Materials Co.",
                        contact_person="Ali Vendor",
                        phone="+201033344455",
                        email="vendor@example.com",
                        rating=4,
                    )
                )

            if not (await db.execute(select(ConstructionPhase).where(ConstructionPhase.project_id == project.id).limit(1))).scalar_one_or_none():
                db.add(
                    ConstructionPhase(
                        project_id=project.id,
                        name_ar="الهيكل الخرساني",
                        name_en="Concrete Structure",
                        planned_start="2025-01-01",
                        planned_end="2025-06-30",
                        progress_percent=65,
                        planned_cost=Decimal("5000000"),
                        actual_cost=Decimal("3200000"),
                    )
                )
                db.add(
                    ConstructionPhase(
                        project_id=project.id,
                        name_ar="التشطيبات",
                        name_en="Finishing",
                        planned_start="2025-07-01",
                        planned_end="2025-12-31",
                        progress_percent=20,
                        planned_cost=Decimal("3000000"),
                        actual_cost=Decimal("400000"),
                    )
                )

            from app.models.property import MaintenanceRequest
            from app.models.customer_service import Ticket

            unit3_r = await db.execute(
                select(Unit).join(Floor).join(Building).where(
                    Building.project_id == project.id, Unit.unit_code == "A1-03"
                )
            )
            unit3 = unit3_r.scalar_one_or_none()
            if unit3 and customer and not (
                await db.execute(select(MaintenanceRequest).where(MaintenanceRequest.company_id == company.id).limit(1))
            ).scalar_one_or_none():
                db.add(
                    MaintenanceRequest(
                        company_id=company.id,
                        unit_id=unit3.id,
                        customer_id=customer.id,
                        title="AC not cooling — Unit A1-03",
                        description="Customer reported AC issue in master bedroom",
                        priority="high",
                        status="open",
                    )
                )
                db.add(
                    MaintenanceRequest(
                        company_id=company.id,
                        unit_id=unit3.id,
                        customer_id=customer.id,
                        title="Plumbing check — Unit A1-03",
                        description="Routine inspection before handover",
                        priority="low",
                        status="in_progress",
                    )
                )

            if customer and not (
                await db.execute(select(Ticket).where(Ticket.company_id == company.id).limit(1))
            ).scalar_one_or_none():
                db.add(
                    Ticket(
                        company_id=company.id,
                        ticket_number="TKT-DEMO-001",
                        category="complaint",
                        subject="Delay in unit delivery timeline",
                        description="Customer asking for updated delivery schedule",
                        customer_id=customer.id,
                        priority="medium",
                        status="open",
                    )
                )
                db.add(
                    Ticket(
                        company_id=company.id,
                        ticket_number="TKT-DEMO-002",
                        category="inquiry",
                        subject="Payment plan modification request",
                        description="Request to adjust installment dates",
                        customer_id=customer.id,
                        priority="high",
                        status="in_progress",
                    )
                )

            payroll_emps = (
                await db.execute(select(Employee).where(Employee.company_id == company.id, Employee.is_active == True))
            ).scalars().all()
            if payroll_emps and not (
                await db.execute(select(PayrollRun).where(PayrollRun.company_id == company.id).limit(1))
            ).scalar_one_or_none():
                month = date.today().strftime("%Y-%m")
                run = PayrollRun(
                    company_id=company.id,
                    period_month=month,
                    status="processed",
                    created_by_id=demo_admin.id if demo_admin else None,
                )
                db.add(run)
                await db.flush()
                tg = td = tn = Decimal("0")
                for emp in payroll_emps:
                    basic = Decimal(str(emp.salary or 0))
                    social = (basic * Decimal("0.11")).quantize(Decimal("0.01"))
                    net = basic - social
                    tg += basic
                    td += social
                    tn += net
                    db.add(
                        Payslip(
                            payroll_run_id=run.id,
                            employee_id=emp.id,
                            basic_salary=basic,
                            allowances=Decimal("0"),
                            social_insurance=social,
                            deductions=social,
                            net_salary=net,
                            status="processed",
                        )
                    )
                run.total_gross = tg
                run.total_deductions = td
                run.total_net = tn

            unit2_r = await db.execute(
                select(Unit).join(Floor).join(Building).where(
                    Building.project_id == project.id, Unit.unit_code == "A1-02"
                )
            )
            unit2 = unit2_r.scalar_one_or_none()
            if unit2 and customer and not (await db.execute(select(Reservation).where(Reservation.company_id == company.id).limit(1))).scalar_one_or_none():
                unit2.is_locked = True
                unit2.status = UnitStatus.RESERVED
                db.add(
                    Reservation(
                        company_id=company.id,
                        reservation_number="RES-DEMO-001",
                        customer_id=customer.id,
                        unit_id=unit2.id,
                        deposit_amount=Decimal("100000"),
                        reservation_date=date.today().isoformat(),
                        expiry_date=(date.today() + timedelta(days=14)).isoformat(),
                        status=ReservationStatus.PENDING_APPROVAL,
                        notes="Demo reservation from Sara Ali lead",
                    )
                )

            unit_r = await db.execute(
                select(Unit).join(Floor).join(Building).where(Building.project_id == project.id, Unit.unit_code == "A1-01")
            )
            unit = unit_r.scalar_one_or_none()
            if unit and customer and not (await db.execute(select(Contract).where(Contract.company_id == company.id).limit(1))).scalar_one_or_none():
                unit.is_locked = True
                unit.status = UnitStatus.CONTRACTED
                contract = Contract(
                    company_id=company.id,
                    contract_number="CNT-DEMO-001",
                    customer_id=customer.id,
                    unit_id=unit.id,
                    total_price=Decimal("2500000"),
                    contract_date=date.today().isoformat(),
                    status=ContractStatus.ACTIVE,
                    is_signed=True,
                )
                db.add(contract)
                await db.flush()
                plan = PaymentPlan(
                    contract_id=contract.id,
                    plan_type=PaymentPlanType.QUARTERLY,
                    down_payment=Decimal("500000"),
                    total_amount=Decimal("2500000"),
                    number_of_installments=4,
                    start_date=date.today().isoformat(),
                )
                db.add(plan)
                await db.flush()
                inst = Installment(
                    payment_plan_id=plan.id,
                    installment_number=1,
                    due_date=date.today().isoformat(),
                    due_amount=Decimal("500000"),
                    paid_amount=Decimal("250000"),
                    remaining_balance=Decimal("250000"),
                    status=InstallmentStatus.PARTIAL,
                )
                db.add(inst)
                await db.flush()
                db.add(
                    Payment(
                        company_id=company.id,
                        installment_id=inst.id,
                        customer_id=customer.id,
                        amount=Decimal("250000"),
                        payment_date=date.today().isoformat(),
                        payment_method="bank_transfer",
                        reference_number="PAY-DEMO-001",
                    )
                )
                revenue = (
                    await db.execute(
                        select(ChartOfAccount).where(ChartOfAccount.company_id == company.id, ChartOfAccount.code == "4000")
                    )
                ).scalar_one_or_none()
                cash = (
                    await db.execute(
                        select(ChartOfAccount).where(ChartOfAccount.company_id == company.id, ChartOfAccount.code == "1000")
                    )
                ).scalar_one_or_none()
                if revenue and cash and not (await db.execute(select(JournalEntry).where(JournalEntry.company_id == company.id).limit(1))).scalar_one_or_none():
                    entry = JournalEntry(
                        company_id=company.id,
                        entry_number="JE-DEMO-001",
                        entry_date=date.today().isoformat(),
                        description="Down payment received - Ahmed Mohamed",
                    )
                    db.add(entry)
                    await db.flush()
                    db.add(JournalLine(journal_entry_id=entry.id, account_id=cash.id, debit=Decimal("250000"), credit=Decimal("0")))
                    db.add(JournalLine(journal_entry_id=entry.id, account_id=revenue.id, debit=Decimal("0"), credit=Decimal("250000")))

        if company:
            company.currency = "EGP"

        await db.commit()
