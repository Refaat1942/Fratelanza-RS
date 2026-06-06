from typing import Optional

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class Employee(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    employee_code: Mapped[str] = mapped_column(String(50), nullable=False)
    full_name_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(100))
    position: Mapped[Optional[str]] = mapped_column(String(100))
    salary: Mapped[Optional[Numeric]] = mapped_column(Numeric(12, 2))
    hire_date: Mapped[Optional[str]] = mapped_column(String(20))
    manager_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))
    is_active: Mapped[bool] = mapped_column(default=True)


class Attendance(Base, TimestampMixin):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False, index=True)
    date: Mapped[str] = mapped_column(String(20), nullable=False)
    check_in: Mapped[Optional[str]] = mapped_column(String(20))
    check_out: Mapped[Optional[str]] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(50), default="present")


class LeaveRequest(Base, TimestampMixin):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False, index=True)
    leave_type: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[str] = mapped_column(String(20), nullable=False)
    end_date: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="pending")
