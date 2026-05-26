"""Client for the Fratelanza VPS business API."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fratelanza.core.config import RemoteAdminSettings


@dataclass(frozen=True)
class TenantDatabaseAssignment:
    """Database assignment returned by the VPS for one customer."""

    customer_id: str
    database_key: str
    display_name: str
    api_base_url: str


class CloudApiClient:
    """Small JSON client used when the EXE works through the VPS API."""

    def __init__(self, settings: RemoteAdminSettings) -> None:
        self._settings = settings

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
    ) -> Any:
        """Send a JSON request to the configured VPS API."""
        body = json.dumps(payload or {}).encode("utf-8") if payload is not None else None
        url = f"{self._settings.api_base_url.rstrip('/')}/{path.lstrip('/')}"
        if query:
            url = f"{url}?{urlencode({key: value for key, value in query.items() if value is not None})}"
        request = Request(
            url,
            data=body,
            method=method.upper(),
            headers={
                "Authorization": f"Bearer {self._settings.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Client-Id": self._settings.client_id,
                "X-Installation-Id": self._settings.installation_id,
            },
        )
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))

    def tenant_assignment(self) -> TenantDatabaseAssignment:
        """Read the VPS database assignment for this installation."""
        payload = self.request("GET", "/installations/database-assignment")
        return TenantDatabaseAssignment(
            customer_id=str(payload["customer_id"]),
            database_key=str(payload["database_key"]),
            display_name=str(payload["display_name"]),
            api_base_url=self._settings.api_base_url,
        )
