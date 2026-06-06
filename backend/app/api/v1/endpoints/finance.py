from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.finance import BankAccount, ChartOfAccount, JournalEntry, JournalLine
from app.models.users import User

router = APIRouter()


class AccountCreate(BaseModel):
    code: str
    name_ar: str
    name_en: str
    account_type: str


@router.get("/accounts")
async def list_accounts(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    result = await db.execute(
        select(ChartOfAccount).where(ChartOfAccount.company_id == current_user.company_id)
    )
    accounts = result.scalars().all()
    return [
        {"id": a.id, "code": a.code, "name_ar": a.name_ar, "name_en": a.name_en, "account_type": a.account_type}
        for a in accounts
    ]


@router.post("/accounts")
async def create_account(
    data: AccountCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    account = ChartOfAccount(company_id=current_user.company_id, **data.model_dump())
    db.add(account)
    await db.flush()
    return {"id": account.id, "code": account.code}


@router.get("/bank-accounts")
async def list_bank_accounts(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    result = await db.execute(
        select(BankAccount).where(BankAccount.company_id == current_user.company_id)
    )
    accounts = result.scalars().all()
    return [
        {
            "id": a.id,
            "bank_name": a.bank_name,
            "account_number": a.account_number,
            "balance": float(a.balance),
            "currency": a.currency,
        }
        for a in accounts
    ]


@router.get("/journal-entries")
async def list_journal_entries(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    result = await db.execute(
        select(JournalEntry).where(JournalEntry.company_id == current_user.company_id).order_by(JournalEntry.id.desc())
    )
    entries = result.scalars().all()
    return [
        {"id": e.id, "entry_number": e.entry_number, "entry_date": e.entry_date, "description": e.description}
        for e in entries
    ]
