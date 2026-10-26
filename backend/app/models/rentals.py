"""Property management: owners, rental contracts, rent receivables, owner settlements,
property expenses, administrative expenses, payroll payments and customer property requests.

Every table carries ``company_id`` (the software tenant). A *property owner* is a business
record inside a tenant — never confuse it with the tenant itself.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin

SETTLEMENT_FREQUENCIES = {"monthly": 1, "quarterly": 3, "four_months": 4, "semiannual": 6, "annual": 12}
RENT_FREQUENCIES = {"monthly": 1, "quarterly": 3, "semiannual": 6, "annual": 12}


class PropertyOwner(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "property_owners"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_owner_company_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mobile: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    national_id: Mapped[Optional[str]] = mapped_column(String(50))
    address: Mapped[Optional[str]] = mapped_column(Text)
    bank_name: Mapped[Optional[str]] = mapped_column(String(255))
    bank_account: Mapped[Optional[str]] = mapped_column(String(100))
    iban: Mapped[Optional[str]] = mapped_column(String(50))
    settlement_frequency: Mapped[str] = mapped_column(String(20), default="monthly")
    # Management commission charged by the company on rent collected for this owner (percent)
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    settlement_day: Mapped[int] = mapped_column(Integer, default=5)
    notes: Mapped[Optional[str]] = mapped_column(Text)


class RentalContract(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "rental_contracts"
    __table_args__ = (
        UniqueConstraint("company_id", "contract_number", name="uq_rental_contract_number"),
        # A unit can only have one active lease at a time
        Index(
            "uq_rental_active_unit",
            "unit_id",
            unique=True,
            postgresql_where=text("status = 'active' AND is_deleted = false"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    contract_number: Mapped[str] = mapped_column(String(50), nullable=False)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), nullable=False, index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("property_owners.id"), index=True)
    tenant_customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customers.id"), index=True)
    tenant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    tenant_mobile: Mapped[Optional[str]] = mapped_column(String(50))
    tenant_id_number: Mapped[Optional[str]] = mapped_column(String(50))
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    rent_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    payment_frequency: Mapped[str] = mapped_column(String(20), default="monthly")
    due_day: Mapped[int] = mapped_column(Integer, default=1)
    deposit_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    other_charges: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    payment_terms: Mapped[Optional[str]] = mapped_column(Text)
    # Overrides the owner's default commission rate when set
    commission_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    # draft | active | terminated | expired | renewed  ("expiring" is derived from end_date)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    termination_date: Mapped[Optional[date]] = mapped_column(Date)
    termination_reason: Mapped[Optional[str]] = mapped_column(Text)
    renewed_from_id: Mapped[Optional[int]] = mapped_column(ForeignKey("rental_contracts.id"))
    attachments: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    assigned_to_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))


class RentReceivable(Base, TimestampMixin):
    __tablename__ = "rent_receivables"
    # Idempotency: one receivable per contract period, so retried schedule jobs never duplicate
    __table_args__ = (
        UniqueConstraint("rental_contract_id", "period_start", name="uq_receivable_contract_period"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    rental_contract_id: Mapped[int] = mapped_column(ForeignKey("rental_contracts.id"), nullable=False, index=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    amount_due: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    # Authorised waivers / discounts (positive reduces what the tenant owes)
    adjustment_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    # pending | partial | paid | waived  (overdue is derived from due_date)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)


class RentPayment(Base, TimestampMixin):
    __tablename__ = "rent_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    receivable_id: Mapped[int] = mapped_column(ForeignKey("rent_receivables.id"), nullable=False, index=True)
    rental_contract_id: Mapped[int] = mapped_column(ForeignKey("rental_contracts.id"), nullable=False, index=True)
    # payment | refund (refund amounts are stored positive)
    kind: Mapped[str] = mapped_column(String(20), default="payment")
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    paid_on: Mapped[date] = mapped_column(Date, nullable=False)
    method: Mapped[str] = mapped_column(String(30), default="cash")
    receipt_reference: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    received_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    # Set when the payment has been included in an owner settlement
    settlement_id: Mapped[Optional[int]] = mapped_column(ForeignKey("owner_settlements.id"), index=True)


class RentAdjustment(Base, TimestampMixin):
    __tablename__ = "rent_adjustments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    receivable_id: Mapped[int] = mapped_column(ForeignKey("rent_receivables.id"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))


class OwnerSettlement(Base, TimestampMixin):
    __tablename__ = "owner_settlements"
    __table_args__ = (
        Index(
            "uq_settlement_owner_period",
            "owner_id",
            "period_start",
            "period_end",
            unique=True,
            postgresql_where=text("status <> 'cancelled'"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("property_owners.id"), nullable=False, index=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    gross_collected: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    expenses_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    commission_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    adjustments: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    adjustments_note: Mapped[Optional[str]] = mapped_column(Text)
    net_payable: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    # draft | approved | partial | paid | cancelled
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    calculation: Mapped[Optional[str]] = mapped_column(Text)  # JSON breakdown for audit
    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))


class OwnerSettlementPayment(Base, TimestampMixin):
    __tablename__ = "owner_settlement_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    settlement_id: Mapped[int] = mapped_column(ForeignKey("owner_settlements.id"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    paid_on: Mapped[date] = mapped_column(Date, nullable=False)
    method: Mapped[str] = mapped_column(String(30), default="bank_transfer")
    reference: Mapped[Optional[str]] = mapped_column(String(100))
    paid_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))


class PropertyExpense(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "property_expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), nullable=False, index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("property_owners.id"), index=True)
    # A maintenance request can generate at most one expense (no duplicate accounting)
    maintenance_request_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("maintenance_requests.id"), unique=True
    )
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    vendor: Mapped[Optional[str]] = mapped_column(String(255))
    attachment_url: Mapped[Optional[str]] = mapped_column(String(500))
    # owner — deducted in the owner settlement; company — borne by the company
    charged_to: Mapped[str] = mapped_column(String(20), default="owner")
    payment_status: Mapped[str] = mapped_column(String(20), default="unpaid")  # unpaid | paid
    approval_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | approved | rejected
    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    settlement_id: Mapped[Optional[int]] = mapped_column(ForeignKey("owner_settlements.id"), index=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))


class AdminExpense(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "admin_expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    payment_status: Mapped[str] = mapped_column(String(20), default="unpaid")  # unpaid | partial | paid
    description: Mapped[Optional[str]] = mapped_column(Text)
    vendor: Mapped[Optional[str]] = mapped_column(String(255))
    document_url: Mapped[Optional[str]] = mapped_column(String(500))
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))


class PayrollPayment(Base, TimestampMixin):
    __tablename__ = "payroll_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    payslip_id: Mapped[int] = mapped_column(ForeignKey("payslips.id"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    paid_on: Mapped[date] = mapped_column(Date, nullable=False)
    method: Mapped[str] = mapped_column(String(30), default="bank_transfer")
    reference: Mapped[Optional[str]] = mapped_column(String(100))
    paid_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))


class PropertyRequest(Base, TimestampMixin, SoftDeleteMixin):
    """Offers (properties for sale / rent) and customer requirements (want to buy / rent)."""

    __tablename__ = "property_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    # offer_sale | offer_rent | request_buy | request_rent
    kind: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customers.id"))
    unit_id: Mapped[Optional[int]] = mapped_column(ForeignKey("units.id"))
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_mobile: Mapped[str] = mapped_column(String(50), nullable=False)
    property_type: Mapped[Optional[str]] = mapped_column(String(50))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    district: Mapped[Optional[str]] = mapped_column(String(150))
    price_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    price_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    area_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    area_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    rooms: Mapped[Optional[int]] = mapped_column(Integer)
    floor: Mapped[Optional[int]] = mapped_column(Integer)
    construction_year: Mapped[Optional[int]] = mapped_column(Integer)
    finishing: Mapped[Optional[str]] = mapped_column(String(30))
    furnishing_status: Mapped[Optional[str]] = mapped_column(String(30))
    has_utility_meters: Mapped[Optional[bool]] = mapped_column(Boolean)
    meter_notes: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open | matched | closed | cancelled
    assigned_to_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))


class DemoEnvironment(Base, TimestampMixin):
    """Configuration of a demo tenant (``companies.is_demo = true``) prepared for a prospect."""

    __tablename__ = "demo_environments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, unique=True)
    prospect_name: Mapped[str] = mapped_column(String(255), nullable=False)
    profile: Mapped[str] = mapped_column(String(50), default="full_erp")
    # JSON list of permitted actions inside the demo (server-enforced on every request)
    allowed_actions: Mapped[Optional[str]] = mapped_column(Text)
    # JSON list of dashboard card keys shown in the demo
    dashboard_cards: Mapped[Optional[str]] = mapped_column(Text)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_reset_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))


class OutboundMessage(Base, TimestampMixin):
    """Every outbound email / WhatsApp / SMS goes through the gateway and is recorded here.

    Demo tenants (and any tenant while OUTBOUND_MODE != "live") only ever get ``suppressed`` /
    ``logged`` rows — nothing leaves the platform.
    """

    __tablename__ = "outbound_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[Optional[int]] = mapped_column(ForeignKey("companies.id"), index=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)  # email | whatsapp | sms
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(255))
    body: Mapped[Optional[str]] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    # sent | logged | suppressed_demo | failed
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    dedupe_key: Mapped[Optional[str]] = mapped_column(String(150))
    error: Mapped[Optional[str]] = mapped_column(Text)
