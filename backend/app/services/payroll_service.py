"""Payroll generation and salary payments (extends the existing HR payroll runs).

Posting: generating a run accrues salaries (Dr 5300 Salaries expense / Cr 2400 Salaries payable,
source ``payroll_run``); each payment settles the liability (Dr 2400 / Cr 1100, source
``payroll_payment``). Both are unique per source so a run is never posted twice.
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hr import Employee, PayrollRun, Payslip
from app.models.rentals import PayrollPayment
from app.services import accounting_service as acc
from app.services.accounting_service import AccountingService

SOCIAL_INSURANCE_RATE = Decimal("0.11")
ZERO = Decimal("0")


class PayrollService:
    @staticmethod
    async def generate(db: AsyncSession, company_id: int, period_month: str, user_id: Optional[int]) -> PayrollRun:
        existing = (
            await db.execute(
                select(PayrollRun).where(PayrollRun.company_id == company_id, PayrollRun.period_month == period_month)
            )
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payroll already generated for this month")
        employees = (
            await db.execute(
                select(Employee).where(
                    Employee.company_id == company_id, Employee.is_active == True, Employee.is_deleted == False  # noqa: E712
                )
            )
        ).scalars().all()
        run = PayrollRun(company_id=company_id, period_month=period_month, status="processed", created_by_id=user_id)
        db.add(run)
        await db.flush()
        total_gross = total_deductions = total_net = ZERO
        for emp in employees:
            basic = Decimal(str(emp.salary or 0))
            social = (basic * SOCIAL_INSURANCE_RATE).quantize(Decimal("0.01"))
            net = basic - social
            total_gross += basic
            total_deductions += social
            total_net += net
            db.add(Payslip(payroll_run_id=run.id, employee_id=emp.id, basic_salary=basic, allowances=ZERO,
                           social_insurance=social, deductions=social, net_salary=net, paid_amount=ZERO, status="processed"))
        run.total_gross, run.total_deductions, run.total_net = total_gross, total_deductions, total_net
        await db.flush()
        if total_gross > 0:
            await AccountingService.post(
                db, company_id, source_type="payroll_run", source_id=run.id,
                entry_date=date.fromisoformat(f"{period_month}-01"), description=f"Payroll {period_month}",
                lines=[
                    (acc.SALARIES_EXPENSE, total_gross, ZERO),
                    (acc.SALARIES_PAYABLE, ZERO, total_net),
                    (acc.SOCIAL_INSURANCE_PAYABLE, ZERO, total_deductions),
                ],
                created_by_id=user_id,
            )
        return run

    @staticmethod
    async def pay(
        db: AsyncSession, payslip: Payslip, amount: Decimal, paid_on: date, method: str, reference: Optional[str],
        user_id: Optional[int],
    ) -> PayrollPayment:
        run = (await db.execute(select(PayrollRun).where(PayrollRun.id == payslip.payroll_run_id))).scalar_one()
        amount = Decimal(str(amount)).quantize(Decimal("0.01"))
        remaining = Decimal(str(payslip.net_salary)) - Decimal(str(payslip.paid_amount or 0))
        if amount <= 0 or amount > remaining:
            raise HTTPException(status_code=400, detail=f"Amount must be within outstanding salary ({remaining})")
        payment = PayrollPayment(company_id=run.company_id, payslip_id=payslip.id, amount=amount, paid_on=paid_on,
                                 method=method, reference=reference, paid_by_id=user_id)
        db.add(payment)
        payslip.paid_amount = Decimal(str(payslip.paid_amount or 0)) + amount
        payslip.status = "paid" if payslip.paid_amount >= Decimal(str(payslip.net_salary)) else "partially_paid"
        await db.flush()
        await AccountingService.post(
            db, run.company_id, source_type="payroll_payment", source_id=payment.id, entry_date=paid_on,
            description=f"Salary payment — payslip #{payslip.id}",
            lines=[(acc.SALARIES_PAYABLE, amount, ZERO), (acc.CASH, ZERO, amount)], created_by_id=user_id,
        )
        return payment
