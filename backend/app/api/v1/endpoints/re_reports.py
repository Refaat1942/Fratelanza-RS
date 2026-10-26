"""Property-management financial & operational reports (module ``reports``) and dashboard cards."""

from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import company_id_of, get_access, get_company_user, log_audit
from app.core.database import get_db
from app.models.users import User
from app.services.access_service import AccessContext, AccessService
from app.services.export_service import ExportService
from app.services.re_dashboard_service import ReDashboardService, visible_cards
from app.services.re_reports_service import CATALOG, ReReportsService
from app.services.rental_service import company_today

router = APIRouter()
dashboard_router = APIRouter()


def _allowed(access: AccessContext, key: str) -> bool:
    _, _, sensitive, module = CATALOG[key]
    if not (access.can("reports", "view") and access.can(module, "view")):
        return False
    if sensitive and not access.can("reports", "view_sensitive"):
        return False
    if key == "payroll" and not access.sees("salaries"):
        return False
    return True


@router.get("/catalog")
async def report_catalog(access: Annotated[AccessContext, Depends(get_access)]):
    return [
        {"key": k, "name_ar": v[0], "name_en": v[1], "sensitive": v[2], "module": v[3]}
        for k, v in CATALOG.items()
        if _allowed(access, k)
    ]


async def _run(db, user, access, key, date_from, date_to):
    if key not in CATALOG:
        raise HTTPException(status_code=404, detail="Report not found")
    if not _allowed(access, key):
        raise HTTPException(status_code=403, detail={"code": "permission_denied", "report": key})
    cid = company_id_of(user)
    today = company_today(await AccessService.load_company(db, cid))
    return await ReReportsService.run(db, key, cid, date_from, date_to, today)


@router.get("/{key}")
async def run_report(
    key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
):
    result = await _run(db, current_user, access, key, date_from, date_to)
    return {"key": key, "name_ar": CATALOG[key][0], "name_en": CATALOG[key][1], **result}


@router.get("/{key}/export")
async def export_report(
    key: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    format: str = Query("xlsx", pattern="^(csv|xlsx)$"),
):
    result = await _run(db, current_user, access, key, date_from, date_to)
    rows = result["rows"] or [{"empty": ""}]
    await log_audit(db, request, current_user, "report_exported", "reports", "report", details=f"{key} {date_from}..{date_to}")
    if format == "xlsx":
        content, fname = ExportService.to_excel(rows, f"{key}.xlsx")
        return Response(content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": f"attachment; filename={fname}"})
    content, fname = ExportService.to_csv(rows, f"{key}.csv")
    return Response(content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={fname}"})


@dashboard_router.get("/cards")
async def dashboard_cards(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    cid = company_id_of(current_user)
    today = company_today(await AccessService.load_company(db, cid))
    keys = visible_cards(access)
    return {"date": today.isoformat(), "cards": await ReDashboardService.compute(db, cid, keys, today)}
