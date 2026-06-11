import enum
from decimal import Decimal
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class CashTransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"


class ChequeDirection(str, enum.Enum):
    RECEIVED = "received"
    ISSUED = "issued"


class ChequeStatus(str, enum.Enum):
    PENDING = "pending"
    DEPOSITED = "deposited"
    CLEARED = "cleared"
    BOUNCED = "bounced"
    CANCELLED = "cancelled"


class ProgressCertificateStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PAID = "paid"
    REJECTED = "rejected"


class ChartOfAccount(Base, TimestampMixin):
    __tablename__ = "chart_of_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("chart_of_accounts.id"))
    is_active: Mapped[bool] = mapped_column(default=True)


class JournalEntry(Base, TimestampMixin):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    entry_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    entry_date: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    lines: Mapped[list["JournalLine"]] = relationship(back_populates="journal_entry", lazy="selectin")


class JournalLine(Base, TimestampMixin):
    __tablename__ = "journal_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    journal_entry_id: Mapped[int] = mapped_column(ForeignKey("journal_entries.id"), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("chart_of_accounts.id"), nullable=False)
    debit: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    credit: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    cost_center: Mapped[Optional[str]] = mapped_column(String(100))

    journal_entry: Mapped["JournalEntry"] = relationship(back_populates="lines")


class BankAccount(Base, TimestampMixin):
    __tablename__ = "bank_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    bank_name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_number: Mapped[str] = mapped_column(String(100), nullable=False)
    iban: Mapped[Optional[str]] = mapped_column(String(50))
    currency: Mapped[str] = mapped_column(String(10), default="EGP")
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    is_active: Mapped[bool] = mapped_column(default=True)


class CashTransaction(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "cash_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    transaction_date: Mapped[str] = mapped_column(String(20), nullable=False)
    transaction_type: Mapped[CashTransactionType] = mapped_column(Enum(CashTransactionType), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), default="cash")
    reference_number: Mapped[Optional[str]] = mapped_column(String(100))
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"))
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))


class Cheque(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "cheques"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    direction: Mapped[ChequeDirection] = mapped_column(Enum(ChequeDirection), nullable=False)
    cheque_number: Mapped[str] = mapped_column(String(100), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(255), nullable=False)
    drawer_name: Mapped[Optional[str]] = mapped_column(String(255))
    payee_name: Mapped[Optional[str]] = mapped_column(String(255))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    issue_date: Mapped[str] = mapped_column(String(20), nullable=False)
    due_date: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[ChequeStatus] = mapped_column(Enum(ChequeStatus), default=ChequeStatus.PENDING)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customers.id"))
    subcontractor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("subcontractors.id"))


class Subcontractor(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "subcontractors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_person: Mapped[Optional[str]] = mapped_column(String(255))
    mobile: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    tax_number: Mapped[Optional[str]] = mapped_column(String(100))

    agreements: Mapped[list["SubcontractAgreement"]] = relationship(back_populates="subcontractor", lazy="selectin")


class SubcontractAgreement(Base, TimestampMixin):
    __tablename__ = "subcontract_agreements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    subcontractor_id: Mapped[int] = mapped_column(ForeignKey("subcontractors.id"), nullable=False, index=True)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"))
    contract_number: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    contract_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    retention_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=10)
    advance_payment: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    start_date: Mapped[Optional[str]] = mapped_column(String(20))
    end_date: Mapped[Optional[str]] = mapped_column(String(20))

    subcontractor: Mapped["Subcontractor"] = relationship(back_populates="agreements")
    certificates: Mapped[list["ProgressCertificate"]] = relationship(back_populates="agreement", lazy="selectin")


class ProgressCertificate(Base, TimestampMixin):
    __tablename__ = "progress_certificates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    agreement_id: Mapped[int] = mapped_column(ForeignKey("subcontract_agreements.id"), nullable=False, index=True)
    certificate_number: Mapped[str] = mapped_column(String(100), nullable=False)
    period_from: Mapped[str] = mapped_column(String(20), nullable=False)
    period_to: Mapped[str] = mapped_column(String(20), nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    cumulative_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    current_gross: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    retention_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    advance_deduction: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    other_deductions: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    net_payable: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    status: Mapped[ProgressCertificateStatus] = mapped_column(
        Enum(ProgressCertificateStatus), default=ProgressCertificateStatus.DRAFT
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)
    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    paid_at: Mapped[Optional[str]] = mapped_column(String(30))

    agreement: Mapped["SubcontractAgreement"] = relationship(back_populates="certificates")
