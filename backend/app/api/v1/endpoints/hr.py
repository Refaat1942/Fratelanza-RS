from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import date

from fastapi import Request

from app.api.deps import get_access, get_company_user, log_audit
from app.core.database import get_db
from app.services.access_service import AccessContext
from app.services.payroll_service import PayrollService
from app.models.hr import Attendance, Employee, LeaveRequest, PayrollRun, Payslip
from app.models.users import User

router = APIRouter()


def _salary_fields(p: Payslip, access: AccessContext) -> dict:
    visible = access.sees("salaries")

    def val(x):
        return float(x or 0) if visible else None

    return {
        "basic_salary": val(p.basic_salary),
        "allowances": val(p.allowances),
        "social_insurance": val(p.social_insurance),
        "deductions": val(p.deductions),
        "net_salary": val(p.net_salary),
        "paid_amount": val(p.paid_amount),
    }


class SalaryPaymentIn(BaseModel):
    amount: Decimal
    paid_on: date
    method: str = "bank_transfer"
    reference: Optional[str] = None



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
    access: Annotated[AccessContext, Depends(get_access)],
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
            "salary": float(e.salary or 0) if access.sees("salaries") else None,
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


@router.delete("/employees/{employee_id}")
async def delete_employee(
    employee_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    result = await db.execute(
        select(Employee).where(
            Employee.id == employee_id,
            Employee.company_id == current_user.company_id,
            Employee.is_deleted == False,
        )
    )
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    emp.soft_delete()
    emp.is_active = False
    await db.flush()
    return {"message": "Employee deleted", "success": True}


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


@router.delete("/leaves/{leave_id}")
async def delete_leave(
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
    await db.delete(leave)
    await db.flush()
    return {"message": "Leave deleted", "success": True}


@router.delete("/attendance/{record_id}")
async def delete_attendance(
    record_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(
        select(Attendance, Employee)
        .join(Employee, Attendance.employee_id == Employee.id)
        .where(Attendance.id == record_id, Employee.company_id == current_user.company_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance not found")
    record, _ = row
    await db.delete(record)
    await db.flush()
    return {"message": "Attendance deleted", "success": True}


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


@router.get("/payslips")
async def list_all_payslips(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    result = await db.execute(
        select(Payslip, Employee, PayrollRun)
        .join(Employee, Payslip.employee_id == Employee.id)
        .join(PayrollRun, Payslip.payroll_run_id == PayrollRun.id)
        .where(PayrollRun.company_id == current_user.company_id)
        .order_by(PayrollRun.period_month.desc(), Employee.employee_code)
    )
    return [
        {
            "id": p.id,
            "period_month": run.period_month,
            "employee_code": e.employee_code,
            "employee_name": e.full_name_ar,
            "department": e.department or "",
            **_salary_fields(p, access),
            "status": p.status,
        }
        for p, e, run in result.all()
    ]


@router.get("/payroll")
async def list_payroll_runs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
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
            "total_gross": float(r.total_gross or 0) if access.sees("salaries") else None,
            "total_deductions": float(r.total_deductions or 0) if access.sees("salaries") else None,
            "total_net": float(r.total_net or 0) if access.sees("salaries") else None,
        }
        for r in runs
    ]


@router.get("/payroll/{run_id}/payslips")
async def list_payslips(
    run_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
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
            **{f"{k}_egp": v for k, v in _salary_fields(p, access).items() if k != "paid_amount"},
            "id": p.id,
            "paid_amount": _salary_fields(p, access)["paid_amount"],
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
    run = await PayrollService.generate(db, current_user.company_id, period_month, current_user.id)
    total_net = run.total_net
    employees = (await db.execute(select(Payslip.id).where(Payslip.payroll_run_id == run.id))).all()
    return {
        "id": run.id,
        "period_month": period_month,
        "total_net_egp": float(total_net),
        "employee_count": len(employees),
    }


@router.post("/payslips/{payslip_id}/payments")
async def pay_salary(
    payslip_id: int,
    data: SalaryPaymentIn,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    if not access.sees("salaries"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Salary details are restricted")
    row = (
        await db.execute(
            select(Payslip, PayrollRun)
            .join(PayrollRun, Payslip.payroll_run_id == PayrollRun.id)
            .where(Payslip.id == payslip_id, PayrollRun.company_id == current_user.company_id)
        )
    ).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payslip not found")
    payslip, _ = row
    payment = await PayrollService.pay(db, payslip, data.amount, data.paid_on, data.method, data.reference, current_user.id)
    await log_audit(db, request, current_user, "salary_paid", "hr", "payslip", payslip.id, after={"amount": payment.amount})
    return {"id": payment.id, "paid_amount": float(payslip.paid_amount), "status": payslip.status}
