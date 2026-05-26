"""Client for the VPS admin API."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class AdminApiSettings:
    api_base_url: str
    admin_key: str


def load_admin_settings() -> AdminApiSettings:
    """Load admin console settings from environment variables."""
    return AdminApiSettings(
        api_base_url=os.getenv("FRATELANZA_ADMIN_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/"),
        admin_key=os.getenv("FRATELANZA_ADMIN_KEY", "change-this-admin-key"),
    )


class AdminApiClient:
    """Small JSON client for customer/license administration."""

    def __init__(self, settings: AdminApiSettings) -> None:
        self._settings = settings

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        body = json.dumps(payload or {}).encode("utf-8") if payload is not None else None
        request = Request(
            f"{self._settings.api_base_url}/{path.lstrip('/')}",
            data=body,
            method=method.upper(),
            headers={
                "X-Admin-Key": self._settings.admin_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))

    def list_customers(self) -> list[dict[str, object]]:
        return self.request("GET", "/admin/customers")

    def create_customer(
        self,
        *,
        customer_id: str,
        display_name: str,
        database_key: str,
        api_key: str,
    ) -> dict[str, object]:
        return self.request(
            "POST",
            "/admin/customers",
            {
                "customer_id": customer_id,
                "display_name": display_name,
                "database_key": database_key,
                "api_key": api_key,
            },
        )

    def update_state(self, customer_id: str, state: str) -> dict[str, object]:
        return self.request("POST", f"/admin/customers/{customer_id}/state/{state}")

    def database_info(self, customer_id: str) -> dict[str, object]:
        return self.request("GET", f"/admin/customers/{customer_id}/database")
