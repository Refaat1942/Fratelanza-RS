import uuid
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
from app.services.installment_calculator_service import build_schedule, money


class ContractService:

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

        schedule = build_schedule(
            total_price=data.total_price,
            down_payment=down_payment,
            plan_type=plan_type.value,
            number_of_installments=installments_count,
            start_date=data.contract_date,
        )
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

        for row in schedule["installments"]:
            due = money(Decimal(str(row["due_amount"])))
            db.add(
                Installment(
                    payment_plan_id=plan.id,
                    installment_number=row["installment_number"],
                    due_date=row["due_date"],
                    due_amount=due,
                    paid_amount=Decimal("0"),
                    remaining_balance=due,
                    is_manual=bool(row.get("is_manual", False)),
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
