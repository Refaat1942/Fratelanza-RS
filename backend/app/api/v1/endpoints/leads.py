from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.crm import CustomerReminder, Lead, LeadStage, ReminderStatus
from app.models.users import SystemRole, User
from app.schemas.common import PaginatedResponse
from app.schemas.lead import LeadAssignRequest, LeadCreate, LeadResponse, LeadUpdate
from app.services.ai_service import AIService
from app.services.follow_up_service import FollowUpService
from app.services.lead_assignment_service import LeadAssignmentService

router = APIRouter()


def _apply_sales_agent_scope(query, current_user: User):
    if current_user.system_role == SystemRole.SALES_AGENT:
        return query.where(Lead.assigned_to_id == current_user.id)
    return query


async def _lead_response(db: AsyncSession, lead: Lead) -> LeadResponse:
    resp = LeadResponse.model_validate(lead)
    if lead.assigned_to_id:
        user = (
            await db.execute(select(User).where(User.id == lead.assigned_to_id))
        ).scalar_one_or_none()
        if user:
            return resp.model_copy(update={"assigned_to_name": user.full_name_en})
    return resp


async def _lead_responses(db: AsyncSession, leads: list[Lead]) -> list[LeadResponse]:
    assignee_ids = {l.assigned_to_id for l in leads if l.assigned_to_id}
    names: dict[int, str] = {}
    if assignee_ids:
        result = await db.execute(select(User).where(User.id.in_(assignee_ids)))
        for user in result.scalars().all():
            names[user.id] = user.full_name_en
    return [
        LeadResponse.model_validate(l).model_copy(
            update={"assigned_to_name": names.get(l.assigned_to_id)} if l.assigned_to_id else {}
        )
        for l in leads
    ]


@router.get("/sales-agents")
async def list_sales_agents(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id and not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    company_id = current_user.company_id
    if not company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company required")
    agents = await LeadAssignmentService.get_sales_agents(db, company_id)
    return [
        {
            "id": a.id,
            "full_name_en": a.full_name_en,
            "full_name_ar": a.full_name_ar,
            "system_role": a.system_role.value,
        }
        for a in agents
    ]


@router.get("", response_model=PaginatedResponse[LeadResponse])
async def list_leads(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    stage: Optional[str] = None,
    assigned_to_id: Optional[int] = None,
):
    if not current_user.company_id and not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    query = select(Lead).where(Lead.is_deleted == False)
    if not current_user.is_super_admin:
        query = query.where(Lead.company_id == current_user.company_id)
    query = _apply_sales_agent_scope(query, current_user)
    if stage:
        query = query.where(Lead.stage == stage)
    if assigned_to_id:
        query = query.where(Lead.assigned_to_id == assigned_to_id)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(query.order_by(Lead.id.desc()).offset((page - 1) * page_size).limit(page_size))
    leads = result.scalars().all()
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=await _lead_responses(db, leads),
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
    payload = data.model_dump()
    requested_assignee = payload.pop("assigned_to_id", None)
    assignee_id = await LeadAssignmentService.resolve_assignee(
        db,
        current_user.company_id,
        requested_assignee,
        fallback_user_id=current_user.id,
    )
    lead = Lead(company_id=current_user.company_id, assigned_to_id=assignee_id, **payload)
    score, ai_score, qualification = AIService.score_lead(lead)
    lead.score = score
    lead.ai_score = ai_score
    lead.ai_qualification = qualification
    db.add(lead)
    await db.flush()
    if assignee_id:
        await LeadAssignmentService.log_assignment(db, lead.id, assignee_id, current_user.id)
        await FollowUpService.auto_schedule_for_lead(db, lead, assignee_id)
    return await _lead_response(db, lead)


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
    if current_user.system_role == SystemRole.SALES_AGENT and lead.assigned_to_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    lead.stage = stage
    score, ai_score, qualification = AIService.score_lead(lead)
    lead.score = score
    lead.ai_score = ai_score
    lead.ai_qualification = qualification
    if stage not in (LeadStage.CONTRACT_SIGNED, LeadStage.LOST):
        follow_up_user = lead.assigned_to_id or current_user.id
        await FollowUpService.auto_schedule_for_lead(db, lead, follow_up_user)
    await db.flush()
    return await _lead_response(db, lead)


@router.get("/kanban")
async def leads_kanban(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    query = select(Lead).where(Lead.is_deleted == False)
    if not current_user.is_super_admin:
        query = query.where(Lead.company_id == current_user.company_id)
    query = _apply_sales_agent_scope(query, current_user)
    result = await db.execute(query.order_by(Lead.score.desc()))
    leads = result.scalars().all()
    lead_ids = [l.id for l in leads]
    assignee_ids = {l.assigned_to_id for l in leads if l.assigned_to_id}
    assignee_names: dict[int, str] = {}
    if assignee_ids:
        users_result = await db.execute(select(User).where(User.id.in_(assignee_ids)))
        for user in users_result.scalars().all():
            assignee_names[user.id] = user.full_name_en

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
                "assigned_to_id": lead.assigned_to_id,
                "assigned_to_name": assignee_names.get(lead.assigned_to_id) if lead.assigned_to_id else None,
                "next_follow_up": lead.next_follow_up or (pending.due_date if pending else None),
                "pending_call_id": pending.id if pending else None,
                "pending_call_date": pending.due_date if pending else None,
            }
        )
    return board


@router.post("/{lead_id}/assign", response_model=LeadResponse)
async def assign_lead(
    lead_id: int,
    data: LeadAssignRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id, Lead.is_deleted == False))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    if not current_user.is_super_admin and lead.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if current_user.system_role == SystemRole.SALES_AGENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers can reassign leads")

    if data.auto:
        assignee_id = await LeadAssignmentService.pick_least_loaded_agent(db, lead.company_id)
    else:
        assignee_id = data.assigned_to_id
    if not assignee_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No sales agent available")
    if not await LeadAssignmentService.is_valid_assignee(db, lead.company_id, assignee_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sales agent")

    lead.assigned_to_id = assignee_id
    score, ai_score, qualification = AIService.score_lead(lead)
    lead.score = score
    lead.ai_score = ai_score
    lead.ai_qualification = qualification
    await LeadAssignmentService.log_assignment(db, lead.id, assignee_id, current_user.id)
    await db.flush()
    return await _lead_response(db, lead)


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
    if current_user.system_role == SystemRole.SALES_AGENT and lead.assigned_to_id != current_user.id:
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
    if current_user.system_role == SystemRole.SALES_AGENT and lead.assigned_to_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    updates = data.model_dump(exclude_unset=True)
    prev_assignee = lead.assigned_to_id
    if "assigned_to_id" in updates and updates["assigned_to_id"]:
        if not await LeadAssignmentService.is_valid_assignee(db, lead.company_id, updates["assigned_to_id"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sales agent")

    for field, value in updates.items():
        setattr(lead, field, value)
    score, ai_score, qualification = AIService.score_lead(lead)
    lead.score = score
    lead.ai_score = ai_score
    lead.ai_qualification = qualification
    if lead.assigned_to_id and lead.assigned_to_id != prev_assignee:
        await LeadAssignmentService.log_assignment(db, lead.id, lead.assigned_to_id, current_user.id)
    await db.flush()
    return await _lead_response(db, lead)
