import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.real_estate import Unit, UnitStatus
from app.models.sales import (
    Contract,
    ContractStatus,
    Installment,
    InstallmentStatus,
    PaymentPlan,
    PaymentPlanType,
    Reservation,
    ReservationStatus,
)
from app.schemas.project import ContractCreate
from app.services.dynamic_pricing_service import DynamicPricingService


class ContractService:
    @staticmethod
    def _generate_installment_dates(start_date: str, count: int, plan_type: PaymentPlanType) -> list[str]:
        base = datetime.strptime(start_date, "%Y-%m-%d")
        delta_map = {
            PaymentPlanType.MONTHLY: 30,
            PaymentPlanType.QUARTERLY: 90,
            PaymentPlanType.SEMI_ANNUAL: 180,
            PaymentPlanType.ANNUAL: 365,
            PaymentPlanType.CUSTOM: 30,
        }
        days = delta_map.get(plan_type, 30)
        return [(base + timedelta(days=days * i)).strftime("%Y-%m-%d") for i in range(count)]

    @staticmethod
    async def create_contract(
        db: AsyncSession,
        company_id: int,
        data: ContractCreate,
        plan_type: PaymentPlanType = PaymentPlanType.QUARTERLY,
        down_payment: Decimal = Decimal("0"),
        installments_count: int = 8,
    ) -> Contract:
        unit_result = await db.execute(select(Unit).where(Unit.id == data.unit_id, Unit.is_deleted == False))
        unit = unit_result.scalar_one_or_none()
        if not unit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

        if data.reservation_id:
            res = await db.execute(select(Reservation).where(Reservation.id == data.reservation_id))
            reservation = res.scalar_one_or_none()
            if reservation:
                reservation.status = ReservationStatus.CONVERTED

        contract = Contract(
            company_id=company_id,
            contract_number=f"CNT-{uuid.uuid4().hex[:8].upper()}",
            customer_id=data.customer_id,
            unit_id=data.unit_id,
            reservation_id=data.reservation_id,
            total_price=data.total_price,
            contract_date=data.contract_date,
            status=ContractStatus.ACTIVE,
            contract_ar=data.contract_ar or f"عقد بيع وحدة رقم {unit.unit_number}",
            contract_en=data.contract_en or f"Sale contract for unit {unit.unit_number}",
            is_signed=False,
        )
        unit.status = UnitStatus.CONTRACTED
        unit.is_locked = True
        db.add(contract)
        await db.flush()

        remaining = data.total_price - down_payment
        installment_amount = remaining / installments_count if installments_count else remaining
        plan = PaymentPlan(
            contract_id=contract.id,
            plan_type=plan_type,
            down_payment=down_payment,
            total_amount=data.total_price,
            number_of_installments=installments_count,
            start_date=data.contract_date,
        )
        db.add(plan)
        await db.flush()

        dates = ContractService._generate_installment_dates(data.contract_date, installments_count, plan_type)
        for i, due_date in enumerate(dates, start=1):
            db.add(
                Installment(
                    payment_plan_id=plan.id,
                    installment_number=i,
                    due_date=due_date,
                    due_amount=installment_amount,
                    paid_amount=Decimal("0"),
                    remaining_balance=installment_amount,
                    status=InstallmentStatus.UPCOMING,
                )
            )
        await db.flush()
        project_id = await DynamicPricingService.get_project_id_for_unit(db, unit.id)
        if project_id:
            await DynamicPricingService.recalculate_project_prices(db, company_id, project_id)
        return contract

    @staticmethod
    async def list_contracts(db: AsyncSession, company_id: int | None) -> list[Contract]:
        query = select(Contract).where(Contract.is_deleted == False).order_by(Contract.id.desc())
        if company_id:
            query = query.where(Contract.company_id == company_id)
        result = await db.execute(query)
        return list(result.scalars().all())
