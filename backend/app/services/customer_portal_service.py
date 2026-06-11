from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.construction import ConstructionPhase, ProjectProgressUpdate
from app.models.customers import Customer
from app.models.real_estate import Building, Floor, Project, Unit
from app.models.sales import Contract, Installment, Payment, PaymentPlan
from app.models.users import SystemRole, User


class CustomerPortalService:
    @staticmethod
    async def resolve_customer(db: AsyncSession, user: User) -> Customer:
        if user.system_role != SystemRole.CUSTOMER and not user.is_super_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer access only")
        if user.is_super_admin:
            demo = (
                await db.execute(select(Customer).order_by(Customer.id).limit(1))
            ).scalar_one_or_none()
            if demo:
                return demo
        customer = (
            await db.execute(select(Customer).where(Customer.user_id == user.id))
        ).scalar_one_or_none()
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer profile not found")
        return customer

    @staticmethod
    async def customer_project_ids(db: AsyncSession, customer_id: int) -> set[int]:
        contracts = (
            await db.execute(
                select(Contract)
                .options(
                    selectinload(Contract.payment_plan),
                )
                .where(Contract.customer_id == customer_id, Contract.is_deleted == False)
            )
        ).scalars().all()
        project_ids: set[int] = set()
        for contract in contracts:
            unit = (
                await db.execute(
                    select(Unit)
                    .options(selectinload(Unit.floor).selectinload(Floor.building))
                    .where(Unit.id == contract.unit_id)
                )
            ).scalar_one_or_none()
            if unit and unit.floor and unit.floor.building:
                project_ids.add(unit.floor.building.project_id)
        return project_ids

    @staticmethod
    async def get_dashboard(db: AsyncSession, customer: Customer) -> dict:
        contracts = (
            await db.execute(
                select(Contract, Unit)
                .join(Unit, Contract.unit_id == Unit.id)
                .where(Contract.customer_id == customer.id, Contract.is_deleted == False)
            )
        ).all()

        contract_rows = []
        total_remaining = 0.0
        total_paid = 0.0
        upcoming_count = 0

        for contract, unit in contracts:
            plan = (
                await db.execute(select(PaymentPlan).where(PaymentPlan.contract_id == contract.id))
            ).scalar_one_or_none()
            remaining = 0.0
            if plan:
                insts = (
                    await db.execute(
                        select(Installment).where(Installment.payment_plan_id == plan.id)
                    )
                ).scalars().all()
                for inst in insts:
                    rem = float(inst.remaining_balance)
                    remaining += rem
                    total_paid += float(inst.paid_amount)
                    if inst.status.value in ("upcoming", "due", "overdue", "partial"):
                        upcoming_count += 1

            total_remaining += remaining
            contract_rows.append(
                {
                    "id": contract.id,
                    "contract_number": contract.contract_number,
                    "unit_code": unit.unit_code,
                    "total_price": float(contract.total_price),
                    "remaining_balance": remaining,
                    "status": contract.status.value,
                    "is_signed": contract.is_signed,
                }
            )

        payments_count = (
            await db.execute(
                select(Payment).where(Payment.customer_id == customer.id)
            )
        ).scalars().all()

        project_ids = await CustomerPortalService.customer_project_ids(db, customer.id)
        phases = []
        if project_ids:
            phase_rows = (
                await db.execute(
                    select(ConstructionPhase, Project)
                    .join(Project, ConstructionPhase.project_id == Project.id)
                    .where(ConstructionPhase.project_id.in_(project_ids))
                )
            ).all()
            for phase, project in phase_rows:
                phases.append(
                    {
                        "project_name_en": project.name_en,
                        "project_name_ar": project.name_ar,
                        "phase_name_en": phase.name_en,
                        "phase_name_ar": phase.name_ar,
                        "progress_percent": phase.progress_percent,
                    }
                )

        return {
            "customer": {
                "id": customer.id,
                "name_ar": customer.full_name_ar,
                "name_en": customer.full_name_en,
                "mobile": customer.mobile,
                "email": customer.email,
            },
            "summary": {
                "contracts_count": len(contract_rows),
                "total_remaining": total_remaining,
                "total_paid": total_paid,
                "upcoming_installments": upcoming_count,
                "receipts_count": len(payments_count),
            },
            "contracts": contract_rows,
            "construction_phases": phases,
        }

    @staticmethod
    async def list_installments(db: AsyncSession, customer: Customer) -> list[dict]:
        rows: list[dict] = []
        contracts = (
            await db.execute(
                select(Contract, Unit)
                .join(Unit, Contract.unit_id == Unit.id)
                .where(Contract.customer_id == customer.id, Contract.is_deleted == False)
            )
        ).all()
        for contract, unit in contracts:
            plan = (
                await db.execute(select(PaymentPlan).where(PaymentPlan.contract_id == contract.id))
            ).scalar_one_or_none()
            if not plan:
                continue
            insts = (
                await db.execute(
                    select(Installment)
                    .where(Installment.payment_plan_id == plan.id)
                    .order_by(Installment.installment_number)
                )
            ).scalars().all()
            for inst in insts:
                rows.append(
                    {
                        "id": inst.id,
                        "contract_number": contract.contract_number,
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

    @staticmethod
    async def list_payments(db: AsyncSession, customer: Customer) -> list[dict]:
        result = await db.execute(
            select(Payment, Installment, Contract)
            .join(Installment, Payment.installment_id == Installment.id)
            .join(PaymentPlan, Installment.payment_plan_id == PaymentPlan.id)
            .join(Contract, PaymentPlan.contract_id == Contract.id)
            .where(Payment.customer_id == customer.id)
            .order_by(Payment.payment_date.desc())
        )
        rows = []
        for payment, inst, contract in result.all():
            rows.append(
                {
                    "id": payment.id,
                    "receipt_number": payment.reference_number or f"RCP-{payment.id:05d}",
                    "contract_number": contract.contract_number,
                    "installment_number": inst.installment_number,
                    "amount": float(payment.amount),
                    "payment_date": payment.payment_date,
                    "payment_method": payment.payment_method,
                    "notes": payment.notes,
                }
            )
        return rows

    @staticmethod
    async def list_progress_updates(db: AsyncSession, customer: Customer) -> list[dict]:
        project_ids = await CustomerPortalService.customer_project_ids(db, customer.id)
        if not project_ids:
            return []
        updates = (
            await db.execute(
                select(ProjectProgressUpdate, Project)
                .join(Project, ProjectProgressUpdate.project_id == Project.id)
                .where(
                    ProjectProgressUpdate.project_id.in_(project_ids),
                    ProjectProgressUpdate.is_published == True,
                )
                .order_by(ProjectProgressUpdate.published_at.desc())
            )
        ).all()
        return [
            {
                "id": u.id,
                "project_name_en": p.name_en,
                "project_name_ar": p.name_ar,
                "title_en": u.title_en,
                "title_ar": u.title_ar,
                "description_en": u.description_en,
                "description_ar": u.description_ar,
                "media_type": u.media_type,
                "media_url": u.media_url,
                "thumbnail_url": u.thumbnail_url,
                "progress_percent": u.progress_percent,
                "published_at": u.published_at,
            }
            for u, p in updates
        ]
