from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.warehouse import (
    EquipmentTransfer,
    HeavyEquipment,
    InventoryItem,
    StockMovement,
    Warehouse,
)
from app.models.users import User
from app.services.inventory_service import transfer_equipment, transfer_stock

router = APIRouter()


class WarehouseCreate(BaseModel):
    name_ar: str
    name_en: str
    code: str
    location: Optional[str] = None
    warehouse_type: str = "central"
    project_id: Optional[int] = None


class WarehouseUpdate(BaseModel):
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    code: Optional[str] = None
    location: Optional[str] = None
    warehouse_type: Optional[str] = None
    project_id: Optional[int] = None
    is_active: Optional[bool] = None


class ItemCreate(BaseModel):
    warehouse_id: int
    sku: str
    name_ar: str
    name_en: str
    quantity: Decimal = Decimal("0")
    min_stock_level: Decimal = Decimal("0")
    unit: str = "pcs"
    barcode: Optional[str] = None
    item_type: str = "raw_material"
    category: Optional[str] = None
    unit_cost: Decimal = Decimal("0")


class ItemUpdate(BaseModel):
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    quantity: Optional[Decimal] = None
    min_stock_level: Optional[Decimal] = None
    unit: Optional[str] = None
    barcode: Optional[str] = None
    category: Optional[str] = None
    unit_cost: Optional[Decimal] = None


class StockTransferCreate(BaseModel):
    item_id: int
    from_warehouse_id: int
    to_warehouse_id: int
    quantity: Decimal
    reference: Optional[str] = None
    notes: Optional[str] = None


class EquipmentCreate(BaseModel):
    asset_code: str
    name_ar: str
    name_en: str
    equipment_type: str
    serial_number: Optional[str] = None
    status: str = "available"
    current_warehouse_id: Optional[int] = None
    project_id: Optional[int] = None
    notes: Optional[str] = None


class EquipmentUpdate(BaseModel):
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    equipment_type: Optional[str] = None
    serial_number: Optional[str] = None
    status: Optional[str] = None
    current_warehouse_id: Optional[int] = None
    project_id: Optional[int] = None
    notes: Optional[str] = None


class EquipmentTransferCreate(BaseModel):
    equipment_id: int
    to_warehouse_id: int
    to_project_id: Optional[int] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


def _warehouse_dict(w: Warehouse) -> dict:
    return {
        "id": w.id,
        "name_ar": w.name_ar,
        "name_en": w.name_en,
        "code": w.code,
        "location": w.location,
        "warehouse_type": w.warehouse_type,
        "project_id": w.project_id,
        "is_active": w.is_active,
    }


@router.get("")
async def list_warehouses(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    warehouse_type: Optional[str] = None,
):
    query = select(Warehouse).order_by(Warehouse.id.desc())
    if not current_user.is_super_admin:
        query = query.where(Warehouse.company_id == current_user.company_id)
    if warehouse_type:
        query = query.where(Warehouse.warehouse_type == warehouse_type)
    result = await db.execute(query)
    return [_warehouse_dict(w) for w in result.scalars().all()]


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


@router.get("/summary")
async def warehouse_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    wh_query = select(Warehouse).where(
        Warehouse.company_id == current_user.company_id,
        Warehouse.is_active == True,
    )
    warehouses = (await db.execute(wh_query)).scalars().all()
    wh_ids = [w.id for w in warehouses]
    items: list[InventoryItem] = []
    if wh_ids:
        items = (
            await db.execute(
                select(InventoryItem).where(InventoryItem.warehouse_id.in_(wh_ids))
            )
        ).scalars().all()
    equipment_count = (
        await db.execute(
            select(HeavyEquipment).where(
                HeavyEquipment.company_id == current_user.company_id,
                HeavyEquipment.is_active == True,
            )
        )
    ).scalars().all()
    low_stock = sum(1 for i in items if float(i.quantity) <= float(i.min_stock_level))
    total_qty = sum(float(i.quantity) for i in items)
    central = sum(1 for w in warehouses if w.warehouse_type == "central")
    site = sum(1 for w in warehouses if w.warehouse_type == "site")
    return {
        "warehouses_count": len(warehouses),
        "central_warehouses": central,
        "site_warehouses": site,
        "items_count": len(items),
        "equipment_count": len(equipment_count),
        "low_stock_count": low_stock,
        "total_quantity": total_qty,
    }


@router.get("/items")
async def list_items(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    warehouse_id: Optional[int] = None,
    item_type: Optional[str] = None,
):
    query = (
        select(InventoryItem, Warehouse)
        .join(Warehouse, InventoryItem.warehouse_id == Warehouse.id)
        .order_by(InventoryItem.id.desc())
    )
    if not current_user.is_super_admin:
        query = query.where(Warehouse.company_id == current_user.company_id)
    if warehouse_id:
        query = query.where(InventoryItem.warehouse_id == warehouse_id)
    if item_type:
        query = query.where(InventoryItem.item_type == item_type)
    result = await db.execute(query)
    return [
        {
            "id": i.id,
            "warehouse_id": i.warehouse_id,
            "warehouse_name": w.name_en,
            "warehouse_code": w.code,
            "warehouse_type": w.warehouse_type,
            "sku": i.sku,
            "barcode": i.barcode,
            "name_ar": i.name_ar,
            "name_en": i.name_en,
            "item_type": i.item_type,
            "category": i.category,
            "quantity": float(i.quantity),
            "min_stock_level": float(i.min_stock_level),
            "low_stock": float(i.quantity) <= float(i.min_stock_level),
            "unit": i.unit,
            "unit_cost": float(i.unit_cost),
        }
        for i, w in result.all()
    ]


@router.post("/items")
async def create_item(
    data: ItemCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if current_user.company_id:
        wh = (
            await db.execute(
                select(Warehouse).where(
                    Warehouse.id == data.warehouse_id,
                    Warehouse.company_id == current_user.company_id,
                )
            )
        ).scalar_one_or_none()
        if not wh:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")
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


@router.post("/transfers")
async def create_stock_transfer(
    data: StockTransferCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    result = await transfer_stock(
        db,
        company_id=current_user.company_id,
        item_id=data.item_id,
        from_warehouse_id=data.from_warehouse_id,
        to_warehouse_id=data.to_warehouse_id,
        quantity=data.quantity,
        reference=data.reference,
        notes=data.notes,
        created_by_id=current_user.id,
    )
    return result


@router.get("/movements")
async def list_movements(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    limit: int = 100,
):
    from_wh = Warehouse.__table__.alias("from_wh")
    to_wh = Warehouse.__table__.alias("to_wh")
    query = (
        select(
            StockMovement,
            InventoryItem,
            from_wh.c.name_en.label("from_name"),
            to_wh.c.name_en.label("to_name"),
        )
        .join(InventoryItem, StockMovement.item_id == InventoryItem.id)
        .join(Warehouse, InventoryItem.warehouse_id == Warehouse.id)
        .outerjoin(from_wh, StockMovement.from_warehouse_id == from_wh.c.id)
        .outerjoin(to_wh, StockMovement.to_warehouse_id == to_wh.c.id)
        .order_by(StockMovement.id.desc())
        .limit(limit)
    )
    if not current_user.is_super_admin and current_user.company_id:
        query = query.where(Warehouse.company_id == current_user.company_id)

    result = await db.execute(query)
    return [
        {
            "id": m.id,
            "item_id": m.item_id,
            "item_name": i.name_en,
            "item_sku": i.sku,
            "movement_type": m.movement_type,
            "quantity": float(m.quantity),
            "from_warehouse_id": m.from_warehouse_id,
            "to_warehouse_id": m.to_warehouse_id,
            "from_warehouse_name": from_name,
            "to_warehouse_name": to_name,
            "reference": m.reference,
            "notes": m.notes,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m, i, from_name, to_name in result.all()
    ]


@router.get("/equipment")
async def list_equipment(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    query = select(HeavyEquipment).where(HeavyEquipment.is_active == True).order_by(HeavyEquipment.id.desc())
    if not current_user.is_super_admin and current_user.company_id:
        query = query.where(HeavyEquipment.company_id == current_user.company_id)
    equipment_list = (await db.execute(query)).scalars().all()
    wh_ids = {e.current_warehouse_id for e in equipment_list if e.current_warehouse_id}
    wh_map: dict[int, Warehouse] = {}
    if wh_ids:
        whs = (await db.execute(select(Warehouse).where(Warehouse.id.in_(wh_ids)))).scalars().all()
        wh_map = {w.id: w for w in whs}
    return [
        {
            "id": e.id,
            "asset_code": e.asset_code,
            "name_ar": e.name_ar,
            "name_en": e.name_en,
            "equipment_type": e.equipment_type,
            "serial_number": e.serial_number,
            "status": e.status,
            "current_warehouse_id": e.current_warehouse_id,
            "warehouse_name": wh_map[e.current_warehouse_id].name_en if e.current_warehouse_id in wh_map else None,
            "warehouse_type": wh_map[e.current_warehouse_id].warehouse_type if e.current_warehouse_id in wh_map else None,
            "project_id": e.project_id,
            "notes": e.notes,
        }
        for e in equipment_list
    ]


@router.post("/equipment")
async def create_equipment(
    data: EquipmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    equipment = HeavyEquipment(company_id=current_user.company_id, **data.model_dump())
    db.add(equipment)
    await db.flush()
    return {"id": equipment.id, "asset_code": equipment.asset_code}


@router.put("/equipment/{equipment_id}")
async def update_equipment(
    equipment_id: int,
    data: EquipmentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(HeavyEquipment).where(HeavyEquipment.id == equipment_id))
    equipment = result.scalar_one_or_none()
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    if not current_user.is_super_admin and equipment.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(equipment, field, value)
    await db.flush()
    return {"id": equipment.id, "success": True}


@router.delete("/equipment/{equipment_id}")
async def delete_equipment(
    equipment_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(HeavyEquipment).where(HeavyEquipment.id == equipment_id))
    equipment = result.scalar_one_or_none()
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    if not current_user.is_super_admin and equipment.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    equipment.is_active = False
    await db.flush()
    return {"message": "Equipment deactivated", "success": True}


@router.post("/equipment/transfers")
async def create_equipment_transfer(
    data: EquipmentTransferCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    return await transfer_equipment(
        db,
        company_id=current_user.company_id,
        equipment_id=data.equipment_id,
        to_warehouse_id=data.to_warehouse_id,
        to_project_id=data.to_project_id,
        reference=data.reference,
        notes=data.notes,
        created_by_id=current_user.id,
    )


@router.get("/equipment/transfers")
async def list_equipment_transfers(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    limit: int = 100,
):
    query = (
        select(EquipmentTransfer, HeavyEquipment)
        .join(HeavyEquipment, EquipmentTransfer.equipment_id == HeavyEquipment.id)
        .order_by(EquipmentTransfer.id.desc())
        .limit(limit)
    )
    if not current_user.is_super_admin and current_user.company_id:
        query = query.where(HeavyEquipment.company_id == current_user.company_id)
    result = await db.execute(query)
    rows = result.all()
    wh_ids: set[int] = set()
    for t, _ in rows:
        if t.from_warehouse_id:
            wh_ids.add(t.from_warehouse_id)
        if t.to_warehouse_id:
            wh_ids.add(t.to_warehouse_id)
    wh_map: dict[int, Warehouse] = {}
    if wh_ids:
        whs = (await db.execute(select(Warehouse).where(Warehouse.id.in_(wh_ids)))).scalars().all()
        wh_map = {w.id: w for w in whs}
    return [
        {
            "id": t.id,
            "equipment_id": t.equipment_id,
            "equipment_name": e.name_en,
            "asset_code": e.asset_code,
            "from_warehouse_id": t.from_warehouse_id,
            "to_warehouse_id": t.to_warehouse_id,
            "from_warehouse_name": wh_map[t.from_warehouse_id].name_en if t.from_warehouse_id in wh_map else None,
            "to_warehouse_name": wh_map[t.to_warehouse_id].name_en if t.to_warehouse_id in wh_map else None,
            "from_project_id": t.from_project_id,
            "to_project_id": t.to_project_id,
            "reference": t.reference,
            "notes": t.notes,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t, e in rows
    ]
