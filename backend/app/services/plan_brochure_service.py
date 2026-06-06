import io
from datetime import datetime
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.tenant import SubscriptionPlan
from app.services.module_service import ModuleService
from app.services.subscription_service import SubscriptionService

MODULE_LABELS = {
    "dashboard": ("Dashboard & KPIs", "لوحة التحكم"),
    "customers": ("Customers CRM", "إدارة العملاء"),
    "leads": ("Leads & Pipeline", "مسار المبيعات"),
    "follow_ups": ("Follow-ups & Calls", "المتابعات"),
    "projects": ("Projects & Units", "المشاريع والوحدات"),
    "reservations": ("Reservations", "الحجوزات"),
    "contracts": ("Contracts", "العقود"),
    "collections": ("Collections", "التحصيل"),
    "brokers": ("Brokers", "الوسطاء"),
    "finance": ("Finance", "المالية"),
    "hr": ("HR & Payroll", "الموارد البشرية"),
    "construction": ("Construction", "المقاولات"),
    "procurement": ("Procurement", "المشتريات"),
    "warehouse": ("Warehouse", "المستودع"),
    "property": ("Property Mgmt", "إدارة الممتلكات"),
    "customer_service": ("Customer Service", "خدمة العملاء"),
    "users": ("Team Users", "مستخدمي الفريق"),
    "reports": ("Reports", "التقارير"),
    "branding": ("Branding", "الهوية البصرية"),
    "ai_assistant": ("AI Assistant", "المساعد الذكي"),
}


class PlanBrochureService:
    @staticmethod
    def _egp(amount: Decimal | float) -> str:
        return f"EGP {float(amount):,.0f}"

    @staticmethod
    def _modules_for_plan(plan: SubscriptionPlan) -> list[str]:
        data = SubscriptionService.plan_to_dict(plan)
        return data.get("enabled_modules") or ModuleService.defaults_for_plan(plan.code)

    @staticmethod
    def generate_pdf(plans: list[SubscriptionPlan]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=14 * mm,
            leftMargin=14 * mm,
            topMargin=14 * mm,
            bottomMargin=14 * mm,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontSize=22,
            textColor=colors.HexColor("#0159a1"),
            spaceAfter=12,
        )
        h2_style = ParagraphStyle(
            "H2",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#0159a1"),
            spaceBefore=16,
            spaceAfter=8,
        )
        body = styles["Normal"]
        rtl = ParagraphStyle("RTL", parent=body, alignment=TA_RIGHT, fontSize=9)

        story = []
        story.append(Paragraph("FRATELANZA Real Estate Platform", title_style))
        story.append(Paragraph("Subscription Plans / باقات الاشتراك", h2_style))
        story.append(
            Paragraph(
                f"Generated {datetime.utcnow().strftime('%d %B %Y')} · support@fratelanza.com · rs.fratelanza.com",
                body,
            )
        )
        story.append(Spacer(1, 8 * mm))

        summary_data = [["Plan", "Monthly", "Yearly", "Users", "Projects", "Storage"]]
        for p in plans:
            storage = f"{p.max_storage_mb // 1024} GB" if p.max_storage_mb >= 1024 else f"{p.max_storage_mb} MB"
            summary_data.append([
                f"{p.name_en} / {p.name_ar}",
                PlanBrochureService._egp(p.price_monthly),
                PlanBrochureService._egp(p.price_yearly),
                str(p.max_users),
                str(p.max_projects),
                storage,
            ])
        summary_table = Table(summary_data, colWidths=[45 * mm, 25 * mm, 25 * mm, 18 * mm, 22 * mm, 22 * mm])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0159a1")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 6 * mm))

        story.append(Paragraph("Payment Terms / شروط الدفع", h2_style))
        story.append(Paragraph("• Monthly or yearly billing (yearly saves ~2 months)", body))
        story.append(Paragraph("• Net 30 days payment terms from invoice date", body))
        story.append(Paragraph("• 14-day trial for new companies", body))
        story.append(Paragraph("• Payment reminders before and after due date", body))
        story.append(Paragraph("للاشتراك تواصلوا مع خدمة العملاء: support@fratelanza.com", rtl))

        all_keys = list(MODULE_LABELS.keys())
        for plan in plans:
            story.append(Paragraph(f"{plan.name_en} Plan — باقة {plan.name_ar}", h2_style))
            enabled = set(PlanBrochureService._modules_for_plan(plan))
            feat_rows = [["", "Feature", "الميزة"]]
            for key in all_keys:
                en, ar = MODULE_LABELS[key]
                mark = "✓" if key in enabled else "—"
                feat_rows.append([mark, en, ar])
            feat_table = Table(feat_rows, colWidths=[10 * mm, 75 * mm, 75 * mm])
            feat_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0ea5e9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                ("ALIGN", (0, 1), (0, -1), "CENTER"),
            ]))
            story.append(feat_table)
            story.append(Spacer(1, 4 * mm))

        story.append(Paragraph("Customer Service / خدمة العملاء", h2_style))
        story.append(
            Paragraph(
                "Contact support@fratelanza.com to subscribe, upgrade, or customize an Enterprise plan.",
                body,
            )
        )

        doc.build(story)
        return buffer.getvalue()
