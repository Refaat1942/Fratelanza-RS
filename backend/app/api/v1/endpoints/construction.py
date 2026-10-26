from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.construction import (
    ConstructionMilestone,
    ConstructionPhase,
    ConstructionTask,
    ProjectProgressUpdate,
)
from app.models.real_estate import Project
from app.models.users import User
from app.services.dynamic_pricing_service import DynamicPricingService

router = APIRouter()


async def _owned_project(db: AsyncSession, project_id: int, user: User) -> Project:
    project = (
        await db.execute(select(Project).where(Project.id == project_id, Project.is_deleted == False))  # noqa: E712
    ).scalar_one_or_none()
    if not project or (not user.is_super_admin and project.company_id != user.company_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


async def _owned_phase(db: AsyncSession, phase_id: int, user: User) -> ConstructionPhase:
    phase = (await db.execute(select(ConstructionPhase).where(ConstructionPhase.id == phase_id))).scalar_one_or_none()
    if not phase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phase not found")
    project = (await db.execute(select(Project).where(Project.id == phase.project_id))).scalar_one_or_none()
    if not project or (not user.is_super_admin and project.company_id != user.company_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phase not found")
    return phase


class PhaseCreate(BaseModel):
    project_id: int
    name_ar: str
    name_en: str
    planned_start: Optional[str] = None
    planned_end: Optional[str] = None


class PhaseUpdate(BaseModel):
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    planned_start: Optional[str] = None
    planned_end: Optional[str] = None
    progress_percent: Optional[int] = None
    planned_cost: Optional[float] = None
    actual_cost: Optional[float] = None


@router.get("/phases")
async def list_phases(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    project_id: Optional[int] = None,
):
    query = (
        select(ConstructionPhase, Project)
        .join(Project, ConstructionPhase.project_id == Project.id)
        .order_by(ConstructionPhase.id.desc())
    )
    if not current_user.is_super_admin and current_user.company_id:
        query = query.where(Project.company_id == current_user.company_id)
    if project_id:
        query = query.where(ConstructionPhase.project_id == project_id)
    result = await db.execute(query)
    return [
        {
            "id": p.id,
            "project_id": p.project_id,
            "project_name": proj.name_ar,
            "name_ar": p.name_ar,
            "name_en": p.name_en,
            "progress_percent": p.progress_percent,
            "planned_cost": float(p.planned_cost),
            "actual_cost": float(p.actual_cost),
            "planned_start": p.planned_start,
            "planned_end": p.planned_end,
        }
        for p, proj in result.all()
    ]


@router.post("/phases")
async def create_phase(
    data: PhaseCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    await _owned_project(db, data.project_id, current_user)
    phase = ConstructionPhase(**data.model_dump())
    db.add(phase)
    await db.flush()
    return {"id": phase.id, "name_ar": phase.name_ar}


@router.put("/phases/{phase_id}")
async def update_phase(
    phase_id: int,
    data: PhaseUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    phase = await _owned_phase(db, phase_id, current_user)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(phase, field, value)
    await db.flush()
    if data.progress_percent is not None:
        project = (
            await db.execute(select(Project).where(Project.id == phase.project_id))
        ).scalar_one_or_none()
        if project:
            await DynamicPricingService.recalculate_project_prices(
                db, project.company_id, phase.project_id
            )
    return {"id": phase.id, "success": True}


@router.delete("/phases/{phase_id}")
async def delete_phase(
    phase_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    phase = await _owned_phase(db, phase_id, current_user)
    await db.delete(phase)
    await db.flush()
    return {"message": "Phase deleted", "success": True}


@router.get("/tasks")
async def list_tasks(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    phase_id: Optional[int] = None,
):
    query = (
        select(ConstructionTask)
        .join(ConstructionPhase, ConstructionTask.phase_id == ConstructionPhase.id)
        .join(Project, ConstructionPhase.project_id == Project.id)
        .order_by(ConstructionTask.id.desc())
    )
    if not current_user.is_super_admin:
        query = query.where(Project.company_id == current_user.company_id)
    if phase_id:
        query = query.where(ConstructionTask.phase_id == phase_id)
    result = await db.execute(query)
    tasks = result.scalars().all()
    return [
        {
            "id": t.id,
            "phase_id": t.phase_id,
            "name_ar": t.name_ar,
            "status": t.status,
            "progress_percent": t.progress_percent,
            "contractor": t.contractor,
        }
        for t in tasks
    ]


@router.get("/milestones")
async def list_milestones(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    project_id: Optional[int] = None,
):
    query = (
        select(ConstructionMilestone)
        .join(Project, ConstructionMilestone.project_id == Project.id)
        .order_by(ConstructionMilestone.target_date)
    )
    if not current_user.is_super_admin:
        query = query.where(Project.company_id == current_user.company_id)
    if project_id:
        query = query.where(ConstructionMilestone.project_id == project_id)
    result = await db.execute(query)
    milestones = result.scalars().all()
    return [
        {
            "id": m.id,
            "project_id": m.project_id,
            "name_ar": m.name_ar,
            "target_date": m.target_date,
            "status": m.status,
        }
        for m in milestones
    ]


class ProgressUpdateCreate(BaseModel):
    project_id: int
    title_ar: str
    title_en: str
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    media_type: str = "image"
    media_url: str
    thumbnail_url: Optional[str] = None
    progress_percent: Optional[int] = None
    published_at: str


@router.get("/progress-updates")
async def list_progress_updates(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    project_id: Optional[int] = None,
):
    query = (
        select(ProjectProgressUpdate, Project)
        .join(Project, ProjectProgressUpdate.project_id == Project.id)
        .order_by(ProjectProgressUpdate.published_at.desc())
    )
    if not current_user.is_super_admin and current_user.company_id:
        query = query.where(ProjectProgressUpdate.company_id == current_user.company_id)
    if project_id:
        query = query.where(ProjectProgressUpdate.project_id == project_id)
    result = await db.execute(query)
    return [
        {
            "id": u.id,
            "project_id": u.project_id,
            "project_name": p.name_en,
            "title_en": u.title_en,
            "title_ar": u.title_ar,
            "media_type": u.media_type,
            "media_url": u.media_url,
            "progress_percent": u.progress_percent,
            "published_at": u.published_at,
            "is_published": u.is_published,
        }
        for u, p in result.all()
    ]


@router.post("/progress-updates")
async def create_progress_update(
    data: ProgressUpdateCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    await _owned_project(db, data.project_id, current_user)
    update = ProjectProgressUpdate(company_id=current_user.company_id, **data.model_dump())
    db.add(update)
    await db.flush()
    return {"id": update.id, "success": True}
