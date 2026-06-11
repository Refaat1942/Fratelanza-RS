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
        sales = context.get("total_sales", 0)
        collections = context.get("total_collections", 0)
        available = context.get("available_units", 0)
        leads = context.get("total_leads", 0)
        msg = message.lower()
        if "مبيعات" in message or "sales" in msg:
            return (
                f"إجمالي المبيعات المسجلة: {float(sales):,.0f} جنيه. "
                f"الوحدات المتاحة: {available}. افتح التقارير → سجل المبيعات للتفاصيل."
            )
        if "تحصيل" in message or "collection" in msg:
            return (
                f"إجمالي التحصيلات: {float(collections):,.0f} جنيه. "
                "راجع تقرير الأقساط المتأخرة لمتابعة المخاطر."
            )
        if "lead" in msg or "عميل" in message or "محتمل" in message:
            return f"لديك {leads} عميلاً محتملاً في المسار. استخدم تقرير Leads Pipeline للتحليل."
        if "اتجاه" in message or "trend" in msg or "سوق" in message:
            return "اطلب «اتجاهات السوق» من مساعد التقارير الذكي لملخص آلي من بيانات CRM."
        return (
            "مرحباً! أنا مساعد التقارير في فراتيلانزا. اسأل عن المبيعات، التحصيلات، أو العملاء المحتملين — "
            f"أو استخدم ملخص الأداء (مبيعات: {float(sales):,.0f} جنيه، تحصيلات: {float(collections):,.0f} جنيه)."
        )
