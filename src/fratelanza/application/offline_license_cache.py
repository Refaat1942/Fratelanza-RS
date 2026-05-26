"""Offline license cache for controlled EXE deployments."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

from fratelanza.application.license import LicenseState


@dataclass(frozen=True)
class CachedLicensePolicy:
    """Last trusted VPS policy stored locally for offline startup."""

    state: LicenseState
    client_id: str
    installation_id: str
    database_key: str
    allow_until: datetime
    message: str = ""

    @property
    def can_run_now(self) -> bool:
        """Return True if the cached policy still allows offline use."""
        return self.state == LicenseState.ACTIVE and datetime.now(timezone.utc) <= self.allow_until


class OfflineLicenseCache:
    """Persist the last valid VPS license policy on the customer device."""

    def __init__(self, cache_path: Path) -> None:
        self._cache_path = cache_path

    def load(self) -> CachedLicensePolicy | None:
        """Load cached license data if it exists and is readable."""
        if not self._cache_path.exists():
            return None
        data = json.loads(self._cache_path.read_text(encoding="utf-8"))
        return CachedLicensePolicy(
            state=LicenseState(str(data["state"])),
            client_id=str(data["client_id"]),
            installation_id=str(data["installation_id"]),
            database_key=str(data.get("database_key", "")),
            allow_until=datetime.fromisoformat(str(data["allow_until"])),
            message=str(data.get("message", "")),
        )

    def save(self, policy: CachedLicensePolicy) -> None:
        """Save a trusted policy locally."""
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(policy)
        data["state"] = policy.state.value
        data["allow_until"] = policy.allow_until.isoformat()
        self._cache_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def clear(self) -> None:
        """Delete cached policy."""
        if self._cache_path.exists():
            self._cache_path.unlink()
