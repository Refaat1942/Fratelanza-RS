from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.config import settings
from app.core.database import get_db
from app.models.users import User
from app.services.ai_reporting_service import AIReportingService
from app.services.export_service import ExportService
from app.services.llm_client import LLMClient
from app.services.reports_service import ReportsService

router = APIRouter()


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
):
    return ReportsService.catalog(is_super_admin=current_user.is_super_admin)


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
