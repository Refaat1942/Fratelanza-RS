from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.customers import Customer, CustomerActivity
from app.models.users import User
from app.schemas.common import PaginatedResponse
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate

router = APIRouter()


@router.get("", response_model=PaginatedResponse[CustomerResponse])
async def list_customers(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
):
    if not current_user.company_id and not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    query = select(Customer).where(Customer.is_deleted == False)
    if not current_user.is_super_admin:
        query = query.where(Customer.company_id == current_user.company_id)
    if search:
        query = query.where(
            or_(
                Customer.full_name_ar.ilike(f"%{search}%"),
                Customer.full_name_en.ilike(f"%{search}%"),
                Customer.mobile.ilike(f"%{search}%"),
            )
        )
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(query.order_by(Customer.id.desc()).offset((page - 1) * page_size).limit(page_size))
    customers = result.scalars().all()
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[CustomerResponse.model_validate(c) for c in customers],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("", response_model=CustomerResponse)
async def create_customer(
    data: CustomerCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    customer = Customer(company_id=current_user.company_id, **data.model_dump())
    db.add(customer)
    await db.flush()
    return CustomerResponse.model_validate(customer)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    if not current_user.is_super_admin and customer.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return CustomerResponse.model_validate(customer)


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    if not current_user.is_super_admin and customer.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)
    await db.flush()
    return CustomerResponse.model_validate(customer)


@router.get("/{customer_id}/timeline")
async def get_customer_timeline(
    customer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(
        select(CustomerActivity)
        .where(CustomerActivity.customer_id == customer_id)
        .order_by(CustomerActivity.created_at.desc())
    )
    activities = result.scalars().all()
    return [
        {
            "id": a.id,
            "activity_type": a.activity_type.value,
            "title": a.title,
            "description": a.description,
            "created_at": str(a.created_at),
        }
        for a in activities
    ]
