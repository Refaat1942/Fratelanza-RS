from decimal import Decimal

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.tenant import Company, CompanyStatus, CompanySubscription, SubscriptionPlan
from app.models.users import SystemRole, User, UserStatus


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
                "CREATE TABLE IF NOT EXISTS payslips ("
                "id SERIAL PRIMARY KEY, payroll_run_id INTEGER NOT NULL, employee_id INTEGER NOT NULL, "
                "basic_salary NUMERIC(12,2), allowances NUMERIC(12,2), deductions NUMERIC(12,2), "
                "social_insurance NUMERIC(12,2), net_salary NUMERIC(12,2), status VARCHAR(50), "
                "created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW())"
            ))
        except Exception:
            pass
        # Subscription plans
        result = await db.execute(select(SubscriptionPlan).limit(1))
        if not result.scalar_one_or_none():
            from app.services.module_service import ModuleService
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
                    features=ModuleService.serialize_plan_features(ModuleService.defaults_for_plan("basic")),
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
                    features=ModuleService.serialize_plan_features(ModuleService.defaults_for_plan("professional")),
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
                    features=ModuleService.serialize_plan_features(ModuleService.defaults_for_plan("enterprise")),
                ),
            ]
            db.add_all(plans)

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

        # Super Admin — create only if missing (do not overwrite password on restart)
        result = await db.execute(select(User).where(User.is_super_admin == True))
        super_admin = result.scalar_one_or_none()
        if not super_admin:
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
                db.add(CompanySubscription(company_id=company.id, plan_id=plan.id, is_active=True))

        # Demo admin — always ensure exists with known password
        demo_email = "admin@demo.fratelanza.com"
        demo_password = "Demo123456"
        demo_result = await db.execute(select(User).where(User.email == demo_email))
        demo_admin = demo_result.scalar_one_or_none()
        if not demo_admin:
            demo_admin = User(
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

            from app.models.hr import Employee, Attendance, LeaveRequest
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

            unit_r = await db.execute(
                select(Unit).join(Floor).join(Building).where(Building.project_id == project.id).limit(1)
            )
            unit = unit_r.scalar_one_or_none()
            if unit and customer and not (await db.execute(select(Contract).where(Contract.company_id == company.id).limit(1))).scalar_one_or_none():
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
