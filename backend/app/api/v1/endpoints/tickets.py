import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.customer_service import Ticket, TicketComment
from app.models.customers import Customer
from app.models.users import User

router = APIRouter()


class TicketCreate(BaseModel):
    category: str
    subject: str
    description: Optional[str] = None
    customer_id: Optional[int] = None
    priority: str = "medium"


class TicketUpdate(BaseModel):
    category: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class CommentCreate(BaseModel):
    comment: str
    is_internal: bool = False


@router.get("")
async def list_tickets(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    query = (
        select(Ticket, Customer)
        .outerjoin(Customer, Ticket.customer_id == Customer.id)
        .order_by(Ticket.id.desc())
    )
    if not current_user.is_super_admin:
        query = query.where(Ticket.company_id == current_user.company_id)
    result = await db.execute(query)
    return [
        {
            "id": t.id,
            "ticket_number": t.ticket_number,
            "subject": t.subject,
            "category": t.category,
            "priority": t.priority,
            "status": t.status,
            "customer_id": t.customer_id,
            "customer_name": c.full_name_ar if c else None,
            "description": t.description,
        }
        for t, c in result.all()
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


@router.put("/{ticket_id}")
async def update_ticket(
    ticket_id: int,
    data: TicketUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if not current_user.is_super_admin and ticket.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ticket, field, value)
    await db.flush()
    return {"id": ticket.id, "success": True}


@router.delete("/{ticket_id}")
async def delete_ticket(
    ticket_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if not current_user.is_super_admin and ticket.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    await db.delete(ticket)
    await db.flush()
    return {"message": "Deleted", "success": True}


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
