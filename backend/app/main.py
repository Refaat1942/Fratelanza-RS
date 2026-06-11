from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

import app.models  # noqa: F401 — register ORM tables before create_all

from app.api.v1.router import api_router
from app.core.config import settings
from app.middleware.module_guard import ModuleGuardMiddleware
from app.middleware.security import AuthRateLimitMiddleware, SecurityHeadersMiddleware
from app.core.database import Base, engine
from app.utils.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_database()
    yield
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

uploads_dir = settings.STORAGE_LOCAL_PATH
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

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
    return {"status": "healthy", "environment": settings.APP_ENV}
