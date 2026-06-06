from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.crm import CustomerReminder, Lead, LeadStage, ReminderStatus
from app.models.users import User
from app.schemas.common import PaginatedResponse
from app.schemas.lead import LeadCreate, LeadResponse, LeadUpdate
from app.services.ai_service import AIService
from app.services.follow_up_service import FollowUpService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[LeadResponse])
async def list_leads(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    stage: Optional[str] = None,
):
    if not current_user.company_id and not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    query = select(Lead).where(Lead.is_deleted == False)
    if not current_user.is_super_admin:
        query = query.where(Lead.company_id == current_user.company_id)
    if stage:
        query = query.where(Lead.stage == stage)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(query.order_by(Lead.id.desc()).offset((page - 1) * page_size).limit(page_size))
    leads = result.scalars().all()
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[LeadResponse.model_validate(l) for l in leads],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("", response_model=LeadResponse)
async def create_lead(
    data: LeadCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    lead = Lead(company_id=current_user.company_id, **data.model_dump())
    score, ai_score, qualification = AIService.score_lead(lead)
    lead.score = score
    lead.ai_score = ai_score
    lead.ai_qualification = qualification
    db.add(lead)
    await db.flush()
    return LeadResponse.model_validate(lead)


@router.patch("/{lead_id}/stage", response_model=LeadResponse)
async def update_lead_stage(
    lead_id: int,
    stage: LeadStage,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id, Lead.is_deleted == False))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    if not current_user.is_super_admin and lead.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    lead.stage = stage
    score, ai_score, qualification = AIService.score_lead(lead)
    lead.score = score
    lead.ai_score = ai_score
    lead.ai_qualification = qualification
    if stage not in (LeadStage.CONTRACT_SIGNED, LeadStage.LOST):
        await FollowUpService.auto_schedule_for_lead(db, lead, current_user.id)
    await db.flush()
    return LeadResponse.model_validate(lead)


@router.get("/kanban")
async def leads_kanban(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    query = select(Lead).where(Lead.is_deleted == False)
    if not current_user.is_super_admin:
        query = query.where(Lead.company_id == current_user.company_id)
    result = await db.execute(query.order_by(Lead.score.desc()))
    leads = result.scalars().all()
    lead_ids = [l.id for l in leads]
    pending_by_lead: dict[int, CustomerReminder] = {}
    if lead_ids:
        rem_result = await db.execute(
            select(CustomerReminder)
            .where(
                CustomerReminder.lead_id.in_(lead_ids),
                CustomerReminder.status == ReminderStatus.PENDING,
            )
            .order_by(CustomerReminder.due_date)
        )
        for rem in rem_result.scalars().all():
            if rem.lead_id and rem.lead_id not in pending_by_lead:
                pending_by_lead[rem.lead_id] = rem
    board: dict[str, list] = {s.value: [] for s in LeadStage}
    for lead in leads:
        pending = pending_by_lead.get(lead.id)
        board[lead.stage.value].append(
            {
                "id": lead.id,
                "full_name": lead.full_name,
                "mobile": lead.mobile,
                "source": lead.source.value,
                "score": lead.score,
                "ai_qualification": lead.ai_qualification,
                "next_follow_up": lead.next_follow_up or (pending.due_date if pending else None),
                "pending_call_id": pending.id if pending else None,
                "pending_call_date": pending.due_date if pending else None,
            }
        )
    return board


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id, Lead.is_deleted == False))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    if not current_user.is_super_admin and lead.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    lead.soft_delete()
    await db.flush()
    return {"message": "Lead deleted", "success": True}


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    data: LeadUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id, Lead.is_deleted == False))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    if not current_user.is_super_admin and lead.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)
    score, ai_score, qualification = AIService.score_lead(lead)
    lead.score = score
    lead.ai_score = ai_score
    lead.ai_qualification = qualification
    await db.flush()
    return LeadResponse.model_validate(lead)
