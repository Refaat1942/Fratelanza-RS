from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.warehouse import InventoryItem, StockMovement, Warehouse
from app.models.users import User

router = APIRouter()


class WarehouseCreate(BaseModel):
    name_ar: str
    name_en: str
    code: str
    location: Optional[str] = None


class ItemCreate(BaseModel):
    warehouse_id: int
    sku: str
    name_ar: str
    name_en: str
    quantity: Decimal = Decimal("0")
    min_stock_level: Decimal = Decimal("0")
    unit: str = "pcs"


@router.get("")
async def list_warehouses(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    query = select(Warehouse).order_by(Warehouse.id.desc())
    if not current_user.is_super_admin:
        query = query.where(Warehouse.company_id == current_user.company_id)
    result = await db.execute(query)
    warehouses = result.scalars().all()
    return [{"id": w.id, "name_ar": w.name_ar, "code": w.code, "location": w.location} for w in warehouses]


@router.post("")
async def create_warehouse(
    data: WarehouseCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    warehouse = Warehouse(company_id=current_user.company_id, **data.model_dump())
    db.add(warehouse)
    await db.flush()
    return {"id": warehouse.id}


@router.get("/items")
async def list_items(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(InventoryItem).order_by(InventoryItem.id.desc()))
    items = result.scalars().all()
    return [
        {
            "id": i.id,
            "sku": i.sku,
            "name_ar": i.name_ar,
            "quantity": float(i.quantity),
            "min_stock_level": float(i.min_stock_level),
            "low_stock": float(i.quantity) <= float(i.min_stock_level),
        }
        for i in items
    ]


@router.post("/items")
async def create_item(
    data: ItemCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    item = InventoryItem(**data.model_dump())
    db.add(item)
    await db.flush()
    return {"id": item.id, "sku": item.sku}


@router.get("/movements")
async def list_movements(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(StockMovement).order_by(StockMovement.id.desc()).limit(100))
    movements = result.scalars().all()
    return [
        {"id": m.id, "item_id": m.item_id, "movement_type": m.movement_type, "quantity": float(m.quantity)}
        for m in movements
    ]
