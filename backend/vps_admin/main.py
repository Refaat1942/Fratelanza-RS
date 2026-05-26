"""FastAPI VPS control plane scaffold.

This is intentionally small but production-shaped: it models customers,
installations, per-customer database assignments, heartbeat/license checks, and
offline grace data returned to the EXE.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from enum import StrEnum
import os
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from backend.vps_admin.storage import (
    load_customers,
    load_tenant_document,
    save_customer,
    save_tenant_document,
    tenant_db_path,
)


class LicenseState(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class CustomerRecord(BaseModel):
    customer_id: str
    display_name: str
    database_key: str
    api_key: str
    license_state: LicenseState = LicenseState.ACTIVE
    offline_grace_hours: int = 72


class InstallationHeartbeat(BaseModel):
    client_id: str
    installation_id: str
    app_version: str
    machine_name: str
    allow_remote_support: bool = False
    sent_at: datetime


class HeartbeatResponse(BaseModel):
    state: LicenseState
    message: str
    customer_id: str
    database_key: str
    display_name: str
    offline_allow_until: datetime


class DatabaseAssignmentResponse(BaseModel):
    customer_id: str
    database_key: str
    display_name: str


class CreateCustomerRequest(BaseModel):
    customer_id: str = Field(pattern=r"^[A-Z0-9_-]{3,40}$")
    display_name: str
    database_key: str = Field(pattern=r"^[a-zA-Z0-9_]{3,80}$")
    api_key: str = Field(min_length=16)


class LoginRequest(BaseModel):
    username: str
    password: str


class NamedCreateRequest(BaseModel):
    name: str
    description: str = ""


class UnitCreateRequest(BaseModel):
    name: str
    symbol: str
    allows_decimals: bool = False


class ProductCreateRequest(BaseModel):
    category_id: int
    brand_id: int | None = None
    unit_id: int
    sku: str
    product_name: str
    product_code: str
    barcode: str | None = None
    cost_price: Decimal = Decimal("0")
    sale_price: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("0")
    quantity_on_hand: Decimal = Decimal("0")
    reorder_level: Decimal = Decimal("0")
    expiry_date: str | None = None


class StockAdjustmentRequest(BaseModel):
    product_id: int
    quantity_delta: Decimal
    notes: str = ""


class CustomerCreateRequest(BaseModel):
    code: str
    name: str
    phone: str = ""
    email: str = ""
    address: str = ""
    tax_number: str = ""
    credit_limit: Decimal = Decimal("0")
    opening_balance: Decimal = Decimal("0")


class SupplierCreateRequest(BaseModel):
    code: str
    name: str
    contact_person: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    tax_number: str = ""
    opening_balance: Decimal = Decimal("0")


class ExpenseCreateRequest(BaseModel):
    category_id: int
    cashbox_id: int | None = None
    amount: Decimal
    expense_date: str | None = None
    date: str | None = None
    description: str = ""
    user_id: int | None = None


class RevenueCreateRequest(BaseModel):
    cashbox_id: int | None = None
    amount: Decimal
    revenue_date: str | None = None
    date: str | None = None
    source_name: str | None = None
    source: str | None = None
    description: str = ""
    user_id: int | None = None


class InvoiceCreateRequest(BaseModel):
    invoice_number: str
    customer_id: int | None = None
    payment_method: str
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    grand_total: Decimal
    paid_total: Decimal
    notes: str = ""
    user_id: int | None = None
    lines: list[dict[str, object]]


class BarcodeUpdateRequest(BaseModel):
    barcode: str


class CompanyProfileRequest(BaseModel):
    company_name: str
    trade_name: str = ""
    tax_number: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    logo_path: str = ""


class TaxCreateRequest(BaseModel):
    name: str
    rate: Decimal
    is_default: bool = False


app = FastAPI(title="Fratelanza VPS Admin API", version="0.1.0")

ADMIN_KEY = os.getenv("FRATELANZA_ADMIN_KEY", "change-this-admin-key")
CUSTOMERS: dict[str, CustomerRecord] = {
    customer_id: CustomerRecord(**row) for customer_id, row in load_customers().items()
}


DEFAULT_PERMISSIONS = [
    "dashboard.view",
    "users.manage",
    "sales.view",
    "sales.create",
    "sales.return",
    "inventory.view",
    "inventory.manage",
    "finance.view",
    "finance.manage",
    "crm.view",
    "crm.manage",
    "reports.view",
    "settings.manage",
    "barcode.manage",
    "admin_panel.manage",
]


def require_customer(
    x_client_id: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> CustomerRecord:
    """Authenticate customer installation by client id and bearer API key."""
    if not x_client_id or x_client_id not in CUSTOMERS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown client.")
    customer = CUSTOMERS[x_client_id]
    expected = f"Bearer {customer.api_key}"
    if authorization != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key.")
    return customer


def require_admin(x_admin_key: Annotated[str | None, Header()] = None) -> None:
    """Protect admin endpoints used by your laptop Admin EXE."""
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin key.")


def tenant_data(customer: CustomerRecord) -> dict[str, list[dict[str, object]] | dict[str, object]]:
    """Return isolated persisted data for a customer database key."""
    default = {
            "categories": [{"CategoryId": 1, "CategoryName": "General", "Description": "", "IsActive": True}],
            "brands": [],
            "units": [{"UnitId": 1, "UnitName": "Piece", "Symbol": "pc", "AllowsDecimals": False}],
            "products": [],
            "customers": [],
            "suppliers": [],
            "cashboxes": [{"CashboxId": 1, "CashboxName": "Main Cashbox", "OpeningBalance": Decimal("0"), "CurrentBalance": Decimal("0"), "IsActive": True}],
            "expense_categories": [{"ExpenseCategoryId": 1, "CategoryName": "General"}],
            "expenses": [],
            "revenues": [],
            "invoices": [],
            "invoice_items": [],
            "taxes": [],
            "company_profile": {
                "CompanyProfileId": 1,
                "CompanyName": customer.display_name,
                "TradeName": customer.display_name,
                "TaxNumber": "",
                "Phone": "",
                "Email": "",
                "AddressLine": "",
                "LogoPath": "",
            },
        }
    return load_tenant_document(customer.database_key, default)


def persist_tenant(customer: CustomerRecord, data: dict[str, object]) -> None:
    save_tenant_document(customer.database_key, data)


def next_id(rows: list[dict[str, object]], key: str) -> int:
    return max([int(row.get(key, 0)) for row in rows] or [0]) + 1


def decimal_value(value: object) -> Decimal:
    return Decimal(str(value or "0"))


def today_text() -> str:
    return date.today().isoformat()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/login")
def login(
    request: LoginRequest,
    customer: Annotated[CustomerRecord, Depends(require_customer)],
) -> dict[str, object]:
    """Authenticate a tenant user.

    The scaffold seeds an admin user for every tenant. Replace this with hashed
    user records in the tenant database before production.
    """
    if request.username != "admin" or request.password != "Admin@12345":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
    return {
        "id": 1,
        "username": "admin",
        "display_name": f"{customer.display_name} Admin",
        "is_active": True,
        "role": {"id": 1, "name": "Admin", "permissions": DEFAULT_PERMISSIONS},
    }


@app.get("/admin/customers", response_model=list[CustomerRecord])
def list_admin_customers(_: Annotated[None, Depends(require_admin)]) -> list[CustomerRecord]:
    """List customers for the Admin EXE."""
    return list(CUSTOMERS.values())


@app.post("/admin/customers", response_model=CustomerRecord)
def create_customer(
    request: CreateCustomerRequest,
    _: Annotated[None, Depends(require_admin)],
) -> CustomerRecord:
    """Create a customer and assign its separate database key."""
    if request.customer_id in CUSTOMERS:
        raise HTTPException(status_code=409, detail="Customer already exists.")
    customer = CustomerRecord(**request.model_dump())
    CUSTOMERS[customer.customer_id] = customer
    save_customer(customer)
    tenant_data(customer)
    return customer


@app.post("/admin/customers/{customer_id}/state/{state}", response_model=CustomerRecord)
def update_license_state(
    customer_id: str,
    state: LicenseState,
    _: Annotated[None, Depends(require_admin)],
) -> CustomerRecord:
    """Suspend/reactivate a customer from your admin panel."""
    customer = CUSTOMERS.get(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found.")
    updated = customer.model_copy(update={"license_state": state})
    CUSTOMERS[customer_id] = updated
    save_customer(updated)
    return updated


@app.get("/admin/customers/{customer_id}/database")
def customer_database_info(
    customer_id: str,
    _: Annotated[None, Depends(require_admin)],
) -> dict[str, str]:
    """Show where a customer's isolated VPS database file lives."""
    customer = CUSTOMERS.get(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found.")
    return {
        "customer_id": customer.customer_id,
        "database_key": customer.database_key,
        "database_path": str(tenant_db_path(customer.database_key)),
    }


@app.post("/installations/heartbeat", response_model=HeartbeatResponse)
def heartbeat(
    payload: InstallationHeartbeat,
    customer: Annotated[CustomerRecord, Depends(require_customer)],
) -> HeartbeatResponse:
    """Return license status and database assignment to the EXE."""
    if payload.client_id != customer.customer_id:
        raise HTTPException(status_code=403, detail="Client mismatch.")
    allow_until = datetime.now(timezone.utc) + timedelta(hours=customer.offline_grace_hours)
    return HeartbeatResponse(
        state=customer.license_state,
        message=f"License is {customer.license_state.value}.",
        customer_id=customer.customer_id,
        database_key=customer.database_key,
        display_name=customer.display_name,
        offline_allow_until=allow_until,
    )


@app.get("/installations/database-assignment", response_model=DatabaseAssignmentResponse)
def database_assignment(
    customer: Annotated[CustomerRecord, Depends(require_customer)],
) -> DatabaseAssignmentResponse:
    """Tell the EXE which isolated customer database key to use through the API."""
    return DatabaseAssignmentResponse(
        customer_id=customer.customer_id,
        database_key=customer.database_key,
        display_name=customer.display_name,
    )


@app.get("/business/categories")
def list_categories(customer: Annotated[CustomerRecord, Depends(require_customer)]) -> list[dict[str, object]]:
    return tenant_data(customer)["categories"]  # type: ignore[return-value]


@app.post("/business/categories")
def add_category(
    request: NamedCreateRequest,
    customer: Annotated[CustomerRecord, Depends(require_customer)],
) -> dict[str, object]:
    data = tenant_data(customer)
    rows = data["categories"]  # type: ignore[assignment]
    row = {"CategoryId": next_id(rows, "CategoryId"), "CategoryName": request.name, "Description": request.description, "IsActive": True}
    rows.append(row)
    persist_tenant(customer, data)
    return row


@app.get("/business/brands")
def list_brands(customer: Annotated[CustomerRecord, Depends(require_customer)]) -> list[dict[str, object]]:
    return tenant_data(customer)["brands"]  # type: ignore[return-value]


@app.post("/business/brands")
def add_brand(
    request: NamedCreateRequest,
    customer: Annotated[CustomerRecord, Depends(require_customer)],
) -> dict[str, object]:
    data = tenant_data(customer)
    rows = data["brands"]  # type: ignore[assignment]
    row = {"BrandId": next_id(rows, "BrandId"), "BrandName": request.name, "IsActive": True}
    rows.append(row)
    persist_tenant(customer, data)
    return row


@app.get("/business/units")
def list_units(customer: Annotated[CustomerRecord, Depends(require_customer)]) -> list[dict[str, object]]:
    return tenant_data(customer)["units"]  # type: ignore[return-value]


@app.post("/business/units")
def add_unit(
    request: UnitCreateRequest,
    customer: Annotated[CustomerRecord, Depends(require_customer)],
) -> dict[str, object]:
    data = tenant_data(customer)
    rows = data["units"]  # type: ignore[assignment]
    row = {"UnitId": next_id(rows, "UnitId"), "UnitName": request.name, "Symbol": request.symbol, "AllowsDecimals": request.allows_decimals}
    rows.append(row)
    persist_tenant(customer, data)
    return row


@app.get("/business/products")
def list_products(
    customer: Annotated[CustomerRecord, Depends(require_customer)],
    search: str = "",
) -> list[dict[str, object]]:
    data = tenant_data(customer)
    products = data["products"]  # type: ignore[assignment]
    if not search:
        return products
    needle = search.lower()
    return [
        product
        for product in products
        if needle in str(product.get("ProductName", "")).lower()
        or needle in str(product.get("Sku", "")).lower()
        or needle in str(product.get("Barcode", "")).lower()
    ]


@app.get("/business/products/next-sequence")
def next_product_sequence(customer: Annotated[CustomerRecord, Depends(require_customer)]) -> dict[str, int]:
    products = tenant_data(customer)["products"]  # type: ignore[assignment]
    return {"next_sequence": len(products) + 1}


@app.post("/business/products")
def add_product(
    request: ProductCreateRequest,
    customer: Annotated[CustomerRecord, Depends(require_customer)],
) -> dict[str, object]:
    data = tenant_data(customer)
    rows = data["products"]  # type: ignore[assignment]
    categories = data["categories"]  # type: ignore[assignment]
    brands = data["brands"]  # type: ignore[assignment]
    units = data["units"]  # type: ignore[assignment]
    category = next((row for row in categories if row["CategoryId"] == request.category_id), categories[0])
    brand = next((row for row in brands if row["BrandId"] == request.brand_id), None)
    unit = next((row for row in units if row["UnitId"] == request.unit_id), units[0])
    row = {
        "ProductId": next_id(rows, "ProductId"),
        "Sku": request.sku,
        "ProductName": request.product_name,
        "ProductCode": request.product_code,
        "Barcode": request.barcode,
        "CategoryName": category["CategoryName"],
        "BrandName": brand["BrandName"] if brand else "",
        "UnitName": unit["UnitName"],
        "CostPrice": request.cost_price,
        "SalePrice": request.sale_price,
        "TaxRate": request.tax_rate,
        "QuantityOnHand": request.quantity_on_hand,
        "ReorderLevel": request.reorder_level,
        "ExpiryDate": request.expiry_date,
        "IsActive": True,
    }
    rows.append(row)
    persist_tenant(customer, data)
    return row


@app.post("/business/stock-adjustments")
def adjust_stock(
    request: StockAdjustmentRequest,
    customer: Annotated[CustomerRecord, Depends(require_customer)],
) -> dict[str, str]:
    data = tenant_data(customer)
    for product in data["products"]:  # type: ignore[union-attr]
        if product["ProductId"] == request.product_id:
            product["QuantityOnHand"] = decimal_value(product["QuantityOnHand"]) + request.quantity_delta
            persist_tenant(customer, data)
            return {"status": "ok"}
    raise HTTPException(status_code=404, detail="Product not found.")


@app.post("/business/products/{product_id}/barcode")
def set_barcode(
    product_id: int,
    request: BarcodeUpdateRequest,
    customer: Annotated[CustomerRecord, Depends(require_customer)],
) -> dict[str, str]:
    data = tenant_data(customer)
    for product in data["products"]:  # type: ignore[union-attr]
        if product["ProductId"] == product_id:
            product["Barcode"] = request.barcode
            persist_tenant(customer, data)
            return {"status": "ok"}
    raise HTTPException(status_code=404, detail="Product not found.")


@app.get("/business/customers")
def list_business_customers(
    customer: Annotated[CustomerRecord, Depends(require_customer)],
    search: str = "",
) -> list[dict[str, object]]:
    rows = tenant_data(customer)["customers"]  # type: ignore[assignment]
    if not search:
        return rows
    needle = search.lower()
    return [row for row in rows if needle in str(row).lower()]


@app.post("/business/customers")
def add_business_customer(
    request: CustomerCreateRequest,
    customer: Annotated[CustomerRecord, Depends(require_customer)],
) -> dict[str, object]:
    data = tenant_data(customer)
    rows = data["customers"]  # type: ignore[assignment]
    row = {
        "CustomerId": next_id(rows, "CustomerId"),
        "CustomerCode": request.code,
        "FullName": request.name,
        "Phone": request.phone,
        "Email": request.email,
        "AddressLine": request.address,
        "TaxNumber": request.tax_number,
        "CreditLimit": request.credit_limit,
        "OpeningBalance": request.opening_balance,
        "IsActive": True,
    }
    rows.append(row)
    persist_tenant(customer, data)
    return row


@app.get("/business/suppliers")
def list_suppliers(
    customer: Annotated[CustomerRecord, Depends(require_customer)],
    search: str = "",
) -> list[dict[str, object]]:
    rows = tenant_data(customer)["suppliers"]  # type: ignore[assignment]
    if not search:
        return rows
    needle = search.lower()
    return [row for row in rows if needle in str(row).lower()]


@app.post("/business/suppliers")
def add_supplier(
    request: SupplierCreateRequest,
    customer: Annotated[CustomerRecord, Depends(require_customer)],
) -> dict[str, object]:
    data = tenant_data(customer)
    rows = data["suppliers"]  # type: ignore[assignment]
    row = {
        "SupplierId": next_id(rows, "SupplierId"),
        "SupplierCode": request.code,
        "SupplierName": request.name,
        "ContactPerson": request.contact_person,
        "Phone": request.phone,
        "Email": request.email,
        "AddressLine": request.address,
        "TaxNumber": request.tax_number,
        "OpeningBalance": request.opening_balance,
        "IsActive": True,
    }
    rows.append(row)
    persist_tenant(customer, data)
    return row


@app.get("/business/cashboxes")
def list_cashboxes(customer: Annotated[CustomerRecord, Depends(require_customer)]) -> list[dict[str, object]]:
    return tenant_data(customer)["cashboxes"]  # type: ignore[return-value]


@app.get("/business/expense-categories")
def list_expense_categories(customer: Annotated[CustomerRecord, Depends(require_customer)]) -> list[dict[str, object]]:
    return tenant_data(customer)["expense_categories"]  # type: ignore[return-value]


@app.post("/business/expense-categories")
def add_expense_category(
    request: NamedCreateRequest,
    customer: Annotated[CustomerRecord, Depends(require_customer)],
) -> dict[str, object]:
    data = tenant_data(customer)
    rows = data["expense_categories"]  # type: ignore[assignment]
    row = {"ExpenseCategoryId": next_id(rows, "ExpenseCategoryId"), "CategoryName": request.name}
    rows.append(row)
    persist_tenant(customer, data)
    return row


@app.get("/business/expenses")
def list_expenses(customer: Annotated[CustomerRecord, Depends(require_customer)]) -> list[dict[str, object]]:
    return tenant_data(customer)["expenses"]  # type: ignore[return-value]


@app.post("/business/expenses")
def add_expense(
    request: ExpenseCreateRequest,
    customer: Annotated[CustomerRecord, Depends(require_customer)],
) -> dict[str, object]:
    data = tenant_data(customer)
    rows = data["expenses"]  # type: ignore[assignment]
    categories = data["expense_categories"]  # type: ignore[assignment]
    cashboxes = data["cashboxes"]  # type: ignore[assignment]
    category = next((row for row in categories if row["ExpenseCategoryId"] == request.category_id), categories[0])
    cashbox = next((row for row in cashboxes if row["CashboxId"] == request.cashbox_id), None)
    row = {
        "ExpenseId": next_id(rows, "ExpenseId"),
        "CategoryName": category["CategoryName"],
        "CashboxName": cashbox["CashboxName"] if cashbox else "",
        "Amount": request.amount,
        "ExpenseDate": request.expense_date or request.date or today_text(),
        "Description": request.description,
        "CreatedAt": datetime.now(timezone.utc).isoformat(),
    }
    rows.append(row)
    if cashbox:
        cashbox["CurrentBalance"] = decimal_value(cashbox["CurrentBalance"]) - request.amount
    persist_tenant(customer, data)
    return row


@app.get("/business/revenues")
def list_revenues(customer: Annotated[CustomerRecord, Depends(require_customer)]) -> list[dict[str, object]]:
    return tenant_data(customer)["revenues"]  # type: ignore[return-value]


@app.post("/business/revenues")
def add_revenue(
    request: RevenueCreateRequest,
    customer: Annotated[CustomerRecord, Depends(require_customer)],
) -> dict[str, object]:
    data = tenant_data(customer)
    rows = data["revenues"]  # type: ignore[assignment]
    cashboxes = data["cashboxes"]  # type: ignore[assignment]
    cashbox = next((row for row in cashboxes if row["CashboxId"] == request.cashbox_id), None)
    row = {
        "RevenueId": next_id(rows, "RevenueId"),
        "CashboxName": cashbox["CashboxName"] if cashbox else "",
        "Amount": request.amount,
        "RevenueDate": request.revenue_date or request.date or today_text(),
        "SourceName": request.source_name or request.source or "",
        "Description": request.description,
        "CreatedAt": datetime.now(timezone.utc).isoformat(),
    }
    rows.append(row)
    if cashbox:
        cashbox["CurrentBalance"] = decimal_value(cashbox["CurrentBalance"]) + request.amount
    persist_tenant(customer, data)
    return row


@app.get("/business/invoices")
def list_invoices(customer: Annotated[CustomerRecord, Depends(require_customer)]) -> list[dict[str, object]]:
    return tenant_data(customer)["invoices"]  # type: ignore[return-value]


@app.get("/business/invoices/next-number")
def next_invoice_number(customer: Annotated[CustomerRecord, Depends(require_customer)]) -> dict[str, str]:
    invoices = tenant_data(customer)["invoices"]  # type: ignore[assignment]
    return {"invoice_number": f"INV-{len(invoices) + 1:06d}"}


@app.post("/business/invoices")
def create_invoice(
    request: InvoiceCreateRequest,
    customer: Annotated[CustomerRecord, Depends(require_customer)],
) -> dict[str, int]:
    data = tenant_data(customer)
    invoices = data["invoices"]  # type: ignore[assignment]
    invoice_items = data["invoice_items"]  # type: ignore[assignment]
    customers = data["customers"]  # type: ignore[assignment]
    products = data["products"]  # type: ignore[assignment]
    business_customer = next((row for row in customers if row["CustomerId"] == request.customer_id), None)
    invoice_id = next_id(invoices, "SalesInvoiceId")
    invoice = {
        "SalesInvoiceId": invoice_id,
        "InvoiceNumber": request.invoice_number,
        "CustomerName": business_customer["FullName"] if business_customer else "Walk-in customer",
        "InvoiceStatus": "paid" if request.paid_total >= request.grand_total else "partially_paid",
        "Subtotal": request.subtotal,
        "DiscountTotal": request.discount_total,
        "TaxTotal": request.tax_total,
        "GrandTotal": request.grand_total,
        "PaidTotal": request.paid_total,
        "CreatedAt": datetime.now(timezone.utc).isoformat(),
    }
    invoices.append(invoice)
    for line in request.lines:
        product_id = int(line["product_id"])
        quantity = decimal_value(line["quantity"])
        product = next((row for row in products if row["ProductId"] == product_id), None)
        if product:
            product["QuantityOnHand"] = decimal_value(product["QuantityOnHand"]) - quantity
        item = dict(line)
        item["SalesInvoiceId"] = invoice_id
        invoice_items.append(item)
    persist_tenant(customer, data)
    return {"invoice_id": invoice_id}


@app.get("/business/reports/summary")
def reports_summary(customer: Annotated[CustomerRecord, Depends(require_customer)]) -> dict[str, object]:
    data = tenant_data(customer)
    invoices = data["invoices"]  # type: ignore[assignment]
    expenses = data["expenses"]  # type: ignore[assignment]
    revenues = data["revenues"]  # type: ignore[assignment]
    products = data["products"]  # type: ignore[assignment]
    sales_total = sum(decimal_value(row.get("GrandTotal")) for row in invoices)
    expense_total = sum(decimal_value(row.get("Amount")) for row in expenses)
    revenue_total = sum(decimal_value(row.get("Amount")) for row in revenues)
    low_stock = [
        row
        for row in products
        if decimal_value(row.get("QuantityOnHand")) <= decimal_value(row.get("ReorderLevel"))
    ]
    return {
        "SalesTotal": sales_total,
        "TodaySales": sales_total,
        "TodayInvoices": len(invoices),
        "ExpenseTotal": expense_total,
        "RevenueTotal": revenue_total,
        "Profit": sales_total + revenue_total - expense_total,
        "ProductCount": len(products),
        "CustomerCount": len(data["customers"]),  # type: ignore[arg-type]
        "LowStockCount": len(low_stock),
    }


@app.get("/business/reports/top-products")
def top_products(customer: Annotated[CustomerRecord, Depends(require_customer)]) -> list[dict[str, object]]:
    data = tenant_data(customer)
    products = {row["ProductId"]: row for row in data["products"]}  # type: ignore[index]
    totals: dict[int, dict[str, object]] = {}
    for item in data["invoice_items"]:  # type: ignore[union-attr]
        product_id = int(item["product_id"])
        product = products.get(product_id, {})
        current = totals.setdefault(
            product_id,
            {"ProductName": product.get("ProductName", product_id), "QuantitySold": Decimal("0"), "SalesTotal": Decimal("0")},
        )
        current["QuantitySold"] = decimal_value(current["QuantitySold"]) + decimal_value(item["quantity"])
        current["SalesTotal"] = decimal_value(current["SalesTotal"]) + decimal_value(item["line_total"])
    return sorted(totals.values(), key=lambda row: row["QuantitySold"], reverse=True)[:20]


@app.get("/business/reports/low-stock")
def low_stock(customer: Annotated[CustomerRecord, Depends(require_customer)]) -> list[dict[str, object]]:
    return [
        {
            "ProductId": row["ProductId"],
            "Sku": row["Sku"],
            "ProductName": row["ProductName"],
            "QuantityOnHand": row["QuantityOnHand"],
            "ReorderLevel": row["ReorderLevel"],
        }
        for row in tenant_data(customer)["products"]  # type: ignore[union-attr]
        if decimal_value(row.get("QuantityOnHand")) <= decimal_value(row.get("ReorderLevel"))
    ]


@app.get("/business/settings/company-profile")
def company_profile(customer: Annotated[CustomerRecord, Depends(require_customer)]) -> dict[str, object]:
    return tenant_data(customer)["company_profile"]  # type: ignore[return-value]


@app.put("/business/settings/company-profile")
def update_company_profile(
    request: CompanyProfileRequest,
    customer: Annotated[CustomerRecord, Depends(require_customer)],
) -> dict[str, object]:
    profile = {
        "CompanyProfileId": 1,
        "CompanyName": request.company_name,
        "TradeName": request.trade_name,
        "TaxNumber": request.tax_number,
        "Phone": request.phone,
        "Email": request.email,
        "AddressLine": request.address,
        "LogoPath": request.logo_path,
    }
    data = tenant_data(customer)
    data["company_profile"] = profile
    persist_tenant(customer, data)
    return profile


@app.get("/business/settings/taxes")
def tax_settings(customer: Annotated[CustomerRecord, Depends(require_customer)]) -> list[dict[str, object]]:
    return tenant_data(customer)["taxes"]  # type: ignore[return-value]


@app.post("/business/settings/taxes")
def add_tax(
    request: TaxCreateRequest,
    customer: Annotated[CustomerRecord, Depends(require_customer)],
) -> dict[str, object]:
    data = tenant_data(customer)
    rows = data["taxes"]  # type: ignore[assignment]
    row = {
        "TaxSettingId": next_id(rows, "TaxSettingId"),
        "TaxName": request.name,
        "TaxRate": request.rate,
        "IsDefault": request.is_default,
        "IsActive": True,
    }
    rows.append(row)
    persist_tenant(customer, data)
    return row
