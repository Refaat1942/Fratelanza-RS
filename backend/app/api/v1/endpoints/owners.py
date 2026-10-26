"""Property owners and owner settlements (module ``owners``)."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import company_id_of, get_access, get_company_user, log_audit
from app.core.database import get_db
from app.core.tenant import get_owned, mask
from app.models.real_estate import Unit
from app.models.rentals import (
    SETTLEMENT_FREQUENCIES,
    OwnerSettlement,
    OwnerSettlementPayment,
    PropertyOwner,
)
from app.models.users import User
from app.services.access_service import AccessContext, AccessService
from app.services.rental_service import company_today
from app.services.settlement_service import SettlementService, next_settlement

router = APIRouter()


class OwnerIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    code: Optional[str] = Field(default=None, max_length=50)
    mobile: Optional[str] = None
    email: Optional[EmailStr] = None
    national_id: Optional[str] = None
    address: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    iban: Optional[str] = None
    settlement_frequency: str = "monthly"
    commission_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    settlement_day: int = Field(default=5, ge=0, le=60)
    notes: Optional[str] = None


class OwnerUpdate(BaseModel):
    full_name: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[EmailStr] = None
    national_id: Optional[str] = None
    address: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    iban: Optional[str] = None
    settlement_frequency: Optional[str] = None
    commission_rate: Optional[Decimal] = Field(default=None, ge=0, le=100)
    settlement_day: Optional[int] = Field(default=None, ge=0, le=60)
    notes: Optional[str] = None


class SettlementIn(BaseModel):
    owner_id: int
    period_start: date
    period_end: date
    adjustments: Decimal = Decimal("0")
    adjustments_note: Optional[str] = None


class SettlementPaymentIn(BaseModel):
    amount: Decimal = Field(gt=0)
    paid_on: date
    method: str = "bank_transfer"
    reference: Optional[str] = None


def _owner_dict(o: PropertyOwner, access: AccessContext, units: int = 0) -> dict:
    fin = access.sees("owner_financials") or access.sees("bank_accounts")
    return {
        "id": o.id, "code": o.code, "full_name": o.full_name, "mobile": o.mobile, "email": o.email,
        "national_id": mask(o.national_id, access.sees("identity")), "address": o.address,
        "bank_name": o.bank_name if fin else None,
        "bank_account": mask(o.bank_account, fin), "iban": mask(o.iban, fin),
        "settlement_frequency": o.settlement_frequency,
        "commission_rate": float(o.commission_rate) if access.sees("commissions") else None,
        "settlement_day": o.settlement_day, "notes": o.notes if access.sees("internal_notes") else None, "units": units,
    }


def _validate_frequency(freq: Optional[str]) -> None:
    if freq is not None and freq not in SETTLEMENT_FREQUENCIES:
        raise HTTPException(status_code=400, detail=f"Invalid settlement frequency (one of {', '.join(SETTLEMENT_FREQUENCIES)})")


@router.get("")
async def list_owners(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
    search: Optional[str] = None,
):
    cid = company_id_of(current_user)
    query = select(PropertyOwner).where(PropertyOwner.company_id == cid, PropertyOwner.is_deleted == False).order_by(PropertyOwner.full_name)  # noqa: E712
    if search:
        query = query.where(PropertyOwner.full_name.ilike(f"%{search}%"))
    owners = (await db.execute(query)).scalars().all()
    counts = dict(
        (await db.execute(
            select(Unit.owner_id, func.count()).where(Unit.company_id == cid, Unit.is_deleted == False, Unit.owner_id.isnot(None)).group_by(Unit.owner_id)  # noqa: E712
        )).all()
    )
    return [_owner_dict(o, access, counts.get(o.id, 0)) for o in owners]


@router.post("")
async def create_owner(
    data: OwnerIn,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    cid = company_id_of(current_user)
    _validate_frequency(data.settlement_frequency)
    payload = data.model_dump()
    payload["code"] = payload.get("code") or f"OWN-{uuid.uuid4().hex[:6].upper()}"
    exists = (await db.execute(select(PropertyOwner.id).where(PropertyOwner.company_id == cid, PropertyOwner.code == payload["code"]))).first()
    if exists:
        raise HTTPException(status_code=409, detail="Owner code already exists")
    owner = PropertyOwner(company_id=cid, **payload)
    db.add(owner)
    await db.flush()
    await log_audit(db, request, current_user, "owner_created", "owners", "property_owner", owner.id, after={"full_name": owner.full_name})
    return {"id": owner.id, "code": owner.code}


# Settlements are declared before "/{owner_id}" so the static paths win.
@router.get("/settlements")
async def list_settlements(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    owner_id: Optional[int] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
):
    cid = company_id_of(current_user)
    query = (
        select(OwnerSettlement, PropertyOwner)
        .join(PropertyOwner, OwnerSettlement.owner_id == PropertyOwner.id)
        .where(OwnerSettlement.company_id == cid)
        .order_by(OwnerSettlement.period_end.desc(), OwnerSettlement.id.desc())
    )
    if owner_id:
        query = query.where(OwnerSettlement.owner_id == owner_id)
    if status_filter:
        query = query.where(OwnerSettlement.status == status_filter)
    return [SettlementService.to_dict(s, o) for s, o in (await db.execute(query)).all()]


@router.get("/settlements/upcoming")
async def upcoming_settlements(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    cid = company_id_of(current_user)
    today = company_today(await AccessService.load_company(db, cid))
    owners = (await db.execute(select(PropertyOwner).where(PropertyOwner.company_id == cid, PropertyOwner.is_deleted == False))).scalars().all()  # noqa: E712
    existing = (await db.execute(select(OwnerSettlement).where(OwnerSettlement.company_id == cid, OwnerSettlement.status != "cancelled"))).scalars().all()
    result = []
    for o in owners:
        start, end, due = next_settlement(o, today)
        done = any(s.owner_id == o.id and s.period_end == end for s in existing)
        result.append({"owner_id": o.id, "owner_name": o.full_name, "frequency": o.settlement_frequency,
                       "period_start": start.isoformat(), "period_end": end.isoformat(), "due_date": due.isoformat(),
                       "days_until_due": (due - today).days, "created": done})
    result.sort(key=lambda r: r["due_date"])
    return result


@router.post("/settlements/preview")
async def preview_settlement(
    data: SettlementIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    cid = company_id_of(current_user)
    owner = await get_owned(db, PropertyOwner, data.owner_id, cid, entity_name="Owner")
    calc = await SettlementService.calculate(db, cid, owner, data.period_end)
    net = calc["gross_collected"] - calc["commission_amount"] - calc["expenses_total"] + data.adjustments
    return {
        "gross_collected": float(calc["gross_collected"]), "commission_amount": float(calc["commission_amount"]),
        "expenses_total": float(calc["expenses_total"]), "adjustments": float(data.adjustments), "net_payable": float(net),
        "contracts": calc["contracts"], "expenses": calc["expenses"],
    }


@router.post("/settlements")
async def create_settlement(
    data: SettlementIn,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    if data.adjustments != 0 and not access.can("owners", "approve"):
        raise HTTPException(status_code=403, detail={"code": "permission_denied", "module": "owners", "action": "approve"})
    settlement = await SettlementService.create(
        db, company_id_of(current_user), owner_id=data.owner_id, period_start=data.period_start, period_end=data.period_end,
        adjustments=data.adjustments, adjustments_note=data.adjustments_note, user_id=current_user.id,
    )
    await log_audit(db, request, current_user, "owner_settlement_created", "owners", "owner_settlement", settlement.id,
                    after={"net_payable": settlement.net_payable, "gross": settlement.gross_collected,
                           "commission": settlement.commission_amount, "expenses": settlement.expenses_total})
    return SettlementService.to_dict(settlement)


async def _settlement(db: AsyncSession, settlement_id: int, user: User) -> OwnerSettlement:
    return await get_owned(db, OwnerSettlement, settlement_id, company_id_of(user), entity_name="Settlement")


@router.get("/settlements/{settlement_id}")
async def get_settlement(
    settlement_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    s = await _settlement(db, settlement_id, current_user)
    owner = (await db.execute(select(PropertyOwner).where(PropertyOwner.id == s.owner_id))).scalar_one_or_none()
    payments = (await db.execute(select(OwnerSettlementPayment).where(OwnerSettlementPayment.settlement_id == s.id))).scalars().all()
    return {**SettlementService.to_dict(s, owner), "payments": [
        {"id": p.id, "amount": float(p.amount), "paid_on": p.paid_on.isoformat(), "method": p.method, "reference": p.reference}
        for p in payments
    ]}


@router.post("/settlements/{settlement_id}/approve")
async def approve_settlement(
    settlement_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    s = await _settlement(db, settlement_id, current_user)
    await SettlementService.approve(db, s, current_user.id)
    await log_audit(db, request, current_user, "owner_settlement_approved", "owners", "owner_settlement", s.id, after={"status": s.status})
    return SettlementService.to_dict(s)


@router.post("/settlements/{settlement_id}/cancel")
async def cancel_settlement(
    settlement_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    s = await _settlement(db, settlement_id, current_user)
    await SettlementService.cancel(db, s)
    await log_audit(db, request, current_user, "owner_settlement_cancelled", "owners", "owner_settlement", s.id)
    return SettlementService.to_dict(s)


@router.post("/settlements/{settlement_id}/payments")
async def pay_settlement(
    settlement_id: int,
    data: SettlementPaymentIn,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    s = await _settlement(db, settlement_id, current_user)
    payment = await SettlementService.pay(db, s, amount=data.amount, paid_on=data.paid_on, method=data.method,
                                          reference=data.reference, user_id=current_user.id)
    await log_audit(db, request, current_user, "owner_settlement_paid", "owners", "owner_settlement", s.id,
                    after={"payment_id": payment.id, "amount": payment.amount, "status": s.status})
    return SettlementService.to_dict(s)


@router.get("/settlements/{settlement_id}/statement")
async def settlement_statement(
    settlement_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    """Printable statement data (the page renders it; print permission required)."""
    s = await _settlement(db, settlement_id, current_user)
    owner = (await db.execute(select(PropertyOwner).where(PropertyOwner.id == s.owner_id))).scalar_one()
    return {"settlement": SettlementService.to_dict(s, owner), "owner": _owner_dict(owner, access)}


@router.get("/{owner_id}")
async def get_owner(
    owner_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    cid = company_id_of(current_user)
    owner = await get_owned(db, PropertyOwner, owner_id, cid, entity_name="Owner")
    units = (await db.execute(select(Unit).where(Unit.owner_id == owner.id, Unit.company_id == cid, Unit.is_deleted == False))).scalars().all()  # noqa: E712
    return {**_owner_dict(owner, access, len(units)),
            "owned_units": [{"id": u.id, "unit_code": u.unit_code, "occupancy_status": u.occupancy_status} for u in units]}


@router.put("/{owner_id}")
async def update_owner(
    owner_id: int,
    data: OwnerUpdate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    owner = await get_owned(db, PropertyOwner, owner_id, company_id_of(current_user), entity_name="Owner")
    changes = data.model_dump(exclude_unset=True)
    _validate_frequency(changes.get("settlement_frequency"))
    sensitive = {"bank_name", "bank_account", "iban"} & set(changes)
    if sensitive and not (access.sees("owner_financials") or access.sees("bank_accounts")):
        raise HTTPException(status_code=403, detail="Not allowed to change owner bank details")
    if "commission_rate" in changes and not access.sees("commissions"):
        raise HTTPException(status_code=403, detail="Not allowed to change commission rates")
    before = {k: getattr(owner, k) for k in changes}
    for k, v in changes.items():
        setattr(owner, k, v)
    await db.flush()
    await log_audit(db, request, current_user, "owner_updated", "owners", "property_owner", owner.id, before=before, after=changes)
    return {"id": owner.id, "success": True}


@router.delete("/{owner_id}")
async def delete_owner(
    owner_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    cid = company_id_of(current_user)
    owner = await get_owned(db, PropertyOwner, owner_id, cid, entity_name="Owner")
    linked = (await db.execute(select(func.count(Unit.id)).where(Unit.owner_id == owner.id, Unit.is_deleted == False))).scalar()  # noqa: E712
    if linked:
        raise HTTPException(status_code=400, detail="Owner still has units — reassign them first")
    owner.soft_delete()
    await db.flush()
    await log_audit(db, request, current_user, "owner_deleted", "owners", "property_owner", owner.id)
    return {"success": True}
