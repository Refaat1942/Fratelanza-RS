from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.users import User
from app.services.installment_calculator_service import build_schedule, recalculate_schedule
from app.services.payment_plan_service import PaymentPlanService
from app.services.payment_service import PaymentService

router = APIRouter()


class PaymentCreate(BaseModel):
    installment_id: int
    customer_id: int
    amount: Decimal
    payment_date: str
    payment_method: str = "cash"
    reference_number: Optional[str] = None


class InstallmentRowInput(BaseModel):
    installment_number: int
    due_date: Optional[str] = None
    due_amount: Optional[Decimal] = None
    paid_amount: Decimal = Decimal("0")
    is_manual: bool = False


class CalculatorPreviewRequest(BaseModel):
    total_price: Decimal = Field(gt=0)
    down_payment: Decimal = Field(ge=0)
    plan_type: str = "quarterly"
    number_of_installments: Optional[int] = Field(default=None, ge=1, le=360)
    start_date: str
    installments: Optional[list[InstallmentRowInput]] = None


class ApplyScheduleRequest(BaseModel):
    contract_id: int
    plan_type: str
    down_payment: Decimal = Field(ge=0)
    start_date: str
    installments: list[InstallmentRowInput]


class AdjustInstallmentRequest(BaseModel):
    due_amount: Decimal = Field(gt=0)


@router.get("/installments")
async def list_installments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    return await PaymentService.list_installments(db, current_user.company_id)


@router.post("/payments")
async def record_payment(
    data: PaymentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    payment = await PaymentService.record_payment(
        db,
        current_user.company_id,
        data.installment_id,
        data.customer_id,
        data.amount,
        data.payment_date,
        data.payment_method,
        current_user.id,
        data.reference_number,
    )
    return {"id": payment.id, "amount": float(payment.amount), "success": True}


@router.post("/calculator/preview")
async def preview_installment_schedule(
    data: CalculatorPreviewRequest,
    current_user: Annotated[User, Depends(get_company_user)],
):
    try:
        rows = [r.model_dump() for r in data.installments] if data.installments else None
        if rows:
            result = build_schedule(
                total_price=data.total_price,
                down_payment=data.down_payment,
                plan_type=data.plan_type,
                number_of_installments=len(rows),
                start_date=data.start_date,
                installment_rows=rows,
            )
        else:
            count = data.number_of_installments or 1
            result = build_schedule(
                total_price=data.total_price,
                down_payment=data.down_payment,
                plan_type=data.plan_type,
                number_of_installments=count,
                start_date=data.start_date,
            )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/calculator/recalculate")
async def recalculate_installment_schedule(
    data: CalculatorPreviewRequest,
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not data.installments:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Installments required")
    try:
        rows = recalculate_schedule(
            total_price=data.total_price,
            down_payment=data.down_payment,
            plan_type=data.plan_type,
            start_date=data.start_date,
            installment_rows=[r.model_dump() for r in data.installments],
        )
        financed = data.total_price - data.down_payment
        schedule_total = sum(Decimal(str(r["due_amount"])) for r in rows)
        return {
            "total_price": float(data.total_price),
            "down_payment": float(data.down_payment),
            "financed_amount": float(financed),
            "plan_type": data.plan_type,
            "number_of_installments": len(rows),
            "start_date": data.start_date,
            "installments": rows,
            "schedule_total": float(schedule_total),
            "balanced": round(schedule_total, 2) == round(financed, 2),
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/payment-plans/{contract_id}")
async def get_payment_plan(
    contract_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    plan = await PaymentPlanService.get_plan_for_contract(db, current_user.company_id, contract_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment plan not found")
    return plan


@router.post("/calculator/apply")
async def apply_installment_schedule(
    data: ApplyScheduleRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    return await PaymentPlanService.apply_schedule(
        db,
        current_user.company_id,
        data.contract_id,
        data.plan_type,
        data.down_payment,
        data.start_date,
        [r.model_dump() for r in data.installments],
    )


@router.patch("/installments/{installment_id}/adjust")
async def adjust_installment_amount(
    installment_id: int,
    data: AdjustInstallmentRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    return await PaymentPlanService.adjust_installment(
        db, current_user.company_id, installment_id, data.due_amount
    )
