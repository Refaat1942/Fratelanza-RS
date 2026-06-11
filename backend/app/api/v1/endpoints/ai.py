from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.config import settings
from app.core.database import get_db
from app.models.users import User
from app.services.ai_reporting_service import AIReportingService
from app.services.llm_client import LLMClient

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    language: Optional[str] = "en"


class AnalyzeReportRequest(BaseModel):
    report_key: str = Field(min_length=1)
    language: Optional[str] = "en"


class SummaryRequest(BaseModel):
    language: Optional[str] = "en"


def _resolve_language(user: User, requested: Optional[str]) -> str:
    if requested:
        return requested.split("-")[0].lower()
    pref = (user.preferred_language or "ar").lower()
    return pref if pref in ("ar", "en") else "en"


@router.post("/chat")
async def ai_chat(
    data: ChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    language = _resolve_language(current_user, data.language)
    result = await AIReportingService.chat_with_context(
        db, current_user, data.message, language=language
    )
    return result


@router.get("/report-summary")
async def ai_report_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    language: Optional[str] = Query(None),
):
    """Legacy endpoint — returns performance summary from sales tables."""
    lang = _resolve_language(current_user, language)
    return await AIReportingService.performance_summary(db, current_user, language=lang)


@router.post("/performance-summary")
async def ai_performance_summary(
    data: SummaryRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    language = _resolve_language(current_user, data.language)
    return await AIReportingService.performance_summary(db, current_user, language=language)


@router.post("/market-trends")
async def ai_market_trends(
    data: SummaryRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    language = _resolve_language(current_user, data.language)
    return await AIReportingService.market_trends(db, current_user, language=language)


@router.post("/analyze-report")
async def ai_analyze_report(
    data: AnalyzeReportRequest,
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


@router.get("/quick-insights")
async def ai_quick_insights(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    language: Optional[str] = Query(None),
):
    """Performance + market trend summaries in one call."""
    lang = _resolve_language(current_user, language)
    performance = await AIReportingService.performance_summary(db, current_user, language=lang)
    trends = await AIReportingService.market_trends(db, current_user, language=lang)
    return {
        "language": lang,
        "performance": performance,
        "market_trends": trends,
    }


@router.get("/provider")
async def ai_provider_status(
    current_user: Annotated[User, Depends(get_company_user)],
):
    return {
        "provider": LLMClient.resolve_provider(),
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "gemini_configured": bool(settings.GEMINI_API_KEY),
    }
