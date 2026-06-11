from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.construction import ConstructionMilestone, ConstructionPhase, ConstructionTask
from app.models.real_estate import Project
from app.models.users import User
from app.services.construction_service import ConstructionService

router = APIRouter()


class PhaseCreate(BaseModel):
    project_id: int
    name_ar: str
    name_en: str
    planned_start: Optional[str] = None
    planned_end: Optional[str] = None
    progress_percent: int = Field(default=0, ge=0, le=100)


class PhaseUpdate(BaseModel):
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    planned_start: Optional[str] = None
    planned_end: Optional[str] = None
    progress_percent: Optional[int] = Field(default=None, ge=0, le=100)
    planned_cost: Optional[float] = None
    actual_cost: Optional[float] = None


class PhaseProgressUpdate(BaseModel):
    progress_percent: int = Field(ge=0, le=100)


class TaskCreate(BaseModel):
    phase_id: int
    name_ar: str
    name_en: str
    contractor: Optional[str] = None
    planned_start: Optional[str] = None
    planned_end: Optional[str] = None
    depends_on_task_id: Optional[int] = None
    status: str = "pending"
    progress_percent: int = Field(default=0, ge=0, le=100)
    planned_cost: float = 0
    actual_cost: float = 0


class TaskUpdate(BaseModel):
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    contractor: Optional[str] = None
    planned_start: Optional[str] = None
    planned_end: Optional[str] = None
    depends_on_task_id: Optional[int] = None
    status: Optional[str] = None
    progress_percent: Optional[int] = Field(default=None, ge=0, le=100)
    planned_cost: Optional[float] = None
    actual_cost: Optional[float] = None


def _company_id(user: User) -> Optional[int]:
    if user.is_super_admin:
        return None
    if not user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    return user.company_id


async def _verify_project(db: AsyncSession, project_id: int, company_id: Optional[int]) -> Project:
    project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if company_id and project.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return project


def _task_dict(t: ConstructionTask, phase_name: str = "") -> dict:
    return {
        "id": t.id,
        "phase_id": t.phase_id,
        "phase_name": phase_name,
        "name_ar": t.name_ar,
        "name_en": t.name_en,
        "contractor": t.contractor,
        "planned_start": t.planned_start,
        "planned_end": t.planned_end,
        "depends_on_task_id": t.depends_on_task_id,
        "status": t.status,
        "progress_percent": t.progress_percent,
        "planned_cost": float(t.planned_cost),
        "actual_cost": float(t.actual_cost),
    }


@router.get("/phases")
async def list_phases(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    project_id: Optional[int] = None,
):
    company_id = _company_id(current_user)
    query = (
        select(ConstructionPhase, Project)
        .join(Project, ConstructionPhase.project_id == Project.id)
        .order_by(ConstructionPhase.id.desc())
    )
    if company_id:
        query = query.where(Project.company_id == company_id)
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
    await _verify_project(db, data.project_id, _company_id(current_user))
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
    phase = await ConstructionService.get_phase_for_company(db, phase_id, _company_id(current_user))
    if not phase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phase not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(phase, field, value)
    await db.flush()
    return {"id": phase.id, "success": True, "progress_percent": phase.progress_percent}


@router.patch("/phases/{phase_id}/progress")
async def update_phase_progress(
    phase_id: int,
    data: PhaseProgressUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    phase = await ConstructionService.get_phase_for_company(db, phase_id, _company_id(current_user))
    if not phase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phase not found")
    phase.progress_percent = data.progress_percent
    await db.flush()
    return {"id": phase.id, "progress_percent": phase.progress_percent}


@router.delete("/phases/{phase_id}")
async def delete_phase(
    phase_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    phase = await ConstructionService.get_phase_for_company(db, phase_id, _company_id(current_user))
    if not phase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phase not found")
    await db.delete(phase)
    await db.flush()
    return {"message": "Phase deleted", "success": True}


@router.get("/tasks")
async def list_tasks(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    phase_id: Optional[int] = None,
    project_id: Optional[int] = None,
):
    company_id = _company_id(current_user)
    query = (
        select(ConstructionTask, ConstructionPhase, Project)
        .join(ConstructionPhase, ConstructionTask.phase_id == ConstructionPhase.id)
        .join(Project, ConstructionPhase.project_id == Project.id)
        .order_by(ConstructionTask.id.desc())
    )
    if company_id:
        query = query.where(Project.company_id == company_id)
    if phase_id:
        query = query.where(ConstructionTask.phase_id == phase_id)
    if project_id:
        query = query.where(ConstructionPhase.project_id == project_id)
    result = await db.execute(query)
    return [_task_dict(t, p.name_ar) for t, p, _ in result.all()]


@router.post("/tasks")
async def create_task(
    data: TaskCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    rollup_phase: bool = Query(True),
):
    phase = await ConstructionService.get_phase_for_company(db, data.phase_id, _company_id(current_user))
    if not phase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phase not found")
    if data.depends_on_task_id:
        dep = (await db.execute(select(ConstructionTask).where(ConstructionTask.id == data.depends_on_task_id))).scalar_one_or_none()
        if not dep or dep.phase_id != data.phase_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid dependency task")
    task = ConstructionTask(**data.model_dump())
    db.add(task)
    await db.flush()
    if rollup_phase:
        await ConstructionService.rollup_phase_progress(db, data.phase_id)
    return _task_dict(task, phase.name_ar)


@router.put("/tasks/{task_id}")
async def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    rollup_phase: bool = Query(True),
):
    result = await db.execute(
        select(ConstructionTask, ConstructionPhase)
        .join(ConstructionPhase, ConstructionTask.phase_id == ConstructionPhase.id)
        .where(ConstructionTask.id == task_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    task, phase = row
    if not await ConstructionService.get_phase_for_company(db, phase.id, _company_id(current_user)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    updates = data.model_dump(exclude_unset=True)
    if "depends_on_task_id" in updates and updates["depends_on_task_id"]:
        dep = (await db.execute(select(ConstructionTask).where(ConstructionTask.id == updates["depends_on_task_id"]))).scalar_one_or_none()
        if not dep or dep.phase_id != task.phase_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid dependency task")
    for field, value in updates.items():
        setattr(task, field, value)
    await db.flush()
    if rollup_phase:
        await ConstructionService.rollup_phase_progress(db, task.phase_id)
    return _task_dict(task, phase.name_ar)


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(
        select(ConstructionTask, ConstructionPhase)
        .join(ConstructionPhase, ConstructionTask.phase_id == ConstructionPhase.id)
        .where(ConstructionTask.id == task_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    task, phase = row
    if not await ConstructionService.get_phase_for_company(db, phase.id, _company_id(current_user)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    phase_id = task.phase_id
    await db.delete(task)
    await db.flush()
    await ConstructionService.rollup_phase_progress(db, phase_id)
    return {"message": "Task deleted", "success": True}


@router.get("/schedule")
async def project_schedule(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    project_id: int = Query(..., ge=1),
):
    return await ConstructionService.build_schedule(db, project_id, _company_id(current_user))


@router.get("/milestones")
async def list_milestones(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    project_id: Optional[int] = None,
):
    company_id = _company_id(current_user)
    query = (
        select(ConstructionMilestone, Project)
        .join(Project, ConstructionMilestone.project_id == Project.id)
        .order_by(ConstructionMilestone.target_date)
    )
    if company_id:
        query = query.where(Project.company_id == company_id)
    if project_id:
        query = query.where(ConstructionMilestone.project_id == project_id)
    result = await db.execute(query)
    return [
        {
            "id": m.id,
            "project_id": m.project_id,
            "name_ar": m.name_ar,
            "target_date": m.target_date,
            "status": m.status,
        }
        for m, _ in result.all()
    ]
