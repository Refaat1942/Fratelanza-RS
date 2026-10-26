import asyncio
import logging
import os
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

import app.models as _all_models  # noqa: F401  (register every model before create_all)
from app.api.v1.router import api_router
from app.api.v1.endpoints.files import router as files_router
from app.core.config import settings
from app.middleware.module_guard import ModuleGuardMiddleware
from app.middleware.security import AuthRateLimitMiddleware, SecurityHeadersMiddleware
from app.core.database import AsyncSessionLocal, Base, engine
from app.services.platform_billing_service import PlatformBillingService
from app.utils.seed import seed_database


logger = logging.getLogger(__name__)

# Postgres advisory lock ids — serialise schema/seed work across uvicorn workers
SCHEMA_LOCK_ID = 814201
SEED_LOCK_ID = 814202


async def bootstrap_database() -> None:
    from app.core.migrations import run_migrations

    async with engine.begin() as conn:
        await conn.execute(text("SELECT pg_advisory_xact_lock(:id)"), {"id": SCHEMA_LOCK_ID})
        await conn.run_sync(Base.metadata.create_all)
        if settings.RUN_MIGRATIONS_ON_STARTUP:
            await conn.run_sync(run_migrations)
    async with engine.connect() as lock_conn:
        await lock_conn.execute(text("SELECT pg_advisory_lock(:id)"), {"id": SEED_LOCK_ID})
        try:
            await seed_database()
        finally:
            await lock_conn.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": SEED_LOCK_ID})
            await lock_conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bootstrap_database()
    async with AsyncSessionLocal() as db:
        await PlatformBillingService.expire_all_due_trials(db)
        await db.commit()
    scheduler_task = None
    if settings.SCHEDULER_ENABLED:
        from app.services.scheduler_service import scheduler_loop

        scheduler_task = asyncio.create_task(scheduler_loop())
    yield
    if scheduler_task:
        scheduler_task.cancel()
        with suppress(asyncio.CancelledError):
            await scheduler_task
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise Real Estate ERP, CRM & Property Management SaaS Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuthRateLimitMiddleware)
app.add_middleware(ModuleGuardMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.STORAGE_LOCAL_PATH, exist_ok=True)
# Uploaded files are no longer a public static mount: only branding logos are public, every
# tenant document goes through an authenticated, tenant-checked endpoint (app/api/v1/endpoints/files.py).
app.include_router(files_router)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {
        "platform": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "api": settings.API_V1_PREFIX,
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.APP_ENV,
        "git_commit": os.getenv("GIT_COMMIT", "unknown"),
        "release_features": [
            "installment_calculator",
            "customer_portal",
            "portal_settings",
            "dynamic_pricing",
            "master_plan",
            "ai_reporting",
            "trial_14_days",
            "multi_tenant_rbac",
            "demo_management",
            "rental_management",
            "owner_settlements",
        ],
    }
