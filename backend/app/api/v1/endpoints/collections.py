from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.users import User
from app.services.payment_service import PaymentService

router = APIRouter()


class PaymentCreate(BaseModel):
    installment_id: int
    customer_id: int
    amount: Decimal
    payment_date: str
    payment_method: str = "cash"
    reference_number: Optional[str] = None


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
