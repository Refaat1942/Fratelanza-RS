"""Configurable real-estate dashboard cards.

A card is returned only when (a) its module is enabled and viewable by the user, (b) financial
cards are additionally gated by ``dashboard:view_sensitive`` (or reports), and (c) for demo
tenants the card is in the demo's configured card list.
"""

from datetime import date, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hr import PayrollRun
from app.models.real_estate import Unit, UnitStatus
from app.models.rentals import (
    AdminExpense,
    OwnerSettlement,
    PropertyExpense,
    PropertyOwner,
    PropertyRequest,
    RentalContract,
    RentReceivable,
)
from app.services.access_service import AccessContext
from app.services.re_reports_service import ReReportsService
from app.services.rental_service import EXPIRING_WINDOW_DAYS, ZERO, money, outstanding
from app.services.settlement_service import next_settlement

# key: (name_ar, name_en, module, sensitive, route, format)
CARDS: dict[str, tuple[str, str, str, bool, str, str]] = {
    "properties_offered": ("عقارات معروضة", "Properties offered", "real_estate_requests", False, "/property-requests?kind=offer", "count"),
    "purchase_requests": ("طلبات شراء العملاء", "Customer purchase requests", "real_estate_requests", False, "/property-requests?kind=request_buy", "count"),
    "rental_requests": ("طلبات الإيجار", "Rental requests", "real_estate_requests", False, "/property-requests?kind=request_rent", "count"),
    "total_units": ("إجمالي الوحدات", "Total units", "rentals", False, "/rentals?tab=units", "count"),
    "available_units": ("الوحدات المتاحة", "Available units", "rentals", False, "/rentals?tab=units", "count"),
    "occupied_units": ("الوحدات المؤجرة", "Occupied units", "rentals", False, "/rentals?tab=units", "count"),
    "active_contracts": ("العقود السارية", "Active contracts", "rentals", False, "/rentals", "count"),
    "expiring_contracts": ("عقود قاربت على الانتهاء", "Contracts nearing expiry", "rentals", False, "/rentals?status=expiring", "count"),
    "upcoming_collections": ("تحصيلات خلال 30 يوماً", "Upcoming rent (30 days)", "rentals", False, "/rentals?tab=receivables", "money"),
    "overdue_rent": ("إيجارات متأخرة", "Overdue rent", "rentals", False, "/rentals?tab=receivables&status=overdue", "money"),
    "upcoming_settlements": ("تسويات ملاك قادمة", "Upcoming owner settlements", "owners", False, "/owners?tab=settlements", "count"),
    "owner_payables": ("مستحقات الملاك القائمة", "Outstanding owner payables", "owners", True, "/owners?tab=settlements", "money"),
    "maintenance_expenses": ("مصروفات الصيانة (الشهر)", "Maintenance expenses (month)", "property_expenses", False, "/property-expenses", "money"),
    "admin_expenses": ("المصروفات الإدارية (الشهر)", "Administrative expenses (month)", "admin_expenses", True, "/admin-expenses", "money"),
    "payroll": ("الرواتب (آخر مسير)", "Payroll (last run)", "hr", True, "/hr", "money"),
    "revenue": ("الإيرادات (الشهر)", "Revenue (month)", "reports", True, "/reports?tab=re&report=profit_loss", "money"),
    "expenses": ("المصروفات (الشهر)", "Expenses (month)", "reports", True, "/reports?tab=re&report=profit_loss", "money"),
    "profit": ("صافي الربح (الشهر)", "Net profit (month)", "reports", True, "/reports?tab=re&report=profit_loss", "money"),
}
CARD_KEYS = list(CARDS)


def visible_cards(access: AccessContext) -> list[str]:
    keys = []
    for key, (_, _, module, sensitive, _, _) in CARDS.items():
        if not access.can(module, "view"):
            continue
        if sensitive and not (access.can("dashboard", "view_sensitive") or access.can(module, "view_sensitive")):
            continue
        if key == "payroll" and not access.sees("salaries"):
            continue
        if access.dashboard_cards is not None and key not in access.dashboard_cards:
            continue
        keys.append(key)
    return keys


class ReDashboardService:
    @staticmethod
    async def compute(db: AsyncSession, cid: int, keys: list[str], today: date) -> list[dict]:
        values: dict[str, float] = {}
        need = set(keys)

        if need & {"properties_offered", "purchase_requests", "rental_requests"}:
            rows = (
                await db.execute(
                    select(PropertyRequest.kind, func.count())
                    .where(PropertyRequest.company_id == cid, PropertyRequest.status == "open", PropertyRequest.is_deleted == False)  # noqa: E712
                    .group_by(PropertyRequest.kind)
                )
            ).all()
            counts = dict(rows)
            values["properties_offered"] = counts.get("offer_sale", 0) + counts.get("offer_rent", 0)
            values["purchase_requests"] = counts.get("request_buy", 0)
            values["rental_requests"] = counts.get("request_rent", 0)

        if need & {"total_units", "available_units", "occupied_units"}:
            units = (
                await db.execute(select(Unit).where(Unit.company_id == cid, Unit.is_deleted == False))  # noqa: E712
            ).scalars().all()
            values["total_units"] = len(units)
            values["occupied_units"] = sum(1 for u in units if u.occupancy_status == "occupied")
            values["available_units"] = sum(
                1 for u in units if u.occupancy_status == "vacant" and u.status == UnitStatus.AVAILABLE
            )

        if need & {"active_contracts", "expiring_contracts"}:
            contracts = (
                await db.execute(
                    select(RentalContract).where(
                        RentalContract.company_id == cid, RentalContract.status == "active", RentalContract.is_deleted == False  # noqa: E712
                    )
                )
            ).scalars().all()
            values["active_contracts"] = sum(1 for c in contracts if c.end_date >= today)
            values["expiring_contracts"] = sum(
                1 for c in contracts if today <= c.end_date <= today + timedelta(days=EXPIRING_WINDOW_DAYS)
            )

        if need & {"upcoming_collections", "overdue_rent"}:
            open_recs = (
                await db.execute(
                    select(RentReceivable).where(
                        RentReceivable.company_id == cid, RentReceivable.status.in_(["pending", "partial"])
                    )
                )
            ).scalars().all()
            values["upcoming_collections"] = float(
                sum((outstanding(r) for r in open_recs if today <= r.due_date <= today + timedelta(days=30)), ZERO)
            )
            values["overdue_rent"] = float(sum((outstanding(r) for r in open_recs if r.due_date < today), ZERO))

        if need & {"upcoming_settlements", "owner_payables"}:
            owners = (
                await db.execute(select(PropertyOwner).where(PropertyOwner.company_id == cid, PropertyOwner.is_deleted == False))  # noqa: E712
            ).scalars().all()
            settlements = (
                await db.execute(select(OwnerSettlement).where(OwnerSettlement.company_id == cid))
            ).scalars().all()
            upcoming = 0
            for o in owners:
                start, end, due = next_settlement(o, today)
                done = any(s.owner_id == o.id and s.period_end == end and s.status != "cancelled" for s in settlements)
                if not done and today <= due <= today + timedelta(days=7):
                    upcoming += 1
            values["upcoming_settlements"] = upcoming
            values["owner_payables"] = float(
                sum(
                    (money(s.net_payable) - money(s.amount_paid) for s in settlements if s.status in ("approved", "partial")),
                    ZERO,
                )
            )

        month_start = date(today.year, today.month, 1)
        if "maintenance_expenses" in need:
            values["maintenance_expenses"] = float(
                money(
                    (
                        await db.execute(
                            select(func.coalesce(func.sum(PropertyExpense.amount), 0)).where(
                                PropertyExpense.company_id == cid,
                                PropertyExpense.is_deleted == False,  # noqa: E712
                                PropertyExpense.approval_status != "rejected",
                                PropertyExpense.expense_date >= month_start,
                                PropertyExpense.expense_date <= today,
                            )
                        )
                    ).scalar()
                )
            )
        if "admin_expenses" in need:
            values["admin_expenses"] = float(
                money(
                    (
                        await db.execute(
                            select(func.coalesce(func.sum(AdminExpense.amount), 0)).where(
                                AdminExpense.company_id == cid,
                                AdminExpense.is_deleted == False,  # noqa: E712
                                AdminExpense.expense_date >= month_start,
                                AdminExpense.expense_date <= today,
                            )
                        )
                    ).scalar()
                )
            )
        if "payroll" in need:
            run: Optional[PayrollRun] = (
                await db.execute(
                    select(PayrollRun).where(PayrollRun.company_id == cid).order_by(PayrollRun.period_month.desc()).limit(1)
                )
            ).scalar_one_or_none()
            values["payroll"] = float(money(run.total_net)) if run else 0.0
        if need & {"revenue", "expenses", "profit"}:
            pl = await ReReportsService.profit_loss_totals(db, cid, month_start, today)
            values["revenue"] = pl["total_revenue"]
            values["expenses"] = pl["total_expenses"]
            values["profit"] = pl["net_profit"]

        cards = []
        for key in keys:
            name_ar, name_en, module, sensitive, route, fmt = CARDS[key]
            cards.append(
                {"key": key, "name_ar": name_ar, "name_en": name_en, "module": module, "value": values.get(key, 0),
                 "format": fmt, "route": route}
            )
        return cards
