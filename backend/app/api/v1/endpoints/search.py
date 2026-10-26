from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_access, get_company_user
from app.core.tenant import apply_data_scope
from app.services.access_service import AccessContext
from app.core.database import get_db
from app.models.brokers import Broker
from app.models.crm import Lead
from app.models.customers import Customer
from app.models.real_estate import Building, Floor, Project, Unit
from app.models.sales import Contract, Reservation
from app.models.users import User

router = APIRouter()


@router.get("")
async def global_search(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
    q: str = Query(min_length=2),
    limit: int = Query(10, ge=1, le=50),
):
    company_id = current_user.company_id

    customers_q = select(Customer).where(
        Customer.is_deleted == False,
        or_(
            Customer.full_name_ar.ilike(f"%{q}%"),
            Customer.full_name_en.ilike(f"%{q}%"),
            Customer.mobile.ilike(f"%{q}%"),
            Customer.email.ilike(f"%{q}%"),
        ),
    )
    if not current_user.is_super_admin and company_id:
        customers_q = customers_q.where(Customer.company_id == company_id)
        customers_q = apply_data_scope(customers_q, Customer.assigned_to_id, access, current_user)
    customers = (await db.execute(customers_q.limit(limit))).scalars().all()

    leads_q = select(Lead).where(
        Lead.is_deleted == False,
        or_(Lead.full_name.ilike(f"%{q}%"), Lead.mobile.ilike(f"%{q}%")),
    )
    if not current_user.is_super_admin and company_id:
        leads_q = leads_q.where(Lead.company_id == company_id)
        leads_q = apply_data_scope(leads_q, Lead.assigned_to_id, access, current_user)
    leads = (await db.execute(leads_q.limit(limit))).scalars().all()

    contracts_q = select(Contract).where(
        Contract.is_deleted == False,
        Contract.contract_number.ilike(f"%{q}%"),
    )
    if not current_user.is_super_admin and company_id:
        contracts_q = contracts_q.where(Contract.company_id == company_id)
    contracts = (await db.execute(contracts_q.limit(limit))).scalars().all()

    units_q = (
        select(Unit, Project)
        .join(Floor, Unit.floor_id == Floor.id)
        .join(Building, Floor.building_id == Building.id)
        .join(Project, Building.project_id == Project.id)
        .where(
            Unit.is_deleted == False,
            or_(Unit.unit_code.ilike(f"%{q}%"), Unit.unit_number.ilike(f"%{q}%")),
        )
    )
    if not current_user.is_super_admin and company_id:
        units_q = units_q.where(Project.company_id == company_id)
    units = (await db.execute(units_q.limit(limit))).all()

    projects_q = select(Project).where(
        Project.is_deleted == False,
        or_(
            Project.name_ar.ilike(f"%{q}%"),
            Project.name_en.ilike(f"%{q}%"),
            Project.code.ilike(f"%{q}%"),
        ),
    )
    if not current_user.is_super_admin and company_id:
        projects_q = projects_q.where(Project.company_id == company_id)
    projects = (await db.execute(projects_q.limit(limit))).scalars().all()

    brokers_q = select(Broker).where(
        Broker.is_deleted == False,
        or_(
            Broker.name_ar.ilike(f"%{q}%"),
            Broker.name_en.ilike(f"%{q}%"),
            Broker.mobile.ilike(f"%{q}%"),
        ),
    )
    if not current_user.is_super_admin and company_id:
        brokers_q = brokers_q.where(Broker.company_id == company_id)
    brokers = (await db.execute(brokers_q.limit(limit))).scalars().all()

    reservations_q = select(Reservation).where(
        Reservation.is_deleted == False,
        Reservation.reservation_number.ilike(f"%{q}%"),
    )
    if not current_user.is_super_admin and company_id:
        reservations_q = reservations_q.where(Reservation.company_id == company_id)
    reservations = (await db.execute(reservations_q.limit(limit))).scalars().all()

    # Only return result groups for modules the caller can view (search is not a side door)
    if not access.can("customers"):
        customers = []
    if not access.can("leads"):
        leads = []
    if not access.can("contracts"):
        contracts = []
    if not access.can("projects"):
        units, projects = [], []
    if not access.can("brokers"):
        brokers = []
    if not access.can("reservations"):
        reservations = []
    return {
        "customers": [
            {"id": c.id, "name": c.full_name_en, "mobile": c.mobile, "type": "customer", "route": "/customers"}
            for c in customers
        ],
        "leads": [
            {"id": l.id, "name": l.full_name, "mobile": l.mobile, "stage": l.stage.value, "type": "lead", "route": "/leads"}
            for l in leads
        ],
        "contracts": [
            {"id": c.id, "number": c.contract_number, "type": "contract", "route": "/contracts"}
            for c in contracts
        ],
        "units": [
            {"id": u.id, "code": u.unit_code, "number": u.unit_number, "project": p.name_en, "type": "unit", "route": "/projects"}
            for u, p in units
        ],
        "projects": [
            {"id": p.id, "name": p.name_en, "code": p.code, "type": "project", "route": "/projects"}
            for p in projects
        ],
        "brokers": [
            {"id": b.id, "name": b.name_en, "mobile": b.mobile, "type": "broker", "route": "/brokers"}
            for b in brokers
        ],
        "reservations": [
            {"id": r.id, "number": r.reservation_number, "type": "reservation", "route": "/reservations"}
            for r in reservations
        ],
    }
