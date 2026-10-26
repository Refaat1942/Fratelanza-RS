"""Sale / rent offers and customer requirements with matching (module ``real_estate_requests``)."""

from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import company_id_of, get_access, get_company_user, log_audit
from app.core.database import get_db
from app.core.tenant import apply_data_scope, ensure_refs
from app.models.customers import Customer
from app.models.real_estate import Unit
from app.models.rentals import PropertyRequest
from app.models.users import User
from app.services.access_service import AccessContext
from app.services.matching_service import CRITERIA, MatchingService

router = APIRouter()

KINDS = ("offer_sale", "offer_rent", "request_buy", "request_rent")


class RequestIn(BaseModel):
    kind: str = Field(pattern="^(offer_sale|offer_rent|request_buy|request_rent)$")
    customer_id: Optional[int] = None
    unit_id: Optional[int] = None
    customer_name: str = Field(min_length=2, max_length=255)
    customer_mobile: str = Field(min_length=6, max_length=50)
    property_type: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    price_min: Optional[Decimal] = Field(default=None, ge=0)
    price_max: Optional[Decimal] = Field(default=None, ge=0)
    area_min: Optional[Decimal] = Field(default=None, ge=0)
    area_max: Optional[Decimal] = Field(default=None, ge=0)
    rooms: Optional[int] = Field(default=None, ge=0)
    floor: Optional[int] = None
    construction_year: Optional[int] = Field(default=None, ge=1800, le=2100)
    finishing: Optional[str] = None
    furnishing_status: Optional[str] = None
    has_utility_meters: Optional[bool] = None
    meter_notes: Optional[str] = None
    notes: Optional[str] = None
    status: str = "open"
    assigned_to_id: Optional[int] = None


class RequestUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_mobile: Optional[str] = None
    property_type: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    price_min: Optional[Decimal] = None
    price_max: Optional[Decimal] = None
    area_min: Optional[Decimal] = None
    area_max: Optional[Decimal] = None
    rooms: Optional[int] = None
    floor: Optional[int] = None
    construction_year: Optional[int] = None
    finishing: Optional[str] = None
    furnishing_status: Optional[str] = None
    has_utility_meters: Optional[bool] = None
    meter_notes: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(open|matched|closed|cancelled)$")
    assigned_to_id: Optional[int] = None


def _dict(r: PropertyRequest) -> dict:
    return {c.name: (float(getattr(r, c.name)) if isinstance(getattr(r, c.name), Decimal) else getattr(r, c.name))
            for c in PropertyRequest.__table__.columns if c.name not in ("is_deleted", "deleted_at", "company_id")} | {
        "created_at": str(r.created_at), "updated_at": str(r.updated_at)}


async def _scoped(db: AsyncSession, request_id: int, user: User, access: AccessContext) -> PropertyRequest:
    query = select(PropertyRequest).where(
        PropertyRequest.id == request_id, PropertyRequest.company_id == company_id_of(user), PropertyRequest.is_deleted == False  # noqa: E712
    )
    query = apply_data_scope(query, PropertyRequest.assigned_to_id, access, user)
    item = (await db.execute(query)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Request not found")
    return item


@router.get("/criteria")
async def matching_criteria():
    return CRITERIA


@router.get("")
async def list_requests(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
    kind: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
):
    query = select(PropertyRequest).where(
        PropertyRequest.company_id == company_id_of(current_user), PropertyRequest.is_deleted == False  # noqa: E712
    ).order_by(PropertyRequest.id.desc())
    query = apply_data_scope(query, PropertyRequest.assigned_to_id, access, current_user)
    if kind == "offer":
        query = query.where(PropertyRequest.kind.in_(["offer_sale", "offer_rent"]))
    elif kind == "request":
        query = query.where(PropertyRequest.kind.in_(["request_buy", "request_rent"]))
    elif kind in KINDS:
        query = query.where(PropertyRequest.kind == kind)
    if status:
        query = query.where(PropertyRequest.status == status)
    if search:
        like = f"%{search}%"
        query = query.where(or_(PropertyRequest.customer_name.ilike(like), PropertyRequest.customer_mobile.ilike(like),
                                PropertyRequest.city.ilike(like), PropertyRequest.district.ilike(like)))
    return [_dict(r) for r in (await db.execute(query)).scalars().all()]


@router.post("")
async def create_request(
    data: RequestIn, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    cid = company_id_of(current_user)
    await ensure_refs(db, cid, [(Customer, data.customer_id, "Customer"), (Unit, data.unit_id, "Unit"),
                                (User, data.assigned_to_id, "User")])
    if data.price_min is not None and data.price_max is not None and data.price_min > data.price_max:
        raise HTTPException(status_code=400, detail="Minimum price exceeds maximum")
    payload = data.model_dump()
    payload["assigned_to_id"] = payload.get("assigned_to_id") or current_user.id
    item = PropertyRequest(company_id=cid, created_by_id=current_user.id, **payload)
    db.add(item)
    await db.flush()
    await log_audit(db, request, current_user, "property_request_created", "real_estate_requests", "property_request", item.id)
    return _dict(item)


@router.get("/{request_id}")
async def get_request(
    request_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    return _dict(await _scoped(db, request_id, current_user, access))


@router.get("/{request_id}/matches")
async def get_matches(
    request_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
    criteria: Optional[str] = Query(None, description="Comma separated criteria keys"),
    min_score: float = Query(0.0, ge=0, le=1),
):
    item = await _scoped(db, request_id, current_user, access)
    keys = [c.strip() for c in criteria.split(",")] if criteria else None
    return await MatchingService.find_matches(db, item.company_id, item, keys, min_score)


@router.put("/{request_id}")
async def update_request(
    request_id: int, data: RequestUpdate, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    item = await _scoped(db, request_id, current_user, access)
    changes = data.model_dump(exclude_unset=True)
    await ensure_refs(db, item.company_id, [(User, changes.get("assigned_to_id"), "User")])
    for k, v in changes.items():
        setattr(item, k, v)
    await db.flush()
    await log_audit(db, request, current_user, "property_request_updated", "real_estate_requests", "property_request", item.id)
    return _dict(item)


@router.delete("/{request_id}")
async def delete_request(
    request_id: int, request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    item = await _scoped(db, request_id, current_user, access)
    item.soft_delete()
    await db.flush()
    await log_audit(db, request, current_user, "property_request_deleted", "real_estate_requests", "property_request", item.id)
    return {"success": True}
