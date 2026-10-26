# Real Estate Gap Analysis

Baseline inspected: commit `9d05570` (branch `main`). FastAPI 0.115 + async SQLAlchemy 2.0 + PostgreSQL 16, React 18 + Vite + Tailwind, Arabic/English i18n (`frontend/src/locales`). Schema was created by `Base.metadata.create_all` in `backend/app/main.py` plus ad-hoc `ALTER TABLE` statements in `backend/app/utils/seed.py`; `alembic.ini` existed but no migration scripts. There were **no automated tests** and no ESLint config.

## What already existed (reused)

| Area | Existing implementation | How it was reused |
|---|---|---|
| Tenant | `Company` (`app/models/tenant.py`) with `company_id` FK on most business tables | Kept as the software tenant; extended with `timezone`, `date_format`, `is_demo`, `permissions_version` |
| Feature flags | `companies.enabled_modules`, `users.allowed_modules`, `ModuleService`, `ModuleGuardMiddleware` | Kept as layer 1 of authorization; guard rewritten as `AccessGuardMiddleware` |
| Roles | `SystemRole` enum on `users`; unused `roles`, `permissions`, `user_roles`, `role_permissions` tables | Tables now power tenant custom roles; each `SystemRole` maps to a default template |
| Real estate | `Project → Building → Floor → Unit` (`app/models/real_estate.py`) | Units extended with owner, furnishing, finishing, rental category, meters, listing purpose, occupancy |
| Sales | Reservations, sale contracts, payment plans, installments, payments | Unchanged (hardened against IDOR) |
| CRM | Customers, leads, reminders | Data scope + field masking added |
| Maintenance | `MaintenanceRequest` (`app/models/property.py`) | Linked 1:1 to property expenses |
| Accounting | Chart of accounts, journal entries/lines, bank accounts | Used for automatic, idempotent postings |
| HR | Employees, payroll runs, payslips | Payroll now posts to accounting; partial salary payments added |
| Notifications | `notifications` table, `NotificationService` | Scheduled reminders with dedupe keys |
| Audit | `audit_logs`, `log_audit()` | Before/after snapshots, append-only trigger, more events |
| UI | Tailwind design system (`index.css`), `DataTable`, `Modal`, `PageHeader`, `StatCard` | All new pages use the same components |

## Security defects found in the baseline (fixed)

| # | Defect | Location (before) | Fix |
|---|---|---|---|
| 1 | Any company user could set their own company `status` / `storage_limit_mb` (bypass trial suspension) | `PUT /companies/me/branding` used `CompanyUpdate` | `CompanyBrandingUpdate` schema |
| 2 | Any company user could create/promote users to `company_admin` | `POST/PUT /users` | Role assignment requires `users.manage_permissions`; admins only editable by admins |
| 3 | Delete any tenant's unit | `DELETE /projects/units/{id}` | tenant check |
| 4 | List any tenant's units by project id | `GET /projects/{id}/units` | tenant check |
| 5 | Create unit on another tenant's floor | `POST /projects/units` | floor → project tenant check |
| 6 | Record payment on any tenant's installment; client-chosen `customer_id` | `PaymentService.record_payment` | tenant join + payer forced to contract customer + row lock |
| 7 | Approve any tenant's reservation; reserve another tenant's unit/customer | `ReservationService` | tenant filters |
| 8 | Contract on another tenant's unit/customer/reservation | `ContractService.create_contract` | tenant filters |
| 9 | Read any customer's timeline | `GET /customers/{id}/timeline` | tenant check |
| 10 | Construction phases/tasks/milestones of all tenants | `construction.py` | tenant joins |
| 11 | Warehouse items/movements of all tenants | `warehouse.py` | tenant joins |
| 12 | Comment on any ticket; approve any broker commission | `tickets.py`, `brokers.py` | tenant checks |
| 13 | Cross-tenant `customer_id/lead_id/project_id/broker_id/assigned_to_id` links | leads, reminders, tickets, maintenance | `ensure_refs()` |
| 14 | Any tenant user could trigger platform-wide seeding | `POST /dashboard/reseed-demo` | super admin only |
| 15 | Contract PDFs and every upload publicly downloadable | `StaticFiles` mount at `/uploads` | `files.py`: logos public, tenant files require same-tenant token |
| 16 | Search and legacy reports bypassed module permissions (e.g. salaries via `/reports/hr_employees`) | `search.py`, `reports.py`, `exports.py` | per-module checks + field masking |
| 17 | Logo upload accepted any extension (incl. SVG) and unbounded size | `POST /companies/me/logo` | whitelist + 5 MB |

Also fixed: hard-coded fake sales chart (`dashboard_service.py`), and a frontend effect loop (`TrialBanner`) that re-requested `/auth/me` continuously.

## Functional gaps (implemented)

| Requirement | Status |
|---|---|
| Owners & owner profiles | **Done** — `property_owners`, `/owners` |
| Offers/requests (sale/rent) + explained matching | **Done** — `property_requests`, `/re-requests/{id}/matches` |
| Unit attributes (owner, furnishing, rental category incl. new-law, year, meters, occupancy) | **Done** |
| Building/floor creation API (was missing) | **Done** — `POST /projects/{id}/buildings`, `POST /projects/buildings/{id}/floors` |
| Rental contract lifecycle (draft/active/expiring/terminated/expired/renewed, replace tenant) | **Done** |
| One active lease per unit | **Done** — partial unique index + 409 |
| Rent receivables, partial payments, waivers, refunds, overdue days | **Done**, idempotent |
| Owner settlements (5 frequencies, commission, expenses, adjustments, partial payouts, statement) | **Done** |
| Property expenses with approval and maintenance link | **Done** |
| Administrative expenses, payroll payments | **Done** |
| Accounting postings without duplicates | **Done** — unique `(company_id, source_type, source_id)` |
| Financial reports (13) + Excel export | **Done** |
| Configurable dashboard cards | **Done** |
| Reminders (3 days before rent, overdue 1/7/30, settlement −7 days, lease −30 days) | **Done** |
| RBAC: module/page/action/data scope/field visibility + admin UI | **Done** (see ROLES_AND_PERMISSIONS.md) |
| Customer demos | **Done** (see DEMO_SETUP.md) |
| Responsive/mobile layout | **Done** — drawer sidebar, card-style tables on phones |

## Remaining gaps (not done — be aware)

* **PostgreSQL row-level security** is not enabled. Isolation is enforced in the middleware and every query; enabling RLS needs per-transaction `SET LOCAL app.company_id` across ~60 tables plus bypass for seeds/jobs — documented as next step in MULTITENANT_ARCHITECTURE.md.
* **Data scope (own/branch)** is applied to customers, leads, property requests, rental contracts/receivables and search/exports. Other legacy modules (reservations, contracts, tickets, …) still use tenant-wide scope.
* **Field masking** covers national ID/passport, owner bank details, commission rates, salaries, internal notes on the new modules, customers and HR. Legacy report rows for other modules are gated by module permission rather than masked field by field.
* **Page-level (tab) permissions** are catalogued (`MODULE_PAGES`) and shown in the matrix but not yet individually enforced; access is enforced per module + action.
* Legacy sale contracts/installments are not posted to the journal (unchanged behaviour); only the new property-management flows post automatically.
* WhatsApp/SMS have no provider integration in the codebase; the gateway records them (`outbound_messages`). Email can be sent via SMTP when `OUTBOUND_MODE=live`.
* No online payment provider exists in the codebase, so there are no external payments to sandbox.
* English translations exist for every new key; some legacy screens still contain hard-coded English labels (pre-existing).
* `vite build` warns that the JS bundle is >500 kB (pre-existing; code splitting not attempted).
