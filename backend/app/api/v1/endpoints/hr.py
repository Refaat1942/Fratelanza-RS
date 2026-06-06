from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.hr import Attendance, Employee, LeaveRequest
from app.models.users import User

router = APIRouter()


class EmployeeCreate(BaseModel):
    employee_code: str
    full_name_ar: str
    full_name_en: str
    department: Optional[str] = None
    position: Optional[str] = None
    hire_date: Optional[str] = None


@router.get("/employees")
async def list_employees(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    result = await db.execute(
        select(Employee).where(Employee.company_id == current_user.company_id, Employee.is_deleted == False)
    )
    employees = result.scalars().all()
    return [
        {
            "id": e.id,
            "employee_code": e.employee_code,
            "full_name_ar": e.full_name_ar,
            "full_name_en": e.full_name_en,
            "department": e.department,
            "position": e.position,
            "is_active": e.is_active,
        }
        for e in employees
    ]


@router.post("/employees")
async def create_employee(
    data: EmployeeCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    employee = Employee(company_id=current_user.company_id, **data.model_dump())
    db.add(employee)
    await db.flush()
    return {"id": employee.id, "employee_code": employee.employee_code}


@router.get("/attendance")
async def list_attendance(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(Attendance).order_by(Attendance.id.desc()).limit(100))
    records = result.scalars().all()
    return [
        {"id": a.id, "employee_id": a.employee_id, "date": a.date, "status": a.status}
        for a in records
    ]


@router.get("/leaves")
async def list_leaves(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(LeaveRequest).order_by(LeaveRequest.id.desc()))
    leaves = result.scalars().all()
    return [
        {
            "id": l.id,
            "employee_id": l.employee_id,
            "leave_type": l.leave_type,
            "start_date": l.start_date,
            "end_date": l.end_date,
            "status": l.status,
        }
        for l in leaves
    ]
