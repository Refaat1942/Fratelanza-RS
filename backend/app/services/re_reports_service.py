"""Property-management reports computed from operational records (never from hard-coded numbers).

Company revenue  = management commissions of approved/partially-paid/paid settlements whose
                   period ends in range  +  rent collected on company-owned units (no owner)
                   −  refunds on those units.
Company expenses = administrative expenses (expense_date in range)
                 + approved company-charged property expenses (expense_date in range)
                 + payroll gross of runs whose month is in range.
Owner funds (rent collected on owner units) are liabilities, never revenue.
"""

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hr import Employee, PayrollRun, Payslip
from app.models.real_estate import Unit
from app.models.rentals import (
    AdminExpense,
    OwnerSettlement,
    PropertyExpense,
    PropertyOwner,
    RentalContract,
    RentPayment,
    RentReceivable,
)
from app.services.rental_service import ZERO, contract_display_status, money, outstanding

# key: (name_ar, name_en, needs view_sensitive, module required to view)
CATALOG: dict[str, tuple[str, str, bool, str]] = {
    "units": ("تقرير الوحدات", "Units report", False, "rentals"),
    "owners": ("تقرير الملاك", "Owners report", True, "owners"),
    "contracts": ("تقرير عقود الإيجار", "Rental contracts report", False, "rentals"),
    "tenants": ("تقرير المستأجرين", "Tenants report", False, "rentals"),
    "collections": ("تقرير التحصيل حسب الفترة", "Collections by period", False, "rentals"),
    "settlements": ("تقرير تسويات الملاك", "Owner settlements report", True, "owners"),
    "maintenance_expenses": ("تقرير مصروفات الصيانة", "Maintenance expenses report", False, "property_expenses"),
    "admin_expenses": ("تقرير المصروفات الإدارية", "Administrative expenses report", True, "admin_expenses"),
    "payroll": ("تقرير الرواتب", "Payroll report", True, "hr"),
    "receivables": ("المستحقات القائمة والمتأخرة", "Outstanding & overdue receivables", False, "rentals"),
    "payables": ("المستحقات للملاك", "Outstanding owner payables", True, "owners"),
    "profit_loss": ("الإيرادات والمصروفات وصافي الربح", "Revenue, expenses & net profit", True, "reports"),
    "monthly_performance": ("الأداء الشهري والسنوي", "Monthly & annual performance", True, "reports"),
}


def _in(d: Optional[date], start: Optional[date], end: Optional[date]) -> bool:
    if d is None:
        return False
    return (start is None or d >= start) and (end is None or d <= end)


def _f(value) -> float:
    return float(money(value))


class ReReportsService:
    @staticmethod
    async def _contracts(db, cid):
        return (
            await db.execute(
                select(RentalContract).where(RentalContract.company_id == cid, RentalContract.is_deleted == False)  # noqa: E712
            )
        ).scalars().all()

    @staticmethod
    async def _receivables(db, cid):
        return (
            await db.execute(
                select(RentReceivable).where(RentReceivable.company_id == cid, RentReceivable.status != "cancelled")
            )
        ).scalars().all()

    @staticmethod
    async def _payments(db, cid):
        return (await db.execute(select(RentPayment).where(RentPayment.company_id == cid))).scalars().all()

    @staticmethod
    async def profit_loss_totals(db: AsyncSession, cid: int, start: Optional[date], end: Optional[date]) -> dict:
        contracts = {c.id: c for c in await ReReportsService._contracts(db, cid)}
        rental_income = ZERO
        for p in await ReReportsService._payments(db, cid):
            c = contracts.get(p.rental_contract_id)
            if c and not c.owner_id and _in(p.paid_on, start, end):
                rental_income += money(p.amount) * (-1 if p.kind == "refund" else 1)
        settlements = (
            await db.execute(
                select(OwnerSettlement).where(
                    OwnerSettlement.company_id == cid, OwnerSettlement.status.in_(["approved", "partial", "paid"])
                )
            )
        ).scalars().all()
        commission = sum((money(s.commission_amount) for s in settlements if _in(s.period_end, start, end)), ZERO)
        admin = (
            await db.execute(
                select(AdminExpense).where(AdminExpense.company_id == cid, AdminExpense.is_deleted == False)  # noqa: E712
            )
        ).scalars().all()
        admin_total = sum((money(a.amount) for a in admin if _in(a.expense_date, start, end)), ZERO)
        prop = (
            await db.execute(
                select(PropertyExpense).where(
                    PropertyExpense.company_id == cid,
                    PropertyExpense.is_deleted == False,  # noqa: E712
                    PropertyExpense.charged_to == "company",
                    PropertyExpense.approval_status == "approved",
                )
            )
        ).scalars().all()
        prop_total = sum((money(e.amount) for e in prop if _in(e.expense_date, start, end)), ZERO)
        runs = (await db.execute(select(PayrollRun).where(PayrollRun.company_id == cid))).scalars().all()
        payroll_total = ZERO
        for r in runs:
            run_day = date.fromisoformat(f"{r.period_month}-01")
            if (start is None or run_day >= date(start.year, start.month, 1)) and (end is None or run_day <= end):
                payroll_total += money(r.total_gross)
        revenue = commission + rental_income
        expenses = admin_total + prop_total + payroll_total
        return {
            "commission_income": _f(commission),
            "rental_income_company_units": _f(rental_income),
            "total_revenue": _f(revenue),
            "admin_expenses": _f(admin_total),
            "company_property_expenses": _f(prop_total),
            "payroll": _f(payroll_total),
            "total_expenses": _f(expenses),
            "net_profit": _f(revenue - expenses),
        }

    @staticmethod
    async def run(db: AsyncSession, key: str, cid: int, start: Optional[date], end: Optional[date], today: date) -> dict:
        if key not in CATALOG:
            return {"rows": [], "totals": {}}
        rows: list[dict] = []
        totals: dict = {}

        if key in ("units", "contracts", "tenants", "collections", "receivables"):
            contracts = {c.id: c for c in await ReReportsService._contracts(db, cid)}
            receivables = await ReReportsService._receivables(db, cid)
            payments = await ReReportsService._payments(db, cid)
            units = {
                u.id: u
                for u in (await db.execute(select(Unit).where(Unit.company_id == cid, Unit.is_deleted == False))).scalars().all()  # noqa: E712
            }

        if key == "units":
            owners = {o.id: o for o in (await db.execute(select(PropertyOwner).where(PropertyOwner.company_id == cid))).scalars().all()}
            expenses = (
                await db.execute(select(PropertyExpense).where(PropertyExpense.company_id == cid, PropertyExpense.is_deleted == False))  # noqa: E712
            ).scalars().all()
            by_unit_paid: dict[int, Decimal] = defaultdict(lambda: ZERO)
            by_unit_out: dict[int, Decimal] = defaultdict(lambda: ZERO)
            for p in payments:
                c = contracts.get(p.rental_contract_id)
                if c and _in(p.paid_on, start, end):
                    by_unit_paid[c.unit_id] += money(p.amount) * (-1 if p.kind == "refund" else 1)
            for r in receivables:
                c = contracts.get(r.rental_contract_id)
                if c and _in(r.due_date, start, end):
                    by_unit_out[c.unit_id] += outstanding(r)
            by_unit_exp: dict[int, Decimal] = defaultdict(lambda: ZERO)
            for e in expenses:
                if e.approval_status == "approved" and _in(e.expense_date, start, end):
                    by_unit_exp[e.unit_id] += money(e.amount)
            active = {c.unit_id: c for c in contracts.values() if c.status == "active"}
            for u in units.values():
                c = active.get(u.id)
                rows.append({
                    "unit_code": u.unit_code,
                    "owner": owners[u.owner_id].full_name if u.owner_id in owners else "",
                    "occupancy": u.occupancy_status,
                    "tenant": c.tenant_name if c else "",
                    "monthly_rent": _f(c.rent_amount) if c else 0.0,
                    "collected": _f(by_unit_paid[u.id]),
                    "outstanding": _f(by_unit_out[u.id]),
                    "expenses": _f(by_unit_exp[u.id]),
                })
        elif key == "contracts":
            bal: dict[int, dict] = defaultdict(lambda: {"billed": ZERO, "paid": ZERO, "out": ZERO, "overdue": ZERO})
            for r in receivables:
                if not _in(r.due_date, start, end):
                    continue
                b = bal[r.rental_contract_id]
                b["billed"] += money(r.amount_due)
                b["paid"] += money(r.amount_paid)
                b["out"] += outstanding(r)
                if r.due_date < today:
                    b["overdue"] += outstanding(r)
            for c in contracts.values():
                b = bal[c.id]
                rows.append({
                    "contract_number": c.contract_number,
                    "unit_code": units[c.unit_id].unit_code if c.unit_id in units else "",
                    "tenant": c.tenant_name,
                    "start_date": c.start_date.isoformat(),
                    "end_date": c.end_date.isoformat(),
                    "status": contract_display_status(c, today),
                    "monthly_rent": _f(c.rent_amount),
                    "billed": _f(b["billed"]),
                    "collected": _f(b["paid"]),
                    "outstanding": _f(b["out"]),
                    "overdue": _f(b["overdue"]),
                })
        elif key == "tenants":
            agg: dict[str, dict] = defaultdict(lambda: {"contracts": 0, "billed": ZERO, "paid": ZERO, "out": ZERO, "mobile": ""})
            for c in contracts.values():
                a = agg[c.tenant_name]
                a["contracts"] += 1
                a["mobile"] = c.tenant_mobile or a["mobile"]
            for r in receivables:
                c = contracts.get(r.rental_contract_id)
                if c and _in(r.due_date, start, end):
                    a = agg[c.tenant_name]
                    a["billed"] += money(r.amount_due)
                    a["paid"] += money(r.amount_paid)
                    a["out"] += outstanding(r)
            for name, a in agg.items():
                rows.append({"tenant": name, "mobile": a["mobile"], "contracts": a["contracts"], "billed": _f(a["billed"]),
                             "collected": _f(a["paid"]), "outstanding": _f(a["out"])})
        elif key == "collections":
            months: dict[str, dict] = defaultdict(lambda: {"due": ZERO, "collected": ZERO, "refunded": ZERO, "out": ZERO})
            for r in receivables:
                if _in(r.due_date, start, end):
                    m = months[r.due_date.strftime("%Y-%m")]
                    m["due"] += money(r.amount_due) - money(r.adjustment_amount)
                    m["out"] += outstanding(r)
            for p in payments:
                if _in(p.paid_on, start, end):
                    m = months[p.paid_on.strftime("%Y-%m")]
                    if p.kind == "refund":
                        m["refunded"] += money(p.amount)
                    else:
                        m["collected"] += money(p.amount)
            for month in sorted(months):
                m = months[month]
                rows.append({"month": month, "due": _f(m["due"]), "collected": _f(m["collected"]),
                             "refunded": _f(m["refunded"]), "outstanding": _f(m["out"])})
        elif key == "receivables":
            for r in receivables:
                rem = outstanding(r)
                if rem <= 0 or not _in(r.due_date, start, end):
                    continue
                c = contracts.get(r.rental_contract_id)
                rows.append({
                    "contract_number": c.contract_number if c else "",
                    "tenant": c.tenant_name if c else "",
                    "unit_code": units[c.unit_id].unit_code if c and c.unit_id in units else "",
                    "due_date": r.due_date.isoformat(),
                    "outstanding": _f(rem),
                    "overdue_days": max((today - r.due_date).days, 0),
                    "is_overdue": r.due_date < today,
                })
            rows.sort(key=lambda x: x["due_date"])
        elif key in ("owners", "settlements", "payables"):
            owners = (
                await db.execute(select(PropertyOwner).where(PropertyOwner.company_id == cid, PropertyOwner.is_deleted == False))  # noqa: E712
            ).scalars().all()
            settlements = (
                await db.execute(select(OwnerSettlement).where(OwnerSettlement.company_id == cid))
            ).scalars().all()
            owner_map = {o.id: o for o in owners}
            if key == "settlements":
                for s in settlements:
                    if not _in(s.period_end, start, end):
                        continue
                    rows.append({
                        "settlement_id": s.id,
                        "owner": owner_map[s.owner_id].full_name if s.owner_id in owner_map else "",
                        "period": f"{s.period_start} → {s.period_end}",
                        "status": s.status,
                        "gross_collected": _f(s.gross_collected),
                        "commission": _f(s.commission_amount),
                        "expenses": _f(s.expenses_total),
                        "adjustments": _f(s.adjustments),
                        "net_payable": _f(s.net_payable),
                        "paid": _f(s.amount_paid),
                        "remaining": _f(money(s.net_payable) - money(s.amount_paid)),
                    })
            else:
                contracts = {c.id: c for c in await ReReportsService._contracts(db, cid)}
                unsettled: dict[int, Decimal] = defaultdict(lambda: ZERO)
                for p in await ReReportsService._payments(db, cid):
                    c = contracts.get(p.rental_contract_id)
                    if c and c.owner_id and p.settlement_id is None:
                        unsettled[c.owner_id] += money(p.amount) * (-1 if p.kind == "refund" else 1)
                for o in owners:
                    own = [s for s in settlements if s.owner_id == o.id and s.status != "cancelled"]
                    in_range = [s for s in own if _in(s.period_end, start, end)]
                    approved_unpaid = sum(
                        (money(s.net_payable) - money(s.amount_paid) for s in own if s.status in ("approved", "partial")), ZERO
                    )
                    row = {
                        "owner": o.full_name,
                        "settlement_frequency": o.settlement_frequency,
                        "collected_unsettled": _f(unsettled[o.id]),
                        "approved_unpaid": _f(approved_unpaid),
                        "total_owed": _f(unsettled[o.id] + approved_unpaid),
                    }
                    if key == "owners":
                        row.update({
                            "units": 0,
                            "gross_collected": _f(sum((money(s.gross_collected) for s in in_range), ZERO)),
                            "commission": _f(sum((money(s.commission_amount) for s in in_range), ZERO)),
                            "expenses": _f(sum((money(s.expenses_total) for s in in_range), ZERO)),
                            "net_paid": _f(sum((money(s.amount_paid) for s in in_range), ZERO)),
                        })
                    rows.append(row)
                if key == "owners":
                    unit_counts: dict[int, int] = defaultdict(int)
                    for u in (await db.execute(select(Unit).where(Unit.company_id == cid, Unit.is_deleted == False))).scalars().all():  # noqa: E712
                        if u.owner_id:
                            unit_counts[u.owner_id] += 1
                    for row, o in zip(rows, owners):
                        row["units"] = unit_counts[o.id]
        elif key == "maintenance_expenses":
            expenses = (
                await db.execute(
                    select(PropertyExpense, Unit)
                    .join(Unit, PropertyExpense.unit_id == Unit.id)
                    .where(PropertyExpense.company_id == cid, PropertyExpense.is_deleted == False)  # noqa: E712
                )
            ).all()
            for e, u in expenses:
                if not _in(e.expense_date, start, end):
                    continue
                rows.append({
                    "date": e.expense_date.isoformat(), "unit_code": u.unit_code, "category": e.category,
                    "vendor": e.vendor or "", "amount": _f(e.amount), "charged_to": e.charged_to,
                    "approval_status": e.approval_status, "payment_status": e.payment_status,
                })
        elif key == "admin_expenses":
            for a in (
                await db.execute(select(AdminExpense).where(AdminExpense.company_id == cid, AdminExpense.is_deleted == False))  # noqa: E712
            ).scalars().all():
                if not _in(a.expense_date, start, end):
                    continue
                rows.append({
                    "date": a.expense_date.isoformat(), "category": a.category, "description": a.description or "",
                    "amount": _f(a.amount), "paid": _f(a.amount_paid), "remaining": _f(money(a.amount) - money(a.amount_paid)),
                    "payment_status": a.payment_status,
                })
        elif key == "payroll":
            data = (
                await db.execute(
                    select(Payslip, PayrollRun, Employee)
                    .join(PayrollRun, Payslip.payroll_run_id == PayrollRun.id)
                    .join(Employee, Payslip.employee_id == Employee.id)
                    .where(PayrollRun.company_id == cid)
                )
            ).all()
            for p, run, emp in data:
                run_day = date.fromisoformat(f"{run.period_month}-01")
                if not ((start is None or run_day >= date(start.year, start.month, 1)) and (end is None or run_day <= end)):
                    continue
                rows.append({
                    "period": run.period_month, "employee": emp.full_name_ar, "gross": _f(p.basic_salary) + _f(p.allowances),
                    "net": _f(p.net_salary), "paid": _f(p.paid_amount), "outstanding": _f(money(p.net_salary) - money(p.paid_amount)),
                })
        elif key == "profit_loss":
            totals = await ReReportsService.profit_loss_totals(db, cid, start, end)
            rows = [{"line": k, "amount": v} for k, v in totals.items()]
        elif key == "monthly_performance":
            year_start = start or date(today.year, 1, 1)
            year_end = end or today
            cursor = date(year_start.year, year_start.month, 1)
            while cursor <= year_end:
                next_month = date(cursor.year + (cursor.month // 12), cursor.month % 12 + 1, 1)
                month_end = min(next_month - timedelta(days=1), year_end)
                t = await ReReportsService.profit_loss_totals(db, cid, cursor, month_end)
                rows.append({"month": cursor.strftime("%Y-%m"), "revenue": t["total_revenue"],
                             "expenses": t["total_expenses"], "net_profit": t["net_profit"]})
                cursor = next_month
            totals = {
                "revenue": round(sum(r["revenue"] for r in rows), 2),
                "expenses": round(sum(r["expenses"] for r in rows), 2),
                "net_profit": round(sum(r["net_profit"] for r in rows), 2),
            }

        if not totals and rows:
            numeric = [k for k, v in rows[0].items() if isinstance(v, float)]
            totals = {k: round(sum(r.get(k, 0.0) for r in rows), 2) for k in numeric}
        return {"rows": rows, "totals": totals}
