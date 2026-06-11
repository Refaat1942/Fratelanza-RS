from datetime import date, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.finance import (
    CashTransaction,
    Cheque,
    ChequeStatus,
    ProgressCertificate,
    ProgressCertificateStatus,
    SubcontractAgreement,
    Subcontractor,
)
from app.models.users import User
from app.schemas.treasury import (
    CashFlowSummary,
    CashTransactionCreate,
    CashTransactionResponse,
    CashTransactionUpdate,
    ChequeCreate,
    ChequeResponse,
    ChequeUpdate,
    ProgressCertificateCalculate,
    ProgressCertificateCreate,
    ProgressCertificateResponse,
    SubcontractAgreementCreate,
    SubcontractAgreementResponse,
    SubcontractorCreate,
    SubcontractorResponse,
)
from app.services.treasury_service import TreasuryService

router = APIRouter()


def _company_id(user: User) -> int:
    if not user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    return user.company_id


# --- Cash transactions ---


@router.get("/cash-transactions/summary", response_model=CashFlowSummary)
async def cash_flow_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    return await TreasuryService.cash_flow_summary(db, _company_id(current_user))


@router.get("/cash-transactions", response_model=list[CashTransactionResponse])
async def list_cash_transactions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    transaction_type: Optional[str] = None,
):
    company_id = _company_id(current_user)
    query = select(CashTransaction).where(
        CashTransaction.company_id == company_id,
        CashTransaction.is_deleted == False,
    )
    if transaction_type:
        query = query.where(CashTransaction.transaction_type == transaction_type)
    result = await db.execute(query.order_by(CashTransaction.transaction_date.desc(), CashTransaction.id.desc()))
    return [CashTransactionResponse.model_validate(t) for t in result.scalars().all()]


@router.post("/cash-transactions", response_model=CashTransactionResponse)
async def create_cash_transaction(
    data: CashTransactionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    company_id = _company_id(current_user)
    txn = CashTransaction(company_id=company_id, created_by_id=current_user.id, **data.model_dump())
    db.add(txn)
    await db.flush()
    return CashTransactionResponse.model_validate(txn)


@router.put("/cash-transactions/{txn_id}", response_model=CashTransactionResponse)
async def update_cash_transaction(
    txn_id: int,
    data: CashTransactionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    company_id = _company_id(current_user)
    result = await db.execute(
        select(CashTransaction).where(
            CashTransaction.id == txn_id,
            CashTransaction.company_id == company_id,
            CashTransaction.is_deleted == False,
        )
    )
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(txn, field, value)
    await db.flush()
    return CashTransactionResponse.model_validate(txn)


@router.delete("/cash-transactions/{txn_id}")
async def delete_cash_transaction(
    txn_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    company_id = _company_id(current_user)
    result = await db.execute(
        select(CashTransaction).where(
            CashTransaction.id == txn_id,
            CashTransaction.company_id == company_id,
            CashTransaction.is_deleted == False,
        )
    )
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    txn.soft_delete()
    await db.flush()
    return {"message": "Transaction deleted", "success": True}


# --- Cheques ---


@router.get("/cheques", response_model=list[ChequeResponse])
async def list_cheques(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    status_filter: Optional[str] = Query(None, alias="status"),
    due_within_days: Optional[int] = None,
):
    company_id = _company_id(current_user)
    query = select(Cheque).where(Cheque.company_id == company_id, Cheque.is_deleted == False)
    if status_filter:
        query = query.where(Cheque.status == status_filter)
    if due_within_days is not None:
        today = date.today()
        limit = (today + timedelta(days=due_within_days)).isoformat()
        query = query.where(
            Cheque.due_date >= today.isoformat(),
            Cheque.due_date <= limit,
            Cheque.status == ChequeStatus.PENDING,
        )
    result = await db.execute(query.order_by(Cheque.due_date))
    return [ChequeResponse.model_validate(c) for c in result.scalars().all()]


@router.post("/cheques", response_model=ChequeResponse)
async def create_cheque(
    data: ChequeCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    company_id = _company_id(current_user)
    cheque = Cheque(company_id=company_id, **data.model_dump())
    db.add(cheque)
    await db.flush()
    return ChequeResponse.model_validate(cheque)


@router.put("/cheques/{cheque_id}", response_model=ChequeResponse)
async def update_cheque(
    cheque_id: int,
    data: ChequeUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    company_id = _company_id(current_user)
    result = await db.execute(
        select(Cheque).where(
            Cheque.id == cheque_id,
            Cheque.company_id == company_id,
            Cheque.is_deleted == False,
        )
    )
    cheque = result.scalar_one_or_none()
    if not cheque:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cheque not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cheque, field, value)
    await db.flush()
    return ChequeResponse.model_validate(cheque)


@router.delete("/cheques/{cheque_id}")
async def delete_cheque(
    cheque_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    company_id = _company_id(current_user)
    result = await db.execute(
        select(Cheque).where(
            Cheque.id == cheque_id,
            Cheque.company_id == company_id,
            Cheque.is_deleted == False,
        )
    )
    cheque = result.scalar_one_or_none()
    if not cheque:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cheque not found")
    cheque.soft_delete()
    await db.flush()
    return {"message": "Cheque deleted", "success": True}


# --- Subcontractors & agreements ---


@router.get("/subcontractors", response_model=list[SubcontractorResponse])
async def list_subcontractors(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    company_id = _company_id(current_user)
    result = await db.execute(
        select(Subcontractor)
        .where(Subcontractor.company_id == company_id, Subcontractor.is_deleted == False)
        .order_by(Subcontractor.name_en)
    )
    return [SubcontractorResponse.model_validate(s) for s in result.scalars().all()]


@router.post("/subcontractors", response_model=SubcontractorResponse)
async def create_subcontractor(
    data: SubcontractorCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    company_id = _company_id(current_user)
    sub = Subcontractor(company_id=company_id, **data.model_dump())
    db.add(sub)
    await db.flush()
    return SubcontractorResponse.model_validate(sub)


@router.get("/subcontract-agreements", response_model=list[SubcontractAgreementResponse])
async def list_agreements(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    company_id = _company_id(current_user)
    result = await db.execute(
        select(SubcontractAgreement)
        .options(selectinload(SubcontractAgreement.subcontractor))
        .where(SubcontractAgreement.company_id == company_id)
        .order_by(SubcontractAgreement.id.desc())
    )
    rows = []
    for a in result.scalars().all():
        resp = SubcontractAgreementResponse.model_validate(a)
        rows.append(
            resp.model_copy(
                update={"subcontractor_name": a.subcontractor.name_en if a.subcontractor else None}
            )
        )
    return rows


@router.post("/subcontract-agreements", response_model=SubcontractAgreementResponse)
async def create_agreement(
    data: SubcontractAgreementCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    company_id = _company_id(current_user)
    sub = (
        await db.execute(
            select(Subcontractor).where(
                Subcontractor.id == data.subcontractor_id,
                Subcontractor.company_id == company_id,
            )
        )
    ).scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subcontractor not found")
    agreement = SubcontractAgreement(company_id=company_id, **data.model_dump())
    db.add(agreement)
    await db.flush()
    return SubcontractAgreementResponse.model_validate(agreement).model_copy(
        update={"subcontractor_name": sub.name_en}
    )


# --- Progress certificates (مستخلصات) ---


@router.post("/progress-certificates/calculate")
async def calculate_progress_certificate(
    data: ProgressCertificateCalculate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    company_id = _company_id(current_user)
    agreement = (
        await db.execute(
            select(SubcontractAgreement).where(
                SubcontractAgreement.id == data.agreement_id,
                SubcontractAgreement.company_id == company_id,
            )
        )
    ).scalar_one_or_none()
    if not agreement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found")
    calc = await TreasuryService.calculate_for_agreement(
        db, agreement, data.progress_percent, data.other_deductions
    )
    return {k: float(v) for k, v in calc.items()}


@router.get("/progress-certificates", response_model=list[ProgressCertificateResponse])
async def list_progress_certificates(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    agreement_id: Optional[int] = None,
):
    company_id = _company_id(current_user)
    query = (
        select(ProgressCertificate)
        .options(selectinload(ProgressCertificate.agreement).selectinload(SubcontractAgreement.subcontractor))
        .where(ProgressCertificate.company_id == company_id)
    )
    if agreement_id:
        query = query.where(ProgressCertificate.agreement_id == agreement_id)
    result = await db.execute(query.order_by(ProgressCertificate.id.desc()))
    rows = []
    for cert in result.scalars().all():
        resp = ProgressCertificateResponse.model_validate(cert)
        agreement = cert.agreement
        rows.append(
            resp.model_copy(
                update={
                    "subcontractor_name": agreement.subcontractor.name_en if agreement and agreement.subcontractor else None,
                    "contract_number": agreement.contract_number if agreement else None,
                }
            )
        )
    return rows


@router.post("/progress-certificates", response_model=ProgressCertificateResponse)
async def create_progress_certificate(
    data: ProgressCertificateCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    company_id = _company_id(current_user)
    agreement = (
        await db.execute(
            select(SubcontractAgreement)
            .options(selectinload(SubcontractAgreement.subcontractor))
            .where(
                SubcontractAgreement.id == data.agreement_id,
                SubcontractAgreement.company_id == company_id,
            )
        )
    ).scalar_one_or_none()
    if not agreement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found")
    calc = await TreasuryService.calculate_for_agreement(
        db, agreement, data.progress_percent, data.other_deductions
    )
    cert = ProgressCertificate(
        company_id=company_id,
        agreement_id=data.agreement_id,
        certificate_number=data.certificate_number,
        period_from=data.period_from,
        period_to=data.period_to,
        progress_percent=data.progress_percent,
        cumulative_value=calc["cumulative_value"],
        current_gross=calc["current_gross"],
        retention_amount=calc["retention_amount"],
        advance_deduction=calc["advance_deduction"],
        other_deductions=data.other_deductions,
        net_payable=calc["net_payable"],
        notes=data.notes,
    )
    db.add(cert)
    await db.flush()
    return ProgressCertificateResponse.model_validate(cert).model_copy(
        update={
            "subcontractor_name": agreement.subcontractor.name_en if agreement.subcontractor else None,
            "contract_number": agreement.contract_number,
        }
    )


@router.post("/progress-certificates/{cert_id}/approve", response_model=ProgressCertificateResponse)
async def approve_progress_certificate(
    cert_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    company_id = _company_id(current_user)
    cert = (
        await db.execute(
            select(ProgressCertificate)
            .options(selectinload(ProgressCertificate.agreement).selectinload(SubcontractAgreement.subcontractor))
            .where(ProgressCertificate.id == cert_id, ProgressCertificate.company_id == company_id)
        )
    ).scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
    cert.status = ProgressCertificateStatus.APPROVED
    cert.approved_by_id = current_user.id
    await db.flush()
    agreement = cert.agreement
    return ProgressCertificateResponse.model_validate(cert).model_copy(
        update={
            "subcontractor_name": agreement.subcontractor.name_en if agreement and agreement.subcontractor else None,
            "contract_number": agreement.contract_number if agreement else None,
        }
    )


@router.post("/progress-certificates/{cert_id}/pay", response_model=ProgressCertificateResponse)
async def pay_progress_certificate(
    cert_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    company_id = _company_id(current_user)
    cert = (
        await db.execute(
            select(ProgressCertificate)
            .options(selectinload(ProgressCertificate.agreement).selectinload(SubcontractAgreement.subcontractor))
            .where(ProgressCertificate.id == cert_id, ProgressCertificate.company_id == company_id)
        )
    ).scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
    if cert.status not in (ProgressCertificateStatus.APPROVED, ProgressCertificateStatus.SUBMITTED):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Certificate must be approved first")
    cert.status = ProgressCertificateStatus.PAID
    cert.paid_at = date.today().isoformat()
    await TreasuryService.create_expense_from_certificate(db, company_id, cert, current_user.id, cert.paid_at)
    await db.flush()
    agreement = cert.agreement
    return ProgressCertificateResponse.model_validate(cert).model_copy(
        update={
            "subcontractor_name": agreement.subcontractor.name_en if agreement and agreement.subcontractor else None,
            "contract_number": agreement.contract_number if agreement else None,
        }
    )
