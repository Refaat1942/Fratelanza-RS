from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.hr import Attendance, Employee, LeaveRequest, PayrollRun, Payslip
from app.models.users import User

router = APIRouter()

SOCIAL_INSURANCE_RATE = Decimal("0.11")


class EmployeeCreate(BaseModel):
    employee_code: str
    full_name_ar: str
    full_name_en: str
    department: Optional[str] = None
    position: Optional[str] = None
    hire_date: Optional[str] = None
    salary: Optional[float] = None


class AttendanceCreate(BaseModel):
    employee_id: int
    date: str
    check_in: Optional[str] = "09:00"
    check_out: Optional[str] = "17:00"
    status: str = "present"


class LeaveCreate(BaseModel):
    employee_id: int
    leave_type: str
    start_date: str
    end_date: str
    reason: Optional[str] = None


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
            "department": e.department or "",
            "position": e.position or "",
            "salary": float(e.salary or 0),
            "hire_date": e.hire_date or "",
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


@router.post("/attendance")
async def record_attendance(
    data: AttendanceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    emp = (
        await db.execute(
            select(Employee).where(
                Employee.id == data.employee_id,
                Employee.company_id == current_user.company_id,
            )
        )
    ).scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    record = Attendance(**data.model_dump())
    db.add(record)
    await db.flush()
    return {"id": record.id, "status": record.status}


@router.get("/attendance")
async def list_attendance(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    result = await db.execute(
        select(Attendance, Employee)
        .join(Employee, Attendance.employee_id == Employee.id)
        .where(Employee.company_id == current_user.company_id)
        .order_by(Attendance.id.desc())
        .limit(200)
    )
    return [
        {
            "id": a.id,
            "employee_name": e.full_name_en,
            "employee_code": e.employee_code,
            "date": a.date,
            "check_in": a.check_in or "",
            "check_out": a.check_out or "",
            "status": a.status,
        }
        for a, e in result.all()
    ]


@router.get("/leaves")
async def list_leaves(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    result = await db.execute(
        select(LeaveRequest, Employee)
        .join(Employee, LeaveRequest.employee_id == Employee.id)
        .where(Employee.company_id == current_user.company_id)
        .order_by(LeaveRequest.id.desc())
    )
    return [
        {
            "id": l.id,
            "employee_name": e.full_name_en,
            "leave_type": l.leave_type,
            "start_date": l.start_date,
            "end_date": l.end_date,
            "status": l.status,
            "reason": l.reason or "",
        }
        for l, e in result.all()
    ]


@router.post("/leaves")
async def create_leave(
    data: LeaveCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    emp = (
        await db.execute(
            select(Employee).where(
                Employee.id == data.employee_id,
                Employee.company_id == current_user.company_id,
            )
        )
    ).scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    leave = LeaveRequest(**data.model_dump())
    db.add(leave)
    await db.flush()
    return {"id": leave.id, "status": leave.status}


@router.post("/leaves/{leave_id}/approve")
async def approve_leave(
    leave_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(
        select(LeaveRequest, Employee)
        .join(Employee, LeaveRequest.employee_id == Employee.id)
        .where(LeaveRequest.id == leave_id, Employee.company_id == current_user.company_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave not found")
    leave, _ = row
    leave.status = "approved"
    await db.flush()
    return {"id": leave.id, "status": leave.status}


@router.get("/payroll")
async def list_payroll_runs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    runs = (
        await db.execute(
            select(PayrollRun)
            .where(PayrollRun.company_id == current_user.company_id)
            .order_by(PayrollRun.id.desc())
        )
    ).scalars().all()
    return [
        {
            "id": r.id,
            "period_month": r.period_month,
            "status": r.status,
            "total_gross": float(r.total_gross or 0),
            "total_deductions": float(r.total_deductions or 0),
            "total_net": float(r.total_net or 0),
        }
        for r in runs
    ]


@router.get("/payroll/{run_id}/payslips")
async def list_payslips(
    run_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    run = (
        await db.execute(
            select(PayrollRun).where(
                PayrollRun.id == run_id,
                PayrollRun.company_id == current_user.company_id,
            )
        )
    ).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payroll run not found")
    result = await db.execute(
        select(Payslip, Employee)
        .join(Employee, Payslip.employee_id == Employee.id)
        .where(Payslip.payroll_run_id == run_id)
    )
    return [
        {
            "employee_code": e.employee_code,
            "employee_name": e.full_name_en,
            "department": e.department or "",
            "basic_salary_egp": float(p.basic_salary),
            "allowances_egp": float(p.allowances),
            "social_insurance_egp": float(p.social_insurance),
            "deductions_egp": float(p.deductions),
            "net_salary_egp": float(p.net_salary),
            "status": p.status,
        }
        for p, e in result.all()
    ]


@router.post("/payroll/generate")
async def generate_payroll(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    period_month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    existing = (
        await db.execute(
            select(PayrollRun).where(
                PayrollRun.company_id == current_user.company_id,
                PayrollRun.period_month == period_month,
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payroll already generated for this month")

    employees = (
        await db.execute(
            select(Employee).where(
                Employee.company_id == current_user.company_id,
                Employee.is_active == True,
                Employee.is_deleted == False,
            )
        )
    ).scalars().all()

    run = PayrollRun(
        company_id=current_user.company_id,
        period_month=period_month,
        status="processed",
        created_by_id=current_user.id,
    )
    db.add(run)
    await db.flush()

    total_gross = Decimal("0")
    total_deductions = Decimal("0")
    total_net = Decimal("0")

    for emp in employees:
        basic = Decimal(str(emp.salary or 0))
        social = (basic * SOCIAL_INSURANCE_RATE).quantize(Decimal("0.01"))
        deductions = social
        net = basic - deductions
        total_gross += basic
        total_deductions += deductions
        total_net += net
        db.add(
            Payslip(
                payroll_run_id=run.id,
                employee_id=emp.id,
                basic_salary=basic,
                allowances=Decimal("0"),
                social_insurance=social,
                deductions=deductions,
                net_salary=net,
                status="processed",
            )
        )

    run.total_gross = total_gross
    run.total_deductions = total_deductions
    run.total_net = total_net
    await db.flush()
    return {
        "id": run.id,
        "period_month": period_month,
        "total_net_egp": float(total_net),
        "employee_count": len(employees),
    }
