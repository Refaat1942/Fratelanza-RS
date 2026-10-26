"""Multi-tenant hardening, RBAC, demo environments and property management.

Additive and idempotent: safe to run against an existing production database whose schema
was created by ``Base.metadata.create_all`` (the app's previous bootstrap), and against a
fresh database where ``create_all`` already produced the new columns.

Tenant ownership of ``units`` is derived deterministically from
units.floor_id → floors.building_id → buildings.project_id → projects.company_id
(all four FKs are NOT NULL), so no row is ever assigned to an arbitrary tenant. If any unit
cannot be resolved the migration stops before enforcing NOT NULL (see
docs/MIGRATION_AND_DEPLOYMENT.md for the reconciliation query).

Revision ID: 20261026_01
Revises:
Create Date: 2026-10-26
"""

import sqlalchemy as sa
from alembic import op

revision = "20261026_01"
down_revision = None
branch_labels = None
depends_on = None


def _exec(sql: str) -> None:
    op.execute(sa.text(sql))


def upgrade() -> None:
    bind = op.get_bind()

    # New tables (property_owners, rental_contracts, ...). checkfirst=True leaves existing tables alone.
    import app.models  # noqa: F401
    from app.core.database import Base

    Base.metadata.create_all(bind=bind, checkfirst=True)

    # --- companies: tenant settings, demo flag, permission cache version -------------------
    _exec("ALTER TABLE companies ADD COLUMN IF NOT EXISTS timezone VARCHAR(64) NOT NULL DEFAULT 'Africa/Cairo'")
    _exec("ALTER TABLE companies ADD COLUMN IF NOT EXISTS date_format VARCHAR(20) NOT NULL DEFAULT 'YYYY-MM-DD'")
    _exec("ALTER TABLE companies ADD COLUMN IF NOT EXISTS is_demo BOOLEAN NOT NULL DEFAULT false")
    _exec("ALTER TABLE companies ADD COLUMN IF NOT EXISTS permissions_version INTEGER NOT NULL DEFAULT 1")

    # --- roles / assignments -------------------------------------------------------------
    _exec("ALTER TABLE roles ADD COLUMN IF NOT EXISTS data_scope VARCHAR(20) NOT NULL DEFAULT 'all'")
    _exec("ALTER TABLE roles ADD COLUMN IF NOT EXISTS field_access TEXT")
    _exec("ALTER TABLE roles ADD COLUMN IF NOT EXISTS base_system_role VARCHAR(50)")
    _exec("ALTER TABLE roles ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true")
    for table, cols, name in (
        ("roles", "company_id, code", "uq_role_company_code"),
        ("user_roles", "user_id, role_id", "uq_user_role"),
        ("role_permissions", "role_id, permission_id", "uq_role_permission"),
    ):
        dupes = bind.execute(
            sa.text(f"SELECT count(*) FROM (SELECT {cols} FROM {table} GROUP BY {cols} HAVING count(*) > 1) d")
        ).scalar()
        if dupes:
            raise RuntimeError(
                f"Migration stopped: {dupes} duplicate ({cols}) groups in {table}. "
                "Resolve them manually (see docs/MIGRATION_AND_DEPLOYMENT.md) and re-run."
            )
        exists = bind.execute(
            sa.text("SELECT 1 FROM pg_constraint WHERE conname = :n UNION SELECT 1 FROM pg_class WHERE relname = :n"),
            {"n": name},
        ).first()
        if not exists:
            _exec(f"ALTER TABLE {table} ADD CONSTRAINT {name} UNIQUE ({cols})")

    # --- units: tenant ownership + property-management attributes ------------------------
    _exec("ALTER TABLE units ADD COLUMN IF NOT EXISTS company_id INTEGER REFERENCES companies(id)")
    _exec(
        """
        UPDATE units u SET company_id = p.company_id
        FROM floors f JOIN buildings b ON b.id = f.building_id JOIN projects p ON p.id = b.project_id
        WHERE u.floor_id = f.id AND u.company_id IS NULL
        """
    )
    # Reconciliation: a unit whose stored tenant differs from its project's tenant is a data error.
    mismatched = bind.execute(
        sa.text(
            """
            SELECT count(*) FROM units u JOIN floors f ON f.id = u.floor_id
            JOIN buildings b ON b.id = f.building_id JOIN projects p ON p.id = b.project_id
            WHERE u.company_id <> p.company_id
            """
        )
    ).scalar()
    unresolved = bind.execute(sa.text("SELECT count(*) FROM units WHERE company_id IS NULL")).scalar()
    if unresolved or mismatched:
        raise RuntimeError(
            f"Migration stopped: {unresolved} unit(s) without a resolvable tenant and {mismatched} unit(s) "
            "whose tenant disagrees with their project. Run the reconciliation query in "
            "docs/MIGRATION_AND_DEPLOYMENT.md, fix the rows, then restart."
        )
    _exec("ALTER TABLE units ALTER COLUMN company_id SET NOT NULL")
    _exec("CREATE INDEX IF NOT EXISTS ix_units_company_id ON units (company_id)")
    _exec("ALTER TABLE units ADD COLUMN IF NOT EXISTS owner_id INTEGER REFERENCES property_owners(id)")
    _exec("CREATE INDEX IF NOT EXISTS ix_units_owner_id ON units (owner_id)")
    for col, ddl in (
        ("furnishing_status", "VARCHAR(30)"),
        ("finishing", "VARCHAR(30)"),
        ("rental_category", "VARCHAR(30)"),
        ("construction_year", "INTEGER"),
        ("electricity_meter", "VARCHAR(100)"),
        ("water_meter", "VARCHAR(100)"),
        ("gas_meter", "VARCHAR(100)"),
        ("listing_purpose", "VARCHAR(20)"),
        ("occupancy_status", "VARCHAR(20) NOT NULL DEFAULT 'vacant'"),
        ("acquisition_info", "TEXT"),
        ("notes", "TEXT"),
    ):
        _exec(f"ALTER TABLE units ADD COLUMN IF NOT EXISTS {col} {ddl}")
    # Unit codes are unique within a tenant (only among non-deleted units)
    dup_codes = bind.execute(
        sa.text(
            "SELECT count(*) FROM (SELECT company_id, unit_code FROM units WHERE is_deleted = false "
            "GROUP BY company_id, unit_code HAVING count(*) > 1) d"
        )
    ).scalar()
    if not dup_codes:
        _exec(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_units_company_code ON units (company_id, unit_code) "
            "WHERE is_deleted = false"
        )

    # --- accounting: link journal entries to their source record (no double posting) -----
    _exec("ALTER TABLE journal_entries ADD COLUMN IF NOT EXISTS source_type VARCHAR(50)")
    _exec("ALTER TABLE journal_entries ADD COLUMN IF NOT EXISTS source_id INTEGER")
    exists = bind.execute(sa.text("SELECT 1 FROM pg_constraint WHERE conname = 'uq_journal_entry_source'")).first()
    if not exists:
        _exec(
            "ALTER TABLE journal_entries ADD CONSTRAINT uq_journal_entry_source "
            "UNIQUE (company_id, source_type, source_id)"
        )

    # --- notifications: idempotent scheduled reminders -----------------------------------
    _exec("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS dedupe_key VARCHAR(150)")
    exists = bind.execute(sa.text("SELECT 1 FROM pg_constraint WHERE conname = 'uq_notification_user_dedupe'")).first()
    if not exists:
        _exec("ALTER TABLE notifications ADD CONSTRAINT uq_notification_user_dedupe UNIQUE (user_id, dedupe_key)")

    # --- audit: before/after snapshots + append-only enforcement --------------------------
    _exec("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS changes TEXT")
    _exec(
        """
        CREATE OR REPLACE FUNCTION audit_logs_append_only() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'audit_logs is append-only';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    _exec("DROP TRIGGER IF EXISTS trg_audit_logs_append_only ON audit_logs")
    _exec(
        "CREATE TRIGGER trg_audit_logs_append_only BEFORE UPDATE OR DELETE ON audit_logs "
        "FOR EACH ROW EXECUTE FUNCTION audit_logs_append_only()"
    )

    # --- payroll: partial salary payments --------------------------------------------------
    _exec("ALTER TABLE payslips ADD COLUMN IF NOT EXISTS paid_amount NUMERIC(12, 2) NOT NULL DEFAULT 0")


def downgrade() -> None:
    # Only drops what this revision added to pre-existing tables; new tables are dropped last.
    _exec("DROP TRIGGER IF EXISTS trg_audit_logs_append_only ON audit_logs")
    _exec("DROP FUNCTION IF EXISTS audit_logs_append_only()")
    _exec("ALTER TABLE payslips DROP COLUMN IF EXISTS paid_amount")
    _exec("ALTER TABLE audit_logs DROP COLUMN IF EXISTS changes")
    _exec("ALTER TABLE notifications DROP CONSTRAINT IF EXISTS uq_notification_user_dedupe")
    _exec("ALTER TABLE notifications DROP COLUMN IF EXISTS dedupe_key")
    _exec("ALTER TABLE journal_entries DROP CONSTRAINT IF EXISTS uq_journal_entry_source")
    _exec("ALTER TABLE journal_entries DROP COLUMN IF EXISTS source_id")
    _exec("ALTER TABLE journal_entries DROP COLUMN IF EXISTS source_type")
    _exec("DROP INDEX IF EXISTS uq_units_company_code")
    for col in (
        "notes", "acquisition_info", "occupancy_status", "listing_purpose", "gas_meter", "water_meter",
        "electricity_meter", "construction_year", "rental_category", "finishing", "furnishing_status", "owner_id",
        "company_id",
    ):
        _exec(f"ALTER TABLE units DROP COLUMN IF EXISTS {col}")
    for table, name in (
        ("role_permissions", "uq_role_permission"),
        ("user_roles", "uq_user_role"),
        ("roles", "uq_role_company_code"),
    ):
        _exec(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {name}")
    for col in ("is_active", "base_system_role", "field_access", "data_scope"):
        _exec(f"ALTER TABLE roles DROP COLUMN IF EXISTS {col}")
    for col in ("permissions_version", "is_demo", "date_format", "timezone"):
        _exec(f"ALTER TABLE companies DROP COLUMN IF EXISTS {col}")
    for table in (
        "outbound_messages", "demo_environments", "property_requests", "payroll_payments", "admin_expenses",
        "property_expenses", "owner_settlement_payments", "rent_adjustments", "rent_payments",
        "rent_receivables", "owner_settlements", "rental_contracts", "property_owners",
    ):
        _exec(f"DROP TABLE IF EXISTS {table} CASCADE")
