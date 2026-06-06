from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.users import User
from app.services.export_service import ExportService
from app.services.reports_service import ReportsService

router = APIRouter()


@router.get("/catalog")
async def reports_catalog(
    current_user: Annotated[User, Depends(get_company_user)],
):
    return ReportsService.catalog(is_super_admin=current_user.is_super_admin)


@router.get("/{report_key}")
async def get_report(
    report_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    sort_by: Optional[str] = None,
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    search: Optional[str] = None,
):
    company_id = None if current_user.is_super_admin else current_user.company_id
    rows, columns = await ReportsService.run(
        db,
        report_key,
        company_id,
        is_super_admin=current_user.is_super_admin,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search,
    )
    meta = next((r for r in ReportsService.catalog(current_user.is_super_admin) if r["key"] == report_key), None)
    if not meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return {
        "key": report_key,
        "name_en": meta["name_en"],
        "name_ar": meta["name_ar"],
        "category": meta["category"],
        "total": len(rows),
        "columns": columns,
        "rows": rows,
    }


@router.get("/{report_key}/export")
async def export_report(
    report_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    format: str = Query("xlsx", pattern="^(csv|xlsx)$"),
    sort_by: Optional[str] = None,
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    search: Optional[str] = None,
):
    company_id = None if current_user.is_super_admin else current_user.company_id
    rows, _ = await ReportsService.run(
        db,
        report_key,
        company_id,
        is_super_admin=current_user.is_super_admin,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search,
    )
    meta = next((r for r in ReportsService.catalog(current_user.is_super_admin) if r["key"] == report_key), None)
    if not meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    filename = f"{report_key}.{format}"
    if format == "xlsx":
        content, filename = ExportService.to_excel(rows, filename)
        return Response(
            content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    content, filename = ExportService.to_csv(rows, filename)
    return Response(content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})
