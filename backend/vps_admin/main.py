"""FastAPI VPS control plane scaffold.

This is intentionally small but production-shaped: it models customers,
installations, per-customer database assignments, heartbeat/license checks, and
offline grace data returned to the EXE.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field


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


app = FastAPI(title="Fratelanza VPS Admin API", version="0.1.0")

# Replace this in production with PostgreSQL/MySQL and hashed API keys.
CUSTOMERS: dict[str, CustomerRecord] = {}


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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/admin/customers", response_model=CustomerRecord)
def create_customer(request: CreateCustomerRequest) -> CustomerRecord:
    """Create a customer and assign its separate database key."""
    if request.customer_id in CUSTOMERS:
        raise HTTPException(status_code=409, detail="Customer already exists.")
    customer = CustomerRecord(**request.model_dump())
    CUSTOMERS[customer.customer_id] = customer
    return customer


@app.post("/admin/customers/{customer_id}/state/{state}", response_model=CustomerRecord)
def update_license_state(customer_id: str, state: LicenseState) -> CustomerRecord:
    """Suspend/reactivate a customer from your admin panel."""
    customer = CUSTOMERS.get(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found.")
    updated = customer.model_copy(update={"license_state": state})
    CUSTOMERS[customer_id] = updated
    return updated


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
