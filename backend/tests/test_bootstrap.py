"""Startup is idempotent: restarting the app (create_all → migrations → seed) must succeed."""

from sqlalchemy import func, select, text

from app.core.database import AsyncSessionLocal, engine
from app.main import bootstrap_database
from app.models.rentals import PropertyOwner
from app.models.tenant import Company


async def test_restart_bootstrap_is_idempotent(database):
    async with AsyncSessionLocal() as db:
        demo = (await db.execute(select(Company).where(Company.code == "DEMO"))).scalar_one()
        owners_before = (await db.execute(select(func.count()).select_from(PropertyOwner).where(PropertyOwner.company_id == demo.id))).scalar()
    await bootstrap_database()
    await bootstrap_database()
    async with AsyncSessionLocal() as db:
        owners_after = (await db.execute(select(func.count()).select_from(PropertyOwner).where(PropertyOwner.company_id == demo.id))).scalar()
    assert owners_before == owners_after == 4
    async with engine.connect() as conn:
        version = (await conn.execute(text("SELECT version_num FROM alembic_version"))).scalar()
        not_null = (await conn.execute(text(
            "SELECT is_nullable FROM information_schema.columns WHERE table_name = 'units' AND column_name = 'company_id'"))).scalar()
    assert version == "20261027_01"
    assert not_null == "NO"


async def test_audit_log_is_append_only(database):
    from app.models.system import AuditLog

    async with AsyncSessionLocal() as db:
        db.add(AuditLog(action="test", module="tests"))
        await db.commit()
        log_id = (await db.execute(select(func.max(AuditLog.id)))).scalar()
        try:
            await db.execute(text("DELETE FROM audit_logs WHERE id = :id"), {"id": log_id})
            await db.commit()
            raise AssertionError("audit rows must not be deletable")
        except Exception as exc:
            await db.rollback()
            assert "append-only" in str(exc)
