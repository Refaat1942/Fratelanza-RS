"""Double-entry postings for property-management operations.

Each operational record posts at most one journal entry per ``source_type`` — enforced by the
unique constraint ``uq_journal_entry_source (company_id, source_type, source_id)`` — so retries
and double clicks can never double-post. Rules are documented in docs/IMPLEMENTATION_PLAN.md
("Accounting rules").
"""

import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import ChartOfAccount, JournalEntry, JournalLine

# code: (name_ar, name_en, type)
SYSTEM_ACCOUNTS: dict[str, tuple[str, str, str]] = {
    "1100": ("النقدية والبنوك", "Cash & Bank", "asset"),
    "2100": ("مستحقات الملاك (أموال محصلة لصالح الملاك)", "Owner payables (funds held for owners)", "liability"),
    "2200": ("تأمينات المستأجرين", "Tenant security deposits", "liability"),
    "2300": ("الموردون والمصروفات المستحقة", "Accounts payable", "liability"),
    "2400": ("رواتب مستحقة", "Salaries payable", "liability"),
    "2500": ("تأمينات اجتماعية مستحقة", "Social insurance payable", "liability"),
    "4100": ("إيرادات إيجار وحدات مملوكة للشركة", "Rental income (company-owned units)", "revenue"),
    "4200": ("إيرادات عمولة إدارة الأملاك", "Property management commission income", "revenue"),
    "5100": ("مصروفات صيانة العقارات", "Property maintenance expense", "expense"),
    "5200": ("مصروفات إدارية وعمومية", "Administrative expenses", "expense"),
    "5300": ("مصروف الرواتب والأجور", "Salaries expense", "expense"),
}

CASH = "1100"
OWNER_PAYABLE = "2100"
DEPOSITS = "2200"
ACCOUNTS_PAYABLE = "2300"
SALARIES_PAYABLE = "2400"
SOCIAL_INSURANCE_PAYABLE = "2500"
RENTAL_INCOME = "4100"
COMMISSION_INCOME = "4200"
MAINTENANCE_EXPENSE = "5100"
ADMIN_EXPENSE = "5200"
SALARIES_EXPENSE = "5300"


class AccountingService:
    @staticmethod
    async def ensure_account(db: AsyncSession, company_id: int, code: str) -> ChartOfAccount:
        account = (
            await db.execute(
                select(ChartOfAccount).where(ChartOfAccount.company_id == company_id, ChartOfAccount.code == code)
            )
        ).scalars().first()
        if account:
            return account
        name_ar, name_en, account_type = SYSTEM_ACCOUNTS[code]
        account = ChartOfAccount(
            company_id=company_id, code=code, name_ar=name_ar, name_en=name_en, account_type=account_type
        )
        db.add(account)
        await db.flush()
        return account

    @staticmethod
    async def find(db: AsyncSession, company_id: int, source_type: str, source_id: int) -> Optional[JournalEntry]:
        return (
            await db.execute(
                select(JournalEntry).where(
                    JournalEntry.company_id == company_id,
                    JournalEntry.source_type == source_type,
                    JournalEntry.source_id == source_id,
                )
            )
        ).scalar_one_or_none()

    @staticmethod
    async def post(
        db: AsyncSession,
        company_id: int,
        *,
        source_type: str,
        source_id: Optional[int],
        entry_date: date,
        description: str,
        lines: list[tuple[str, Decimal, Decimal]],
        created_by_id: Optional[int] = None,
    ) -> JournalEntry:
        """Post a balanced entry. Returns the existing entry if this source was already posted."""
        if source_id is not None:
            existing = await AccountingService.find(db, company_id, source_type, source_id)
            if existing:
                return existing
        total_debit = sum((d for _, d, _ in lines), Decimal("0"))
        total_credit = sum((c for _, _, c in lines), Decimal("0"))
        if total_debit != total_credit or total_debit <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unbalanced journal entry")
        entry = JournalEntry(
            company_id=company_id,
            entry_number=f"JE-{uuid.uuid4().hex[:10].upper()}",
            entry_date=entry_date.isoformat(),
            description=description,
            created_by_id=created_by_id,
            source_type=source_type,
            source_id=source_id,
        )
        db.add(entry)
        await db.flush()
        for code, debit, credit in lines:
            account = await AccountingService.ensure_account(db, company_id, code)
            db.add(JournalLine(journal_entry_id=entry.id, account_id=account.id, debit=debit, credit=credit))
        await db.flush()
        return entry
