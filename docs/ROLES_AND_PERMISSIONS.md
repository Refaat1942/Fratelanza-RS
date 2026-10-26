# Roles and Permissions

Source of truth: `backend/app/core/permissions.py` (catalog + default templates) and `backend/app/services/access_service.py` (resolution). The frontend reads `GET /api/v1/auth/me/permissions` only to hide menus/buttons — **the backend authorises every call**.

## Three independent layers

| Layer | Stored in | Managed by | Meaning |
|---|---|---|---|
| Tenant feature flags | `companies.enabled_modules` (+ optional `users.allowed_modules`) | Platform super admin (`/super-admin/companies` → modules) | What the company bought / the demo shows |
| User permissions | `roles`, `role_permissions`, `user_roles` (or default template of `users.system_role`) | Tenant admin (`/roles`) | What the user may do inside enabled modules |
| Demo restrictions | `demo_environments.allowed_actions`, `dashboard_cards`, expiry/revocation | Platform super admin (`/super-admin/demos`) | Extra limits for demo tenants |

`effective(module, action) = enabled(module) AND role_grants(module, action) AND (not demo OR action ∈ demo.allowed_actions)`.

## Dimensions

* **Modules**: every key in `app/core/platform_modules.py` (dashboard, customers, leads, follow_ups, projects, reservations, contracts, collections, brokers, finance, hr, construction, procurement, warehouse, property, customer_service, real_estate_requests, rentals, owners, property_expenses, admin_expenses, users (incl. roles), customer_portal, reports, branding, ai_assistant).
* **Pages**: a module is a page/route; sidebar links and direct URLs are gated (`ModuleRoute`). Sub-pages are catalogued in `MODULE_PAGES` (display only today).
* **Actions**: view, create, edit, delete, approve, cancel, export, print, collect, refund, terminate, manage_permissions, view_sensitive. The middleware maps GET→view, POST→create, PUT/PATCH→edit, DELETE→delete, and path suffixes `/approve`, `/cancel`, `/terminate`, `/payments`, `/refunds`, `/adjustments`, `/export`, `/pdf|/statement` and all `/roles` writes to their specific action (`resolve_action`).
* **Data scope** (`roles.data_scope`): `all`, `branch` (records assigned to users of the same branch), `own` (records assigned to the user). Applied to customers, leads, property requests, rental contracts & receivables, search, customer/lead exports.
* **Field groups** (`roles.field_access`): identity (national ID/passport), owner_financials, salaries, commissions, bank_accounts, internal_notes. Hidden values are masked (`••••12`) or returned as `null`; masked values sent back by the UI never overwrite stored data.

## Default templates (no custom role assigned)

| System role | Suggested name | Highlights |
|---|---|---|
| company_admin / ceo / managing_director | Company Admin / General Manager | everything, all fields |
| sales_director / sales_manager / sales_agent | Sales | CRM, requests, reservations; agent = `own` scope, no IDs |
| customer_service | Customer Service | customers, tickets, maintenance |
| collection_officer | Collections Officer | rentals/collections: view, collect, print |
| accountant / finance_manager | Accountant / Finance | finance, owners, expenses, reports incl. sensitive; finance manager approves |
| project_manager | Property Manager | projects, property, rentals incl. approve/terminate |
| engineer | Maintenance Officer | property/maintenance, expense entry |
| hr_manager | HR / Payroll Officer | HR with salaries only |
| (template `auditor`) | Read-only Auditor | view + export everywhere, no writes |

## Administration UI (`/roles`, Arabic)

1. **الأدوار** — create a role from scratch or from a template, edit the module × action matrix (click a module to toggle the row), choose data scope and sensitive fields.
2. **تعيين الأدوار للمستخدمين** — pick a user, tick roles, see the resulting **effective permissions**.
3. **سجل التغييرات** — audit trail of permission changes.

Rules enforced by the API:
* Writes require `users.manage_permissions`.
* You cannot grant an action or field group you don't hold yourself.
* Roles of another tenant can't be assigned (404).
* Assigning any job role other than `sales_agent`, resetting an admin's password or editing an admin requires `manage_permissions`.
* **Lock-out guard**: a change that would leave no active user able to manage permissions is rejected (`lockout_prevented`); the last platform super admin can't be suspended or deleted.
* Changes apply on the next request (no redeploy): every write bumps `companies.permissions_version`.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/auth/me/permissions` | caller's effective permissions |
| GET | `/api/v1/roles/catalog` | modules, actions, field groups, scopes, templates |
| GET/POST | `/api/v1/roles` | list / create |
| POST | `/api/v1/roles/from-template` | `{ "template": "accountant" }` |
| GET/PUT/DELETE | `/api/v1/roles/{id}` | |
| GET/PUT | `/api/v1/roles/assignments/{user_id}` | `{ "role_ids": [..] }` + effective view |
| GET | `/api/v1/roles/audit/log` | tenant audit trail |
