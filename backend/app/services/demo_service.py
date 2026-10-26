"""Customer demo environments.

A demo is a normal tenant (``companies.is_demo = true``) plus a ``demo_environments`` row holding
its presentation configuration. Data is created through the same models and services as
production, using only fictional people. Reset deletes *only* that tenant's business data
(resolved generically through foreign keys) and re-seeds the baseline.
"""

import json
import random
import secrets
import shutil
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import Base
from app.core.platform_modules import ALL_MODULE_KEYS
from app.core.security import get_password_hash
from app.models.crm import Lead, LeadSource, LeadStage
from app.models.customers import Customer
from app.models.hr import Employee, PayrollRun, Payslip
from app.models.property import MaintenanceRequest
from app.models.real_estate import Building, Floor, Project, ProjectStatus, Unit, UnitStatus, UnitType
from app.models.rentals import DemoEnvironment, PropertyOwner, PropertyRequest
from app.models.system import Notification
from app.models.tenant import Company, CompanyStatus
from app.models.users import SystemRole, User, UserStatus
from app.services.access_service import DEFAULT_DEMO_ACTIONS, AccessService
from app.services.expense_service import ExpenseService
from app.services.rental_service import RentalService, add_months, company_today
from app.services.re_dashboard_service import CARD_KEYS
from app.services.settlement_service import SettlementService, frequency_block

PROFILES: dict[str, dict] = {
    "property_management": {
        "name_ar": "إدارة الأملاك", "name_en": "Property Management",
        "modules": ["dashboard", "customers", "projects", "rentals", "owners", "property_expenses", "property", "reports"],
        "cards": ["total_units", "available_units", "occupied_units", "active_contracts", "expiring_contracts",
                  "upcoming_collections", "overdue_rent", "upcoming_settlements", "owner_payables", "maintenance_expenses"],
    },
    "sales_brokerage": {
        "name_ar": "المبيعات والوساطة", "name_en": "Sales & Brokerage",
        "modules": ["dashboard", "customers", "leads", "follow_ups", "projects", "real_estate_requests", "reservations",
                    "contracts", "brokers", "reports"],
        "cards": ["properties_offered", "purchase_requests", "rental_requests", "total_units", "available_units"],
    },
    "rental_collections": {
        "name_ar": "الإيجارات والتحصيل", "name_en": "Rental & Collections",
        "modules": ["dashboard", "customers", "rentals", "owners", "property_expenses", "reports"],
        "cards": ["active_contracts", "expiring_contracts", "upcoming_collections", "overdue_rent", "upcoming_settlements",
                  "owner_payables", "revenue", "expenses", "profit"],
    },
    "full_erp": {
        "name_ar": "نظام عقاري متكامل", "name_en": "Full Real Estate ERP",
        "modules": [m for m in ALL_MODULE_KEYS if m not in ("ai_assistant", "branding", "customer_portal")],
        "cards": list(CARD_KEYS),
    },
}

# Never deleted by a reset: tenant identity, people, configuration, and the audit trail
KEEP_TABLES = {
    "companies", "branches", "users", "roles", "user_roles", "role_permissions", "permissions", "subscription_plans",
    "company_subscriptions", "demo_environments", "audit_logs", "system_settings",
}
# FKs that point at kept tables never make a row tenant-owned by themselves
NON_OWNING_PARENTS = {"users", "companies", "branches", "roles", "permissions", "subscription_plans"}


def _tenant_clause(table, company_id: int, seen: Optional[set] = None):
    """WHERE clause selecting the rows of ``table`` that belong to ``company_id`` (via FKs)."""
    seen = seen or set()
    if "company_id" in table.c:
        return table.c.company_id == company_id
    if table.name in seen:
        return None
    seen = seen | {table.name}
    for fk in sorted(table.foreign_keys, key=lambda f: f.parent.name):
        parent = fk.column.table
        if parent.name in NON_OWNING_PARENTS or parent.name == table.name:
            continue
        parent_clause = _tenant_clause(parent, company_id, seen)
        if parent_clause is not None:
            return fk.parent.in_(select(fk.column).where(parent_clause))
    return None


def reset_plan() -> dict[str, str]:
    """For each table: 'keep', 'direct', 'via_fk' or 'unresolved' (used by tests)."""
    plan = {}
    for table in Base.metadata.sorted_tables:
        if table.name in KEEP_TABLES:
            plan[table.name] = "keep"
        elif "company_id" in table.c:
            plan[table.name] = "direct"
        elif _tenant_clause(table, 0) is not None:
            plan[table.name] = "via_fk"
        else:
            plan[table.name] = "unresolved"
    return plan


async def purge_tenant_data(db: AsyncSession, company_id: int) -> int:
    company = (await db.execute(select(Company).where(Company.id == company_id))).scalar_one()
    if not company.is_demo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only demo tenants can be reset")
    deleted = 0
    # Children first. Clauses are built before deleting so parent sub-selects still see rows.
    clauses = []
    for table in reversed(Base.metadata.sorted_tables):
        if table.name in KEEP_TABLES:
            continue
        clause = _tenant_clause(table, company_id)
        if clause is not None:
            clauses.append((table, clause))
    # Two passes: rows referenced only through deeper chains are removed in the second pass.
    for _ in range(2):
        for table, clause in clauses:
            result = await db.execute(delete(table).where(clause))
            deleted += result.rowcount or 0
    await db.flush()
    storage = Path(settings.STORAGE_LOCAL_PATH) / "tenants" / str(company_id)
    if storage.exists():
        shutil.rmtree(storage, ignore_errors=True)
    return deleted


def _demo_dict(company: Company, demo: DemoEnvironment, users: list[User]) -> dict:
    reason = AccessService.demo_state(demo)
    return {
        "id": demo.id,
        "company_id": company.id,
        "company_code": company.code,
        "company_name_ar": company.name_ar,
        "company_name_en": company.name_en,
        "logo_url": company.logo_url,
        "prospect_name": demo.prospect_name,
        "profile": demo.profile,
        "enabled_modules": json.loads(company.enabled_modules) if company.enabled_modules else [],
        "allowed_actions": json.loads(demo.allowed_actions) if demo.allowed_actions else DEFAULT_DEMO_ACTIONS,
        "dashboard_cards": json.loads(demo.dashboard_cards) if demo.dashboard_cards else None,
        "expires_at": demo.expires_at.isoformat() if demo.expires_at else None,
        "is_enabled": demo.is_enabled,
        "revoked_at": demo.revoked_at.isoformat() if demo.revoked_at else None,
        "last_reset_at": demo.last_reset_at.isoformat() if demo.last_reset_at else None,
        "status": reason or "active",
        "notes": demo.notes,
        "users": [
            {"id": u.id, "username": u.username, "email": u.email, "full_name_ar": u.full_name_ar,
             "system_role": u.system_role.value, "status": u.status.value}
            for u in users
        ],
    }


class DemoService:
    @staticmethod
    async def get(db: AsyncSession, demo_id: int) -> tuple[Company, DemoEnvironment]:
        demo = (await db.execute(select(DemoEnvironment).where(DemoEnvironment.id == demo_id))).scalar_one_or_none()
        if not demo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo not found")
        company = (await db.execute(select(Company).where(Company.id == demo.company_id))).scalar_one()
        return company, demo

    @staticmethod
    async def users_of(db: AsyncSession, company_id: int) -> list[User]:
        return list(
            (await db.execute(select(User).where(User.company_id == company_id, User.is_deleted == False).order_by(User.id))).scalars().all()  # noqa: E712
        )

    @staticmethod
    async def describe(db: AsyncSession, company: Company, demo: DemoEnvironment) -> dict:
        return _demo_dict(company, demo, await DemoService.users_of(db, company.id))

    @staticmethod
    async def list_all(db: AsyncSession) -> list[dict]:
        rows = (
            await db.execute(select(Company, DemoEnvironment).join(DemoEnvironment, DemoEnvironment.company_id == Company.id).order_by(DemoEnvironment.id.desc()))
        ).all()
        return [await DemoService.describe(db, c, d) for c, d in rows]

    @staticmethod
    def _validate_config(modules: Optional[list[str]], actions: Optional[list[str]], cards: Optional[list[str]]) -> None:
        from app.core.permissions import ACTION_KEYS

        if modules is not None and set(modules) - set(ALL_MODULE_KEYS):
            raise HTTPException(status_code=400, detail=f"Unknown modules: {sorted(set(modules) - set(ALL_MODULE_KEYS))}")
        if actions is not None and set(actions) - set(ACTION_KEYS):
            raise HTTPException(status_code=400, detail=f"Unknown actions: {sorted(set(actions) - set(ACTION_KEYS))}")
        if actions is not None and "manage_permissions" in actions:
            raise HTTPException(status_code=400, detail="Demo users cannot manage permissions")
        if cards is not None and set(cards) - set(CARD_KEYS):
            raise HTTPException(status_code=400, detail=f"Unknown dashboard cards: {sorted(set(cards) - set(CARD_KEYS))}")

    @staticmethod
    async def create(db: AsyncSession, data: dict, actor: User) -> tuple[Company, DemoEnvironment, list[dict]]:
        profile = data.get("profile") or "full_erp"
        if profile not in PROFILES:
            raise HTTPException(status_code=400, detail="Unknown demo profile")
        modules = data.get("enabled_modules") or PROFILES[profile]["modules"]
        actions = data.get("allowed_actions") or DEFAULT_DEMO_ACTIONS
        cards = data.get("dashboard_cards") if data.get("dashboard_cards") is not None else PROFILES[profile]["cards"]
        DemoService._validate_config(modules, actions, cards)
        code = f"DEMO-{uuid.uuid4().hex[:6].upper()}"
        company = Company(
            name_ar=data["company_name_ar"], name_en=data["company_name_en"], code=code, country="Egypt",
            currency=data.get("currency") or "EGP", default_language="ar", status=CompanyStatus.ACTIVE,
            is_demo=True, timezone=data.get("timezone") or "Africa/Cairo", logo_url=data.get("logo_url"),
            enabled_modules=json.dumps([m for m in ALL_MODULE_KEYS if m in set(modules) | {"dashboard"}]),
            email=f"{code.lower()}@demo.fratelanza.com",
        )
        db.add(company)
        await db.flush()
        expires_at = data.get("expires_at") or (datetime.now(timezone.utc) + timedelta(days=int(data.get("valid_days") or 14)))
        demo = DemoEnvironment(
            company_id=company.id, prospect_name=data["prospect_name"], profile=profile,
            allowed_actions=json.dumps(sorted(set(actions))), dashboard_cards=json.dumps(cards),
            expires_at=expires_at, is_enabled=True, notes=data.get("notes"), created_by_id=actor.id,
        )
        db.add(demo)
        await db.flush()
        credentials = []
        for spec in data.get("users") or [{"role": "company_admin"}]:
            credentials.append(await DemoService.add_user(db, company, spec.get("role", "company_admin"), spec.get("full_name")))
        if data.get("seed", True):
            await DemoSeeder(db, company).run()
            demo.last_reset_at = datetime.now(timezone.utc)
        await db.flush()
        return company, demo, credentials

    @staticmethod
    async def add_user(db: AsyncSession, company: Company, role: str, full_name: Optional[str] = None) -> dict:
        try:
            system_role = SystemRole(role)
        except ValueError:
            raise HTTPException(status_code=400, detail="Unknown role")
        if system_role in (SystemRole.SUPER_ADMIN, SystemRole.CUSTOMER, SystemRole.BROKER):
            raise HTTPException(status_code=400, detail="Role not allowed in demos")
        suffix = uuid.uuid4().hex[:5]
        username = f"{company.code.lower().replace('-', '')}.{system_role.value}.{suffix}"
        password = secrets.token_urlsafe(9)
        user = User(
            company_id=company.id, username=username, email=f"{username}@demo.fratelanza.com",
            password_hash=get_password_hash(password), full_name_ar=full_name or f"مستخدم تجريبي ({system_role.value})",
            full_name_en=full_name or f"Demo {system_role.value}", system_role=system_role, status=UserStatus.ACTIVE,
            is_super_admin=False,
        )
        db.add(user)
        await db.flush()
        # The password is returned once to the platform admin and never stored in clear text
        return {"user_id": user.id, "username": username, "password": password, "role": system_role.value}

    @staticmethod
    async def update(db: AsyncSession, company: Company, demo: DemoEnvironment, data: dict) -> None:
        DemoService._validate_config(data.get("enabled_modules"), data.get("allowed_actions"), data.get("dashboard_cards"))
        if data.get("enabled_modules") is not None:
            company.enabled_modules = json.dumps([m for m in ALL_MODULE_KEYS if m in set(data["enabled_modules"]) | {"dashboard"}])
        if data.get("allowed_actions") is not None:
            demo.allowed_actions = json.dumps(sorted(set(data["allowed_actions"])))
        if "dashboard_cards" in data and data["dashboard_cards"] is not None:
            demo.dashboard_cards = json.dumps(data["dashboard_cards"])
        for field in ("prospect_name", "notes", "expires_at", "is_enabled"):
            if data.get(field) is not None:
                setattr(demo, field, data[field])
        for field in ("company_name_ar", "company_name_en", "logo_url"):
            if data.get(field) is not None:
                setattr(company, field.replace("company_", ""), data[field])
        if data.get("profile"):
            if data["profile"] not in PROFILES:
                raise HTTPException(status_code=400, detail="Unknown demo profile")
            demo.profile = data["profile"]
        demo.updated_at = datetime.now(timezone.utc)
        await AccessService.bump_version(db, company.id)
        await db.flush()

    @staticmethod
    async def reset(db: AsyncSession, company: Company, demo: DemoEnvironment) -> int:
        deleted = await purge_tenant_data(db, company.id)
        await DemoSeeder(db, company).run()
        demo.last_reset_at = datetime.now(timezone.utc)
        await db.flush()
        return deleted


class DemoSeeder:
    """Fictional, internally consistent data created through the real services."""

    OWNERS = [
        ("م. سامح عبد الرحيم", "+201000000101", "quarterly", Decimal("8")),
        ("السيدة نادية فهمي", "+201000000102", "monthly", Decimal("10")),
        ("شركة الأفق للاستثمار العقاري", "+201000000103", "semiannual", Decimal("7.5")),
        ("أ. كريم البنا", "+201000000104", "monthly", Decimal("10")),
    ]
    RENTERS = [
        ("محمود عادل", "+201100000201"), ("رنا سمير", "+201100000202"), ("هشام توفيق", "+201100000203"),
        ("داليا منصور", "+201100000204"), ("شريف لطفي", "+201100000205"), ("منى جلال", "+201100000206"),
        ("وليد سعيد", "+201100000207"), ("ياسمين رأفت", "+201100000208"),
    ]

    def __init__(self, db: AsyncSession, company: Company):
        self.db = db
        self.company = company
        self.cid = company.id
        self.rng = random.Random(company.id)  # deterministic baseline per demo
        self.today = company_today(company)

    async def run(self) -> None:
        admin = (
            await self.db.execute(select(User).where(User.company_id == self.cid, User.is_deleted == False).order_by(User.id).limit(1))  # noqa: E712
        ).scalar_one_or_none()
        self.actor_id = admin.id if admin else None
        owners = await self._owners()
        units = await self._units(owners)
        renters = await self._customers()
        await self._rentals(units, renters)
        await self._expenses(units)
        await self._settlements(owners)
        await self._admin_and_payroll()
        await self._requests_and_leads(renters)
        await self._notifications()

    async def _owners(self) -> list[PropertyOwner]:
        owners = []
        for i, (name, mobile, freq, rate) in enumerate(self.OWNERS, start=1):
            o = PropertyOwner(
                company_id=self.cid, code=f"OWN-{i:03d}", full_name=name, mobile=mobile, email=f"owner{i}@demo.fratelanza.com",
                national_id=f"2{self.rng.randint(10**12, 10**13 - 1)}", bank_name="بنك تجريبي",
                bank_account=f"DEMO{self.rng.randint(10**9, 10**10 - 1)}", settlement_frequency=freq, commission_rate=rate,
                settlement_day=5,
            )
            self.db.add(o)
            owners.append(o)
        await self.db.flush()
        return owners

    async def _units(self, owners: list[PropertyOwner]) -> list[Unit]:
        project = Project(company_id=self.cid, name_ar="أبراج النخيل (تجريبي)", name_en="Palm Towers (Demo)", code="PALM",
                          city="القاهرة الجديدة", status=ProjectStatus.ACTIVE, total_units=12, available_units=12)
        self.db.add(project)
        await self.db.flush()
        units = []
        for b_code, b_name in (("A", "مبنى أ"), ("B", "مبنى ب")):
            building = Building(project_id=project.id, name_ar=b_name, name_en=f"Building {b_code}", code=b_code, total_floors=3)
            self.db.add(building)
            await self.db.flush()
            for floor_no in (1, 2, 3):
                floor = Floor(building_id=building.id, floor_number=floor_no, name_ar=f"الدور {floor_no}", name_en=f"Floor {floor_no}")
                self.db.add(floor)
                await self.db.flush()
                for n in (1, 2):
                    idx = len(units)
                    unit_type = UnitType.OFFICE if (b_code == "B" and floor_no == 1) else UnitType.APARTMENT
                    unit = Unit(
                        company_id=self.cid, floor_id=floor.id, unit_code=f"PALM-{b_code}{floor_no}-{n:02d}", unit_number=f"{floor_no}0{n}",
                        unit_type=unit_type, area_sqm=Decimal(str(95 + 15 * ((idx * 7) % 5))), bedrooms=2 + (idx % 2),
                        bathrooms=1 + (idx % 2), price=Decimal(str(2_400_000 + 150_000 * idx)), base_price=Decimal(str(2_400_000 + 150_000 * idx)),
                        status=UnitStatus.AVAILABLE, owner_id=owners[idx % len(owners)].id,
                        furnishing_status=["unfurnished", "semi", "furnished"][idx % 3],
                        finishing=["semi", "full", "super_lux"][idx % 3],
                        rental_category="commercial" if unit_type == UnitType.OFFICE else ("old_law" if idx == 11 else "new_law"),
                        construction_year=2015 + idx % 8, electricity_meter=f"E-{100200 + idx}", water_meter=f"W-{55000 + idx}",
                        gas_meter=f"G-{77000 + idx}" if unit_type == UnitType.APARTMENT else None,
                        listing_purpose="rent" if idx < 9 else ("sale" if idx < 11 else "both"), occupancy_status="vacant",
                    )
                    self.db.add(unit)
                    units.append(unit)
        await self.db.flush()
        return units

    async def _customers(self) -> list[Customer]:
        renters = []
        for name, mobile in self.RENTERS:
            c = Customer(company_id=self.cid, full_name_ar=name, full_name_en=name, mobile=mobile, city="القاهرة",
                         national_id=f"2{self.rng.randint(10**12, 10**13 - 1)}", assigned_to_id=self.actor_id)
            self.db.add(c)
            renters.append(c)
        await self.db.flush()
        return renters

    async def _rentals(self, units: list[Unit], renters: list[Customer]) -> None:
        t = self.today
        month_start = date(t.year, t.month, 1)
        plans = [
            # unit idx, renter idx, start offset months, duration months, rent, frequency
            (0, 0, -8, 12, Decimal("12000"), "monthly"),
            (1, 1, -5, 12, Decimal("15000"), "monthly"),
            (2, 2, -11, 12, Decimal("9500"), "monthly"),      # ends within ~1 month → expiring
            (3, 3, -4, 24, Decimal("18000"), "quarterly"),
            (4, 4, -2, 12, Decimal("11000"), "monthly"),
            (6, 5, -6, 12, Decimal("22000"), "monthly"),       # office
        ]
        self.contracts = []
        for unit_idx, renter_idx, offset, months, rent, freq in plans:
            start = add_months(month_start, offset)
            end = add_months(start, months) - timedelta(days=1)
            c = await RentalService.create_contract(
                self.db, self.cid,
                {"unit_id": units[unit_idx].id, "tenant_customer_id": renters[renter_idx].id, "start_date": start, "end_date": end,
                 "rent_amount": rent, "payment_frequency": freq, "deposit_amount": rent, "tenant_id_number": renters[renter_idx].national_id,
                 "payment_terms": "الدفع مقدماً أول كل فترة", "activate": True},
                self.actor_id,
            )
            self.contracts.append(c)
        # Historic: a terminated lease replaced by a new tenant on unit 5
        old_start = add_months(month_start, -14)
        old = await RentalService.create_contract(
            self.db, self.cid,
            {"unit_id": units[5].id, "tenant_customer_id": renters[6].id, "start_date": old_start,
             "end_date": add_months(old_start, 12) - timedelta(days=1), "rent_amount": Decimal("10000"), "activate": True},
            self.actor_id,
        )
        await self._pay_history(old, ratio=1.0, upto=old_start + timedelta(days=150))
        await RentalService.terminate(self.db, old, old_start + timedelta(days=180), "انتقال المستأجر لمدينة أخرى")
        new = await RentalService.create_contract(
            self.db, self.cid,
            {"unit_id": units[5].id, "tenant_customer_id": renters[7].id, "start_date": add_months(month_start, -3),
             "end_date": add_months(month_start, 9) - timedelta(days=1), "rent_amount": Decimal("11500"), "activate": True},
            self.actor_id,
        )
        self.contracts.append(new)
        # Payment behaviour: mostly paid, one partial, one overdue
        for i, c in enumerate(self.contracts):
            ratio = {2: 0.5, 4: 0.0}.get(i, 1.0)
            await self._pay_history(c, ratio=ratio, upto=t - timedelta(days=20))
        # A draft contract to show the lifecycle
        await RentalService.create_contract(
            self.db, self.cid,
            {"unit_id": units[7].id, "tenant_name": "عميل محتمل (مسودة)", "tenant_mobile": "+201200000299",
             "start_date": add_months(month_start, 1), "end_date": add_months(month_start, 13) - timedelta(days=1),
             "rent_amount": Decimal("13000")},
            self.actor_id,
        )

    async def _pay_history(self, contract, *, ratio: float, upto: date) -> None:
        from app.models.rentals import RentReceivable

        recs = (
            await self.db.execute(
                select(RentReceivable).where(RentReceivable.rental_contract_id == contract.id, RentReceivable.due_date <= upto)
                .order_by(RentReceivable.due_date)
            )
        ).scalars().all()
        for r in recs:
            if r.status not in ("pending", "partial") or ratio <= 0:
                continue
            amount = (Decimal(str(r.amount_due)) * Decimal(str(ratio))).quantize(Decimal("0.01"))
            if amount <= 0:
                continue
            await RentalService.record_payment(
                self.db, self.cid, r.id, amount=amount, paid_on=min(r.due_date + timedelta(days=self.rng.randint(0, 6)), self.today),
                method=self.rng.choice(["cash", "bank_transfer", "instapay"]), receipt_reference=None, notes=None, user_id=self.actor_id,
            )

    async def _expenses(self, units: list[Unit]) -> None:
        t = self.today
        mr = MaintenanceRequest(company_id=self.cid, unit_id=units[1].id, title="إصلاح تسريب مياه بالمطبخ", priority="high",
                                status="completed", assigned_to_id=self.actor_id)
        self.db.add(mr)
        await self.db.flush()
        specs = [
            (units[1].id, mr.id, "plumbing", Decimal("1850"), "owner", True, True, -25),
            (units[0].id, None, "painting", Decimal("4200"), "owner", True, False, -12),
            (units[3].id, None, "electrical", Decimal("950"), "owner", False, False, -5),
            (units[6].id, None, "security", Decimal("3000"), "company", True, True, -18),
        ]
        for unit_id, mr_id, cat, amount, charged, approve, paid, offset in specs:
            e = await ExpenseService.create_property_expense(
                self.db, self.cid,
                {"unit_id": unit_id, "maintenance_request_id": mr_id, "expense_date": t + timedelta(days=offset), "category": cat,
                 "description": f"مصروف تجريبي — {cat}", "amount": amount, "vendor": "مورد تجريبي", "charged_to": charged},
                self.actor_id,
            )
            if approve:
                await ExpenseService.approve(self.db, e, self.actor_id)
            if paid:
                await ExpenseService.mark_paid(self.db, e, t + timedelta(days=offset + 2), self.actor_id)

    async def _settlements(self, owners: list[PropertyOwner]) -> None:
        # Owner 2 (monthly): last month settled & paid; owner 4: last month draft
        prev_start, prev_end = frequency_block(date(self.today.year, self.today.month, 1) - timedelta(days=1), "monthly")
        s = await SettlementService.create(self.db, self.cid, owner_id=owners[1].id, period_start=prev_start, period_end=prev_end,
                                           adjustments=Decimal("0"), adjustments_note=None, user_id=self.actor_id)
        await SettlementService.approve(self.db, s, self.actor_id)
        if s.net_payable > 0:
            await SettlementService.pay(self.db, s, amount=s.net_payable, paid_on=min(prev_end + timedelta(days=5), self.today),
                                        method="bank_transfer", reference="TRX-DEMO-1", user_id=self.actor_id)
        await SettlementService.create(self.db, self.cid, owner_id=owners[3].id, period_start=prev_start, period_end=prev_end,
                                       adjustments=Decimal("0"), adjustments_note=None, user_id=self.actor_id)

    async def _admin_and_payroll(self) -> None:
        t = self.today
        for offset, cat, amount, pay in ((-40, "rent", Decimal("25000"), True), (-35, "utilities", Decimal("3200"), True),
                                         (-10, "marketing", Decimal("8500"), False), (-3, "office_supplies", Decimal("1200"), False)):
            e = await ExpenseService.create_admin_expense(
                self.db, self.cid, {"category": cat, "expense_date": t + timedelta(days=offset), "amount": amount,
                                    "description": f"مصروف إداري تجريبي — {cat}"}, self.actor_id)
            if pay:
                await ExpenseService.pay_admin_expense(self.db, e, amount, t + timedelta(days=offset + 1), self.actor_id)
        employees = []
        for i, (name, dept, salary) in enumerate((("أحمد الشريف", "التحصيل", 9000), ("سارة حمدي", "المحاسبة", 12000),
                                                  ("عمرو ناجي", "إدارة الأملاك", 11000))):
            emp = Employee(company_id=self.cid, employee_code=f"PM-EMP-{i + 1:03d}", full_name_ar=name, full_name_en=name,
                           department=dept, position=dept, salary=Decimal(str(salary)), hire_date="2023-01-01")
            self.db.add(emp)
            employees.append(emp)
        await self.db.flush()
        prev = date(t.year, t.month, 1) - timedelta(days=1)
        from app.services.payroll_service import PayrollService

        already = (
            await self.db.execute(
                select(PayrollRun.id).where(PayrollRun.company_id == self.cid, PayrollRun.period_month == prev.strftime("%Y-%m"))
            )
        ).first()
        if already:
            return

        run = await PayrollService.generate(self.db, self.cid, prev.strftime("%Y-%m"), self.actor_id)
        payslips = (await self.db.execute(select(Payslip).where(Payslip.payroll_run_id == run.id))).scalars().all()
        for i, p in enumerate(payslips):
            amount = Decimal(str(p.net_salary)) if i < 2 else (Decimal(str(p.net_salary)) / 2).quantize(Decimal("0.01"))
            await PayrollService.pay(self.db, p, amount, prev + timedelta(days=2), "bank_transfer", None, self.actor_id)

    async def _requests_and_leads(self, renters: list[Customer]) -> None:
        reqs = [
            ("request_rent", "دينا مراد", "+201500000301", "apartment", "القاهرة الجديدة", None, Decimal("16000"), Decimal("100"), None, 2, "furnished"),
            ("request_buy", "طارق زكي", "+201500000302", "apartment", "القاهرة الجديدة", Decimal("2500000"), Decimal("3500000"), Decimal("110"), Decimal("160"), 3, None),
            ("offer_sale", "حازم يسري", "+201500000303", "apartment", "القاهرة الجديدة", Decimal("3100000"), Decimal("3100000"), Decimal("140"), Decimal("140"), 3, "semi"),
            ("offer_rent", "إيمان صبري", "+201500000304", "apartment", "القاهرة الجديدة", Decimal("14000"), Decimal("14000"), Decimal("120"), Decimal("120"), 2, "furnished"),
            ("request_rent", "مصطفى حلمي", "+201500000305", "office", "القاهرة الجديدة", None, Decimal("25000"), Decimal("90"), None, None, None),
            ("offer_sale", "نهى الصاوي", "+201500000306", "villa", "الشيخ زايد", Decimal("9500000"), Decimal("9500000"), Decimal("320"), Decimal("320"), 5, "unfurnished"),
        ]
        for kind, name, mobile, ptype, city, pmin, pmax, amin, amax, rooms, furn in reqs:
            self.db.add(PropertyRequest(
                company_id=self.cid, kind=kind, customer_name=name, customer_mobile=mobile, property_type=ptype, city=city,
                price_min=pmin, price_max=pmax, area_min=amin, area_max=amax, rooms=rooms, furnishing_status=furn, status="open",
                assigned_to_id=self.actor_id, created_by_id=self.actor_id,
            ))
        for i, (name, mobile) in enumerate((("علا فاروق", "+201600000401"), ("باسم رشدي", "+201600000402"),
                                            ("نورهان عزت", "+201600000403"))):
            self.db.add(Lead(company_id=self.cid, full_name=name, mobile=mobile, source=[LeadSource.FACEBOOK, LeadSource.WEBSITE, LeadSource.REFERRAL][i],
                             stage=[LeadStage.NEW, LeadStage.INTERESTED, LeadStage.SITE_VISIT][i], score=40 + 20 * i,
                             budget_min=Decimal("2000000"), budget_max=Decimal("3500000"), assigned_to_id=self.actor_id))
        await self.db.flush()

    async def _notifications(self) -> None:
        users = (await self.db.execute(select(User).where(User.company_id == self.cid, User.is_deleted == False))).scalars().all()  # noqa: E712
        for u in users:
            self.db.add(Notification(company_id=self.cid, user_id=u.id, title_ar="مرحباً بك في النسخة التجريبية",
                                     title_en="Welcome to your demo", message_ar="جميع البيانات وهمية ولا تُرسل أي رسائل حقيقية.",
                                     message_en="All data is fictional and no real messages are sent.", notification_type="info"))
        await self.db.flush()
        from app.services.scheduler_service import run_company_jobs

        await run_company_jobs(self.db, self.cid, self.today)
