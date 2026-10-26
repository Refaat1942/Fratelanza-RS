from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.core.tenant import ensure_refs
from app.models.tenant import Branch
from app.models.real_estate import Building, Floor, Project, Unit
from app.models.users import User
from app.schemas.common import PaginatedResponse
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate, UnitCreate, UnitResponse
from app.services.dynamic_pricing_service import DynamicPricingService
from app.services.master_plan_service import MasterPlanService
from app.services.unit_pricing_helpers import unit_to_response

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    if not current_user.company_id and not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    query = select(Project).where(Project.is_deleted == False)
    if not current_user.is_super_admin:
        query = query.where(Project.company_id == current_user.company_id)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(query.order_by(Project.id.desc()).offset((page - 1) * page_size).limit(page_size))
    projects = result.scalars().all()
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[ProjectResponse.model_validate(p) for p in projects],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("", response_model=ProjectResponse)
async def create_project(
    data: ProjectCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    await ensure_refs(db, current_user.company_id, [(Branch, data.branch_id, "Branch")])
    project = Project(company_id=current_user.company_id, **data.model_dump())
    db.add(project)
    await db.flush()
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}/master-plan")
async def get_master_plan(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    project = (
        await db.execute(
            select(Project).where(Project.id == project_id, Project.is_deleted == False)
        )
    ).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if not current_user.is_super_admin and project.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    plan = await MasterPlanService.get_master_plan(db, project_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return plan


@router.get("/{project_id}/units", response_model=PaginatedResponse[UnitResponse])
async def list_project_units(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
):
    project = (
        await db.execute(select(Project).where(Project.id == project_id, Project.is_deleted == False))
    ).scalar_one_or_none()
    if not project or (not current_user.is_super_admin and project.company_id != current_user.company_id):
        raise HTTPException(status_code=404, detail="Project not found")
    query = (
        select(Unit)
        .join(Floor, Unit.floor_id == Floor.id)
        .join(Building, Floor.building_id == Building.id)
        .where(Building.project_id == project_id, Unit.is_deleted == False, Unit.company_id == project.company_id)
    )
    if status:
        query = query.where(Unit.status == status)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    units = result.scalars().all()
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[unit_to_response(u) for u in units],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/units/board")
async def units_status_board(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    query = (
        select(Unit)
        .join(Floor, Unit.floor_id == Floor.id)
        .join(Building, Floor.building_id == Building.id)
        .join(Project, Building.project_id == Project.id)
        .where(Unit.is_deleted == False, Project.is_deleted == False)
    )
    if not current_user.is_super_admin:
        query = query.where(Unit.company_id == current_user.company_id)
    result = await db.execute(query)
    units = result.scalars().all()
    board: dict[str, list] = {}
    for u in units:
        st = u.status.value
        base = float(u.base_price or u.price)
        price = float(u.price)
        adjustment = round((price - base) / base * 100, 2) if base > 0 else 0.0
        board.setdefault(st, []).append(
            {
                "id": u.id,
                "unit_code": u.unit_code,
                "unit_number": u.unit_number,
                "unit_type": u.unit_type.value,
                "price": price,
                "base_price": base,
                "adjustment_percent": adjustment,
                "area_sqm": float(u.area_sqm),
            }
        )
    return board


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.is_deleted == False)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if not current_user.is_super_admin and project.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await db.flush()
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.is_deleted == False)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if not current_user.is_super_admin and project.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    project.soft_delete()
    await db.flush()
    return {"message": "Project deleted", "success": True}


@router.get("/floors")
async def list_floors(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    project_id: Optional[int] = None,
):
    query = (
        select(Floor, Building, Project)
        .join(Building, Floor.building_id == Building.id)
        .join(Project, Building.project_id == Project.id)
    )
    if not current_user.is_super_admin:
        query = query.where(Project.company_id == current_user.company_id)
    if project_id:
        query = query.where(Project.id == project_id)
    result = await db.execute(query)
    return [
        {
            "id": f.id,
            "building_id": f.building_id,
            "project_id": p.id,
            "project_name": p.name_ar,
            "floor_number": f.floor_number,
            "name_ar": f.name_ar,
            "name_en": f.name_en,
        }
        for f, b, p in result.all()
    ]


@router.post("/units", response_model=UnitResponse)
async def create_unit(
    data: UnitCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    payload = data.model_dump()
    if payload.get("base_price") is None:
        payload["base_price"] = payload["price"]
    # The unit inherits the tenant of the floor's project; a floor of another tenant is "not found".
    floor_row = (
        await db.execute(
            select(Floor, Project)
            .join(Building, Floor.building_id == Building.id)
            .join(Project, Building.project_id == Project.id)
            .where(Floor.id == data.floor_id, Project.is_deleted == False)
        )
    ).first()
    if not floor_row or (not current_user.is_super_admin and floor_row[1].company_id != current_user.company_id):
        raise HTTPException(status_code=404, detail="Floor not found")
    company_id = floor_row[1].company_id
    from app.models.rentals import PropertyOwner

    await ensure_refs(db, company_id, [(PropertyOwner, data.owner_id, "Owner")])
    duplicate = (
        await db.execute(
            select(Unit.id).where(
                Unit.company_id == company_id, Unit.unit_code == data.unit_code, Unit.is_deleted == False
            )
        )
    ).first()
    if duplicate:
        raise HTTPException(status_code=400, detail="Unit code already exists")
    unit = Unit(company_id=company_id, **payload)
    db.add(unit)
    await db.flush()
    await DynamicPricingService.recalculate_project_prices(db, company_id, floor_row[1].id)
    return unit_to_response(unit)


@router.delete("/units/{unit_id}")
async def delete_unit(
    unit_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(Unit).where(Unit.id == unit_id, Unit.is_deleted == False))
    unit = result.scalar_one_or_none()
    if not unit or (not current_user.is_super_admin and unit.company_id != current_user.company_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    unit.soft_delete()
    await db.flush()
    return {"message": "Unit deleted", "success": True}


class BuildingCreate(BaseModel):
    name_ar: str
    name_en: str
    code: str
    total_floors: int = 0


class FloorCreate(BaseModel):
    floor_number: int
    name_ar: Optional[str] = None
    name_en: Optional[str] = None


@router.post("/{project_id}/buildings")
async def create_building(
    project_id: int,
    data: BuildingCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    project = (
        await db.execute(select(Project).where(Project.id == project_id, Project.is_deleted == False))
    ).scalar_one_or_none()
    if not project or (not current_user.is_super_admin and project.company_id != current_user.company_id):
        raise HTTPException(status_code=404, detail="Project not found")
    building = Building(project_id=project.id, **data.model_dump())
    db.add(building)
    await db.flush()
    return {"id": building.id, "project_id": project.id, "code": building.code}


@router.post("/buildings/{building_id}/floors")
async def create_floor(
    building_id: int,
    data: FloorCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    row = (
        await db.execute(
            select(Building, Project)
            .join(Project, Building.project_id == Project.id)
            .where(Building.id == building_id, Building.is_deleted == False, Project.is_deleted == False)
        )
    ).first()
    if not row or (not current_user.is_super_admin and row[1].company_id != current_user.company_id):
        raise HTTPException(status_code=404, detail="Building not found")
    floor = Floor(building_id=building_id, **data.model_dump())
    db.add(floor)
    await db.flush()
    return {"id": floor.id, "building_id": building_id, "floor_number": floor.floor_number}
