# Migration and Deployment

## What changes in the database

Alembic is now set up (`backend/alembic/`). Revision `20261026_01` (`alembic/versions/20261026_01_multitenant_rbac_rentals.py`) is **additive and idempotent**:

* creates the new tables (`property_owners`, `rental_contracts`, `rent_receivables`, `rent_payments`, `rent_adjustments`, `owner_settlements`, `owner_settlement_payments`, `property_expenses`, `admin_expenses`, `payroll_payments`, `property_requests`, `demo_environments`, `outbound_messages`);
* adds columns: `companies(timezone, date_format, is_demo, permissions_version)`, `roles(data_scope, field_access, base_system_role, is_active)`, `units(company_id, owner_id, furnishing_status, finishing, rental_category, construction_year, electricity/water/gas_meter, listing_purpose, occupancy_status, acquisition_info, notes)`, `journal_entries(source_type, source_id)`, `notifications(dedupe_key)`, `audit_logs(changes)`, `payslips(paid_amount)`;
* backfills `units.company_id` from `floors → buildings → projects.company_id`, verifies there are **no unresolved and no mismatching** units, then sets `NOT NULL`. If either check fails, the migration raises and the transaction rolls back — nothing is assigned to an arbitrary tenant;
* adds unique constraints (roles, user_roles, role_permissions, journal source, notification dedupe, unit code per tenant). Duplicate groups stop the migration with a message instead of deleting data;
* installs an append-only trigger on `audit_logs`.

`downgrade()` removes what the revision added.

### Startup order
`app/main.py: bootstrap_database()` → Postgres advisory lock → `create_all` (new tables only) → `alembic upgrade head` → seed (separate advisory lock). Safe with the 2 uvicorn workers used in production. Disable with `RUN_MIGRATIONS_ON_STARTUP=false` and run `cd backend && alembic upgrade head` yourself if preferred.

### Reconciliation query (only if the migration stops)
```sql
SELECT u.id, u.unit_code, u.company_id AS unit_company, p.company_id AS project_company
FROM units u JOIN floors f ON f.id = u.floor_id
JOIN buildings b ON b.id = f.building_id JOIN projects p ON p.id = b.project_id
WHERE u.company_id IS NULL OR u.company_id <> p.company_id;
```
Decide per row which tenant legitimately owns the unit, fix it, restart.

Verified locally: the database created by the **original** code (17 units, existing seed data) upgraded cleanly; all units received their project's tenant; restarting twice is a no-op (`tests/test_bootstrap.py`).

## Login (since revision `20261027_01`)

* **One sign-in page** (`/login`) for the platform owner, company staff and buyers; `/portal/login` redirects there. After sign-in each user lands on their area (super admin → `/super-admin`, staff → `/dashboard`, buyers → `/portal`).
* Sign-in is by **username only, case-sensitive** (`Ahmed` ≠ `ahmed`). E-mail is an optional contact field and is not accepted as a login.
* Platform owner: username **`superadmin`**. On the first start of this version an existing installation sets the owner's username to `superadmin` and password to **`123456`** exactly once (`SUPER_ADMIN_RESET_PASSWORD`); later password changes are never overwritten. ⚠️ `123456` is weak — change it after the first login (key icon in the header).
* Existing users keep their current usernames (shown in Users). Company admins created by the super admin get the username typed in the company form.
* Customer demos are opened with a link — see DEMO_SETUP.md.

## Production deploy (Hostinger VPS, unchanged procedure)

`DEPLOY-VPS.sh` now backs the database up to `/root/fratelanza-backups/` before changing anything, and adopts containers that were created outside the `fratelanza` compose project (the "container name … already in use" error). If the old database lives in a different volume it copies the files into the production volume (old volume untouched) only when it is safe; otherwise it stops without deleting anything.

1. **Back up first** (also done automatically by the script):
   ```bash
   cd /opt/fratelanza
   docker exec fratelanza_postgres pg_dump -U fratelanza fratelanza_db > /root/fratelanza_pre_rbac_$(date +%F).sql
   ```
2. Merge the branch into `main`, then:
   ```bash
   cd /opt/fratelanza
   git fetch origin && git reset --hard origin/main
   bash DEPLOY-VPS.sh
   ```
3. Verify:
   ```bash
   curl -s http://127.0.0.1:9000/health        # release_features includes multi_tenant_rbac, demo_management
   docker logs fratelanza_backend 2>&1 | grep -i "migration stopped" || echo "migrations OK"
   docker exec fratelanza_postgres psql -U fratelanza fratelanza_db -c "select version_num from alembic_version"
   ```
4. Optional `.env` additions (defaults are safe): `OUTBOUND_MODE=log`, `SCHEDULER_ENABLED=true`, `SCHEDULER_INTERVAL_SECONDS=3600`.

### Behaviour changes operators should know
* Existing companies keep their stored `enabled_modules`; the new modules (rentals, owners, property_expenses, admin_expenses, real_estate_requests) must be switched on per company by the super admin. Plans `professional/enterprise/full` include them for new companies.
* Existing users keep working through default templates of their `system_role`. Some roles now see less than before (e.g. sales agents no longer see finance/HR, agents only see customers/leads assigned to them, national IDs are masked for agents). Assign custom roles in `/roles` if a team needs more.
* `/uploads/...` files other than logos now require login; contract PDFs open via the authenticated API.
* `POST /dashboard/reseed-demo` is super-admin only.

## Local development

```bash
# Postgres + Redis via Docker (dev compose) or a local Postgres
docker compose up -d postgres redis
cd backend && python -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt
DATABASE_URL=postgresql+asyncpg://fratelanza:fratelanza_secret@localhost:5432/fratelanza_db \
DATABASE_URL_SYNC=postgresql://fratelanza:fratelanza_secret@localhost:5432/fratelanza_db \
uvicorn app.main:app --reload            # http://localhost:8000/docs
cd ../frontend && npm ci && VITE_API_URL=http://localhost:8000 npm run dev   # http://localhost:5173
```

## Tests
```bash
createdb -O fratelanza fratelanza_test     # name must contain "test"; schema is dropped on every run
cd backend && TEST_DATABASE_URL=postgresql+asyncpg://fratelanza:fratelanza_secret@localhost:5432/fratelanza_test python -m pytest -q
cd frontend && npx tsc --noEmit && npm run build
```
