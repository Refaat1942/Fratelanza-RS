"""Settings repositories."""

from __future__ import annotations

from fratelanza.infrastructure.repositories.base import SqlServerRepository


class SettingsRepository(SqlServerRepository):
    """Read and update company and application settings."""

    def company_profile(self) -> dict[str, object] | None:
        return self.fetch_one(
            """
            SELECT TOP 1 CompanyProfileId, CompanyName, TradeName, TaxNumber,
                   Phone, Email, AddressLine, LogoPath
            FROM settings.CompanyProfile
            ORDER BY CompanyProfileId
            """
        )

    def update_company_profile(
        self,
        *,
        company_name: str,
        trade_name: str,
        tax_number: str,
        phone: str,
        email: str,
        address: str,
        logo_path: str,
    ) -> None:
        profile = self.company_profile()
        if profile is None:
            self.execute(
                """
                INSERT INTO settings.CompanyProfile
                    (CompanyName, TradeName, TaxNumber, Phone, Email, AddressLine, LogoPath)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                company_name,
                trade_name,
                tax_number,
                phone,
                email,
                address,
                logo_path,
            )
            return
        self.execute(
            """
            UPDATE settings.CompanyProfile
            SET CompanyName = ?, TradeName = ?, TaxNumber = ?, Phone = ?, Email = ?,
                AddressLine = ?, LogoPath = ?, UpdatedAt = sysutcdatetime()
            WHERE CompanyProfileId = ?
            """,
            company_name,
            trade_name,
            tax_number,
            phone,
            email,
            address,
            logo_path,
            profile["CompanyProfileId"],
        )

    def tax_settings(self) -> list[dict[str, object]]:
        return self.fetch_all(
            """
            SELECT TaxSettingId, TaxName, TaxRate, IsDefault, IsActive
            FROM settings.TaxSettings
            ORDER BY TaxName
            """
        )

    def add_tax(self, name: str, rate: str, is_default: bool) -> None:
        self.execute(
            "INSERT INTO settings.TaxSettings (TaxName, TaxRate, IsDefault) VALUES (?, ?, ?)",
            name,
            rate,
            is_default,
        )
