# Multi-Tenant Architecture

## Concepts

* **Software tenant** = `companies` row. Every business table has `company_id` (directly, or through a NOT NULL FK chain such as `floors → buildings → projects.company_id`).
* **Property owner** = `property_owners` row *inside* a tenant. It never grants access to anything.
* **Demo tenant** = a normal tenant with `companies.is_demo = true` plus a `demo_environments` row.

## Where the tenant comes from

The tenant is always `users.company_id` of the authenticated user, loaded from the database on every request (`app/api/deps.py:get_current_user`, `app/middleware/module_guard.py`). No endpoint accepts a tenant id from the client for tenant users; only the platform super admin can address a company by id (`/super-admin/*`, `/modules/company/{id}`, `/demos/*`).

## Enforcement layers

```
request ─► AccessGuardMiddleware (app/middleware/module_guard.py)
            1. decode JWT, load user + company (+ demo row)
            2. demo revoked / disabled / expired?           → 403 demo_*
            3. module of the path (ModuleService.module_for_path)
            4. module enabled for tenant (∩ user allowlist)? → 403 "Module ... not enabled"
            5. action from method + path (resolve_action)
            6. AccessContext.can(module, action)?           → 403 permission_denied
        ─► endpoint
            7. get_owned()/ensure_refs()  (app/core/tenant.py) — every id resolved
               WHERE id = :id AND company_id = :caller_company → else 404
            8. apply_data_scope()  — own / branch / all
            9. mask() — sensitive field groups
```

Cross-tenant ids return **404**, never 403, so ids cannot be probed.

### Related-record validation
`ensure_refs(db, company_id, [(Customer, id, "Customer"), (Unit, id, "Unit"), ...])` is called before linking records (contracts, reservations, leads, maintenance, reminders, tickets, property requests, role assignments). Units created through a floor inherit the floor's project tenant.

### Files
`app/api/v1/endpoints/files.py`: uploads are stored under `uploads/tenants/<company_id>/<category>/<uuid>.<ext>` (extension whitelist, 10 MB). `GET /uploads/...` serves `logo_*` publicly; `tenants/<id>/` and `contracts/<id>/` require a bearer token of that tenant (others get 404). Path traversal is rejected. Attachments on expenses must point into the caller's own folder.

### Background jobs
`app/services/scheduler_service.py` iterates companies and calls `run_company_jobs(db, company_id)` in a **separate session per tenant**; every query inside filters by that explicit `company_id`. Only one worker runs the loop (`pg_try_advisory_lock`). Writes are idempotent (unique receivable period, unique notification dedupe key). Tenants can trigger only their own run via `POST /rentals/jobs/run`.

### Caches
The only cache is the in-process permission cache in `AccessService` (`app/services/access_service.py`). Keys include `user_id`, `company_id`, `companies.permissions_version`, the tenant/user module lists and the demo row timestamp, so entries can neither leak across tenants nor survive a permission change (any change bumps `permissions_version` in the DB, which all workers read on every request).

### Exports & reports
Reports compute from tenant-filtered queries (`re_reports_service.py`, legacy `reports_service.py`). Legacy reports are additionally gated by the permission of the module whose data they expose (`REPORT_MODULES` in `reports.py`). Exports require the `export` action and are audited.

### Database constraints
* `units.company_id NOT NULL` + index; unique `(company_id, unit_code)` for live units.
* `uq_rental_contract_number (company_id, contract_number)`, `uq_owner_company_code`, `uq_role_company_code`.
* `uq_rental_active_unit` (partial unique index: one active lease per unit).
* `uq_receivable_contract_period`, `uq_settlement_owner_period` (partial), `uq_journal_entry_source`, `uq_notification_user_dedupe`.
* `audit_logs` is append-only (trigger rejects UPDATE/DELETE).

### Row-level security (not enabled — recommended next step)
RLS was **not** switched on: the app connects as the table owner and seeds/jobs/super-admin need cross-tenant access, so enabling it safely requires `SET LOCAL app.company_id` in `get_db`, `FORCE ROW LEVEL SECURITY` per table, and a separate bypass role for jobs. Isolation today rests on the middleware + per-query filters above, covered by `backend/tests/test_tenant_isolation.py`.

## Existing-data migration
See MIGRATION_AND_DEPLOYMENT.md. Units receive `company_id` from their own project (deterministic, never an arbitrary tenant); the migration stops if any unit cannot be resolved or disagrees with its project.
