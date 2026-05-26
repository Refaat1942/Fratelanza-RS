# Fratelanza Business Suite

Fratelanza Business Suite is a modern Python desktop business management system
foundation built for wholesale stores, cosmetics shops, retail stores, small
businesses, and general trading companies.

The repository is structured as a reusable commercial product starter that can
be customized per client and evolved toward ERP, SaaS, or web delivery later.

## Technology

- Python 3.11+
- PyQt6 professional desktop UI
- SQL Server with automated schema creation
- Clean architecture / MVC-friendly presentation layer
- Repository pattern for data access
- Dark/light theme-ready UI components
- Offline-first local SQL Server deployment model

## Project Structure

```text
config/                         Runtime configuration templates
database/sqlserver/             SQL Server schema and seed scripts
docs/                           Product and architecture documentation
src/fratelanza/
  application/                  Use cases and business services
  core/                         Config, security, logging, permissions
  domain/                       Reusable business entities and enums
  infrastructure/               SQL Server connection and repositories
  presentation/                 PyQt6 application shell and UI modules
tests/                          Focused validation tests
```

## Quick Start

1. Create and activate a virtual environment.
2. Install the package:

   ```bash
   pip install -e ".[dev]"
   ```

3. Copy `.env.example` to `.env` and update SQL Server settings.
4. Create the database schema:

   ```bash
   python -m fratelanza.database bootstrap
   ```

5. Launch the desktop app:

   ```bash
   python -m fratelanza
   ```

The default seeded administrator is configured in
`database/sqlserver/001_create_schema.sql`. Change the password immediately
after deployment.

## Included Foundation

- Login screen and authentication service
- Multi-user, role, and permission schema
- Password hashing with PBKDF2-SHA256
- User activity logging table and service hook
- SQL Server connection factory and repository base classes
- Dashboard layout with business KPI cards, module navigation, and placeholders
- Inventory, sales, finance, CRM, reports, barcode, and settings module shells
- Centralized configuration, logging, exception handling, and styling

## Commercial Customization Notes

Client-specific business rules should be added in the `application` layer and
client branding/theme changes should be isolated in `presentation/theme.py` and
`config/app.toml`. Database changes should be introduced as incremental scripts
under `database/sqlserver/` so deployments remain repeatable.
