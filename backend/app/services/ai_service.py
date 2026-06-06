from decimal import Decimal
from typing import Optional

from app.models.crm import Lead, LeadStage


class AIService:
    """AI service layer — integrates with LLM providers in production."""

    @staticmethod
    def score_lead(lead: Lead) -> tuple[int, Optional[Decimal], Optional[str]]:
        score = 0
        if lead.email:
            score += 10
        if lead.budget_max and lead.budget_min:
            score += 25
        if lead.stage in (LeadStage.INTERESTED, LeadStage.SITE_VISIT, LeadStage.NEGOTIATION):
            score += 30
        if lead.assigned_to_id:
            score += 15
        ai_score = Decimal(str(min(score, 100)))
        qualification = "hot" if score >= 70 else "warm" if score >= 40 else "cold"
        return score, ai_score, qualification

    @staticmethod
    def summarize_report(data: dict) -> str:
        return (
            f"ملخص: إجمالي المبيعات {data.get('total_sales', 0)} "
            f"| التحصيلات {data.get('total_collections', 0)} "
            f"| الوحدات المتاحة {data.get('available_units', 0)}"
        )

    @staticmethod
    def chat_response(message: str, context: Optional[dict] = None) -> str:
        context = context or {}
        if "مبيعات" in message or "sales" in message.lower():
            return "يمكنك مراجعة لوحة المبيعات للحصول على تفاصيل الأداء الشهري."
        if "تحصيل" in message or "collection" in message.lower():
            return "راجع لوحة التحصيلات لمعرفة الأقساط المستحقة والمتأخرة."
        return "مرحباً! أنا مساعد فراتيلانزا. كيف يمكنني مساعدتك اليوم؟"
