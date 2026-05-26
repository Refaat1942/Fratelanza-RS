"""Settings use cases."""

from __future__ import annotations

from fratelanza.infrastructure.repositories.settings_repository import SettingsRepository


class SettingsService:
    """Manage company, tax, and customization settings."""

    def __init__(self, repository: SettingsRepository) -> None:
        self._repository = repository

    def company_profile(self) -> dict[str, object] | None:
        return self._repository.company_profile()

    def save_company_profile(self, values: dict[str, object]) -> None:
        self._repository.update_company_profile(
            company_name=str(values.get("company_name") or "").strip(),
            trade_name=str(values.get("trade_name") or "").strip(),
            tax_number=str(values.get("tax_number") or "").strip(),
            phone=str(values.get("phone") or "").strip(),
            email=str(values.get("email") or "").strip(),
            address=str(values.get("address") or "").strip(),
            logo_path=str(values.get("logo_path") or "").strip(),
        )

    def tax_settings(self) -> list[dict[str, object]]:
        return self._repository.tax_settings()

    def add_tax(self, name: str, rate: str, is_default: bool) -> None:
        self._repository.add_tax(name.strip(), rate.strip(), is_default)
