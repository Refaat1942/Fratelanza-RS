from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import (
    CashTransaction,
    CashTransactionType,
    Cheque,
    ChequeStatus,
    ProgressCertificate,
    ProgressCertificateStatus,
    SubcontractAgreement,
)


class TreasuryService:
    @staticmethod
    async def cash_flow_summary(db: AsyncSession, company_id: int) -> dict:
        income = (
            await db.execute(
                select(func.coalesce(func.sum(CashTransaction.amount), 0)).where(
                    CashTransaction.company_id == company_id,
                    CashTransaction.is_deleted == False,
                    CashTransaction.transaction_type == CashTransactionType.INCOME,
                )
            )
        ).scalar() or Decimal(0)
        expense = (
            await db.execute(
                select(func.coalesce(func.sum(CashTransaction.amount), 0)).where(
                    CashTransaction.company_id == company_id,
                    CashTransaction.is_deleted == False,
                    CashTransaction.transaction_type == CashTransactionType.EXPENSE,
                )
            )
        ).scalar() or Decimal(0)
        count = (
            await db.execute(
                select(func.count()).select_from(CashTransaction).where(
                    CashTransaction.company_id == company_id,
                    CashTransaction.is_deleted == False,
                )
            )
        ).scalar() or 0
        return {
            "total_income": float(income),
            "total_expense": float(expense),
            "net_cash_flow": float(income - expense),
            "transaction_count": count,
        }

    @staticmethod
    async def get_previous_cumulative_gross(
        db: AsyncSession, agreement_id: int, exclude_cert_id: Optional[int] = None
    ) -> Decimal:
        query = select(func.coalesce(func.sum(ProgressCertificate.current_gross), 0)).where(
            ProgressCertificate.agreement_id == agreement_id,
            ProgressCertificate.status.in_(
                [ProgressCertificateStatus.APPROVED, ProgressCertificateStatus.PAID]
            ),
        )
        if exclude_cert_id:
            query = query.where(ProgressCertificate.id != exclude_cert_id)
        return (await db.execute(query)).scalar() or Decimal(0)

    @staticmethod
    async def get_advance_recovered(db: AsyncSession, agreement_id: int) -> Decimal:
        return (
            await db.execute(
                select(func.coalesce(func.sum(ProgressCertificate.advance_deduction), 0)).where(
                    ProgressCertificate.agreement_id == agreement_id,
                    ProgressCertificate.status.in_(
                        [ProgressCertificateStatus.APPROVED, ProgressCertificateStatus.PAID]
                    ),
                )
            )
        ).scalar() or Decimal(0)

    @staticmethod
    def calculate_progress_billing(
        contract_value: Decimal,
        retention_percent: Decimal,
        advance_payment: Decimal,
        progress_percent: int,
        previous_cumulative_gross: Decimal,
        advance_recovered: Decimal,
        other_deductions: Decimal = Decimal(0),
    ) -> dict:
        cumulative = (contract_value * Decimal(progress_percent) / Decimal(100)).quantize(Decimal("0.01"))
        current_gross = max(cumulative - previous_cumulative_gross, Decimal(0))
        retention_amount = (current_gross * retention_percent / Decimal(100)).quantize(Decimal("0.01"))
        total_advance_due = (advance_payment * Decimal(progress_percent) / Decimal(100)).quantize(Decimal("0.01"))
        advance_deduction = min(
            max(total_advance_due - advance_recovered, Decimal(0)),
            current_gross,
        ).quantize(Decimal("0.01"))
        net_payable = max(
            current_gross - retention_amount - advance_deduction - other_deductions,
            Decimal(0),
        ).quantize(Decimal("0.01"))
        return {
            "cumulative_value": cumulative,
            "current_gross": current_gross,
            "retention_amount": retention_amount,
            "advance_deduction": advance_deduction,
            "net_payable": net_payable,
        }

    @staticmethod
    async def calculate_for_agreement(
        db: AsyncSession,
        agreement: SubcontractAgreement,
        progress_percent: int,
        other_deductions: Decimal = Decimal(0),
        exclude_cert_id: Optional[int] = None,
    ) -> dict:
        previous = await TreasuryService.get_previous_cumulative_gross(db, agreement.id, exclude_cert_id)
        recovered = await TreasuryService.get_advance_recovered(db, agreement.id)
        return TreasuryService.calculate_progress_billing(
            agreement.contract_value,
            agreement.retention_percent,
            agreement.advance_payment,
            progress_percent,
            previous,
            recovered,
            other_deductions,
        )

    @staticmethod
    async def create_expense_from_certificate(
        db: AsyncSession,
        company_id: int,
        certificate: ProgressCertificate,
        user_id: Optional[int],
        payment_date: str,
    ) -> CashTransaction:
        txn = CashTransaction(
            company_id=company_id,
            transaction_date=payment_date,
            transaction_type=CashTransactionType.EXPENSE,
            category="subcontractor_payment",
            description=f"Progress certificate {certificate.certificate_number}",
            amount=certificate.net_payable,
            payment_method="bank_transfer",
            reference_number=certificate.certificate_number,
            created_by_id=user_id,
        )
        db.add(txn)
        await db.flush()
        return txn
