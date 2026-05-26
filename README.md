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
- English and Arabic localization with right-to-left layout support
- Client branding with custom name, logo path, and primary color

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

To run your laptop admin console:

To build the Windows desktop EXE, run `scripts\build_customer_exe.bat` on
Windows.

The build script copies editable runtime files beside the EXE:

```text
dist\FratelanzaBusinessSuite\config\app.toml
dist\FratelanzaBusinessSuite\.env.example
```

Create `dist\FratelanzaBusinessSuite\.env` from `.env.example` and set local SQL
Server values before running the EXE.

The default seeded administrator is configured in
`database/sqlserver/001_create_schema.sql`. Change the password immediately
after deployment.

### SQL Server driver troubleshooting

If Windows shows `Data source name not found and no default driver specified`,
run:

```bash
python -m fratelanza.database doctor
```

The app automatically uses the best installed SQL Server ODBC driver in this
order: Driver 18, Driver 17, SQL Server Native Client 11.0, then SQL Server.
For SQL Server running locally in SSMS as `A-REFAAT`, create a `.env` with:

```env
FRATELANZA_DB_SERVER=A-REFAAT
FRATELANZA_DB_ENCRYPT=false
```

## Included Foundation

- Login screen and authentication service
- Multi-user, role, and permission schema
- Password hashing with PBKDF2-SHA256
- User activity logging table and service hook
- SQL Server connection factory and repository base classes
- Dashboard layout with business KPI cards, module navigation, and placeholders
- Inventory, sales, finance, CRM, reports, barcode, and settings module shells
- Centralized configuration, logging, exception handling, and styling

## Language and Branding

Set `FRATELANZA_LOCALE=en` or `FRATELANZA_LOCALE=ar` in `.env`. Arabic switches
the Qt layout direction to right-to-left automatically. Client branding can be
configured with:

```env
FRATELANZA_CLIENT_DISPLAY_NAME="Customer Company"
FRATELANZA_LOGO_PATH="/absolute/path/to/logo.png"
FRATELANZA_PRIMARY_COLOR="#55d6be"
```

## Commercial Customization Notes

Client-specific business rules should be added in the `application` layer and
client branding/theme changes should be isolated in `presentation/theme.py` and
`config/app.toml`. Database changes should be introduced as incremental scripts
under `database/sqlserver/` so deployments remain repeatable.
