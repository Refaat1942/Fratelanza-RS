from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.access_service import AccessContext
from app.api.deps import get_access, get_company_user
from app.core.config import settings
from app.core.database import get_db
from app.models.users import User
from app.services.ai_reporting_service import AIReportingService
from app.services.export_service import ExportService
from app.services.llm_client import LLMClient
from app.services.reports_service import ReportsService

router = APIRouter()

# Legacy report → the module whose data it exposes. Reports never bypass module permissions.
REPORT_MODULES: dict[str, str] = {
    "units_inventory": "projects", "projects_summary": "projects", "sales_register": "contracts",
    "reservations": "reservations", "collections_installments": "collections", "collections_overdue": "collections",
    "collections_payments": "collections", "customers": "customers", "leads_pipeline": "leads",
    "broker_performance": "brokers", "tickets": "customer_service", "finance_trial_balance": "finance",
    "finance_profit_loss": "finance", "finance_cash_position": "finance", "finance_journal": "finance",
    "hr_employees": "hr", "hr_payroll": "hr", "customer_reminders": "follow_ups",
}
SENSITIVE_REPORTS = {"finance_trial_balance", "finance_profit_loss", "finance_cash_position", "finance_journal",
                     "hr_employees", "hr_payroll"}


def assert_report_access(report_key: str, access: AccessContext) -> None:
    if access.is_super_admin:
        return
    module = REPORT_MODULES.get(report_key)
    if module is None or not access.can(module, "view"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "permission_denied", "report": report_key})
    if report_key in SENSITIVE_REPORTS and not access.can("reports", "view_sensitive"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "permission_denied", "report": report_key})
    if report_key.startswith("hr_") and not access.sees("salaries"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "field_restricted", "report": report_key})


class _SummaryRequest(BaseModel):
    language: Optional[str] = "en"


class _AnalyzeReportRequest(BaseModel):
    report_key: str = Field(min_length=1)
    language: Optional[str] = "en"


class _ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    language: Optional[str] = "en"


def _resolve_language(user: User, requested: Optional[str]) -> str:
    if requested:
        return requested.split("-")[0].lower()
    pref = (user.preferred_language or "ar").lower()
    return pref if pref in ("ar", "en") else "en"


@router.get("/catalog")
async def reports_catalog(
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
):
    allowed = []
    for report in ReportsService.catalog(is_super_admin=current_user.is_super_admin):
        try:
            assert_report_access(report["key"], access)
            allowed.append(report)
        except HTTPException:
            continue
    return allowed


@router.get("/ai/provider")
async def reports_ai_provider(
    current_user: Annotated[User, Depends(get_company_user)],
):
    return {
        "provider": LLMClient.resolve_provider(),
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "gemini_configured": bool(settings.GEMINI_API_KEY),
    }


@router.post("/ai/performance-summary")
async def reports_ai_performance(
    data: _SummaryRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    language = _resolve_language(current_user, data.language)
    return await AIReportingService.performance_summary(db, current_user, language=language)


@router.post("/ai/market-trends")
async def reports_ai_trends(
    data: _SummaryRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    language = _resolve_language(current_user, data.language)
    return await AIReportingService.market_trends(db, current_user, language=language)


@router.post("/ai/analyze-report")
async def reports_ai_analyze(
    data: _AnalyzeReportRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    language = _resolve_language(current_user, data.language)
    try:
        return await AIReportingService.analyze_report(
            db, current_user, data.report_key, language=language
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")


@router.post("/ai/chat")
async def reports_ai_chat(
    data: _ChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    language = _resolve_language(current_user, data.language)
    return await AIReportingService.chat_with_context(
        db, current_user, data.message, language=language
    )


@router.get("/ai/quick-insights")
async def reports_ai_quick_insights(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    language: Optional[str] = Query(None),
):
    lang = _resolve_language(current_user, language)
    performance = await AIReportingService.performance_summary(db, current_user, language=lang)
    trends = await AIReportingService.market_trends(db, current_user, language=lang)
    return {"language": lang, "performance": performance, "market_trends": trends}


@router.get("/{report_key}")
async def get_report(
    report_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    access: Annotated[AccessContext, Depends(get_access)],
    sort_by: Optional[str] = None,
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    search: Optional[str] = None,
):
    assert_report_access(report_key, access)
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
    access: Annotated[AccessContext, Depends(get_access)],
    format: str = Query("xlsx", pattern="^(csv|xlsx)$"),
    sort_by: Optional[str] = None,
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    search: Optional[str] = None,
):
    assert_report_access(report_key, access)
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
