from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


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
    # Operational record that produced this entry — unique per tenant so a record is never posted twice
    source_type: Mapped[Optional[str]] = mapped_column(String(50))
    source_id: Mapped[Optional[int]] = mapped_column(Integer)

    __table_args__ = (
        UniqueConstraint("company_id", "source_type", "source_id", name="uq_journal_entry_source"),
    )

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
