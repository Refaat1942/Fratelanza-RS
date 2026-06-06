from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.rbac import Permission, ROLE_PERMISSIONS
from app.db.session import get_db
from app.models import Project, Unit, UnitStatus, UnitType, User
from app.schemas import ProjectCreate, ProjectRead, UnitCreate, UnitRead

router = APIRouter()


@router.get("/projects", response_model=list[ProjectRead])
def list_projects(
    company_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PROJECTS_MANAGE)),
) -> list[Project]:
    query = select(Project).order_by(Project.created_at.desc())
    if Permission.PLATFORM_ALL in ROLE_PERMISSIONS[current_user.role]:
        if company_id:
            query = query.where(Project.company_id == company_id)
    else:
        query = query.where(Project.company_id == current_user.company_id)
    return list(db.scalars(query.limit(200)))


@router.post("/projects", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PROJECTS_MANAGE)),
) -> Project:
    company_id = payload.company_id
    if Permission.PLATFORM_ALL not in ROLE_PERMISSIONS[current_user.role]:
        company_id = current_user.company_id

    project = Project(**payload.model_dump(exclude={"company_id"}), company_id=company_id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/units", response_model=list[UnitRead])
def list_units(
    project_id: str | None = None,
    status_filter: UnitStatus | None = Query(default=None, alias="status"),
    unit_type: UnitType | None = None,
    company_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CUSTOMERS_READ)),
) -> list[Unit]:
    query = select(Unit).order_by(Unit.unit_code)
    if Permission.PLATFORM_ALL in ROLE_PERMISSIONS[current_user.role]:
        if company_id:
            query = query.where(Unit.company_id == company_id)
    else:
        query = query.where(Unit.company_id == current_user.company_id)

    if project_id:
        query = query.where(Unit.project_id == project_id)
    if status_filter:
        query = query.where(Unit.status == status_filter)
    if unit_type:
        query = query.where(Unit.unit_type == unit_type)
    return list(db.scalars(query.limit(500)))


@router.post("/units", response_model=UnitRead, status_code=status.HTTP_201_CREATED)
def create_unit(
    payload: UnitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.UNITS_MANAGE)),
) -> Unit:
    company_id = payload.company_id
    if Permission.PLATFORM_ALL not in ROLE_PERMISSIONS[current_user.role]:
        company_id = current_user.company_id

    unit = Unit(**payload.model_dump(exclude={"company_id"}), company_id=company_id)
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit
