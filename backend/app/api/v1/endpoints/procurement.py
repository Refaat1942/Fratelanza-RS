from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.procurement import PurchaseOrder, RFQ, Vendor
from app.models.users import User

router = APIRouter()


class VendorCreate(BaseModel):
    name_ar: str
    name_en: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


@router.get("/vendors")
async def list_vendors(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    query = select(Vendor).order_by(Vendor.id.desc())
    if not current_user.is_super_admin:
        query = query.where(Vendor.company_id == current_user.company_id)
    result = await db.execute(query)
    vendors = result.scalars().all()
    return [{"id": v.id, "name_ar": v.name_ar, "name_en": v.name_en, "rating": v.rating} for v in vendors]


@router.post("/vendors")
async def create_vendor(
    data: VendorCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    vendor = Vendor(company_id=current_user.company_id, **data.model_dump())
    db.add(vendor)
    await db.flush()
    return {"id": vendor.id}


@router.get("/rfqs")
async def list_rfqs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    query = select(RFQ).order_by(RFQ.id.desc())
    if not current_user.is_super_admin:
        query = query.where(RFQ.company_id == current_user.company_id)
    result = await db.execute(query)
    rfqs = result.scalars().all()
    return [{"id": r.id, "rfq_number": r.rfq_number, "title": r.title, "status": r.status} for r in rfqs]


@router.get("/purchase-orders")
async def list_purchase_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    query = select(PurchaseOrder).order_by(PurchaseOrder.id.desc())
    if not current_user.is_super_admin:
        query = query.where(PurchaseOrder.company_id == current_user.company_id)
    result = await db.execute(query)
    pos = result.scalars().all()
    return [
        {"id": p.id, "po_number": p.po_number, "vendor_id": p.vendor_id, "total_amount": float(p.total_amount), "status": p.status}
        for p in pos
    ]
