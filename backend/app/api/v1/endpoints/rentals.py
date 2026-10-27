"""Rental contracts, rent receivables and collections (module ``rentals``)."""

from datetime import date
from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import company_id_of, get_access, get_company_user, log_audit
from app.core.database import get_db
from app.core.tenant import apply_data_scope, get_owned, mask
from app.models.real_estate import Building, Floor, Project, Unit
from app.models.rentals import PropertyOwner, RentAdjustment, RentalContract, RentPayment, RentReceivable
from app.models.users import User
from app.services.access_service import AccessContext
from app.services.rental_service import (
    RentalService,
    company_today,
    contract_display_status,
    money,
    outstanding,
)

router = APIRouter()


class ContractIn(BaseModel):
    unit_id: int
    owner_id: Optional[int] = None
    tenant_customer_id: Optional[int] = None
    tenant_name: Optional[str] = Field(default=None, max_length=255)
    tenant_mobile: Optional[str] = Field(default=None, max_length=50)
    tenant_id_number: Optional[str] = Field(default=None, max_length=50)
    start_date: date
    end_date: date
    rent_amount: Decimal = Field(gt=0)
    payment_frequency: str = "monthly"
    due_day: int = Field(default=1, ge=1, le=28)
    deposit_amount: Decimal = Field(default=Decimal("0"), ge=0)
    other_charges: Decimal = Field(default=Decimal("0"), ge=0)
    payment_terms: Optional[str] = None
    commission_rate: Optional[Decimal] = Field(default=None, ge=0, le=100)
    notes: Optional[str] = None
    attachments: Optional[str] = None
    contract_number: Optional[str] = Field(default=None, max_length=50)
    assigned_to_id: Optional[int] = None
    activate: bool = False


class ContractUpdate(BaseModel):
    tenant_name: Optional[str] = None
    tenant_mobile: Optional[str] = None
    tenant_id_number: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    rent_amount: Optional[Decimal] = Field(default=None, gt=0)
    payment_frequency: Optional[str] = None
    deposit_amount: Optional[Decimal] = Field(default=None, ge=0)
    other_charges: Optional[Decimal] = Field(default=None, ge=0)
    payment_terms: Optional[str] = None
    commission_rate: Optional[Decimal] = Field(default=None, ge=0, le=100)
    notes: Optional[str] = None
    attachments: Optional[str] = None


class TerminateIn(BaseModel):
    termination_date: date
    reason: str = Field(min_length=3)


class RenewIn(BaseModel):
    new_end_date: date
    new_rent_amount: Optional[Decimal] = Field(default=None, gt=0)
    payment_frequency: Optional[str] = None
    notes: Optional[str] = None


class ReplaceTenantIn(BaseModel):
    termination_date: date
    reason: str = Field(min_length=3)
    new_contract: ContractIn


class PaymentIn(BaseModel):
    amount: Decimal = Field(gt=0)
    paid_on: date
    method: str = Field(default="cash", max_length=30)
    receipt_reference: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = None


class RefundIn(BaseModel):
    amount: Decimal = Field(gt=0)
    paid_on: date
    method: str = Field(default="cash", max_length=30)
    notes: Optional[str] = None


class AdjustmentIn(BaseModel):
    amount: Decimal = Field(gt=0)
    reason: str = Field(min_length=3)


class UnitPropertyUpdate(BaseModel):
    owner_id: Optional[int] = None
    furnishing_status: Optional[str] = None
    finishing: Optional[str] = None
    rental_category: Optional[str] = None
    construction_year: Optional[int] = Field(default=None, ge=1800, le=2100)
    electricity_meter: Optional[str] = None
    water_meter: Optional[str] = None
    gas_meter: Optional[str] = None
    listing_purpose: Optional[str] = None
    acquisition_info: Optional[str] = None
    notes: Optional[str] = None


class UnitQuickCreate(UnitPropertyUpdate):
    """Register a unit directly; the property / building / floor are found or created by name."""

    property_name: str = Field(min_length=2, max_length=255)
    city: Optional[str] = None
    building: str = Field(default="A", min_length=1, max_length=50)
    floor_number: int = Field(default=0, ge=-5, le=200)
    unit_code: str = Field(min_length=1, max_length=50)
    unit_number: Optional[str] = Field(default=None, max_length=50)
    unit_type: str = "apartment"
    area_sqm: Decimal = Field(gt=0)
    bedrooms: int = Field(default=0, ge=0)
    bathrooms: int = Field(default=0, ge=0)
    price: Decimal = Field(default=Decimal("0"), ge=0)


CONTRACT_AUDIT_FIELDS = ["status", "start_date", "end_date", "rent_amount", "unit_id", "tenant_name"]


async def _company(db: AsyncSession, user: User):
    from app.services.access_service import AccessService

    return await AccessService.load_company(db, company_id_of(user))


def _contract_dict(c: RentalContract, unit: Optional[Unit], owner: Optional[PropertyOwner], access: AccessContext,
                   today: date, balance: Optional[dict] = None) -> dict:
    balance = balance or {}
    return {
        "id": c.id,
        "contract_number": c.contract_number,
        "unit_id": c.unit_id,
        "unit_code": unit.unit_code if unit else None,
        "owner_id": c.owner_id,
        "owner_name": owner.full_name if owner else None,
        "tenant_customer_id": c.tenant_customer_id,
        "tenant_name": c.tenant_name,
        "tenant_mobile": c.tenant_mobile,
        "tenant_id_number": mask(c.tenant_id_number, access.sees("identity")),
        "start_date": c.start_date.isoformat(),
        "end_date": c.end_date.isoformat(),
        "duration_months": round(((c.end_date - c.start_date).days + 1) / 30.44),
        "rent_amount": float(c.rent_amount),
        "payment_frequency": c.payment_frequency,
        "total_value": float(money(c.rent_amount) * round(((c.end_date - c.start_date).days + 1) / 30.44)),
        "deposit_amount": float(c.deposit_amount or 0),
        "other_charges": float(c.other_charges or 0),
        "payment_terms": c.payment_terms,
        "commission_rate": float(c.commission_rate) if c.commission_rate is not None and access.sees("commissions") else None,
        "status": contract_display_status(c, today),
        "stored_status": c.status,
        "termination_date": c.termination_date.isoformat() if c.termination_date else None,
        "termination_reason": c.termination_reason,
        "renewed_from_id": c.renewed_from_id,
        "notes": c.notes if access.sees("internal_notes") else None,
        "attachments": c.attachments,
        "assigned_to_id": c.assigned_to_id,
        "billed": float(balance.get("billed", 0)),
        "collected": float(balance.get("paid", 0)),
        "outstanding": float(balance.get("outstanding", 0)),
    }


async def _scoped_contract(db: AsyncSession, contract_id: int, user: User, access: AccessContext) -> RentalContract:
    query = select(RentalContract).where(
        RentalContract.id == contract_id,
        RentalContract.company_id == company_id_of(user),
        RentalContract.is_deleted == False,  # noqa: E712
    )
    query = apply_data_scope(query, RentalContract.assigned_to_id, access, user)
    contract = (await db.execute(query)).scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    return contract


# ----------------------------------------------------------------------------- contracts
@router.get("/contracts")
async def list_contracts(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
    status_filter: Optional[str] = Query(None, alias="status"),
    unit_id: Optional[int] = None,
    owner_id: Optional[int] = None,
    search: Optional[str] = None,
):
    cid = company_id_of(current_user)
    company = await _company(db, current_user)
    today = company_today(company)
    query = (
        select(RentalContract, Unit, PropertyOwner)
        .join(Unit, RentalContract.unit_id == Unit.id)
        .outerjoin(PropertyOwner, RentalContract.owner_id == PropertyOwner.id)
        .where(RentalContract.company_id == cid, RentalContract.is_deleted == False)  # noqa: E712
        .order_by(RentalContract.id.desc())
    )
    query = apply_data_scope(query, RentalContract.assigned_to_id, access, current_user)
    if unit_id:
        query = query.where(RentalContract.unit_id == unit_id)
    if owner_id:
        query = query.where(RentalContract.owner_id == owner_id)
    if search:
        like = f"%{search}%"
        query = query.where(or_(RentalContract.tenant_name.ilike(like), RentalContract.contract_number.ilike(like), Unit.unit_code.ilike(like)))
    rows = (await db.execute(query)).all()
    balances = await RentalService.contract_balances(db, cid, [c.id for c, _, _ in rows])
    items = [_contract_dict(c, u, o, access, today, balances.get(c.id)) for c, u, o in rows]
    if status_filter:
        items = [i for i in items if i["status"] == status_filter]
    return items


@router.post("/contracts")
async def create_contract(
    data: ContractIn,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    cid = company_id_of(current_user)
    if data.activate and not access.can("rentals", "approve"):
        raise HTTPException(status_code=403, detail={"code": "permission_denied", "module": "rentals", "action": "approve"})
    contract = await RentalService.create_contract(db, cid, data.model_dump(), current_user.id)
    await log_audit(db, request, current_user, "rental_contract_created", "rentals", "rental_contract", contract.id,
                    after={f: getattr(contract, f) for f in CONTRACT_AUDIT_FIELDS})
    return {"id": contract.id, "contract_number": contract.contract_number, "status": contract.status}


@router.get("/contracts/{contract_id}")
async def get_contract(
    contract_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    contract = await _scoped_contract(db, contract_id, current_user, access)
    cid = contract.company_id
    company = await _company(db, current_user)
    today = company_today(company)
    unit = (await db.execute(select(Unit).where(Unit.id == contract.unit_id))).scalar_one_or_none()
    owner = (await db.execute(select(PropertyOwner).where(PropertyOwner.id == contract.owner_id))).scalar_one_or_none() if contract.owner_id else None
    balances = await RentalService.contract_balances(db, cid, [contract.id])
    receivables = (
        await db.execute(
            select(RentReceivable).where(RentReceivable.rental_contract_id == contract.id).order_by(RentReceivable.period_start)
        )
    ).scalars().all()
    history = []
    cursor = contract
    while cursor.renewed_from_id:
        prev = (await db.execute(select(RentalContract).where(RentalContract.id == cursor.renewed_from_id, RentalContract.company_id == cid))).scalar_one_or_none()
        if not prev:
            break
        history.append({"id": prev.id, "contract_number": prev.contract_number, "start_date": prev.start_date.isoformat(),
                        "end_date": prev.end_date.isoformat(), "rent_amount": float(prev.rent_amount), "status": prev.status})
        cursor = prev
    unit_history = (
        await db.execute(
            select(RentalContract).where(RentalContract.unit_id == contract.unit_id, RentalContract.company_id == cid,
                                         RentalContract.is_deleted == False).order_by(RentalContract.start_date)  # noqa: E712
        )
    ).scalars().all()
    return {
        **_contract_dict(contract, unit, owner, access, today, balances.get(contract.id)),
        "receivables": [RentalService.receivable_dict(r, contract, unit, today) for r in receivables],
        "renewal_history": history,
        "unit_tenant_history": [
            {"id": c.id, "contract_number": c.contract_number, "tenant_name": c.tenant_name, "start_date": c.start_date.isoformat(),
             "end_date": c.end_date.isoformat(), "status": contract_display_status(c, today), "rent_amount": float(c.rent_amount)}
            for c in unit_history
        ],
    }


@router.put("/contracts/{contract_id}")
async def update_contract(
    contract_id: int,
    data: ContractUpdate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    contract = await _scoped_contract(db, contract_id, current_user, access)
    changes = data.model_dump(exclude_unset=True)
    financial = {"start_date", "end_date", "rent_amount", "payment_frequency", "deposit_amount"}
    if contract.status != "draft" and financial & set(changes):
        raise HTTPException(status_code=400, detail="Dates and rent of an active contract cannot be edited — renew instead")
    before = {f: getattr(contract, f) for f in changes}
    for k, v in changes.items():
        setattr(contract, k, v)
    await db.flush()
    await log_audit(db, request, current_user, "rental_contract_updated", "rentals", "rental_contract", contract.id,
                    before=before, after=changes)
    return {"id": contract.id, "success": True}


@router.post("/contracts/{contract_id}/approve")
async def activate_contract(
    contract_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    contract = await _scoped_contract(db, contract_id, current_user, access)
    await RentalService.activate(db, contract)
    await log_audit(db, request, current_user, "rental_contract_activated", "rentals", "rental_contract", contract.id,
                    after={"status": contract.status})
    return {"id": contract.id, "status": contract.status}


@router.post("/contracts/{contract_id}/terminate")
async def terminate_contract(
    contract_id: int,
    data: TerminateIn,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    contract = await _scoped_contract(db, contract_id, current_user, access)
    before = {"status": contract.status}
    await RentalService.terminate(db, contract, data.termination_date, data.reason)
    await log_audit(db, request, current_user, "rental_contract_terminated", "rentals", "rental_contract", contract.id,
                    before=before, after={"status": contract.status, "termination_date": data.termination_date, "reason": data.reason})
    return {"id": contract.id, "status": contract.status}


@router.post("/contracts/{contract_id}/renew")
async def renew_contract(
    contract_id: int,
    data: RenewIn,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    contract = await _scoped_contract(db, contract_id, current_user, access)
    renewed = await RentalService.renew(
        db, contract, new_end_date=data.new_end_date, new_rent_amount=data.new_rent_amount,
        payment_frequency=data.payment_frequency, user_id=current_user.id, notes=data.notes,
    )
    await log_audit(db, request, current_user, "rental_contract_renewed", "rentals", "rental_contract", contract.id,
                    before={"contract_id": contract.id, "rent_amount": contract.rent_amount, "end_date": contract.end_date},
                    after={"new_contract_id": renewed.id, "rent_amount": renewed.rent_amount, "end_date": renewed.end_date})
    return {"id": renewed.id, "contract_number": renewed.contract_number, "previous_contract_id": contract.id}


@router.post("/contracts/{contract_id}/replace-tenant")
async def replace_tenant(
    contract_id: int,
    data: ReplaceTenantIn,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    """Terminate the current lease and start a new one on the same unit — history is kept."""
    if not access.can("rentals", "terminate"):
        raise HTTPException(status_code=403, detail={"code": "permission_denied", "module": "rentals", "action": "terminate"})
    contract = await _scoped_contract(db, contract_id, current_user, access)
    if data.new_contract.unit_id != contract.unit_id:
        raise HTTPException(status_code=400, detail="New contract must be on the same unit")
    await RentalService.terminate(db, contract, data.termination_date, data.reason)
    payload = data.new_contract.model_dump()
    payload["activate"] = True
    new_contract = await RentalService.create_contract(db, contract.company_id, payload, current_user.id)
    await log_audit(db, request, current_user, "rental_tenant_replaced", "rentals", "rental_contract", contract.id,
                    after={"new_contract_id": new_contract.id, "reason": data.reason})
    return {"terminated_id": contract.id, "new_contract_id": new_contract.id}


@router.delete("/contracts/{contract_id}")
async def delete_contract(
    contract_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    contract = await _scoped_contract(db, contract_id, current_user, access)
    if contract.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft contracts can be deleted — terminate active contracts")
    contract.soft_delete()
    await db.flush()
    await log_audit(db, request, current_user, "rental_contract_deleted", "rentals", "rental_contract", contract.id)
    return {"success": True}


# ----------------------------------------------------------------------------- receivables
@router.get("/receivables")
async def list_receivables(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
    status_filter: Optional[str] = Query(None, alias="status"),
    contract_id: Optional[int] = None,
    due_from: Optional[date] = None,
    due_to: Optional[date] = None,
):
    cid = company_id_of(current_user)
    today = company_today(await _company(db, current_user))
    query = (
        select(RentReceivable, RentalContract, Unit)
        .join(RentalContract, RentReceivable.rental_contract_id == RentalContract.id)
        .join(Unit, RentalContract.unit_id == Unit.id)
        .where(RentReceivable.company_id == cid, RentalContract.is_deleted == False)  # noqa: E712
        .order_by(RentReceivable.due_date)
    )
    query = apply_data_scope(query, RentalContract.assigned_to_id, access, current_user)
    if contract_id:
        query = query.where(RentReceivable.rental_contract_id == contract_id)
    if due_from:
        query = query.where(RentReceivable.due_date >= due_from)
    if due_to:
        query = query.where(RentReceivable.due_date <= due_to)
    items = [RentalService.receivable_dict(r, c, u, today) for r, c, u in (await db.execute(query)).all()]
    if status_filter == "open":
        items = [i for i in items if i["status"] in ("pending", "partial", "overdue")]
    elif status_filter:
        items = [i for i in items if i["status"] == status_filter]
    return items


@router.get("/receivables/{receivable_id}/payments")
async def receivable_payments(
    receivable_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    cid = company_id_of(current_user)
    await get_owned(db, RentReceivable, receivable_id, cid, entity_name="Receivable")
    payments = (
        await db.execute(select(RentPayment).where(RentPayment.receivable_id == receivable_id, RentPayment.company_id == cid).order_by(RentPayment.id))
    ).scalars().all()
    adjustments = (
        await db.execute(select(RentAdjustment).where(RentAdjustment.receivable_id == receivable_id, RentAdjustment.company_id == cid))
    ).scalars().all()
    return {
        "payments": [
            {"id": p.id, "kind": p.kind, "amount": float(p.amount), "paid_on": p.paid_on.isoformat(), "method": p.method,
             "receipt_reference": p.receipt_reference, "notes": p.notes, "settled": p.settlement_id is not None}
            for p in payments
        ],
        "adjustments": [
            {"id": a.id, "amount": float(a.amount), "reason": a.reason, "approved_by_id": a.approved_by_id, "created_at": str(a.created_at)}
            for a in adjustments
        ],
    }


@router.post("/receivables/{receivable_id}/payments")
async def collect_payment(
    receivable_id: int,
    data: PaymentIn,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    payment = await RentalService.record_payment(
        db, company_id_of(current_user), receivable_id, amount=data.amount, paid_on=data.paid_on, method=data.method,
        receipt_reference=data.receipt_reference, notes=data.notes, user_id=current_user.id,
    )
    await log_audit(db, request, current_user, "rent_collected", "rentals", "rent_payment", payment.id,
                    after={"receivable_id": receivable_id, "amount": payment.amount, "method": payment.method})
    return {"id": payment.id, "receipt_reference": payment.receipt_reference, "amount": float(payment.amount)}


@router.post("/receivables/{receivable_id}/refunds")
async def refund_payment(
    receivable_id: int,
    data: RefundIn,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    refund = await RentalService.record_refund(
        db, company_id_of(current_user), receivable_id, amount=data.amount, paid_on=data.paid_on, method=data.method,
        notes=data.notes, user_id=current_user.id,
    )
    await log_audit(db, request, current_user, "rent_refunded", "rentals", "rent_payment", refund.id,
                    after={"receivable_id": receivable_id, "amount": refund.amount})
    return {"id": refund.id, "amount": float(refund.amount)}


@router.post("/receivables/{receivable_id}/adjustments")
async def waive_amount(
    receivable_id: int,
    data: AdjustmentIn,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    adj = await RentalService.adjust(db, company_id_of(current_user), receivable_id, amount=data.amount, reason=data.reason, user_id=current_user.id)
    await log_audit(db, request, current_user, "rent_waived", "rentals", "rent_receivable", receivable_id,
                    after={"amount": adj.amount, "reason": adj.reason})
    return {"id": adj.id, "amount": float(adj.amount)}


# ----------------------------------------------------------------------------- units & jobs
@router.get("/units")
async def rental_units(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    cid = company_id_of(current_user)
    rows = (
        await db.execute(
            select(Unit, Floor, Project, PropertyOwner)
            .join(Floor, Unit.floor_id == Floor.id)
            .join(Building, Floor.building_id == Building.id)
            .join(Project, Building.project_id == Project.id)
            .outerjoin(PropertyOwner, Unit.owner_id == PropertyOwner.id)
            .where(Unit.company_id == cid, Unit.is_deleted == False)  # noqa: E712
            .order_by(Unit.unit_code)
        )
    ).all()
    active = {
        c.unit_id: c
        for c in (
            await db.execute(select(RentalContract).where(RentalContract.company_id == cid, RentalContract.status == "active", RentalContract.is_deleted == False))  # noqa: E712
        ).scalars().all()
    }
    return [
        {
            "id": u.id, "unit_code": u.unit_code, "unit_type": u.unit_type.value, "project_name": p.name_ar, "city": p.city,
            "floor_number": f.floor_number, "area_sqm": float(u.area_sqm), "bedrooms": u.bedrooms, "status": u.status.value,
            "occupancy_status": u.occupancy_status, "owner_id": u.owner_id, "owner_name": o.full_name if o else None,
            "furnishing_status": u.furnishing_status, "finishing": u.finishing, "rental_category": u.rental_category,
            "construction_year": u.construction_year, "electricity_meter": u.electricity_meter, "water_meter": u.water_meter,
            "gas_meter": u.gas_meter, "listing_purpose": u.listing_purpose, "acquisition_info": u.acquisition_info if access.sees("owner_financials") else None,
            "notes": u.notes, "active_contract_id": active[u.id].id if u.id in active else None,
            "current_tenant": active[u.id].tenant_name if u.id in active else None,
        }
        for u, f, p, o in rows
    ]


@router.post("/units")
async def create_unit_quick(
    data: UnitQuickCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    from app.models.real_estate import ProjectStatus, UnitStatus, UnitType

    cid = company_id_of(current_user)
    try:
        unit_type = UnitType(data.unit_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid unit type")
    if data.owner_id:
        await get_owned(db, PropertyOwner, data.owner_id, cid, entity_name="Owner")
    if (await db.execute(select(Unit.id).where(Unit.company_id == cid, Unit.unit_code == data.unit_code, Unit.is_deleted == False))).first():  # noqa: E712
        raise HTTPException(status_code=409, detail="Unit code already exists")
    name = data.property_name.strip()
    project = (
        await db.execute(select(Project).where(Project.company_id == cid, Project.name_ar == name, Project.is_deleted == False))  # noqa: E712
    ).scalars().first()
    if not project:
        import uuid as _uuid

        project = Project(company_id=cid, name_ar=name, name_en=name, code=f"P-{_uuid.uuid4().hex[:6].upper()}",
                          city=data.city, status=ProjectStatus.ACTIVE)
        db.add(project)
        await db.flush()
    building = (
        await db.execute(select(Building).where(Building.project_id == project.id, Building.code == data.building, Building.is_deleted == False))  # noqa: E712
    ).scalars().first()
    if not building:
        building = Building(project_id=project.id, name_ar=f"مبنى {data.building}", name_en=f"Building {data.building}", code=data.building)
        db.add(building)
        await db.flush()
    floor = (
        await db.execute(select(Floor).where(Floor.building_id == building.id, Floor.floor_number == data.floor_number))
    ).scalars().first()
    if not floor:
        floor = Floor(building_id=building.id, floor_number=data.floor_number, name_ar=f"الدور {data.floor_number}", name_en=f"Floor {data.floor_number}")
        db.add(floor)
        await db.flush()
    attributes = data.model_dump(include=set(UnitPropertyUpdate.model_fields), exclude_unset=True)
    unit = Unit(
        company_id=cid, floor_id=floor.id, unit_code=data.unit_code, unit_number=data.unit_number or data.unit_code,
        unit_type=unit_type, area_sqm=data.area_sqm, bedrooms=data.bedrooms, bathrooms=data.bathrooms,
        price=data.price, base_price=data.price, status=UnitStatus.AVAILABLE, occupancy_status="vacant", **attributes,
    )
    db.add(unit)
    await db.flush()
    await log_audit(db, request, current_user, "unit_created", "rentals", "unit", unit.id,
                    after={"unit_code": unit.unit_code, "property": name})
    return {"id": unit.id, "unit_code": unit.unit_code}


@router.put("/units/{unit_id}")
async def update_unit_property(
    unit_id: int,
    data: UnitPropertyUpdate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    cid = company_id_of(current_user)
    unit = await get_owned(db, Unit, unit_id, cid, entity_name="Unit")
    changes = data.model_dump(exclude_unset=True)
    if changes.get("owner_id"):
        await get_owned(db, PropertyOwner, changes["owner_id"], cid, entity_name="Owner")
    before = {k: getattr(unit, k) for k in changes}
    for k, v in changes.items():
        setattr(unit, k, v)
    await db.flush()
    await log_audit(db, request, current_user, "unit_updated", "rentals", "unit", unit.id, before=before, after=changes)
    return {"id": unit.id, "success": True}


@router.get("/summary")
async def rentals_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    cid = company_id_of(current_user)
    today = company_today(await _company(db, current_user))
    contracts = (
        await db.execute(select(RentalContract).where(RentalContract.company_id == cid, RentalContract.is_deleted == False))  # noqa: E712
    ).scalars().all()
    statuses = [contract_display_status(c, today) for c in contracts]
    recs = (
        await db.execute(select(RentReceivable).where(RentReceivable.company_id == cid, RentReceivable.status.in_(["pending", "partial"])))
    ).scalars().all()
    return {
        "active": sum(1 for s in statuses if s in ("active", "expiring")),
        "expiring": statuses.count("expiring"),
        "terminated": statuses.count("terminated"),
        "draft": statuses.count("draft"),
        "outstanding": float(sum((outstanding(r) for r in recs), Decimal("0"))),
        "overdue": float(await RentalService.overdue_total(db, cid, today)),
    }


@router.post("/jobs/run")
async def run_jobs_now(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    """Run the daily jobs for the caller's tenant only (receivables, expiry, reminders)."""
    from app.services.scheduler_service import run_company_jobs

    stats = await run_company_jobs(db, company_id_of(current_user))
    await log_audit(db, request, current_user, "rental_jobs_run", "rentals", details=str(stats))
    return stats
