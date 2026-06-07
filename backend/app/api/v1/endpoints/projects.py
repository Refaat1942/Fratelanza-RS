from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.real_estate import Building, Floor, Project, Unit
from app.models.users import User
from app.schemas.common import PaginatedResponse
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate, UnitCreate, UnitResponse

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
        select(Unit, Project)
        .join(Floor, Unit.floor_id == Floor.id)
        .join(Building, Floor.building_id == Building.id)
        .join(Project, Building.project_id == Project.id)
        .where(Unit.is_deleted == False)
    )
    if not current_user.is_super_admin and current_user.company_id:
        query = query.where(Project.company_id == current_user.company_id)
    result = await db.execute(query)
    board: dict[str, list] = {}
    for u, project in result.all():
        st = u.status.value
        board.setdefault(st, []).append(
            {
                "id": u.id,
                "unit_code": u.unit_code,
                "unit_number": u.unit_number,
                "unit_type": u.unit_type.value,
                "price": float(u.price),
                "area_sqm": float(u.area_sqm),
                "project_id": project.id,
                "project_name": project.name_en,
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
    if not current_user.is_super_admin and current_user.company_id:
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
    unit = Unit(**data.model_dump())
    db.add(unit)
    await db.flush()
    return UnitResponse.model_validate(unit)


@router.delete("/units/{unit_id}")
async def delete_unit(
    unit_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(Unit).where(Unit.id == unit_id, Unit.is_deleted == False))
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    unit.soft_delete()
    await db.flush()
    return {"message": "Unit deleted", "success": True}
