import json
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.users import User
from app.services.dashboard_service import DashboardService
from app.services.llm_client import LLMClient
from app.services.reports_service import ReportsService


def _json_default(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _rows_to_markdown(title: str, rows: list[dict], limit: Optional[int] = None) -> str:
    if not rows:
        return f"### {title}\n(no rows)\n"
    cap = limit or settings.AI_MAX_TABLE_ROWS
    sample = rows[:cap]
    keys = list(sample[0].keys())
    header = "| " + " | ".join(keys) + " |"
    sep = "| " + " | ".join("---" for _ in keys) + " |"
    body_lines = []
    for row in sample:
        body_lines.append("| " + " | ".join(str(row.get(k, "")) for k in keys) + " |")
    suffix = f"\n(showing {len(sample)} of {len(rows)} rows)\n" if len(rows) > len(sample) else "\n"
    return f"### {title}\n{header}\n{sep}\n" + "\n".join(body_lines) + suffix


class AIReportingService:
    SALES_REPORT_KEYS = [
        "sales_register",
        "collections_payments",
        "collections_overdue",
        "leads_pipeline",
        "projects_summary",
        "reservations",
        "units_inventory",
    ]

    @staticmethod
    def _language_name(code: str) -> str:
        return "Arabic" if code.startswith("ar") else "English"

    @staticmethod
    async def gather_data_context(
        db: AsyncSession,
        user: User,
    ) -> dict[str, Any]:
        company_id = user.company_id if not user.is_super_admin else None
        is_super = user.is_super_admin

        if company_id:
            dashboard = await DashboardService.company_dashboard(db, company_id)
        else:
            dashboard = await DashboardService.super_admin_dashboard(db)

        stats = dashboard.stats.model_dump()
        tables: dict[str, list[dict]] = {}
        for key in AIReportingService.SALES_REPORT_KEYS:
            rows, _ = await ReportsService.run(db, key, company_id, is_super_admin=is_super)
            tables[key] = rows

        leads = tables.get("leads_pipeline", [])
        stage_counts = Counter(r.get("stage", "unknown") for r in leads)
        source_counts = Counter(r.get("source", "unknown") for r in leads)

        overdue = tables.get("collections_overdue", [])
        overdue_total = sum(float(r.get("remaining_balance", 0) or 0) for r in overdue)

        sales = tables.get("sales_register", [])
        sales_value = sum(float(r.get("total_price", 0) or 0) for r in sales)

        payments = tables.get("collections_payments", [])
        payments_total = sum(float(r.get("amount", 0) or 0) for r in payments)

        units = tables.get("units_inventory", [])
        status_counts = Counter(r.get("status", "unknown") for r in units)

        return {
            "stats": stats,
            "tables": tables,
            "aggregates": {
                "lead_stages": dict(stage_counts),
                "lead_sources": dict(source_counts),
                "unit_status": dict(status_counts),
                "sales_register_total": sales_value,
                "sales_contract_count": len(sales),
                "payments_total": payments_total,
                "payments_count": len(payments),
                "overdue_installments": len(overdue),
                "overdue_amount": overdue_total,
                "leads_pipeline_stages": dashboard.leads_pipeline,
            },
        }

    @staticmethod
    def format_context_for_prompt(context: dict[str, Any]) -> str:
        parts = [
            "## KPI snapshot",
            json.dumps(
                {"stats": context["stats"], "aggregates": context["aggregates"]},
                indent=2,
                default=_json_default,
            ),
        ]
        labels = {
            "sales_register": "Sales register (contracts)",
            "collections_payments": "Payments received",
            "collections_overdue": "Overdue installments",
            "leads_pipeline": "Leads pipeline",
            "projects_summary": "Projects summary",
            "reservations": "Reservations",
            "units_inventory": "Unit inventory",
        }
        for key, title in labels.items():
            parts.append(_rows_to_markdown(title, context["tables"].get(key, [])))
        return "\n\n".join(parts)

    @staticmethod
    def _local_performance_summary(context: dict[str, Any], language: str) -> str:
        stats = context["stats"]
        agg = context["aggregates"]
        ar = language.startswith("ar")

        sales = float(stats.get("total_sales") or agg.get("sales_register_total") or 0)
        collections = float(stats.get("total_collections") or agg.get("payments_total") or 0)
        available = int(stats.get("available_units") or 0)
        leads = int(stats.get("total_leads") or 0)
        overdue_amt = float(agg.get("overdue_amount") or stats.get("overdue_amount") or 0)
        overdue_n = int(agg.get("overdue_installments") or 0)
        contracts = int(agg.get("sales_contract_count") or 0)

        if ar:
            lines = [
                f"**ملخص الأداء** — تم التحليل في {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
                "",
                f"• إجمالي قيمة العقود المسجلة: {sales:,.0f} جنيه ({contracts} عقد).",
                f"• التحصيلات المحصلة: {collections:,.0f} جنيه.",
                f"• الوحدات المتاحة للبيع: {available} وحدة.",
                f"• العملاء المحتملون النشطون: {leads} lead.",
            ]
            if overdue_n:
                lines.append(f"• **تنبيه تحصيل:** {overdue_n} قسط متأخر بإجمالي {overdue_amt:,.0f} جنيه.")
            else:
                lines.append("• لا توجد أقساط متأخرة حالياً — وضع التحصيل مستقر.")
            if agg.get("lead_stages"):
                top_stage = max(agg["lead_stages"], key=agg["lead_stages"].get)
                lines.append(f"• أكثر مرحلة في مسار المبيعات: {top_stage} ({agg['lead_stages'][top_stage]} lead).")
            if agg.get("unit_status"):
                lines.append(
                    "• توزيع الوحدات: "
                    + "، ".join(f"{k}: {v}" for k, v in agg["unit_status"].items())
                )
            return "\n".join(lines)

        lines = [
            f"**Performance summary** — generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            f"• Total registered contract value: EGP {sales:,.0f} ({contracts} contracts).",
            f"• Collections received: EGP {collections:,.0f}.",
            f"• Units available for sale: {available}.",
            f"• Active leads in pipeline: {leads}.",
        ]
        if overdue_n:
            lines.append(f"• **Collections alert:** {overdue_n} overdue installment(s) totaling EGP {overdue_amt:,.0f}.")
        else:
            lines.append("• No overdue installments — collections position is stable.")
        if agg.get("lead_stages"):
            top_stage = max(agg["lead_stages"], key=agg["lead_stages"].get)
            lines.append(f"• Busiest pipeline stage: {top_stage} ({agg['lead_stages'][top_stage]} leads).")
        if agg.get("unit_status"):
            lines.append("• Unit mix: " + ", ".join(f"{k}: {v}" for k, v in agg["unit_status"].items()))
        return "\n".join(lines)

    @staticmethod
    def _local_market_trends(context: dict[str, Any], language: str) -> str:
        agg = context["aggregates"]
        leads = context["tables"].get("leads_pipeline", [])
        projects = context["tables"].get("projects_summary", [])
        ar = language.startswith("ar")

        sources = agg.get("lead_sources") or {}
        stages = agg.get("lead_stages") or {}
        avg_budget = 0.0
        budgets = [
            (float(r.get("budget_min") or 0) + float(r.get("budget_max") or 0)) / 2
            for r in leads
            if float(r.get("budget_max") or 0) > 0
        ]
        if budgets:
            avg_budget = sum(budgets) / len(budgets)

        if ar:
            lines = [
                "**اتجاهات السوق (من بيانات CRM والمشاريع)**",
                "",
                f"• عدد العملاء المحتملين في النظام: {len(leads)}.",
            ]
            if sources:
                top_src = max(sources, key=sources.get)
                lines.append(f"• أهم مصدر للـ leads: {top_src} ({sources[top_src]}).")
            if stages:
                lines.append("• توزيع المراحل: " + "، ".join(f"{k}: {v}" for k, v in stages.items()))
            if avg_budget > 0:
                lines.append(f"• متوسط ميزانية العملاء المحتملين: {avg_budget:,.0f} جنيه.")
            if projects:
                cities = Counter(p.get("city", "") for p in projects if p.get("city"))
                if cities:
                    lines.append("• المشاريع حسب المدينة: " + "، ".join(f"{c}: {n}" for c, n in cities.items()))
            lines.append("• يُنصح بتركيز الحملات على المصادر والمراحل ذات التحويل الأعلى.")
            return "\n".join(lines)

        lines = [
            "**Market trends (from CRM & project tables)**",
            "",
            f"• Leads in system: {len(leads)}.",
        ]
        if sources:
            top_src = max(sources, key=sources.get)
            lines.append(f"• Top lead source: {top_src} ({sources[top_src]}).")
        if stages:
            lines.append("• Stage distribution: " + ", ".join(f"{k}: {v}" for k, v in stages.items()))
        if avg_budget > 0:
            lines.append(f"• Average lead budget (midpoint): EGP {avg_budget:,.0f}.")
        if projects:
            cities = Counter(p.get("city", "") for p in projects if p.get("city"))
            if cities:
                lines.append("• Projects by city: " + ", ".join(f"{c}: {n}" for c, n in cities.items()))
        lines.append("• Focus marketing on high-converting sources and stages.")
        return "\n".join(lines)

    @staticmethod
    async def _generate_summary(
        system_prompt: str,
        user_prompt: str,
        context: dict[str, Any],
        language: str,
        local_fallback,
    ) -> dict[str, Any]:
        generated_at = datetime.now(timezone.utc).isoformat()
        try:
            summary, provider = await LLMClient.complete(system_prompt, user_prompt)
        except RuntimeError:
            summary = local_fallback(context, language)
            provider = "local"

        return {
            "summary": summary,
            "provider": provider,
            "language": language,
            "generated_at": generated_at,
            "highlights": context["aggregates"],
        }

    @staticmethod
    async def performance_summary(
        db: AsyncSession,
        user: User,
        language: str = "en",
    ) -> dict[str, Any]:
        context = await AIReportingService.gather_data_context(db, user)
        lang_name = AIReportingService._language_name(language)
        system = (
            "You are a senior real estate analyst for Fratelanza. "
            "Write clear, actionable executive summaries using ONLY the provided data. "
            "Do not invent figures. Use bullet points and short paragraphs."
        )
        user_prompt = (
            f"Analyze company performance and write a summary in {lang_name}.\n"
            f"Cover: sales, collections, inventory, overdue risk, and pipeline health.\n\n"
            f"{AIReportingService.format_context_for_prompt(context)}"
        )
        return await AIReportingService._generate_summary(
            system,
            user_prompt,
            context,
            language,
            AIReportingService._local_performance_summary,
        )

    @staticmethod
    async def market_trends(
        db: AsyncSession,
        user: User,
        language: str = "en",
    ) -> dict[str, Any]:
        context = await AIReportingService.gather_data_context(db, user)
        lang_name = AIReportingService._language_name(language)
        system = (
            "You are a real estate market analyst. Identify demand signals, lead sources, "
            "budget trends, and geographic patterns from the CRM tables. Use only provided data."
        )
        user_prompt = (
            f"Summarize market trends and demand indicators in {lang_name}.\n\n"
            f"{AIReportingService.format_context_for_prompt(context)}"
        )
        return await AIReportingService._generate_summary(
            system,
            user_prompt,
            context,
            language,
            AIReportingService._local_market_trends,
        )

    @staticmethod
    async def analyze_report(
        db: AsyncSession,
        user: User,
        report_key: str,
        language: str = "en",
    ) -> dict[str, Any]:
        company_id = user.company_id if not user.is_super_admin else None
        rows, columns = await ReportsService.run(
            db, report_key, company_id, is_super_admin=user.is_super_admin
        )
        meta = next(
            (r for r in ReportsService.catalog(user.is_super_admin) if r["key"] == report_key),
            None,
        )
        if not meta:
            raise ValueError("report_not_found")

        context = await AIReportingService.gather_data_context(db, user)
        lang_name = AIReportingService._language_name(language)
        table_md = _rows_to_markdown(meta["name_en"], rows)
        system = "You are a business intelligence assistant. Summarize the report table insights concisely."
        user_prompt = (
            f"Report: {meta['name_en']} ({report_key}). Language: {lang_name}.\n"
            f"Total rows: {len(rows)}. Columns: {[c['key'] for c in columns]}.\n\n"
            f"{table_md}\n\n"
            "KPI context:\n"
            f"{json.dumps(context['aggregates'], indent=2, default=_json_default)}"
        )

        def local_report(_ctx: dict, lang: str) -> str:
            ar = lang.startswith("ar")
            if ar:
                return (
                    f"**ملخص التقرير: {meta['name_ar']}**\n\n"
                    f"• عدد السجلات: {len(rows)}.\n"
                    f"• راجع الجدول للتفاصيل؛ أكبر القيم في الأعمدة الرقمية تمثل أهم البنود."
                )
            return (
                f"**Report summary: {meta['name_en']}**\n\n"
                f"• Row count: {len(rows)}.\n"
                f"• Review the table for detail; focus on largest numeric values for priorities."
            )

        result = await AIReportingService._generate_summary(
            system, user_prompt, context, language, local_report
        )
        result["report_key"] = report_key
        result["report_name_en"] = meta["name_en"]
        result["report_name_ar"] = meta["name_ar"]
        result["row_count"] = len(rows)
        return result

    @staticmethod
    async def chat_with_context(
        db: AsyncSession,
        user: User,
        message: str,
        language: str = "en",
    ) -> dict[str, Any]:
        context = await AIReportingService.gather_data_context(db, user)
        lang_name = AIReportingService._language_name(language)
        system = (
            "You are Fratelanza AI reporting assistant. Answer questions about sales, "
            "collections, leads, and inventory using the company data below. Be concise."
        )
        user_prompt = (
            f"User question ({lang_name}): {message}\n\n"
            f"{AIReportingService.format_context_for_prompt(context)}"
        )
        try:
            response, provider = await LLMClient.complete(system, user_prompt, max_tokens=800)
        except RuntimeError:
            from app.services.ai_service import AIService

            response = AIService.chat_response(message, context["stats"])
            provider = "local"
        return {
            "response": response,
            "provider": provider,
            "language": language,
        }
