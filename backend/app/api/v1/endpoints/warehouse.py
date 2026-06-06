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


class WarehouseUpdate(BaseModel):
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    code: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None


class ItemCreate(BaseModel):
    warehouse_id: int
    sku: str
    name_ar: str
    name_en: str
    quantity: Decimal = Decimal("0")
    min_stock_level: Decimal = Decimal("0")
    unit: str = "pcs"


class ItemUpdate(BaseModel):
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    quantity: Optional[Decimal] = None
    min_stock_level: Optional[Decimal] = None
    unit: Optional[str] = None


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
    return [
        {
            "id": w.id,
            "name_ar": w.name_ar,
            "name_en": w.name_en,
            "code": w.code,
            "location": w.location,
            "is_active": w.is_active,
        }
        for w in warehouses
    ]


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


@router.put("/{warehouse_id}")
async def update_warehouse(
    warehouse_id: int,
    data: WarehouseUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    warehouse = result.scalar_one_or_none()
    if not warehouse:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")
    if not current_user.is_super_admin and warehouse.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(warehouse, field, value)
    await db.flush()
    return {"id": warehouse.id, "success": True}


@router.delete("/{warehouse_id}")
async def delete_warehouse(
    warehouse_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    warehouse = result.scalar_one_or_none()
    if not warehouse:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")
    if not current_user.is_super_admin and warehouse.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    warehouse.is_active = False
    await db.flush()
    return {"message": "Warehouse deactivated", "success": True}


@router.get("/items")
async def list_items(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    warehouse_id: Optional[int] = None,
):
    query = select(InventoryItem).order_by(InventoryItem.id.desc())
    if warehouse_id:
        query = query.where(InventoryItem.warehouse_id == warehouse_id)
    result = await db.execute(query)
    items = result.scalars().all()
    return [
        {
            "id": i.id,
            "warehouse_id": i.warehouse_id,
            "sku": i.sku,
            "name_ar": i.name_ar,
            "name_en": i.name_en,
            "quantity": float(i.quantity),
            "min_stock_level": float(i.min_stock_level),
            "low_stock": float(i.quantity) <= float(i.min_stock_level),
            "unit": i.unit,
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


@router.put("/items/{item_id}")
async def update_item(
    item_id: int,
    data: ItemUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.flush()
    return {"id": item.id, "success": True}


@router.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    await db.delete(item)
    await db.flush()
    return {"message": "Item deleted", "success": True}


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
