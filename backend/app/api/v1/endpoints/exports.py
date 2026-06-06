from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.customers import Customer
from app.models.crm import Lead
from app.models.users import User
from app.services.export_service import ExportService
from app.services.reports_service import ReportsService

router = APIRouter()


class RowsExport(BaseModel):
    rows: list[dict[str, Any]]
    filename: str = "export"


def _file_response(rows: list[dict], filename: str, format: str) -> Response:
    if format == "xlsx":
        content, filename = ExportService.to_excel(rows, filename if filename.endswith(".xlsx") else f"{filename}.xlsx")
        return Response(
            content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    content, filename = ExportService.to_csv(rows, filename if filename.endswith(".csv") else f"{filename}.csv")
    return Response(content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.post("/rows")
async def export_rows(
    data: RowsExport,
    _: Annotated[User, Depends(get_company_user)],
    format: str = Query("xlsx", pattern="^(csv|xlsx)$"),
):
    if not data.rows:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No rows to export")
    return _file_response(data.rows, data.filename, format)


@router.get("/module/{module_key}")
async def export_module(
    module_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    format: str = Query("xlsx", pattern="^(csv|xlsx)$"),
):
    company_id = None if current_user.is_super_admin else current_user.company_id
    rows, _ = await ReportsService.run(db, module_key, company_id, current_user.is_super_admin)
    if not rows:
        catalog_keys = [r["key"] for r in ReportsService.catalog(current_user.is_super_admin)]
        if module_key not in catalog_keys:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    return _file_response(rows, f"{module_key}.{format}", format)


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
