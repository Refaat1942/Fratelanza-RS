from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brokers import Broker, BrokerCommission
from app.models.construction import ConstructionPhase
from app.models.crm import CustomerReminder, Lead
from app.models.customers import Customer
from app.models.customer_service import Ticket
from app.models.procurement import PurchaseOrder, Vendor
from app.models.property import MaintenanceRequest
from app.models.real_estate import Building, Floor, Project, Unit
from app.models.sales import Contract, Installment, Payment, PaymentPlan, Reservation
from app.models.tenant import Company
from app.models.users import User
from app.models.hr import Employee, PayrollRun, Payslip
from app.models.warehouse import InventoryItem, Warehouse
from app.services.finance_service import FinanceService


REPORT_CATALOG: list[dict[str, Any]] = [
    {"key": "units_inventory", "category": "inventory", "name_en": "Unit Inventory", "name_ar": "مخزون الوحدات"},
    {"key": "projects_summary", "category": "inventory", "name_en": "Projects Summary", "name_ar": "ملخص المشاريع"},
    {"key": "sales_register", "category": "sales", "name_en": "Sales Register", "name_ar": "سجل المبيعات"},
    {"key": "reservations", "category": "sales", "name_en": "Reservations", "name_ar": "الحجوزات"},
    {"key": "collections_installments", "category": "collections", "name_en": "Installments Schedule", "name_ar": "جدول الأقساط"},
    {"key": "collections_overdue", "category": "collections", "name_en": "Overdue Installments", "name_ar": "الأقساط المتأخرة"},
    {"key": "collections_payments", "category": "collections", "name_en": "Payments Received", "name_ar": "المدفوعات المحصلة"},
    {"key": "customers", "category": "crm", "name_en": "Customers List", "name_ar": "قائمة العملاء"},
    {"key": "leads_pipeline", "category": "crm", "name_en": "Leads Pipeline", "name_ar": "مسار العملاء المحتملين"},
    {"key": "broker_performance", "category": "brokers", "name_en": "Broker Performance", "name_ar": "أداء الوسطاء"},
    {"key": "tickets", "category": "service", "name_en": "Support Tickets", "name_ar": "تذاكر الدعم"},
    {"key": "companies_overview", "category": "platform", "name_en": "Companies Overview", "name_ar": "نظرة عامة على الشركات", "super_admin_only": True},
    {"key": "platform_users", "category": "platform", "name_en": "Platform Users", "name_ar": "مستخدمو المنصة", "super_admin_only": True},
    {"key": "finance_trial_balance", "category": "finance", "name_en": "Trial Balance", "name_ar": "ميزان المراجعة"},
    {"key": "finance_profit_loss", "category": "finance", "name_en": "Profit & Loss Summary", "name_ar": "ملخص الأرباح والخسائر"},
    {"key": "finance_cash_position", "category": "finance", "name_en": "Cash & Bank Position", "name_ar": "المركز النقدي والبنوك"},
    {"key": "finance_journal", "category": "finance", "name_en": "Journal Register", "name_ar": "سجل القيود اليومية"},
    {"key": "hr_employees", "category": "hr", "name_en": "Employees Register", "name_ar": "سجل الموظفين"},
    {"key": "hr_payroll", "category": "hr", "name_en": "Payroll Summary", "name_ar": "ملخص الرواتب"},
    {"key": "customer_reminders", "category": "crm", "name_en": "Call Reminders", "name_ar": "تذكيرات المكالمات"},
    {"key": "sales_summary", "category": "sales", "name_en": "Sales Summary by Status", "name_ar": "ملخص المبيعات حسب الحالة"},
    {"key": "collections_aging", "category": "collections", "name_en": "Collections Aging Summary", "name_ar": "ملخص أعمار التحصيلات"},
    {"key": "construction_progress", "category": "operations", "name_en": "Construction Progress", "name_ar": "تقدم المقاولات"},
    {"key": "procurement_vendors", "category": "operations", "name_en": "Vendors Register", "name_ar": "سجل الموردين"},
    {"key": "procurement_orders", "category": "operations", "name_en": "Purchase Orders", "name_ar": "أوامر الشراء"},
    {"key": "warehouse_inventory", "category": "operations", "name_en": "Warehouse Inventory", "name_ar": "مخزون المستودعات"},
    {"key": "property_maintenance", "category": "operations", "name_en": "Maintenance Requests", "name_ar": "طلبات الصيانة"},
    {"key": "team_users", "category": "admin", "name_en": "Team Users", "name_ar": "مستخدمو الفريق"},
]


def _sort_rows(rows: list[dict], sort_by: Optional[str], sort_order: str) -> list[dict]:
    if not rows or not sort_by:
        return rows
    reverse = sort_order.lower() == "desc"

    def sort_key(row: dict) -> Any:
        val = row.get(sort_by)
        if val is None:
            return ""
        return val

    try:
        return sorted(rows, key=sort_key, reverse=reverse)
    except TypeError:
        return sorted(rows, key=lambda r: str(r.get(sort_by, "")), reverse=reverse)


def _filter_rows(rows: list[dict], search: Optional[str]) -> list[dict]:
    if not search:
        return rows
    q = search.lower()
    return [r for r in rows if any(q in str(v).lower() for v in r.values() if v is not None)]


def _aging_days(due_date: str) -> int:
    try:
        due = datetime.strptime(due_date, "%Y-%m-%d").date()
        return (date.today() - due).days
    except ValueError:
        return 0


class ReportsService:
    @staticmethod
    def catalog(is_super_admin: bool = False) -> list[dict]:
        if is_super_admin:
            return REPORT_CATALOG
        return [r for r in REPORT_CATALOG if not r.get("super_admin_only")]

    @staticmethod
    async def run(
        db: AsyncSession,
        report_key: str,
        company_id: Optional[int],
        is_super_admin: bool = False,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        search: Optional[str] = None,
    ) -> tuple[list[dict], list[dict]]:
        fetchers = {
            "units_inventory": ReportsService._units_inventory,
            "projects_summary": ReportsService._projects_summary,
            "sales_register": ReportsService._sales_register,
            "reservations": ReportsService._reservations,
            "collections_installments": ReportsService._collections_installments,
            "collections_overdue": ReportsService._collections_overdue,
            "collections_payments": ReportsService._collections_payments,
            "customers": ReportsService._customers,
            "leads_pipeline": ReportsService._leads_pipeline,
            "broker_performance": ReportsService._broker_performance,
            "tickets": ReportsService._tickets,
            "companies_overview": ReportsService._companies_overview,
            "platform_users": ReportsService._platform_users,
            "finance_trial_balance": ReportsService._finance_trial_balance,
            "finance_profit_loss": ReportsService._finance_profit_loss,
            "finance_cash_position": ReportsService._finance_cash_position,
            "finance_journal": ReportsService._finance_journal,
            "hr_employees": ReportsService._hr_employees,
            "hr_payroll": ReportsService._hr_payroll,
            "customer_reminders": ReportsService._customer_reminders,
            "sales_summary": ReportsService._sales_summary,
            "collections_aging": ReportsService._collections_aging,
            "construction_progress": ReportsService._construction_progress,
            "procurement_vendors": ReportsService._procurement_vendors,
            "procurement_orders": ReportsService._procurement_orders,
            "warehouse_inventory": ReportsService._warehouse_inventory,
            "property_maintenance": ReportsService._property_maintenance,
            "team_users": ReportsService._team_users,
        }
        if report_key not in fetchers:
            return [], []
        meta = next((r for r in REPORT_CATALOG if r["key"] == report_key), None)
        if meta and meta.get("super_admin_only") and not is_super_admin:
            return [], []
        rows = await fetchers[report_key](db, company_id, is_super_admin)
        rows = _filter_rows(rows, search)
        rows = _sort_rows(rows, sort_by, sort_order)
        columns = ReportsService._columns_for(report_key, rows)
        return rows, columns

    @staticmethod
    def _columns_for(report_key: str, rows: list[dict]) -> list[dict]:
        labels = {
            "units_inventory": {
                "unit_code": ("Unit Code", "كود الوحدة"),
                "unit_number": ("Unit #", "رقم الوحدة"),
                "project": ("Project", "المشروع"),
                "unit_type": ("Type", "النوع"),
                "area_sqm": ("Area m²", "المساحة"),
                "price": ("Price", "السعر"),
                "status": ("Status", "الحالة"),
            },
            "projects_summary": {
                "code": ("Code", "الكود"),
                "name_en": ("Project", "المشروع"),
                "city": ("City", "المدينة"),
                "status": ("Status", "الحالة"),
                "total_units": ("Total Units", "إجمالي الوحدات"),
                "available_units": ("Available", "المتاح"),
                "sold_units": ("Sold", "المباع"),
            },
            "sales_register": {
                "contract_number": ("Contract #", "رقم العقد"),
                "customer": ("Customer", "العميل"),
                "unit_code": ("Unit", "الوحدة"),
                "project": ("Project", "المشروع"),
                "total_price": ("Total Price", "السعر الإجمالي"),
                "contract_date": ("Date", "التاريخ"),
                "status": ("Status", "الحالة"),
                "is_signed": ("Signed", "موقع"),
            },
            "reservations": {
                "reservation_number": ("Reservation #", "رقم الحجز"),
                "customer": ("Customer", "العميل"),
                "unit_code": ("Unit", "الوحدة"),
                "deposit_amount": ("Deposit", "العربون"),
                "reservation_date": ("Date", "التاريخ"),
                "expiry_date": ("Expiry", "الانتهاء"),
                "status": ("Status", "الحالة"),
            },
            "collections_installments": {
                "contract_number": ("Contract #", "رقم العقد"),
                "installment_number": ("#", "القسط"),
                "due_date": ("Due Date", "تاريخ الاستحقاق"),
                "due_amount": ("Due Amount", "المبلغ المستحق"),
                "paid_amount": ("Paid", "المدفوع"),
                "remaining_balance": ("Balance", "المتبقي"),
                "status": ("Status", "الحالة"),
                "aging_days": ("Aging Days", "أيام التأخير"),
            },
            "collections_overdue": {
                "contract_number": ("Contract #", "رقم العقد"),
                "installment_number": ("#", "القسط"),
                "due_date": ("Due Date", "تاريخ الاستحقاق"),
                "due_amount": ("Due Amount", "المبلغ"),
                "remaining_balance": ("Balance", "المتبقي"),
                "aging_days": ("Aging Days", "أيام التأخير"),
                "aging_bucket": ("Aging", "فئة التأخير"),
            },
            "collections_payments": {
                "payment_date": ("Date", "التاريخ"),
                "amount": ("Amount", "المبلغ"),
                "payment_method": ("Method", "طريقة الدفع"),
                "reference_number": ("Reference", "المرجع"),
                "customer": ("Customer", "العميل"),
            },
            "customers": {
                "full_name_en": ("Name", "الاسم"),
                "mobile": ("Mobile", "الجوال"),
                "email": ("Email", "البريد"),
                "city": ("City", "المدينة"),
                "national_id": ("National ID", "الرقم القومي"),
            },
            "leads_pipeline": {
                "full_name": ("Name", "الاسم"),
                "mobile": ("Mobile", "الجوال"),
                "source": ("Source", "المصدر"),
                "stage": ("Stage", "المرحلة"),
                "score": ("Score", "النقاط"),
                "budget_min": ("Budget Min", "الحد الأدنى"),
                "budget_max": ("Budget Max", "الحد الأقصى"),
            },
            "broker_performance": {
                "name_en": ("Broker", "الوسيط"),
                "mobile": ("Mobile", "الجوال"),
                "commission_rate": ("Rate %", "نسبة العمولة"),
                "total_sales": ("Total Sales", "إجمالي المبيعات"),
                "commissions_pending": ("Pending", "معلق"),
                "commissions_paid": ("Paid", "مدفوع"),
                "rank_score": ("Rank", "التصنيف"),
            },
            "tickets": {
                "ticket_number": ("Ticket #", "رقم التذكرة"),
                "subject": ("Subject", "الموضوع"),
                "category": ("Category", "الفئة"),
                "priority": ("Priority", "الأولوية"),
                "status": ("Status", "الحالة"),
            },
            "companies_overview": {
                "code": ("Code", "الكود"),
                "name_en": ("Company", "الشركة"),
                "status": ("Status", "الحالة"),
                "city": ("City", "المدينة"),
                "users_count": ("Users", "المستخدمون"),
            },
            "platform_users": {
                "email": ("Email", "البريد"),
                "full_name_en": ("Name", "الاسم"),
                "system_role": ("Role", "الدور"),
                "status": ("Status", "الحالة"),
                "company_id": ("Company ID", "الشركة"),
            },
            "sales_summary": {
                "status": ("Status", "الحالة"),
                "contract_count": ("Contracts", "العقود"),
                "total_value": ("Total Value", "القيمة الإجمالية"),
                "avg_value": ("Average Value", "متوسط القيمة"),
            },
            "collections_aging": {
                "aging_bucket": ("Aging Bucket", "فئة التأخير"),
                "installment_count": ("Installments", "الأقساط"),
                "total_due": ("Total Due", "إجمالي المستحق"),
                "total_remaining": ("Remaining", "المتبقي"),
            },
            "construction_progress": {
                "project": ("Project", "المشروع"),
                "phase": ("Phase", "المرحلة"),
                "progress_percent": ("Progress %", "نسبة الإنجاز"),
                "planned_cost": ("Planned Cost", "التكلفة المخططة"),
                "actual_cost": ("Actual Cost", "التكلفة الفعلية"),
                "variance": ("Variance", "الفرق"),
            },
            "procurement_vendors": {
                "name_en": ("Vendor", "المورد"),
                "contact_person": ("Contact", "جهة الاتصال"),
                "phone": ("Phone", "الهاتف"),
                "email": ("Email", "البريد"),
                "rating": ("Rating", "التقييم"),
                "status": ("Status", "الحالة"),
            },
            "procurement_orders": {
                "po_number": ("PO #", "رقم أمر الشراء"),
                "vendor": ("Vendor", "المورد"),
                "project": ("Project", "المشروع"),
                "total_amount": ("Amount", "المبلغ"),
                "status": ("Status", "الحالة"),
            },
            "warehouse_inventory": {
                "warehouse": ("Warehouse", "المستودع"),
                "sku": ("SKU", "الرمز"),
                "name_en": ("Item", "الصنف"),
                "quantity": ("Quantity", "الكمية"),
                "min_stock_level": ("Min Stock", "الحد الأدنى"),
                "unit": ("Unit", "الوحدة"),
                "stock_status": ("Status", "الحالة"),
            },
            "property_maintenance": {
                "title": ("Title", "العنوان"),
                "unit_code": ("Unit", "الوحدة"),
                "customer": ("Customer", "العميل"),
                "priority": ("Priority", "الأولوية"),
                "status": ("Status", "الحالة"),
            },
            "team_users": {
                "username": ("Username", "اسم المستخدم"),
                "full_name_en": ("Name", "الاسم"),
                "email": ("Email", "البريد"),
                "system_role": ("Role", "الدور"),
                "status": ("Status", "الحالة"),
            },
        }
        mapping = labels.get(report_key, {})
        if not rows:
            return [{"key": k, "label_en": v[0], "label_ar": v[1], "sortable": True} for k, v in mapping.items()]
        keys = list(rows[0].keys())
        return [
            {
                "key": k,
                "label_en": mapping.get(k, (k.replace("_", " ").title(), k))[0],
                "label_ar": mapping.get(k, (k, k))[1],
                "sortable": True,
            }
            for k in keys
        ]

    @staticmethod
    async def _units_inventory(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        query = (
            select(Unit, Project)
            .join(Floor, Unit.floor_id == Floor.id)
            .join(Building, Floor.building_id == Building.id)
            .join(Project, Building.project_id == Project.id)
            .where(Unit.is_deleted == False)
        )
        if company_id:
            query = query.where(Project.company_id == company_id)
        result = await db.execute(query)
        return [
            {
                "unit_code": u.unit_code,
                "unit_number": u.unit_number,
                "project": p.name_en,
                "unit_type": u.unit_type.value,
                "area_sqm": float(u.area_sqm),
                "price": float(u.price),
                "status": u.status.value,
            }
            for u, p in result.all()
        ]

    @staticmethod
    async def _projects_summary(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        query = select(Project).where(Project.is_deleted == False)
        if company_id:
            query = query.where(Project.company_id == company_id)
        projects = (await db.execute(query)).scalars().all()
        return [
            {
                "code": p.code,
                "name_en": p.name_en,
                "name_ar": p.name_ar,
                "city": p.city or "",
                "status": p.status.value,
                "total_units": p.total_units,
                "available_units": p.available_units,
                "sold_units": p.total_units - p.available_units,
            }
            for p in projects
        ]

    @staticmethod
    async def _sales_register(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        query = (
            select(Contract, Customer, Unit, Project)
            .join(Customer, Contract.customer_id == Customer.id)
            .join(Unit, Contract.unit_id == Unit.id)
            .join(Floor, Unit.floor_id == Floor.id)
            .join(Building, Floor.building_id == Building.id)
            .join(Project, Building.project_id == Project.id)
            .where(Contract.is_deleted == False)
        )
        if company_id:
            query = query.where(Contract.company_id == company_id)
        result = await db.execute(query)
        return [
            {
                "contract_number": c.contract_number,
                "customer": cust.full_name_en,
                "unit_code": u.unit_code,
                "project": p.name_en,
                "total_price": float(c.total_price),
                "contract_date": c.contract_date,
                "status": c.status.value,
                "is_signed": "Yes" if c.is_signed else "No",
            }
            for c, cust, u, p in result.all()
        ]

    @staticmethod
    async def _reservations(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        query = (
            select(Reservation, Customer, Unit)
            .join(Customer, Reservation.customer_id == Customer.id)
            .join(Unit, Reservation.unit_id == Unit.id)
            .where(Reservation.is_deleted == False)
        )
        if company_id:
            query = query.where(Reservation.company_id == company_id)
        result = await db.execute(query)
        return [
            {
                "reservation_number": r.reservation_number,
                "customer": cust.full_name_en,
                "unit_code": u.unit_code,
                "deposit_amount": float(r.deposit_amount),
                "reservation_date": r.reservation_date,
                "expiry_date": r.expiry_date,
                "status": r.status.value,
            }
            for r, cust, u in result.all()
        ]

    @staticmethod
    async def _collections_installments(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        query = (
            select(Installment, Contract)
            .join(PaymentPlan, Installment.payment_plan_id == PaymentPlan.id)
            .join(Contract, PaymentPlan.contract_id == Contract.id)
            .where(Contract.is_deleted == False)
        )
        if company_id:
            query = query.where(Contract.company_id == company_id)
        result = await db.execute(query)
        rows = []
        for inst, contract in result.all():
            aging = _aging_days(inst.due_date) if inst.status.value in ("due", "overdue", "partial") else 0
            rows.append({
                "contract_number": contract.contract_number,
                "installment_number": inst.installment_number,
                "due_date": inst.due_date,
                "due_amount": float(inst.due_amount),
                "paid_amount": float(inst.paid_amount),
                "remaining_balance": float(inst.remaining_balance),
                "status": inst.status.value,
                "aging_days": aging,
            })
        return rows

    @staticmethod
    async def _collections_overdue(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        rows = await ReportsService._collections_installments(db, company_id, _)
        overdue = [r for r in rows if r["status"] == "overdue" or (r["remaining_balance"] > 0 and r["aging_days"] > 0)]
        for r in overdue:
            days = r["aging_days"]
            if days <= 30:
                r["aging_bucket"] = "1-30 days"
            elif days <= 60:
                r["aging_bucket"] = "31-60 days"
            elif days <= 90:
                r["aging_bucket"] = "61-90 days"
            else:
                r["aging_bucket"] = "90+ days"
        return overdue

    @staticmethod
    async def _collections_payments(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        query = select(Payment, Customer).join(Customer, Payment.customer_id == Customer.id)
        if company_id:
            query = query.where(Payment.company_id == company_id)
        result = await db.execute(query)
        return [
            {
                "payment_date": p.payment_date,
                "amount": float(p.amount),
                "payment_method": p.payment_method,
                "reference_number": p.reference_number or "",
                "customer": c.full_name_en,
            }
            for p, c in result.all()
        ]

    @staticmethod
    async def _customers(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        query = select(Customer).where(Customer.is_deleted == False)
        if company_id:
            query = query.where(Customer.company_id == company_id)
        customers = (await db.execute(query)).scalars().all()
        return [
            {
                "full_name_en": c.full_name_en,
                "full_name_ar": c.full_name_ar,
                "mobile": c.mobile,
                "email": c.email or "",
                "city": c.city or "",
                "national_id": c.national_id or "",
            }
            for c in customers
        ]

    @staticmethod
    async def _leads_pipeline(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        query = select(Lead).where(Lead.is_deleted == False)
        if company_id:
            query = query.where(Lead.company_id == company_id)
        leads = (await db.execute(query)).scalars().all()
        return [
            {
                "full_name": l.full_name,
                "mobile": l.mobile,
                "source": l.source.value,
                "stage": l.stage.value,
                "score": l.score,
                "budget_min": float(l.budget_min) if l.budget_min else 0,
                "budget_max": float(l.budget_max) if l.budget_max else 0,
            }
            for l in leads
        ]

    @staticmethod
    async def _broker_performance(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        query = select(Broker).where(Broker.is_deleted == False)
        if company_id:
            query = query.where(Broker.company_id == company_id)
        brokers = (await db.execute(query)).scalars().all()
        rows = []
        for b in brokers:
            comm_q = select(BrokerCommission).where(BrokerCommission.broker_id == b.id)
            commissions = (await db.execute(comm_q)).scalars().all()
            pending = sum(float(c.amount) for c in commissions if c.status.value == "pending")
            paid = sum(float(c.amount) for c in commissions if c.status.value == "paid")
            rows.append({
                "name_en": b.name_en,
                "name_ar": b.name_ar,
                "mobile": b.mobile,
                "commission_rate": float(b.commission_rate),
                "total_sales": float(b.total_sales),
                "commissions_pending": pending,
                "commissions_paid": paid,
                "rank_score": b.rank_score,
            })
        return rows

    @staticmethod
    async def _tickets(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        query = select(Ticket)
        if company_id:
            query = query.where(Ticket.company_id == company_id)
        tickets = (await db.execute(query)).scalars().all()
        return [
            {
                "ticket_number": t.ticket_number,
                "subject": t.subject,
                "category": t.category,
                "priority": t.priority,
                "status": t.status,
            }
            for t in tickets
        ]

    @staticmethod
    async def _companies_overview(db: AsyncSession, _: Optional[int], is_super_admin: bool) -> list[dict]:
        if not is_super_admin:
            return []
        companies = (await db.execute(select(Company).where(Company.is_deleted == False))).scalars().all()
        rows = []
        for c in companies:
            count = (await db.execute(
                select(func.count()).select_from(User).where(User.company_id == c.id, User.is_deleted == False)
            )).scalar() or 0
            rows.append({
                "code": c.code,
                "name_en": c.name_en,
                "name_ar": c.name_ar,
                "status": c.status.value,
                "city": c.city or "",
                "users_count": count,
            })
        return rows

    @staticmethod
    async def _finance_trial_balance(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        if not company_id:
            return []
        return await FinanceService.trial_balance(db, company_id)

    @staticmethod
    async def _finance_profit_loss(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        if not company_id:
            return []
        return await FinanceService.profit_loss_summary(db, company_id)

    @staticmethod
    async def _finance_cash_position(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        if not company_id:
            return []
        return await FinanceService.cash_position(db, company_id)

    @staticmethod
    async def _finance_journal(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        if not company_id:
            return []
        return await FinanceService.journal_register(db, company_id)

    @staticmethod
    async def _hr_employees(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        if not company_id:
            return []
        employees = (
            await db.execute(
                select(Employee).where(Employee.company_id == company_id, Employee.is_deleted == False)
            )
        ).scalars().all()
        return [
            {
                "employee_code": e.employee_code,
                "full_name_en": e.full_name_en,
                "department": e.department or "",
                "position": e.position or "",
                "salary_egp": float(e.salary or 0),
                "hire_date": e.hire_date or "",
                "status": "active" if e.is_active else "inactive",
            }
            for e in employees
        ]

    @staticmethod
    async def _hr_payroll(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        if not company_id:
            return []
        result = await db.execute(
            select(Payslip, Employee, PayrollRun)
            .join(Employee, Payslip.employee_id == Employee.id)
            .join(PayrollRun, Payslip.payroll_run_id == PayrollRun.id)
            .where(PayrollRun.company_id == company_id)
            .order_by(PayrollRun.period_month.desc())
        )
        return [
            {
                "period": run.period_month,
                "employee_code": emp.employee_code,
                "employee_name": emp.full_name_en,
                "basic_salary_egp": float(ps.basic_salary),
                "social_insurance_egp": float(ps.social_insurance),
                "net_salary_egp": float(ps.net_salary),
                "status": ps.status,
            }
            for ps, emp, run in result.all()
        ]

    @staticmethod
    async def _customer_reminders(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        if not company_id:
            return []
        reminders = (
            await db.execute(
                select(CustomerReminder).where(CustomerReminder.company_id == company_id)
            )
        ).scalars().all()
        return [
            {
                "title": r.title,
                "type": r.reminder_type.value,
                "due_date": r.due_date,
                "due_time": r.due_time or "",
                "status": r.status.value,
                "notes": r.notes or "",
            }
            for r in reminders
        ]

    @staticmethod
    async def _sales_summary(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        query = select(Contract).where(Contract.is_deleted == False)
        if company_id:
            query = query.where(Contract.company_id == company_id)
        contracts = (await db.execute(query)).scalars().all()
        buckets: dict[str, dict] = {}
        for c in contracts:
            status = c.status.value
            if status not in buckets:
                buckets[status] = {"status": status, "contract_count": 0, "total_value": 0.0}
            buckets[status]["contract_count"] += 1
            buckets[status]["total_value"] += float(c.total_price)
        rows = []
        for b in buckets.values():
            count = b["contract_count"]
            b["total_value"] = round(b["total_value"], 2)
            b["avg_value"] = round(b["total_value"] / count, 2) if count else 0
            rows.append(b)
        return rows

    @staticmethod
    async def _collections_aging(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        installments = await ReportsService._collections_installments(db, company_id, _)
        overdue = [r for r in installments if r["remaining_balance"] > 0]
        buckets: dict[str, dict] = {}
        for r in overdue:
            days = r.get("aging_days", 0)
            if days <= 0:
                bucket = "Current"
            elif days <= 30:
                bucket = "1-30 days"
            elif days <= 60:
                bucket = "31-60 days"
            elif days <= 90:
                bucket = "61-90 days"
            else:
                bucket = "90+ days"
            if bucket not in buckets:
                buckets[bucket] = {
                    "aging_bucket": bucket,
                    "installment_count": 0,
                    "total_due": 0.0,
                    "total_remaining": 0.0,
                }
            buckets[bucket]["installment_count"] += 1
            buckets[bucket]["total_due"] += r["due_amount"]
            buckets[bucket]["total_remaining"] += r["remaining_balance"]
        order = ["Current", "1-30 days", "31-60 days", "61-90 days", "90+ days"]
        return [
            {
                **buckets[k],
                "total_due": round(buckets[k]["total_due"], 2),
                "total_remaining": round(buckets[k]["total_remaining"], 2),
            }
            for k in order
            if k in buckets
        ]

    @staticmethod
    async def _construction_progress(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        query = (
            select(ConstructionPhase, Project)
            .join(Project, ConstructionPhase.project_id == Project.id)
            .where(Project.is_deleted == False)
        )
        if company_id:
            query = query.where(Project.company_id == company_id)
        result = await db.execute(query)
        return [
            {
                "project": p.name_en,
                "phase": phase.name_en,
                "progress_percent": phase.progress_percent,
                "planned_cost": float(phase.planned_cost),
                "actual_cost": float(phase.actual_cost),
                "variance": round(float(phase.actual_cost) - float(phase.planned_cost), 2),
            }
            for phase, p in result.all()
        ]

    @staticmethod
    async def _procurement_vendors(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        query = select(Vendor)
        if company_id:
            query = query.where(Vendor.company_id == company_id)
        vendors = (await db.execute(query)).scalars().all()
        return [
            {
                "name_en": v.name_en,
                "name_ar": v.name_ar,
                "contact_person": v.contact_person or "",
                "phone": v.phone or "",
                "email": v.email or "",
                "rating": v.rating,
                "status": "active" if v.is_active else "inactive",
            }
            for v in vendors
        ]

    @staticmethod
    async def _procurement_orders(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        query = (
            select(PurchaseOrder, Vendor, Project)
            .join(Vendor, PurchaseOrder.vendor_id == Vendor.id)
            .outerjoin(Project, PurchaseOrder.project_id == Project.id)
        )
        if company_id:
            query = query.where(PurchaseOrder.company_id == company_id)
        result = await db.execute(query)
        return [
            {
                "po_number": po.po_number,
                "vendor": v.name_en,
                "project": p.name_en if p else "",
                "total_amount": float(po.total_amount),
                "status": po.status,
            }
            for po, v, p in result.all()
        ]

    @staticmethod
    async def _warehouse_inventory(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        query = (
            select(InventoryItem, Warehouse)
            .join(Warehouse, InventoryItem.warehouse_id == Warehouse.id)
        )
        if company_id:
            query = query.where(Warehouse.company_id == company_id)
        result = await db.execute(query)
        rows = []
        for item, wh in result.all():
            qty = float(item.quantity)
            min_stock = float(item.min_stock_level)
            rows.append({
                "warehouse": wh.name_en,
                "sku": item.sku,
                "name_en": item.name_en,
                "quantity": qty,
                "min_stock_level": min_stock,
                "unit": item.unit,
                "stock_status": "low" if qty <= min_stock else "ok",
            })
        return rows

    @staticmethod
    async def _property_maintenance(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        query = (
            select(MaintenanceRequest, Unit, Customer)
            .join(Unit, MaintenanceRequest.unit_id == Unit.id)
            .outerjoin(Customer, MaintenanceRequest.customer_id == Customer.id)
        )
        if company_id:
            query = query.where(MaintenanceRequest.company_id == company_id)
        result = await db.execute(query)
        return [
            {
                "title": req.title,
                "unit_code": u.unit_code,
                "customer": c.full_name_en if c else "",
                "priority": req.priority,
                "status": req.status,
            }
            for req, u, c in result.all()
        ]

    @staticmethod
    async def _team_users(db: AsyncSession, company_id: Optional[int], _: bool) -> list[dict]:
        if not company_id:
            return []
        users = (
            await db.execute(
                select(User).where(
                    User.company_id == company_id,
                    User.is_deleted == False,
                    User.is_super_admin == False,
                )
            )
        ).scalars().all()
        return [
            {
                "username": u.username,
                "full_name_en": u.full_name_en,
                "full_name_ar": u.full_name_ar,
                "email": u.email,
                "system_role": u.system_role.value,
                "status": u.status.value,
            }
            for u in users
        ]

    @staticmethod
    async def _platform_users(db: AsyncSession, _: Optional[int], is_super_admin: bool) -> list[dict]:
        if not is_super_admin:
            return []
        users = (await db.execute(select(User).where(User.is_deleted == False))).scalars().all()
        return [
            {
                "email": u.email,
                "full_name_en": u.full_name_en,
                "full_name_ar": u.full_name_ar,
                "system_role": u.system_role.value,
                "status": u.status.value,
                "company_id": u.company_id or "",
            }
            for u in users
        ]
