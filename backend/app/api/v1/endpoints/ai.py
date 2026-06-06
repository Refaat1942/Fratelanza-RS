from typing import Annotated, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.users import User
from app.services.ai_service import AIService
from app.services.dashboard_service import DashboardService

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def ai_chat(
    data: ChatRequest,
    current_user: Annotated[User, Depends(get_company_user)],
):
    return {"response": AIService.chat_response(data.message)}


@router.get("/report-summary")
async def ai_report_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if current_user.company_id:
        dashboard = await DashboardService.company_dashboard(db, current_user.company_id)
        data = dashboard.stats.model_dump()
    else:
        dashboard = await DashboardService.super_admin_dashboard(db)
        data = dashboard.stats.model_dump()
    return {"summary": AIService.summarize_report(data)}
