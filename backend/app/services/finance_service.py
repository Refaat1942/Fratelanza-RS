from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import BankAccount, ChartOfAccount, JournalEntry, JournalLine
from app.models.sales import Contract, Installment, Payment, PaymentPlan


class FinanceService:
    @staticmethod
    async def trial_balance(db: AsyncSession, company_id: int) -> list[dict]:
        accounts = (
            await db.execute(select(ChartOfAccount).where(ChartOfAccount.company_id == company_id))
        ).scalars().all()
        lines_q = (
            select(JournalLine.account_id, func.sum(JournalLine.debit), func.sum(JournalLine.credit))
            .join(JournalEntry, JournalLine.journal_entry_id == JournalEntry.id)
            .where(JournalEntry.company_id == company_id)
            .group_by(JournalLine.account_id)
        )
        totals = {row[0]: (float(row[1] or 0), float(row[2] or 0)) for row in (await db.execute(lines_q)).all()}
        rows = []
        for acc in accounts:
            debit, credit = totals.get(acc.id, (0.0, 0.0))
            balance = debit - credit
            rows.append({
                "account_code": acc.code,
                "account_name": acc.name_en,
                "account_type": acc.account_type,
                "debit": round(debit, 2),
                "credit": round(credit, 2),
                "balance": round(balance, 2),
            })
        return rows

    @staticmethod
    async def profit_loss_summary(db: AsyncSession, company_id: int) -> list[dict]:
        contracts = (
            await db.execute(
                select(func.sum(Contract.total_price)).where(
                    Contract.company_id == company_id, Contract.is_deleted == False
                )
            )
        ).scalar() or Decimal("0")
        collected = (
            await db.execute(
                select(func.sum(Payment.amount)).where(Payment.company_id == company_id)
            )
        ).scalar() or Decimal("0")
        from app.models.sales import InstallmentStatus
        overdue = (
            await db.execute(
                select(func.sum(Installment.remaining_balance))
                .join(PaymentPlan, Installment.payment_plan_id == PaymentPlan.id)
                .join(Contract, PaymentPlan.contract_id == Contract.id)
                .where(
                    Contract.company_id == company_id,
                    Installment.status == InstallmentStatus.OVERDUE,
                )
            )
        ).scalar() or Decimal("0")
        return [
            {"line_item": "Total Contracted Sales", "amount_egp": float(contracts), "category": "revenue"},
            {"line_item": "Collections Received", "amount_egp": float(collected), "category": "cash_in"},
            {"line_item": "Outstanding Overdue", "amount_egp": float(overdue), "category": "receivable"},
            {"line_item": "Net Cash Position", "amount_egp": float(collected), "category": "summary"},
        ]

    @staticmethod
    async def cash_position(db: AsyncSession, company_id: int) -> list[dict]:
        banks = (
            await db.execute(select(BankAccount).where(BankAccount.company_id == company_id))
        ).scalars().all()
        rows = []
        for b in banks:
            rows.append({
                "bank_name": b.bank_name,
                "account_number": b.account_number,
                "currency": b.currency or "EGP",
                "balance_egp": float(b.balance),
            })
        if not rows:
            collected = (
                await db.execute(
                    select(func.sum(Payment.amount)).where(Payment.company_id == company_id)
                )
            ).scalar() or Decimal("0")
            rows.append({
                "bank_name": "Treasury / Cash",
                "account_number": "-",
                "currency": "EGP",
                "balance_egp": float(collected),
            })
        return rows

    @staticmethod
    async def journal_register(db: AsyncSession, company_id: int) -> list[dict]:
        entries = (
            await db.execute(
                select(JournalEntry).where(JournalEntry.company_id == company_id).order_by(JournalEntry.id.desc())
            )
        ).scalars().all()
        rows = []
        for e in entries:
            lines = (
                await db.execute(select(JournalLine).where(JournalLine.journal_entry_id == e.id))
            ).scalars().all()
            for line in lines:
                acc = (
                    await db.execute(select(ChartOfAccount).where(ChartOfAccount.id == line.account_id))
                ).scalar_one_or_none()
                rows.append({
                    "entry_number": e.entry_number,
                    "entry_date": e.entry_date,
                    "description": e.description or "",
                    "account_code": acc.code if acc else "",
                    "account_name": acc.name_en if acc else "",
                    "debit": float(line.debit),
                    "credit": float(line.credit),
                })
        return rows
