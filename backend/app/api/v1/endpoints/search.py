from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.customers import Customer
from app.models.real_estate import Building, Floor, Project, Unit
from app.models.sales import Contract, Payment
from app.models.users import User

router = APIRouter()


@router.get("")
async def global_search(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    q: str = Query(min_length=2),
    limit: int = Query(10, ge=1, le=50),
):
    company_filter = True
    company_id = current_user.company_id

    customers_q = select(Customer).where(
        Customer.is_deleted == False,
        or_(
            Customer.full_name_ar.ilike(f"%{q}%"),
            Customer.full_name_en.ilike(f"%{q}%"),
            Customer.mobile.ilike(f"%{q}%"),
        ),
    )
    if not current_user.is_super_admin and company_id:
        customers_q = customers_q.where(Customer.company_id == company_id)
    customers = (await db.execute(customers_q.limit(limit))).scalars().all()

    contracts_q = select(Contract).where(
        Contract.is_deleted == False,
        Contract.contract_number.ilike(f"%{q}%"),
    )
    if not current_user.is_super_admin and company_id:
        contracts_q = contracts_q.where(Contract.company_id == company_id)
    contracts = (await db.execute(contracts_q.limit(limit))).scalars().all()

    units_q = (
        select(Unit)
        .join(Floor)
        .join(Building)
        .join(Project)
        .where(
            Unit.is_deleted == False,
            or_(Unit.unit_code.ilike(f"%{q}%"), Unit.unit_number.ilike(f"%{q}%")),
        )
    )
    if not current_user.is_super_admin and company_id:
        units_q = units_q.where(Project.company_id == company_id)
    units = (await db.execute(units_q.limit(limit))).scalars().all()

    return {
        "customers": [{"id": c.id, "name": c.full_name_ar, "mobile": c.mobile} for c in customers],
        "contracts": [{"id": c.id, "number": c.contract_number} for c in contracts],
        "units": [{"id": u.id, "code": u.unit_code, "number": u.unit_number} for u in units],
    }
