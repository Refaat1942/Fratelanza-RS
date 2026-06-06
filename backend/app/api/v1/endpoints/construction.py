from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.construction import ConstructionMilestone, ConstructionPhase, ConstructionTask
from app.models.users import User

router = APIRouter()


class PhaseCreate(BaseModel):
    project_id: int
    name_ar: str
    name_en: str
    planned_start: Optional[str] = None
    planned_end: Optional[str] = None


@router.get("/phases")
async def list_phases(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    project_id: Optional[int] = None,
):
    query = select(ConstructionPhase).order_by(ConstructionPhase.id.desc())
    if project_id:
        query = query.where(ConstructionPhase.project_id == project_id)
    result = await db.execute(query)
    phases = result.scalars().all()
    return [
        {
            "id": p.id,
            "project_id": p.project_id,
            "name_ar": p.name_ar,
            "name_en": p.name_en,
            "progress_percent": p.progress_percent,
            "planned_cost": float(p.planned_cost),
            "actual_cost": float(p.actual_cost),
        }
        for p in phases
    ]


@router.post("/phases")
async def create_phase(
    data: PhaseCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    phase = ConstructionPhase(**data.model_dump())
    db.add(phase)
    await db.flush()
    return {"id": phase.id, "name_ar": phase.name_ar}


@router.get("/tasks")
async def list_tasks(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    phase_id: Optional[int] = None,
):
    query = select(ConstructionTask).order_by(ConstructionTask.id.desc())
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
    query = select(ConstructionMilestone).order_by(ConstructionMilestone.target_date)
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
