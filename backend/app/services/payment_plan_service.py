from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.sales import Contract, Installment, InstallmentStatus, PaymentPlan, PaymentPlanType
from app.services.installment_calculator_service import build_schedule, money, recalculate_schedule


class PaymentPlanService:
    @staticmethod
    async def get_plan_for_contract(db: AsyncSession, company_id: int, contract_id: int) -> dict | None:
        contract = await PaymentPlanService._get_contract(db, company_id, contract_id)
        plan = (
            await db.execute(
                select(PaymentPlan)
                .options(selectinload(PaymentPlan.installments))
                .where(PaymentPlan.contract_id == contract.id)
            )
        ).scalar_one_or_none()
        if not plan:
            return None
        installments = sorted(plan.installments, key=lambda i: i.installment_number)
        return {
            "contract_id": contract.id,
            "contract_number": contract.contract_number,
            "total_price": float(contract.total_price),
            "payment_plan_id": plan.id,
            "plan_type": plan.plan_type.value,
            "down_payment": float(plan.down_payment),
            "total_amount": float(plan.total_amount),
            "number_of_installments": plan.number_of_installments,
            "start_date": plan.start_date,
            "installments": [
                {
                    "id": inst.id,
                    "installment_number": inst.installment_number,
                    "due_date": inst.due_date,
                    "due_amount": float(inst.due_amount),
                    "paid_amount": float(inst.paid_amount),
                    "remaining_balance": float(inst.remaining_balance),
                    "is_manual": inst.is_manual,
                    "status": inst.status.value,
                }
                for inst in installments
            ],
        }

    @staticmethod
    async def apply_schedule(
        db: AsyncSession,
        company_id: int,
        contract_id: int,
        plan_type: str,
        down_payment: Decimal,
        start_date: str,
        installments: list[dict],
    ) -> dict:
        contract = await PaymentPlanService._get_contract(db, company_id, contract_id)
        existing = (
            await db.execute(
                select(PaymentPlan)
                .options(selectinload(PaymentPlan.installments))
                .where(PaymentPlan.contract_id == contract.id)
            )
        ).scalar_one_or_none()

        if existing:
            for inst in existing.installments:
                if inst.paid_amount > 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot replace plan — payments already recorded on installments",
                    )
            for inst in existing.installments:
                await db.delete(inst)
            await db.delete(existing)
            await db.flush()

        try:
            plan_enum = PaymentPlanType(plan_type)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid plan type")

        plan = PaymentPlan(
            contract_id=contract.id,
            plan_type=plan_enum,
            down_payment=down_payment,
            total_amount=contract.total_price,
            number_of_installments=len(installments),
            start_date=start_date,
        )
        db.add(plan)
        await db.flush()

        for row in installments:
            due = money(Decimal(str(row["due_amount"])))
            paid = money(Decimal(str(row.get("paid_amount", 0))))
            db.add(
                Installment(
                    payment_plan_id=plan.id,
                    installment_number=int(row["installment_number"]),
                    due_date=row["due_date"],
                    due_amount=due,
                    paid_amount=paid,
                    remaining_balance=money(max(due - paid, Decimal("0"))),
                    is_manual=bool(row.get("is_manual", False)),
                    status=InstallmentStatus.UPCOMING if paid <= 0 else InstallmentStatus.PARTIAL,
                )
            )
        await db.flush()
        return await PaymentPlanService.get_plan_for_contract(db, company_id, contract_id) or {}

    @staticmethod
    async def adjust_installment(
        db: AsyncSession,
        company_id: int,
        installment_id: int,
        new_due_amount: Decimal,
    ) -> dict:
        inst = (
            await db.execute(
                select(Installment)
                .join(PaymentPlan, Installment.payment_plan_id == PaymentPlan.id)
                .join(Contract, PaymentPlan.contract_id == Contract.id)
                .where(
                    Installment.id == installment_id,
                    Contract.company_id == company_id,
                )
            )
        ).scalar_one_or_none()
        if not inst:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Installment not found")

        plan = (
            await db.execute(
                select(PaymentPlan)
                .options(selectinload(PaymentPlan.installments))
                .where(PaymentPlan.id == inst.payment_plan_id)
            )
        ).scalar_one_or_none()
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment plan not found")

        if new_due_amount < inst.paid_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Due amount cannot be less than amount already paid",
            )

        rows = []
        for item in sorted(plan.installments, key=lambda x: x.installment_number):
            due_amount = item.due_amount
            is_manual = item.is_manual
            if item.id == installment_id:
                due_amount = new_due_amount
                is_manual = True
            elif item.paid_amount > 0:
                is_manual = True
            rows.append(
                {
                    "installment_number": item.installment_number,
                    "due_date": item.due_date,
                    "due_amount": float(due_amount),
                    "paid_amount": float(item.paid_amount),
                    "is_manual": is_manual or item.paid_amount > 0,
                }
            )

        recalculated = recalculate_schedule(
            total_price=plan.total_amount,
            down_payment=plan.down_payment,
            plan_type=plan.plan_type.value,
            start_date=plan.start_date,
            installment_rows=rows,
        )

        by_number = {r["installment_number"]: r for r in recalculated}
        for item in plan.installments:
            row = by_number[item.installment_number]
            item.due_amount = money(Decimal(str(row["due_amount"])))
            item.remaining_balance = money(
                max(item.due_amount - item.paid_amount, Decimal("0"))
            )
            item.is_manual = bool(row.get("is_manual", False))
            if item.remaining_balance <= 0 and item.paid_amount > 0:
                item.status = InstallmentStatus.PAID
            elif item.paid_amount > 0:
                item.status = InstallmentStatus.PARTIAL

        await db.flush()
        contract = (
            await db.execute(select(Contract).where(Contract.id == plan.contract_id))
        ).scalar_one()
        return await PaymentPlanService.get_plan_for_contract(db, company_id, contract.id) or {}

    @staticmethod
    async def _get_contract(db: AsyncSession, company_id: int, contract_id: int) -> Contract:
        contract = (
            await db.execute(
                select(Contract).where(
                    Contract.id == contract_id,
                    Contract.company_id == company_id,
                    Contract.is_deleted == False,
                )
            )
        ).scalar_one_or_none()
        if not contract:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
        return contract
