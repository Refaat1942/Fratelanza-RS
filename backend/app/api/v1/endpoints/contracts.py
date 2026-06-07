from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.customers import Customer
from app.models.real_estate import Building, Floor, Project, Unit
from app.models.sales import Contract, ContractStatus
from app.models.users import User
from app.schemas.project import ContractCreate, ContractUpdate
from app.services.contract_service import ContractService

router = APIRouter()


def _contract_dict(
    c: Contract,
    customer: Customer | None = None,
    unit: Unit | None = None,
    project: Project | None = None,
) -> dict:
    return {
        "id": c.id,
        "contract_number": c.contract_number,
        "customer_id": c.customer_id,
        "customer_name": (customer.full_name_ar if customer else None),
        "unit_id": c.unit_id,
        "unit_code": (unit.unit_code if unit else None),
        "project_id": (project.id if project else None),
        "project_name": (project.name_en if project else None),
        "reservation_id": c.reservation_id,
        "total_price": float(c.total_price),
        "contract_date": c.contract_date,
        "status": c.status.value,
        "is_signed": c.is_signed,
    }


@router.get("")
async def list_contracts(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    company_id = None if current_user.is_super_admin else current_user.company_id
    query = (
        select(Contract, Customer, Unit, Project)
        .join(Customer, Contract.customer_id == Customer.id)
        .join(Unit, Contract.unit_id == Unit.id)
        .join(Floor, Unit.floor_id == Floor.id)
        .join(Building, Floor.building_id == Building.id)
        .join(Project, Building.project_id == Project.id)
        .where(Contract.is_deleted == False)
    )
    if company_id:
        query = query.where(Contract.company_id == company_id)
    result = await db.execute(query.order_by(Contract.id.desc()))
    return [_contract_dict(c, cust, u, p) for c, cust, u, p in result.all()]


@router.post("")
async def create_contract(
    data: ContractCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    contract = await ContractService.create_contract(db, current_user.company_id, data)
    return {"id": contract.id, "contract_number": contract.contract_number, "status": contract.status.value}


@router.put("/{contract_id}")
async def update_contract(
    contract_id: int,
    data: ContractUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id, Contract.is_deleted == False)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    if not current_user.is_super_admin and contract.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "status" and value:
            setattr(contract, field, ContractStatus(value))
        else:
            setattr(contract, field, value)
    await db.flush()
    cust = (await db.execute(select(Customer).where(Customer.id == contract.customer_id))).scalar_one_or_none()
    unit = (await db.execute(select(Unit).where(Unit.id == contract.unit_id))).scalar_one_or_none()
    return _contract_dict(contract, cust, unit)


@router.delete("/{contract_id}")
async def delete_contract(
    contract_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id, Contract.is_deleted == False)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    if not current_user.is_super_admin and contract.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    contract.soft_delete()
    await db.flush()
    return {"message": "Contract deleted", "success": True}
