# Architecture

Fratelanza Business Suite is organized around clean architecture boundaries so
the desktop product can later share business logic with SaaS or web front ends.

## Layers

### Domain

`src/fratelanza/domain` contains business entities and enumerations with no UI or
database dependencies. These objects describe reusable concepts such as users,
products, invoices, customers, suppliers, and dashboard metrics.

### Application

`src/fratelanza/application` contains use cases and orchestration services. UI
classes call this layer instead of directly reaching into SQL Server.

### Infrastructure

`src/fratelanza/infrastructure` contains SQL Server connectivity, schema
bootstrap helpers, and repositories. It owns pyodbc-specific implementation
details behind small interfaces.

### Presentation

`src/fratelanza/presentation` contains the PyQt6 application, reusable widgets,
theme system, login dialog, dashboard, navigation shell, and module placeholders.

## Current Modules

- Authentication and users
- Sales
- Inventory
- Finance
- Customers and suppliers
- Reports and analytics
- Settings
- Barcode system

Each module starts with a UI shell and database tables. New business behavior
should be added module-by-module using application services and repositories.

## Database Strategy

SQL Server scripts live under `database/sqlserver`. The first script creates the
database, security model, inventory, sales, finance, CRM, reporting support, and
settings tables. Future changes should be added as numbered migration scripts.

## Customization Strategy

- Branding: `config/app.toml` and `presentation/theme.py`
- Client-specific logic: new application services
- Client-specific fields: additive SQL migration scripts
- UI extensions: new widgets/views under `presentation/modules`
