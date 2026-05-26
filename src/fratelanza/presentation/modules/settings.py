"""Settings module UI."""

from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QTabWidget, QVBoxLayout, QWidget

from fratelanza.application.settings_service import SettingsService
from fratelanza.core.config import ApplicationSettings
from fratelanza.presentation.components.data_table import DataEntryPanel, DataTable, FieldSpec


class SettingsView(QWidget):
    """Company profile, taxes, language, branding, and backup settings."""

    def __init__(self, service: SettingsService, settings: ApplicationSettings) -> None:
        super().__init__()
        self._service = service
        self._settings = settings
        self._build()

    def _build(self) -> None:
        tabs = QTabWidget()
        tabs.addTab(self._company_page(), "Company")
        tabs.addTab(self._tax_page(), "Taxes")
        tabs.addTab(self._system_page(), "System")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(tabs)

    def _company_page(self) -> QWidget:
        page = QWidget()
        profile = self._service.company_profile() or {}
        form = DataEntryPanel(
            title="Company Information",
            fields=[
                FieldSpec("company_name", "Company Name"),
                FieldSpec("trade_name", "Trade Name"),
                FieldSpec("tax_number", "Tax Number"),
                FieldSpec("phone", "Phone"),
                FieldSpec("email", "Email"),
                FieldSpec("address", "Address"),
                FieldSpec("logo_path", "Logo Path"),
            ],
            submit_label="Save Company Profile",
            on_submit=self._service.save_company_profile,
        )
        info = QLabel(
            "Current profile:\n"
            f"Company: {profile.get('CompanyName', '-')}\n"
            f"Trade name: {profile.get('TradeName', '-')}\n"
            f"Logo: {profile.get('LogoPath', '-')}"
        )
        info.setObjectName("Muted")
        layout = QHBoxLayout(page)
        layout.addWidget(info, stretch=1)
        layout.addWidget(form, stretch=2)
        return page

    def _tax_page(self) -> QWidget:
        page = QWidget()
        table = DataTable(
            title="Tax Settings",
            columns=[
                ("TaxSettingId", "ID"),
                ("TaxName", "Name"),
                ("TaxRate", "Rate"),
                ("IsDefault", "Default"),
                ("IsActive", "Active"),
            ],
            load_rows=lambda search: self._service.tax_settings(),
            searchable=False,
        )
        form = DataEntryPanel(
            title="Add Tax",
            fields=[
                FieldSpec("name", "Tax Name"),
                FieldSpec("rate", "Rate %", "0"),
                FieldSpec("is_default", "Default", field_type="bool"),
            ],
            submit_label="Save Tax",
            on_submit=lambda values: self._service.add_tax(
                str(values.get("name") or ""),
                str(values.get("rate") or "0"),
                bool(values.get("is_default")),
            ),
            on_success=table.refresh,
        )
        layout = QHBoxLayout(page)
        layout.addWidget(table, stretch=3)
        layout.addWidget(form, stretch=1)
        return page

    def _system_page(self) -> QWidget:
        page = QWidget()
        text = QLabel(
            "Runtime Settings\n\n"
            f"Language: {self._settings.default_locale}\n"
            f"Startup theme: {self._settings.theme}\n"
            "Available themes: dark, light\n"
            f"Currency: {self._settings.currency}\n"
            f"Backup enabled: {self._settings.auto_backup_enabled}\n"
            f"Backup folder: {self._settings.backup_directory}\n"
            f"Client display name: {self._settings.branding.client_display_name}\n"
            f"Configured logo: {self._settings.branding.logo_path or '-'}\n"
            f"VPS enabled: {self._settings.remote_admin.enabled}"
        )
        text.setObjectName("Muted")
        layout = QVBoxLayout(page)
        layout.addWidget(text)
        layout.addStretch()
        return page
