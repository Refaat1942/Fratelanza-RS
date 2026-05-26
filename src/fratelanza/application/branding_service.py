"""Branding and white-label customization service."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fratelanza.core.config import ApplicationSettings


@dataclass(frozen=True)
class BrandingProfile:
    """Branding data used by login, shell, reports, and invoices."""

    vendor_name: str
    product_name: str
    client_display_name: str
    logo_path: Path | None
    primary_color: str
    allow_client_branding: bool

    @property
    def display_name(self) -> str:
        """Return the visible company name for the active installation."""
        return self.client_display_name if self.allow_client_branding else self.vendor_name

    @property
    def has_logo(self) -> bool:
        """Return True when a logo file is configured and available."""
        return self.logo_path is not None and self.logo_path.exists()


class BrandingService:
    """Resolve active branding from application and client settings."""

    def __init__(self, settings: ApplicationSettings) -> None:
        self._settings = settings

    def current_profile(self) -> BrandingProfile:
        """Return the branding profile for the current installation."""
        return BrandingProfile(
            vendor_name=self._settings.brand_name,
            product_name=self._settings.product_name,
            client_display_name=self._settings.branding.client_display_name,
            logo_path=self._settings.branding.logo_path,
            primary_color=self._settings.branding.primary_color,
            allow_client_branding=self._settings.branding.allow_client_branding,
        )
