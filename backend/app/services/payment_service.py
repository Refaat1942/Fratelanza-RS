from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sales import Installment, InstallmentStatus, Payment


class PaymentService:
    @staticmethod
    async def record_payment(
        db: AsyncSession,
        company_id: int,
        installment_id: int,
        customer_id: int,
        amount: Decimal,
        payment_date: str,
        payment_method: str = "cash",
        received_by_id: int | None = None,
        reference_number: str | None = None,
    ) -> Payment:
        result = await db.execute(select(Installment).where(Installment.id == installment_id))
        installment = result.scalar_one_or_none()
        if not installment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Installment not found")

        installment.paid_amount += amount
        installment.remaining_balance = max(installment.due_amount - installment.paid_amount, Decimal("0"))
        if installment.remaining_balance <= 0:
            installment.status = InstallmentStatus.PAID
        elif installment.paid_amount > 0:
            installment.status = InstallmentStatus.PARTIAL
        else:
            installment.status = InstallmentStatus.DUE

        payment = Payment(
            company_id=company_id,
            installment_id=installment_id,
            customer_id=customer_id,
            amount=amount,
            payment_date=payment_date,
            payment_method=payment_method,
            received_by_id=received_by_id,
            reference_number=reference_number,
        )
        db.add(payment)
        await db.flush()
        return payment

    @staticmethod
    async def list_installments(db: AsyncSession, company_id: int) -> list[dict]:
        from app.models.customers import Customer
        from app.models.real_estate import Unit
        from app.models.sales import PaymentPlan, Contract

        query = (
            select(Installment, Contract, Customer, Unit)
            .join(PaymentPlan, Installment.payment_plan_id == PaymentPlan.id)
            .join(Contract, PaymentPlan.contract_id == Contract.id)
            .join(Customer, Contract.customer_id == Customer.id)
            .join(Unit, Contract.unit_id == Unit.id)
            .where(Contract.company_id == company_id, Contract.is_deleted == False)
            .order_by(Installment.due_date)
        )
        result = await db.execute(query)
        rows = []
        for inst, contract, customer, unit in result.all():
            rows.append(
                {
                    "id": inst.id,
                    "contract_id": contract.id,
                    "contract_number": contract.contract_number,
                    "customer_id": contract.customer_id,
                    "customer_name": customer.full_name_ar,
                    "unit_code": unit.unit_code,
                    "installment_number": inst.installment_number,
                    "due_date": inst.due_date,
                    "due_amount": float(inst.due_amount),
                    "paid_amount": float(inst.paid_amount),
                    "remaining_balance": float(inst.remaining_balance),
                    "status": inst.status.value,
                }
            )
        return rows
