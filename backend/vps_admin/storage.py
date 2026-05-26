"""Persistent storage helpers for the VPS admin backend.

The backend uses one admin SQLite database for customers/licenses and one
separate SQLite database file per customer database key. Each tenant database
stores the current business document as JSON so the API contract can be evolved
before introducing a larger relational schema.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import json
import os
from pathlib import Path
import sqlite3
from typing import Any


DATA_ROOT = Path(os.getenv("FRATELANZA_VPS_DATA_ROOT", "runtime/vps_data")).resolve()
ADMIN_DB_PATH = DATA_ROOT / "admin.sqlite3"


def connection(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_admin_store() -> None:
    with connection(ADMIN_DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                database_key TEXT NOT NULL UNIQUE,
                api_key TEXT NOT NULL,
                license_state TEXT NOT NULL,
                offline_grace_hours INTEGER NOT NULL
            )
            """
        )


def load_customers() -> dict[str, dict[str, Any]]:
    initialize_admin_store()
    with connection(ADMIN_DB_PATH) as conn:
        rows = conn.execute("SELECT * FROM customers ORDER BY customer_id").fetchall()
    return {row["customer_id"]: dict(row) for row in rows}


def save_customer(customer: Any) -> None:
    initialize_admin_store()
    with connection(ADMIN_DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO customers
                (customer_id, display_name, database_key, api_key, license_state, offline_grace_hours)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(customer_id) DO UPDATE SET
                display_name = excluded.display_name,
                database_key = excluded.database_key,
                api_key = excluded.api_key,
                license_state = excluded.license_state,
                offline_grace_hours = excluded.offline_grace_hours
            """,
            (
                customer.customer_id,
                customer.display_name,
                customer.database_key,
                customer.api_key,
                customer.license_state.value
                if hasattr(customer.license_state, "value")
                else customer.license_state,
                customer.offline_grace_hours,
            ),
        )


def tenant_db_path(database_key: str) -> Path:
    safe_key = "".join(ch for ch in database_key if ch.isalnum() or ch in {"_", "-"})
    return DATA_ROOT / "tenants" / f"{safe_key}.sqlite3"


def load_tenant_document(database_key: str, default: dict[str, Any]) -> dict[str, Any]:
    path = tenant_db_path(database_key)
    with connection(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tenant_documents (
                document_key TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        row = conn.execute(
            "SELECT payload_json FROM tenant_documents WHERE document_key = 'business_data'"
        ).fetchone()
        if row is None:
            save_tenant_document(database_key, default)
            return default
        return json.loads(row["payload_json"], parse_float=Decimal)


def save_tenant_document(database_key: str, payload: dict[str, Any]) -> None:
    path = tenant_db_path(database_key)
    with connection(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tenant_documents (
                document_key TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO tenant_documents (document_key, payload_json, updated_at)
            VALUES ('business_data', ?, ?)
            ON CONFLICT(document_key) DO UPDATE SET
                payload_json = excluded.payload_json,
                updated_at = excluded.updated_at
            """,
            (json.dumps(payload, default=json_default), datetime.utcnow().isoformat()),
        )


def json_default(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")
