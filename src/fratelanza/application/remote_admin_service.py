"""VPS-connected remote admin and licensing control."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import logging
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from fratelanza.application.license import LicenseState
from fratelanza.application.offline_license_cache import CachedLicensePolicy, OfflineLicenseCache
from fratelanza.core.config import RemoteAdminSettings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RemoteAdminStatus:
    """Current remote-admin state for the local installation."""

    state: LicenseState
    client_id: str
    installation_id: str
    api_base_url: str
    allow_remote_support: bool
    allow_remote_disable: bool
    last_heartbeat_at: datetime | None
    database_key: str = ""
    offline_allow_until: datetime | None = None
    message: str = ""

    @property
    def can_run(self) -> bool:
        """Return True when the local installation should be allowed to run."""
        return self.state in {
            LicenseState.ACTIVE,
            LicenseState.OFFLINE_GRACE,
            LicenseState.NOT_CONFIGURED,
        }


class RemoteAdminClient:
    """Small HTTPS JSON client for the Fratelanza VPS control API."""

    def __init__(self, settings: RemoteAdminSettings) -> None:
        self._settings = settings

    def heartbeat(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send a heartbeat and return the VPS response."""
        url = f"{self._settings.api_base_url}/installations/heartbeat"
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._settings.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        # URL is operator-configured in the VPS remote-admin settings.
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))


class RemoteAdminService:
    """Coordinate licensing, remote support, and VPS control state."""

    def __init__(
        self,
        settings: RemoteAdminSettings,
        client: RemoteAdminClient | None = None,
        license_cache: OfflineLicenseCache | None = None,
    ) -> None:
        self._settings = settings
        self._client = client or RemoteAdminClient(settings)
        self._license_cache = license_cache
        self._last_status = self._not_configured_status()

    def current_status(self) -> RemoteAdminStatus:
        """Return the most recent known VPS status."""
        return self._last_status

    def sync_installation(self, *, app_version: str, machine_name: str) -> RemoteAdminStatus:
        """Send installation heartbeat to the VPS and update local status."""
        if not self._settings.is_configured:
            self._last_status = self._not_configured_status()
            return self._last_status

        now = datetime.now(timezone.utc)
        payload = {
            "client_id": self._settings.client_id,
            "installation_id": self._settings.installation_id,
            "app_version": app_version,
            "machine_name": machine_name,
            "allow_remote_support": self._settings.allow_remote_support,
            "sent_at": now.isoformat(),
        }
        try:
            response = self._client.heartbeat(payload)
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            logger.warning("VPS heartbeat failed; using offline grace mode: %s", exc)
            cached_policy = self._license_cache.load() if self._license_cache else None
            if cached_policy and cached_policy.can_run_now:
                self._last_status = self._status(
                    LicenseState.OFFLINE_GRACE,
                    now,
                    "VPS is offline. Cached license policy allows temporary use.",
                    database_key=cached_policy.database_key,
                    offline_allow_until=cached_policy.allow_until,
                )
            else:
                self._last_status = self._status(
                    LicenseState.EXPIRED,
                    now,
                    "Cannot reach VPS and no valid offline license remains.",
                )
            return self._last_status

        try:
            state = LicenseState(str(response.get("state", LicenseState.ACTIVE.value)))
        except ValueError:
            state = LicenseState.OFFLINE_GRACE
        message = str(response.get("message", ""))
        database_key = str(response.get("database_key", ""))
        offline_allow_until = now + timedelta(hours=self._settings.offline_grace_hours)
        self._last_status = self._status(
            state,
            now,
            message,
            database_key=database_key,
            offline_allow_until=offline_allow_until,
        )
        if self._license_cache and state == LicenseState.ACTIVE:
            self._license_cache.save(
                CachedLicensePolicy(
                    state=LicenseState.ACTIVE,
                    client_id=self._settings.client_id,
                    installation_id=self._settings.installation_id,
                    database_key=database_key,
                    allow_until=offline_allow_until,
                    message=message,
                )
            )
        return self._last_status

    def _not_configured_status(self) -> RemoteAdminStatus:
        return self._status(LicenseState.NOT_CONFIGURED, None, "VPS control is not configured.")

    def _status(
        self,
        state: LicenseState,
        last_heartbeat_at: datetime | None,
        message: str,
        *,
        database_key: str = "",
        offline_allow_until: datetime | None = None,
    ) -> RemoteAdminStatus:
        return RemoteAdminStatus(
            state=state,
            client_id=self._settings.client_id,
            installation_id=self._settings.installation_id,
            api_base_url=self._settings.api_base_url,
            allow_remote_support=self._settings.allow_remote_support,
            allow_remote_disable=self._settings.allow_remote_disable,
            last_heartbeat_at=last_heartbeat_at,
            database_key=database_key,
            offline_allow_until=offline_allow_until,
            message=message,
        )
