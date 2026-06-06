from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.rbac import Permission, ROLE_PERMISSIONS
from app.db.session import get_db
from app.models import Contract, Installment, Lead, LeadStage, Unit, UnitStatus, User
from app.schemas import DashboardKPI, ExecutiveDashboard

router = APIRouter()


@router.get("/executive", response_model=ExecutiveDashboard)
def executive_dashboard(
    company_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.REPORTS_READ)),
) -> ExecutiveDashboard:
    scoped_company_id = company_id if Permission.PLATFORM_ALL in ROLE_PERMISSIONS[current_user.role] else current_user.company_id

    def with_scope(stmt, model):
        if scoped_company_id:
            return stmt.where(model.company_id == scoped_company_id)
        return stmt

    total_sales = db.scalar(with_scope(select(func.coalesce(func.sum(Contract.total_value), 0)), Contract))
    overdue_balance = db.scalar(
        with_scope(
            select(func.coalesce(func.sum(Installment.due_amount - Installment.paid_amount), 0)),
            Installment,
        )
    )

    lead_rows = db.execute(
        with_scope(select(Lead.stage, func.count(Lead.id)).group_by(Lead.stage), Lead)
    ).all()
    unit_rows = db.execute(
        with_scope(select(Unit.status, func.count(Unit.id)).group_by(Unit.status), Unit)
    ).all()

    sales_pipeline = {stage.value: 0 for stage in LeadStage}
    sales_pipeline.update({stage.value: count for stage, count in lead_rows})

    unit_inventory = {status.value: 0 for status in UnitStatus}
    unit_inventory.update({status.value: count for status, count in unit_rows})

    return ExecutiveDashboard(
        kpis=[
            DashboardKPI(
                key="total_sales",
                label_ar="إجمالي المبيعات",
                label_en="Total Sales",
                value=float(total_sales or 0),
            ),
            DashboardKPI(
                key="overdue_balance",
                label_ar="المتأخرات",
                label_en="Overdue Balance",
                value=float(overdue_balance or 0),
            ),
            DashboardKPI(
                key="available_units",
                label_ar="الوحدات المتاحة",
                label_en="Available Units",
                value=unit_inventory.get(UnitStatus.AVAILABLE.value, 0),
            ),
            DashboardKPI(
                key="active_leads",
                label_ar="العملاء المحتملون النشطون",
                label_en="Active Leads",
                value=sum(count for stage, count in sales_pipeline.items() if stage != LeadStage.LOST.value),
            ),
        ],
        sales_pipeline=sales_pipeline,
        unit_inventory=unit_inventory,
        collections={
            "overdue_balance": Decimal(overdue_balance or 0),
            "forecast_30_days": Decimal("0.00"),
        },
    )
