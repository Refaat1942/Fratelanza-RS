import io
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.plan_limits import format_limit, is_unlimited
from app.models.tenant import SubscriptionPlan
from app.services.module_service import ModuleService
from app.services.subscription_service import SubscriptionService

FONT_DIR = Path(__file__).resolve().parents[2] / "assets" / "fonts"
AR_FONT = "NotoSansArabic"
AR_FONT_BOLD = "NotoSansArabic-Bold"

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
    "documents": ("Document Management", "إدارة المستندات"),
    "property": ("Property Mgmt", "إدارة الممتلكات"),
    "customer_service": ("Customer Service", "خدمة العملاء"),
    "users": ("Team Users", "مستخدمي الفريق"),
    "reports": ("Reports", "التقارير"),
    "branding": ("Branding", "الهوية البصرية"),
    "ai_assistant": ("AI Assistant", "المساعد الذكي"),
}


def _register_fonts() -> None:
    if AR_FONT not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(AR_FONT, str(FONT_DIR / "NotoSansArabic-Regular.ttf")))
    if AR_FONT_BOLD not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(AR_FONT_BOLD, str(FONT_DIR / "NotoSansArabic-Bold.ttf")))


def _shape_ar(text: str) -> str:
    return get_display(arabic_reshaper.reshape(text))


def _ar_para(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(_shape_ar(text), style)


class PlanBrochureService:
    @staticmethod
    def _egp(amount: Decimal | float) -> str:
        return f"EGP {float(amount):,.0f}"

    @staticmethod
    def _modules_for_plan(plan: SubscriptionPlan) -> list[str]:
        data = SubscriptionService.plan_to_dict(plan)
        return data.get("enabled_modules") or ModuleService.defaults_for_plan(plan.code)

    @staticmethod
    def generate_pdf(plans: list[SubscriptionPlan], *, trial_days: int = 14, single_plan: bool = False) -> bytes:
        _register_fonts()
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
        ar_style = ParagraphStyle(
            "Arabic",
            parent=body,
            fontName=AR_FONT,
            fontSize=9,
            alignment=TA_RIGHT,
            leading=12,
        )
        ar_bold = ParagraphStyle(
            "ArabicBold",
            parent=ar_style,
            fontName=AR_FONT_BOLD,
            fontSize=9,
        )
        ar_cell = ParagraphStyle(
            "ArabicCell",
            parent=ar_style,
            fontSize=8,
            alignment=TA_RIGHT,
        )
        en_cell = ParagraphStyle("EnCell", parent=body, fontSize=8)

        story = []
        story.append(Paragraph("FRATELANZA Real Estate Platform", title_style))
        if single_plan and len(plans) == 1:
            story.append(Paragraph(f"{plans[0].name_en} Plan", h2_style))
            story.append(_ar_para(f"باقة {plans[0].name_ar}", ar_bold))
        else:
            story.append(Paragraph("Subscription Plans", h2_style))
            story.append(_ar_para("باقات الاشتراك", ar_bold))
        story.append(Spacer(1, 2 * mm))
        story.append(
            Paragraph(
                f"Generated {datetime.utcnow().strftime('%d %B %Y')} · support@fratelanza.com · rs.fratelanza.com",
                body,
            )
        )
        story.append(Spacer(1, 8 * mm))

        summary_data = [
            [
                Paragraph("Plan", en_cell),
                Paragraph(_shape_ar("الباقة"), ar_cell),
                Paragraph("Monthly", en_cell),
                Paragraph("Yearly", en_cell),
                Paragraph("Users", en_cell),
                Paragraph("Projects", en_cell),
                Paragraph("Storage", en_cell),
            ]
        ]
        for p in plans:
            users = format_limit(p.max_users)["en"]
            projects = format_limit(p.max_projects)["en"]
            if is_unlimited(p.max_storage_mb):
                storage = "Unlimited"
            elif p.max_storage_mb >= 1024:
                storage = f"{p.max_storage_mb // 1024} GB"
            else:
                storage = f"{p.max_storage_mb} MB"
            billing_type = getattr(p, "billing_type", "recurring") or "recurring"
            if billing_type == "one_time":
                monthly_cell = f"Once: {PlanBrochureService._egp(p.price_one_time)}"
                hosting = Decimal(getattr(p, "hosting_fee_monthly", 0) or 0)
                yearly_cell = f"{PlanBrochureService._egp(hosting)}/mo host" if hosting > 0 else "—"
            else:
                monthly_cell = PlanBrochureService._egp(p.price_monthly)
                yearly_cell = PlanBrochureService._egp(p.price_yearly)
            summary_data.append([
                Paragraph(p.name_en, en_cell),
                _ar_para(p.name_ar, ar_cell),
                Paragraph(monthly_cell, en_cell),
                Paragraph(yearly_cell, en_cell),
                Paragraph(users, en_cell),
                Paragraph(projects, en_cell),
                Paragraph(storage, en_cell),
            ])
        summary_table = Table(
            summary_data,
            colWidths=[32 * mm, 32 * mm, 22 * mm, 22 * mm, 16 * mm, 20 * mm, 20 * mm],
        )
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

        story.append(Paragraph("Payment Terms", h2_style))
        story.append(_ar_para("شروط الدفع", ar_bold))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph("• Monthly or yearly billing (yearly saves ~2 months)", body))
        story.append(_ar_para("• الفوترة شهرية أو سنوية (التوفير شهرين مع السنوي)", ar_style))
        story.append(Paragraph("• Net 30 days payment terms from invoice date", body))
        story.append(_ar_para("• صافي 30 يوماً من تاريخ الفاتورة", ar_style))
        story.append(Paragraph(f"• {trial_days}-day free trial for new companies", body))
        story.append(_ar_para(f"• تجربة مجانية {trial_days} يوماً للشركات الجديدة", ar_style))
        story.append(Paragraph("• Payment reminders before and after due date", body))
        story.append(_ar_para("• تذكيرات الدفع قبل وبعد تاريخ الاستحقاق", ar_style))
        story.append(Spacer(1, 2 * mm))
        story.append(_ar_para("للاشتراك تواصلوا مع خدمة العملاء: support@fratelanza.com", ar_style))

        all_keys = list(MODULE_LABELS.keys())
        for plan in plans:
            if not single_plan:
                story.append(Paragraph(f"{plan.name_en} Plan", h2_style))
                story.append(_ar_para(f"باقة {plan.name_ar}", ar_bold))
            if plan.description_en:
                story.append(Paragraph(plan.description_en, body))
            if plan.description_ar:
                story.append(_ar_para(plan.description_ar, ar_style))
                story.append(Spacer(1, 2 * mm))
            support_months = getattr(plan, "support_months", 0) or 0
            includes_hosting = bool(getattr(plan, "includes_hosting", False))
            if support_months > 0:
                story.append(Paragraph(f"• {support_months} months free premium support included", body))
                story.append(_ar_para(f"• دعم فني مجاني لمدة {support_months} شهراً", ar_style))
            hosting_en = "Managed server hosting included" if includes_hosting else "Software only (no server hosting)"
            hosting_ar = "يشمل استضافة سيرفر مُدارة" if includes_hosting else "برنامج فقط (بدون استضافة سيرفر)"
            story.append(Paragraph(f"• {hosting_en}", body))
            story.append(_ar_para(f"• {hosting_ar}", ar_style))
            story.append(Spacer(1, 2 * mm))
            enabled = set(PlanBrochureService._modules_for_plan(plan))
            feat_rows = [
                [
                    Paragraph("", en_cell),
                    Paragraph("Feature", en_cell),
                    Paragraph(_shape_ar("الميزة"), ar_cell),
                ]
            ]
            for key in all_keys:
                en, ar = MODULE_LABELS[key]
                mark = "Yes" if key in enabled else "No"
                feat_rows.append([
                    Paragraph(mark, ParagraphStyle("Mark", parent=en_cell, alignment=TA_CENTER)),
                    Paragraph(en, en_cell),
                    _ar_para(ar, ar_cell),
                ])
            feat_table = Table(feat_rows, colWidths=[12 * mm, 75 * mm, 75 * mm])
            feat_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0ea5e9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                ("ALIGN", (0, 1), (0, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(feat_table)
            story.append(Spacer(1, 4 * mm))

        story.append(Paragraph("Customer Service", h2_style))
        story.append(_ar_para("خدمة العملاء", ar_bold))
        story.append(Spacer(1, 2 * mm))
        story.append(
            Paragraph(
                "Contact support@fratelanza.com to subscribe, upgrade, or customize an Enterprise plan.",
                body,
            )
        )
        story.append(
            _ar_para(
                "للاشتراك أو ترقية الباقة، تواصل مع فريق خدمة العملاء. يمكن تخصيص الباقة المؤسسية حسب احتياجاتكم.",
                ar_style,
            )
        )

        doc.build(story)
        return buffer.getvalue()
