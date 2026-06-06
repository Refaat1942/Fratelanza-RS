from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.customers import Customer
from app.models.crm import Lead
from app.models.users import User
from app.services.export_service import ExportService

router = APIRouter()


@router.get("/customers")
async def export_customers(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    format: str = Query("csv", pattern="^(csv|xlsx)$"),
):
    query = select(Customer).where(Customer.is_deleted == False)
    if not current_user.is_super_admin and current_user.company_id:
        query = query.where(Customer.company_id == current_user.company_id)
    result = await db.execute(query)
    rows = [
        {"id": c.id, "name_ar": c.full_name_ar, "name_en": c.full_name_en, "mobile": c.mobile, "email": c.email or ""}
        for c in result.scalars().all()
    ]
    if format == "xlsx":
        content, filename = ExportService.to_excel(rows, "customers.xlsx")
        return Response(
            content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    content, filename = ExportService.to_csv(rows, "customers.csv")
    return Response(content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.get("/leads")
async def export_leads(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    format: str = Query("csv", pattern="^(csv|xlsx)$"),
):
    query = select(Lead).where(Lead.is_deleted == False)
    if not current_user.is_super_admin and current_user.company_id:
        query = query.where(Lead.company_id == current_user.company_id)
    result = await db.execute(query)
    rows = [
        {"id": l.id, "name": l.full_name, "mobile": l.mobile, "source": l.source.value, "stage": l.stage.value, "score": l.score}
        for l in result.scalars().all()
    ]
    if format == "xlsx":
        content, filename = ExportService.to_excel(rows, "leads.xlsx")
        return Response(
            content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    content, filename = ExportService.to_csv(rows, "leads.csv")
    return Response(content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})
