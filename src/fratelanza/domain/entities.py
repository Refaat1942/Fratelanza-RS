"""Small domain entities used by services and presentation view models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from fratelanza.domain.enums import InvoiceStatus, PaymentMethod


@dataclass(frozen=True)
class Role:
    id: int
    name: str
    permissions: frozenset[str]


@dataclass(frozen=True)
class User:
    id: int
    username: str
    display_name: str
    role: Role
    is_active: bool
    last_login_at: datetime | None = None


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str


@dataclass(frozen=True)
class Product:
    id: int
    sku: str
    name: str
    category_name: str
    brand_name: str | None
    unit_name: str
    barcode: str | None
    sale_price: Money
    cost_price: Money
    quantity_on_hand: Decimal
    reorder_level: Decimal
    expiry_date: date | None = None


@dataclass(frozen=True)
class BusinessPartner:
    id: int
    code: str
    name: str
    phone: str | None
    email: str | None
    balance: Money


@dataclass(frozen=True)
class SalesInvoiceLine:
    product_id: int
    product_name: str
    quantity: Decimal
    unit_price: Money
    discount_amount: Money
    tax_amount: Money
    line_total: Money


@dataclass(frozen=True)
class SalesInvoice:
    id: int
    invoice_number: str
    customer: BusinessPartner | None
    status: InvoiceStatus
    payment_method: PaymentMethod
    subtotal: Money
    discount_total: Money
    tax_total: Money
    grand_total: Money
    created_at: datetime
    lines: tuple[SalesInvoiceLine, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DashboardMetric:
    title: str
    value: str
    subtitle: str
    accent: str
