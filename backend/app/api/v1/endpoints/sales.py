from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.rbac import Permission, ROLE_PERMISSIONS
from app.db.session import get_db
from app.models import (
    Contract,
    ContractStatus,
    Installment,
    Lead,
    Reservation,
    ReservationStatus,
    Unit,
    UnitStatus,
    User,
)
from app.schemas import (
    ContractCreate,
    ContractRead,
    InstallmentRead,
    LeadCreate,
    LeadRead,
    ReservationCreate,
    ReservationRead,
)

router = APIRouter()


def _scope_company(current_user: User, requested_company_id: str | None = None) -> str | None:
    if Permission.PLATFORM_ALL in ROLE_PERMISSIONS[current_user.role]:
        return requested_company_id
    return current_user.company_id


@router.get("/leads", response_model=list[LeadRead])
def list_leads(
    company_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CRM_MANAGE)),
) -> list[Lead]:
    query = select(Lead).order_by(Lead.created_at.desc())
    scoped_company_id = _scope_company(current_user, company_id)
    if scoped_company_id:
        query = query.where(Lead.company_id == scoped_company_id)
    return list(db.scalars(query.limit(200)))


@router.post("/leads", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
def create_lead(
    payload: LeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CRM_MANAGE)),
) -> Lead:
    lead = Lead(company_id=current_user.company_id, **payload.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/reservations", response_model=list[ReservationRead])
def list_reservations(
    company_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.RESERVATIONS_MANAGE)),
) -> list[Reservation]:
    query = select(Reservation).order_by(Reservation.created_at.desc())
    scoped_company_id = _scope_company(current_user, company_id)
    if scoped_company_id:
        query = query.where(Reservation.company_id == scoped_company_id)
    return list(db.scalars(query.limit(200)))


@router.post("/reservations", response_model=ReservationRead, status_code=status.HTTP_201_CREATED)
def create_reservation(
    payload: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.RESERVATIONS_MANAGE)),
) -> Reservation:
    unit = db.get(Unit, payload.unit_id)
    if unit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    if Permission.PLATFORM_ALL not in ROLE_PERMISSIONS[current_user.role]:
        if unit.company_id != current_user.company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid tenant scope")
    if unit.status != UnitStatus.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unit is not available for reservation",
        )

    reservation = Reservation(
        company_id=unit.company_id,
        status=ReservationStatus.PENDING_APPROVAL,
        **payload.model_dump(),
    )
    unit.status = UnitStatus.RESERVED
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


@router.get("/contracts", response_model=list[ContractRead])
def list_contracts(
    company_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CONTRACTS_MANAGE)),
) -> list[Contract]:
    query = select(Contract).order_by(Contract.created_at.desc())
    scoped_company_id = _scope_company(current_user, company_id)
    if scoped_company_id:
        query = query.where(Contract.company_id == scoped_company_id)
    return list(db.scalars(query.limit(200)))


@router.post("/contracts", response_model=ContractRead, status_code=status.HTTP_201_CREATED)
def create_contract(
    payload: ContractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CONTRACTS_MANAGE)),
) -> Contract:
    unit = db.get(Unit, payload.unit_id)
    if unit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    if Permission.PLATFORM_ALL not in ROLE_PERMISSIONS[current_user.role]:
        if unit.company_id != current_user.company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid tenant scope")

    reservation = db.get(Reservation, payload.reservation_id) if payload.reservation_id else None
    if reservation and reservation.unit_id != unit.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reservation unit mismatch")

    contract = Contract(
        company_id=unit.company_id,
        status=ContractStatus.ACTIVE,
        **payload.model_dump(),
    )
    unit.status = UnitStatus.CONTRACTED
    if reservation:
        reservation.status = ReservationStatus.CONVERTED_TO_CONTRACT
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


@router.get("/installments", response_model=list[InstallmentRead])
def list_installments(
    contract_id: str | None = None,
    company_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.COLLECTIONS_MANAGE)),
) -> list[Installment]:
    query = select(Installment).order_by(Installment.due_date)
    scoped_company_id = _scope_company(current_user, company_id)
    if scoped_company_id:
        query = query.where(Installment.company_id == scoped_company_id)
    if contract_id:
        query = query.where(Installment.contract_id == contract_id)
    return list(db.scalars(query.limit(500)))
