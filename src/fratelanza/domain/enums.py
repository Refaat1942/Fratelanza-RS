"""Business enumerations shared across modules."""

from enum import StrEnum


class InvoiceStatus(StrEnum):
    DRAFT = "draft"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class PaymentMethod(StrEnum):
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    MOBILE_WALLET = "mobile_wallet"
    CREDIT = "credit"


class StockMovementType(StrEnum):
    PURCHASE = "purchase"
    SALE = "sale"
    RETURN_IN = "return_in"
    RETURN_OUT = "return_out"
    ADJUSTMENT_IN = "adjustment_in"
    ADJUSTMENT_OUT = "adjustment_out"
    EXPIRY_WRITE_OFF = "expiry_write_off"


class AccountType(StrEnum):
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    CASHBOX = "cashbox"
