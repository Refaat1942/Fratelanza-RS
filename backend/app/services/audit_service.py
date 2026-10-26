"""Audit trail helpers. Audit rows are append-only: no API updates or deletes them."""

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

# Never persisted in audit history
REDACTED_KEYS = {
    "password", "password_hash", "new_password", "current_password", "token", "access_token",
    "refresh_token", "totp_secret", "national_id", "passport_number", "tenant_id_number",
    "bank_account", "iban", "account_number",
}


def _clean(value: Any) -> Any:
    if isinstance(value, (Decimal,)):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return value


def sanitize(data: Optional[dict]) -> Optional[dict]:
    if data is None:
        return None
    return {k: ("[redacted]" if k in REDACTED_KEYS else _clean(v)) for k, v in data.items()}


def serialize_changes(before: Optional[dict], after: Optional[dict]) -> Optional[str]:
    if before is None and after is None:
        return None
    return json.dumps({"before": sanitize(before), "after": sanitize(after)}, ensure_ascii=False, default=str)


def snapshot(entity: Any, fields: list[str]) -> dict:
    return {f: getattr(entity, f, None) for f in fields}
