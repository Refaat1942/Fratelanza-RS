from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.real_estate import Building, Floor, Project, Unit
from app.models.users import User
from app.schemas.common import PaginatedResponse
from app.schemas.project import ProjectCreate, ProjectResponse, UnitCreate, UnitResponse

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
    project = Project(company_id=current_user.company_id, **data.model_dump())
    db.add(project)
    await db.flush()
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}/units", response_model=PaginatedResponse[UnitResponse])
async def list_project_units(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
):
    query = (
        select(Unit)
        .join(Floor, Unit.floor_id == Floor.id)
        .join(Building, Floor.building_id == Building.id)
        .where(Building.project_id == project_id, Unit.is_deleted == False)
    )
    if status:
        query = query.where(Unit.status == status)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    units = result.scalars().all()
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[UnitResponse.model_validate(u) for u in units],
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
        .where(Unit.is_deleted == False)
    )
    if not current_user.is_super_admin and current_user.company_id:
        query = query.where(Project.company_id == current_user.company_id)
    result = await db.execute(query)
    units = result.scalars().all()
    board: dict[str, list] = {}
    for u in units:
        st = u.status.value
        board.setdefault(st, []).append(
            {
                "id": u.id,
                "unit_code": u.unit_code,
                "unit_number": u.unit_number,
                "unit_type": u.unit_type.value,
                "price": float(u.price),
                "area_sqm": float(u.area_sqm),
            }
        )
    return board


@router.post("/units", response_model=UnitResponse)
async def create_unit(
    data: UnitCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    unit = Unit(**data.model_dump())
    db.add(unit)
    await db.flush()
    return UnitResponse.model_validate(unit)
