import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.customer_service import Ticket, TicketComment
from app.models.users import User

router = APIRouter()


class TicketCreate(BaseModel):
    category: str
    subject: str
    description: Optional[str] = None
    customer_id: Optional[int] = None
    priority: str = "medium"


class CommentCreate(BaseModel):
    comment: str
    is_internal: bool = False


@router.get("")
async def list_tickets(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    query = select(Ticket).order_by(Ticket.id.desc())
    if not current_user.is_super_admin:
        query = query.where(Ticket.company_id == current_user.company_id)
    result = await db.execute(query)
    tickets = result.scalars().all()
    return [
        {
            "id": t.id,
            "ticket_number": t.ticket_number,
            "subject": t.subject,
            "category": t.category,
            "priority": t.priority,
            "status": t.status,
        }
        for t in tickets
    ]


@router.post("")
async def create_ticket(
    data: TicketCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    ticket = Ticket(
        company_id=current_user.company_id,
        ticket_number=f"TKT-{uuid.uuid4().hex[:8].upper()}",
        **data.model_dump(),
    )
    db.add(ticket)
    await db.flush()
    return {"id": ticket.id, "ticket_number": ticket.ticket_number}


@router.post("/{ticket_id}/comments")
async def add_comment(
    ticket_id: int,
    data: CommentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    comment = TicketComment(ticket_id=ticket_id, user_id=current_user.id, **data.model_dump())
    db.add(comment)
    await db.flush()
    return {"id": comment.id}
