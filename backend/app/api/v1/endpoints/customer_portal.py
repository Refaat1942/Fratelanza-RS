from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.customers import Customer
from app.models.sales import Contract, Installment, Payment, PaymentPlan, Reservation
from app.models.users import SystemRole, User

router = APIRouter()


@router.get("/dashboard")
async def customer_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.system_role != SystemRole.CUSTOMER and not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer access only")

    customer_result = await db.execute(select(Customer).where(Customer.user_id == current_user.id))
    customer = customer_result.scalar_one_or_none()
    if not customer and not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer profile not found")

    customer_id = customer.id if customer else 0
    contracts = (
        await db.execute(select(Contract).where(Contract.customer_id == customer_id, Contract.is_deleted == False))
    ).scalars().all()
    reservations = (
        await db.execute(select(Reservation).where(Reservation.customer_id == customer_id, Reservation.is_deleted == False))
    ).scalars().all()

    installments = []
    for contract in contracts:
        plan_result = await db.execute(select(PaymentPlan).where(PaymentPlan.contract_id == contract.id))
        plan = plan_result.scalar_one_or_none()
        if plan:
            inst_result = await db.execute(
                select(Installment).where(Installment.payment_plan_id == plan.id).order_by(Installment.due_date)
            )
            for inst in inst_result.scalars().all():
                installments.append(
                    {
                        "contract_number": contract.contract_number,
                        "due_date": inst.due_date,
                        "due_amount": float(inst.due_amount),
                        "paid_amount": float(inst.paid_amount),
                        "status": inst.status.value,
                    }
                )

    return {
        "customer": {
            "name_ar": customer.full_name_ar if customer else "Demo",
            "mobile": customer.mobile if customer else "",
        },
        "contracts": [
            {"id": c.id, "number": c.contract_number, "total_price": float(c.total_price), "status": c.status.value}
            for c in contracts
        ],
        "reservations": [
            {"id": r.id, "number": r.reservation_number, "status": r.status.value}
            for r in reservations
        ],
        "installments": installments,
    }
