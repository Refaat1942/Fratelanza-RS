from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    ticket_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customers.id"))
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(50), default="open")
    assigned_to_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    sla_due_at: Mapped[Optional[str]] = mapped_column(String(30))

    comments: Mapped[list["TicketComment"]] = relationship(back_populates="ticket", lazy="selectin")


class TicketComment(Base, TimestampMixin):
    __tablename__ = "ticket_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(default=False)

    ticket: Mapped["Ticket"] = relationship(back_populates="comments")
