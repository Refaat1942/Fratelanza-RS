from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.rbac import Permission, ROLE_PERMISSIONS
from app.db.session import get_db
from app.models import Customer, User
from app.schemas import CustomerCreate, CustomerRead

router = APIRouter()


@router.get("", response_model=list[CustomerRead])
def search_customers(
    q: str | None = Query(default=None, min_length=2),
    company_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CUSTOMERS_READ)),
) -> list[Customer]:
    query = select(Customer).order_by(Customer.created_at.desc())
    if Permission.PLATFORM_ALL in ROLE_PERMISSIONS[current_user.role]:
        if company_id:
            query = query.where(Customer.company_id == company_id)
    else:
        query = query.where(Customer.company_id == current_user.company_id)

    if q:
        like = f"%{q}%"
        query = query.where(
            or_(
                Customer.full_name.ilike(like),
                Customer.mobile.ilike(like),
                Customer.email.ilike(like),
                Customer.national_id.ilike(like),
                Customer.passport_number.ilike(like),
            )
        )
    return list(db.scalars(query.limit(100)))


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CUSTOMERS_WRITE)),
) -> Customer:
    customer = Customer(company_id=current_user.company_id, **payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer
