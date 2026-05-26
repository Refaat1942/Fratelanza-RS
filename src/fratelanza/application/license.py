"""License state shared by VPS control and offline cache."""

from enum import StrEnum


class LicenseState(StrEnum):
    """Installation state returned by the Fratelanza VPS control plane."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    OFFLINE_GRACE = "offline_grace"
    NOT_CONFIGURED = "not_configured"
