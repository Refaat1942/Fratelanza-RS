from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class ConstructionPhase(Base, TimestampMixin):
    __tablename__ = "construction_phases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    name_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    planned_start: Mapped[Optional[str]] = mapped_column(String(20))
    planned_end: Mapped[Optional[str]] = mapped_column(String(20))
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    planned_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    actual_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)

    tasks: Mapped[list["ConstructionTask"]] = relationship(back_populates="phase", lazy="selectin")


class ConstructionTask(Base, TimestampMixin):
    __tablename__ = "construction_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phase_id: Mapped[int] = mapped_column(ForeignKey("construction_phases.id"), nullable=False, index=True)
    name_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    assigned_to_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    contractor: Mapped[Optional[str]] = mapped_column(String(255))
    planned_start: Mapped[Optional[str]] = mapped_column(String(20))
    planned_end: Mapped[Optional[str]] = mapped_column(String(20))
    depends_on_task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("construction_tasks.id"))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    planned_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    actual_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)

    phase: Mapped["ConstructionPhase"] = relationship(back_populates="tasks")


class ConstructionMilestone(Base, TimestampMixin):
    __tablename__ = "construction_milestones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    name_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    target_date: Mapped[str] = mapped_column(String(20), nullable=False)
    completed_date: Mapped[Optional[str]] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    notes: Mapped[Optional[str]] = mapped_column(Text)
