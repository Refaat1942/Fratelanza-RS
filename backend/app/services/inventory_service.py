from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.warehouse import (
    EquipmentTransfer,
    HeavyEquipment,
    InventoryItem,
    StockMovement,
    Warehouse,
)


async def _get_warehouse_for_company(
    db: AsyncSession, warehouse_id: int, company_id: int
) -> Warehouse:
    result = await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    warehouse = result.scalar_one_or_none()
    if not warehouse or warehouse.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")
    if not warehouse.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Warehouse is inactive")
    return warehouse


async def transfer_stock(
    db: AsyncSession,
    *,
    company_id: int,
    item_id: int,
    from_warehouse_id: int,
    to_warehouse_id: int,
    quantity: Decimal,
    reference: str | None,
    notes: str | None,
    created_by_id: int | None,
) -> dict:
    if from_warehouse_id == to_warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source and destination warehouses must differ",
        )
    if quantity <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be positive")

    await _get_warehouse_for_company(db, from_warehouse_id, company_id)
    await _get_warehouse_for_company(db, to_warehouse_id, company_id)

    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.id == item_id,
            InventoryItem.warehouse_id == from_warehouse_id,
        )
    )
    source_item = result.scalar_one_or_none()
    if not source_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in source warehouse")
    if source_item.quantity < quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")

    dest_result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.warehouse_id == to_warehouse_id,
            InventoryItem.sku == source_item.sku,
        )
    )
    dest_item = dest_result.scalar_one_or_none()
    if not dest_item:
        dest_item = InventoryItem(
            warehouse_id=to_warehouse_id,
            sku=source_item.sku,
            barcode=source_item.barcode,
            name_ar=source_item.name_ar,
            name_en=source_item.name_en,
            item_type=source_item.item_type,
            category=source_item.category,
            quantity=Decimal("0"),
            min_stock_level=source_item.min_stock_level,
            unit=source_item.unit,
            unit_cost=source_item.unit_cost,
        )
        db.add(dest_item)
        await db.flush()

    source_item.quantity -= quantity
    dest_item.quantity += quantity

    movement = StockMovement(
        item_id=source_item.id,
        movement_type="transfer",
        quantity=quantity,
        from_warehouse_id=from_warehouse_id,
        to_warehouse_id=to_warehouse_id,
        reference=reference,
        notes=notes,
        created_by_id=created_by_id,
    )
    db.add(movement)
    await db.flush()

    return {
        "movement_id": movement.id,
        "source_item_id": source_item.id,
        "dest_item_id": dest_item.id,
        "source_quantity": float(source_item.quantity),
        "dest_quantity": float(dest_item.quantity),
    }


async def transfer_equipment(
    db: AsyncSession,
    *,
    company_id: int,
    equipment_id: int,
    to_warehouse_id: int,
    to_project_id: int | None,
    reference: str | None,
    notes: str | None,
    created_by_id: int | None,
) -> dict:
    result = await db.execute(
        select(HeavyEquipment).where(
            HeavyEquipment.id == equipment_id,
            HeavyEquipment.company_id == company_id,
            HeavyEquipment.is_active == True,
        )
    )
    equipment = result.scalar_one_or_none()
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")

    to_warehouse = await _get_warehouse_for_company(db, to_warehouse_id, company_id)
    if to_warehouse.id == equipment.current_warehouse_id and to_project_id == equipment.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Equipment is already at the destination",
        )

    transfer = EquipmentTransfer(
        equipment_id=equipment.id,
        from_warehouse_id=equipment.current_warehouse_id,
        to_warehouse_id=to_warehouse_id,
        from_project_id=equipment.project_id,
        to_project_id=to_project_id,
        reference=reference,
        notes=notes,
        created_by_id=created_by_id,
    )
    db.add(transfer)

    equipment.current_warehouse_id = to_warehouse_id
    equipment.project_id = to_project_id
    equipment.status = "in_use" if to_warehouse.warehouse_type == "site" else "available"
    await db.flush()

    return {"transfer_id": transfer.id, "equipment_id": equipment.id}
