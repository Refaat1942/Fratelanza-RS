from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.users import User
from app.schemas.project import ContractCreate
from app.services.contract_service import ContractService

router = APIRouter()


@router.get("")
async def list_contracts(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    company_id = None if current_user.is_super_admin else current_user.company_id
    contracts = await ContractService.list_contracts(db, company_id)
    return [
        {
            "id": c.id,
            "contract_number": c.contract_number,
            "customer_id": c.customer_id,
            "unit_id": c.unit_id,
            "total_price": float(c.total_price),
            "contract_date": c.contract_date,
            "status": c.status.value,
            "is_signed": c.is_signed,
        }
        for c in contracts
    ]


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
