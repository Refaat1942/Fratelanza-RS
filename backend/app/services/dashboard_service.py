from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crm import Lead, LeadStage
from app.models.customers import Customer
from app.models.real_estate import Building, Floor, Project, Unit, UnitStatus
from app.models.sales import Contract, ContractStatus, Installment, InstallmentStatus, Payment, PaymentPlan
from app.models.customer_service import Ticket
from app.models.tenant import Company
from app.models.users import User
from app.schemas.dashboard import ChartDataPoint, DashboardResponse, DashboardStats, KPICard


class DashboardService:
    @staticmethod
    async def super_admin_dashboard(db: AsyncSession) -> DashboardResponse:
        companies = (await db.execute(select(func.count(Company.id)))).scalar() or 0
        users = (await db.execute(select(func.count(User.id)).where(User.is_deleted == False))).scalar() or 0
        customers = (await db.execute(select(func.count(Customer.id)).where(Customer.is_deleted == False))).scalar() or 0
        stats = DashboardStats(
            total_companies=companies,
            total_users=users,
            total_customers=customers,
        )
        kpis = [
            KPICard(label_ar="الشركات", label_en="Companies", value=str(companies)),
            KPICard(label_ar="المستخدمون", label_en="Users", value=str(users)),
            KPICard(label_ar="العملاء", label_en="Customers", value=str(customers)),
        ]
        return DashboardResponse(stats=stats, kpis=kpis)

    @staticmethod
    async def company_dashboard(db: AsyncSession, company_id: int) -> DashboardResponse:
        unit_base = (
            select(func.count(Unit.id))
            .join(Floor, Unit.floor_id == Floor.id)
            .join(Building, Floor.building_id == Building.id)
            .join(Project, Building.project_id == Project.id)
            .where(Project.company_id == company_id, Unit.is_deleted == False)
        )
        total_units_count = (await db.execute(unit_base)).scalar() or 0

        available_count = (
            await db.execute(unit_base.where(Unit.status == UnitStatus.AVAILABLE))
        ).scalar() or 0

        leads_count = (
            await db.execute(
                select(func.count(Lead.id)).where(Lead.company_id == company_id, Lead.is_deleted == False)
            )
        ).scalar() or 0

        customers_count = (
            await db.execute(
                select(func.count(Customer.id)).where(Customer.company_id == company_id, Customer.is_deleted == False)
            )
        ).scalar() or 0

        sales_total = (
            await db.execute(
                select(func.coalesce(func.sum(Contract.total_price), 0)).where(
                    Contract.company_id == company_id,
                    Contract.status.in_([ContractStatus.ACTIVE, ContractStatus.COMPLETED]),
                    Contract.is_deleted == False,
                )
            )
        ).scalar() or Decimal("0")

        collections_total = (
            await db.execute(
                select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.company_id == company_id)
            )
        ).scalar() or Decimal("0")

        overdue = (
            await db.execute(
                select(func.coalesce(func.sum(Installment.remaining_balance), 0))
                .join(PaymentPlan, Installment.payment_plan_id == PaymentPlan.id)
                .join(Contract, PaymentPlan.contract_id == Contract.id)
                .where(Contract.company_id == company_id, Installment.status == InstallmentStatus.OVERDUE)
            )
        ).scalar() or Decimal("0")

        open_tickets = (
            await db.execute(
                select(func.count(Ticket.id)).where(Ticket.company_id == company_id, Ticket.status == "open")
            )
        ).scalar() or 0

        pipeline: dict[str, int] = {}
        for stage in LeadStage:
            count = (
                await db.execute(
                    select(func.count(Lead.id)).where(
                        Lead.company_id == company_id, Lead.stage == stage, Lead.is_deleted == False
                    )
                )
            ).scalar() or 0
            pipeline[stage.value] = count

        stats = DashboardStats(
            total_customers=customers_count,
            total_leads=leads_count,
            total_units=total_units_count,
            available_units=available_count,
            total_sales=sales_total,
            total_collections=collections_total,
            overdue_amount=overdue,
            open_tickets=open_tickets,
        )
        kpis = [
            KPICard(label_ar="إجمالي المبيعات", label_en="Total Sales", value=f"{sales_total:,.0f}"),
            KPICard(label_ar="التحصيلات", label_en="Collections", value=f"{collections_total:,.0f}"),
            KPICard(label_ar="الوحدات المتاحة", label_en="Available Units", value=str(available_count)),
            KPICard(label_ar="العملاء المحتملون", label_en="Leads", value=str(leads_count)),
        ]
        # Real monthly contract value for the last 6 months (contract_date is stored as YYYY-MM-DD)
        from datetime import date as _date

        today = _date.today()
        months = []
        for back in range(5, -1, -1):
            y, m = today.year, today.month - back
            while m <= 0:
                m += 12
                y -= 1
            months.append(f"{y:04d}-{m:02d}")
        month_col = func.substr(Contract.contract_date, 1, 7)
        monthly = dict(
            (
                await db.execute(
                    select(month_col, func.coalesce(func.sum(Contract.total_price), 0))
                    .where(
                        Contract.company_id == company_id,
                        Contract.is_deleted == False,  # noqa: E712
                        Contract.status.in_([ContractStatus.ACTIVE, ContractStatus.COMPLETED]),
                        month_col.in_(months),
                    )
                    .group_by(month_col)
                )
            ).all()
        )
        sales_chart = [ChartDataPoint(label=m, value=float(monthly.get(m, 0))) for m in months]
        return DashboardResponse(
            stats=stats,
            kpis=kpis,
            sales_chart=sales_chart,
            leads_pipeline=pipeline,
        )
