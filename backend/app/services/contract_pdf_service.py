import io
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from fastapi import HTTPException, status
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.customers import Customer
from app.models.real_estate import Building, Floor, Project, Unit
from app.models.sales import Contract, Installment, PaymentPlan
from app.models.tenant import Company

FONT_DIR = Path(__file__).resolve().parents[2] / "assets" / "fonts"
AR_FONT = "NotoSansArabic"
AR_FONT_BOLD = "NotoSansArabic-Bold"

PLAN_LABELS = {
    "monthly": ("Monthly", "شهري"),
    "quarterly": ("Quarterly", "ربع سنوي"),
    "semi_annual": ("Semi-Annual", "نصف سنوي"),
    "annual": ("Annual", "سنوي"),
    "custom": ("Custom", "مخصص"),
}


@dataclass
class ContractPdfContext:
    contract: Contract
    company: Company
    customer: Customer
    unit: Unit
    project: Project | None
    building: Building | None
    payment_plan: PaymentPlan | None
    installments: list[Installment]


def _register_fonts() -> None:
    if AR_FONT not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(AR_FONT, str(FONT_DIR / "NotoSansArabic-Regular.ttf")))
    if AR_FONT_BOLD not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(AR_FONT_BOLD, str(FONT_DIR / "NotoSansArabic-Bold.ttf")))


def _shape_ar(text: str) -> str:
    if not text:
        return ""
    return get_display(arabic_reshaper.reshape(text))


def _ar(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(_shape_ar(text), style)


def _egp(amount: Decimal | float) -> str:
    return f"EGP {float(amount):,.2f}"


class ContractPdfService:
    @staticmethod
    async def load_context(db: AsyncSession, company_id: int, contract_id: int) -> ContractPdfContext:
        result = await db.execute(
            select(Contract)
            .options(selectinload(Contract.payment_plan).selectinload(PaymentPlan.installments))
            .where(Contract.id == contract_id, Contract.company_id == company_id, Contract.is_deleted == False)
        )
        contract = result.scalar_one_or_none()
        if not contract:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")

        company = (
            await db.execute(select(Company).where(Company.id == company_id))
        ).scalar_one_or_none()
        customer = (
            await db.execute(select(Customer).where(Customer.id == contract.customer_id))
        ).scalar_one_or_none()
        unit = (
            await db.execute(
                select(Unit)
                .options(selectinload(Unit.floor).selectinload(Floor.building).selectinload(Building.project))
                .where(Unit.id == contract.unit_id)
            )
        ).scalar_one_or_none()

        if not company or not customer or not unit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract data incomplete")

        project = None
        building = None
        if unit.floor:
            building = unit.floor.building
            if building:
                project = building.project

        plan = contract.payment_plan
        installments: list[Installment] = []
        if plan:
            installments = sorted(plan.installments, key=lambda i: i.installment_number)

        return ContractPdfContext(
            contract=contract,
            company=company,
            customer=customer,
            unit=unit,
            project=project,
            building=building,
            payment_plan=plan,
            installments=installments,
        )

    @staticmethod
    def context_to_dict(ctx: ContractPdfContext) -> dict:
        plan = ctx.payment_plan
        return {
            "contract_number": ctx.contract.contract_number,
            "contract_date": ctx.contract.contract_date,
            "status": ctx.contract.status.value,
            "is_signed": ctx.contract.is_signed,
            "signed_at": ctx.contract.signed_at,
            "total_price": float(ctx.contract.total_price),
            "company": {
                "name_ar": ctx.company.name_ar,
                "name_en": ctx.company.name_en,
                "phone": ctx.company.phone,
                "email": ctx.company.email,
                "address": ctx.company.address,
                "tax_number": ctx.company.tax_number,
            },
            "customer": {
                "name_ar": ctx.customer.full_name_ar,
                "name_en": ctx.customer.full_name_en,
                "mobile": ctx.customer.mobile,
                "email": ctx.customer.email,
                "national_id": ctx.customer.national_id,
                "address": ctx.customer.address,
            },
            "unit": {
                "code": ctx.unit.unit_code,
                "number": ctx.unit.unit_number,
                "type": ctx.unit.unit_type.value,
                "area_sqm": float(ctx.unit.area_sqm),
                "bedrooms": ctx.unit.bedrooms,
                "bathrooms": ctx.unit.bathrooms,
            },
            "project": {
                "name_ar": ctx.project.name_ar if ctx.project else None,
                "name_en": ctx.project.name_en if ctx.project else None,
                "city": ctx.project.city if ctx.project else None,
            } if ctx.project else None,
            "payment_plan": {
                "plan_type": plan.plan_type.value if plan else None,
                "down_payment": float(plan.down_payment) if plan else 0,
                "number_of_installments": plan.number_of_installments if plan else 0,
                "start_date": plan.start_date if plan else None,
                "installments": [
                    {
                        "installment_number": i.installment_number,
                        "due_date": i.due_date,
                        "due_amount": float(i.due_amount),
                    }
                    for i in ctx.installments
                ],
            } if plan else None,
        }

    @staticmethod
    def generate_pdf(ctx: ContractPdfContext) -> bytes:
        _register_fonts()
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=16 * mm,
            leftMargin=16 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title=f"Contract {ctx.contract.contract_number}",
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#0159a1"),
            alignment=TA_CENTER,
            spaceAfter=8,
            fontName="Helvetica-Bold",
        )
        ar_title = ParagraphStyle(
            "ArTitle",
            parent=title_style,
            fontName=AR_FONT_BOLD,
            alignment=TA_CENTER,
        )
        h2 = ParagraphStyle(
            "H2",
            parent=styles["Heading2"],
            fontSize=12,
            textColor=colors.HexColor("#0159a1"),
            spaceBefore=10,
            spaceAfter=6,
            fontName="Helvetica-Bold",
        )
        ar_h2 = ParagraphStyle("ArH2", parent=h2, fontName=AR_FONT_BOLD, alignment=TA_RIGHT)
        body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14)
        ar_body = ParagraphStyle("ArBody", parent=body, fontName=AR_FONT, alignment=TA_RIGHT, fontSize=10)

        story: list = []
        story.append(Paragraph("UNIT SALE CONTRACT", title_style))
        story.append(_ar("عقد بيع وحدة", ar_title))
        story.append(Spacer(1, 6))
        story.append(
            Paragraph(
                f"<b>Contract No:</b> {ctx.contract.contract_number} &nbsp;|&nbsp; "
                f"<b>Date:</b> {ctx.contract.contract_date}",
                body,
            )
        )
        if ctx.contract.is_signed and ctx.contract.signed_at:
            story.append(Paragraph(f"<b>Signed:</b> {ctx.contract.signed_at}", body))

        story.append(Spacer(1, 10))
        story.append(Paragraph("1. Parties", h2))
        story.append(_ar("١. أطراف العقد", ar_h2))
        parties = [
            ["Seller (Developer)", f"{ctx.company.name_en}\n{ctx.company.address or ''}\nTel: {ctx.company.phone or '—'}"],
            ["Buyer", f"{ctx.customer.full_name_en}\nID: {ctx.customer.national_id or '—'}\nMobile: {ctx.customer.mobile}"],
        ]
        pt = Table(parties, colWidths=[45 * mm, 120 * mm])
        pt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f7ff")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(pt)
        story.append(Spacer(1, 4))
        story.append(_ar(f"البائع: {ctx.company.name_ar}", ar_body))
        story.append(_ar(f"المشتري: {ctx.customer.full_name_ar}", ar_body))

        story.append(Paragraph("2. Unit Details", h2))
        story.append(_ar("٢. بيانات الوحدة", ar_h2))
        project_name = ctx.project.name_en if ctx.project else "—"
        unit_rows = [
            ["Project", project_name],
            ["Unit Code", ctx.unit.unit_code],
            ["Unit Type", ctx.unit.unit_type.value.replace("_", " ").title()],
            ["Area (m²)", f"{float(ctx.unit.area_sqm):,.2f}"],
            ["Bedrooms / Baths", f"{ctx.unit.bedrooms} / {ctx.unit.bathrooms}"],
            ["Total Price", _egp(ctx.contract.total_price)],
        ]
        ut = Table(unit_rows, colWidths=[50 * mm, 115 * mm])
        ut.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(ut)

        story.append(Paragraph("3. Payment Plan", h2))
        story.append(_ar("٣. جدول السداد", ar_h2))
        if ctx.payment_plan:
            plan_en, plan_ar = PLAN_LABELS.get(ctx.payment_plan.plan_type.value, ("—", "—"))
            story.append(Paragraph(
                f"Down payment: <b>{_egp(ctx.payment_plan.down_payment)}</b> — "
                f"Frequency: <b>{plan_en}</b> ({ctx.payment_plan.number_of_installments} installments)",
                body,
            ))
            story.append(_ar(f"المقدم: {_egp(ctx.payment_plan.down_payment)} — الدورية: {plan_ar}", ar_body))
            inst_header = ["#", "Due Date", "Amount (EGP)"]
            inst_data = [inst_header]
            for inst in ctx.installments:
                inst_data.append([
                    str(inst.installment_number),
                    inst.due_date,
                    f"{float(inst.due_amount):,.2f}",
                ])
            financed = ctx.contract.total_price - ctx.payment_plan.down_payment
            inst_data.append(["", "Financed balance", f"{float(financed):,.2f}"])
            it = Table(inst_data, colWidths=[15 * mm, 50 * mm, 50 * mm])
            it.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0159a1")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f0f7ff")),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ]))
            story.append(Spacer(1, 4))
            story.append(it)
        else:
            story.append(Paragraph("Payment plan to be agreed separately.", body))

        story.append(Spacer(1, 10))
        story.append(Paragraph("4. Terms & Conditions", h2))
        story.append(_ar("٤. الشروط والأحكام", ar_h2))
        terms_en = (
            "The buyer agrees to pay according to the schedule above. Late payments may incur penalties "
            "as per company policy. The unit is sold in current condition. This contract is governed by "
            "Egyptian law. Disputes shall be resolved through competent courts in Egypt."
        )
        terms_ar = (
            "يوافق المشتري على السداد وفق الجدول أعلاه. التأخر في السداد قد يترتب عليه غرامات وفق سياسة الشركة. "
            "تُباع الوحدة بحالتها الراهنة. يخضع هذا العقد للقانون المصري وتُحل النزاعات أمام المحاكم المختصة."
        )
        story.append(Paragraph(terms_en, body))
        story.append(_ar(terms_ar, ar_body))

        story.append(Spacer(1, 16))
        story.append(Paragraph("5. Signatures", h2))
        story.append(_ar("٥. التوقيعات", ar_h2))
        sig_rows = [
            ["Buyer Signature", "_________________________", "Date", "____________"],
            ["Seller Representative", "_________________________", "Date", "____________"],
        ]
        st = Table(sig_rows, colWidths=[40 * mm, 55 * mm, 20 * mm, 35 * mm])
        st.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(st)
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            "<i>E-signature ready — sign above or use platform mark-signed after digital approval.</i>",
            ParagraphStyle("Fine", parent=body, fontSize=8, textColor=colors.grey),
        ))

        generated = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        story.append(Spacer(1, 8))
        story.append(Paragraph(f"Generated by Fratelanza Platform — {generated}", ParagraphStyle(
            "Footer", parent=body, fontSize=7, textColor=colors.grey, alignment=TA_CENTER,
        )))

        doc.build(story)
        return buffer.getvalue()

    @staticmethod
    async def generate_and_store(
        db: AsyncSession,
        company_id: int,
        contract_id: int,
    ) -> tuple[bytes, str]:
        ctx = await ContractPdfService.load_context(db, company_id, contract_id)
        pdf_bytes = ContractPdfService.generate_pdf(ctx)
        rel_dir = Path("contracts") / str(company_id)
        abs_dir = Path(settings.STORAGE_LOCAL_PATH) / rel_dir
        abs_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{ctx.contract.contract_number}.pdf"
        rel_path = str(rel_dir / filename)
        abs_path = abs_dir / filename
        abs_path.write_bytes(pdf_bytes)
        return pdf_bytes, rel_path
