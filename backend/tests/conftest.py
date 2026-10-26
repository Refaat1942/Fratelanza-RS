"""Integration test fixtures.

Tests run against a real PostgreSQL database (TEST_DATABASE_URL, default
``postgresql+asyncpg://fratelanza:fratelanza_secret@localhost:5432/fratelanza_test``). The schema is
dropped and rebuilt through the application's own bootstrap (create_all → Alembic → seed), so the
migration is exercised on every run. Never point TEST_DATABASE_URL at a real database.
"""

import os
import uuid

TEST_DB = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://fratelanza:fratelanza_secret@localhost:5432/fratelanza_test"
)
if "test" not in TEST_DB.rsplit("/", 1)[-1]:
    raise RuntimeError("Refusing to run tests against a database whose name does not contain 'test'")
os.environ["DATABASE_URL"] = TEST_DB
os.environ["DATABASE_URL_SYNC"] = TEST_DB.replace("+asyncpg", "")
os.environ["DEBUG"] = "false"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["OUTBOUND_MODE"] = "log"
os.environ.setdefault("STORAGE_LOCAL_PATH", "/tmp/fratelanza-test-uploads")

import httpx  # noqa: E402
import pytest  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database import engine  # noqa: E402
from app.main import app, bootstrap_database  # noqa: E402
from app.middleware import security as security_middleware  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
async def database():
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
    await bootstrap_database()
    yield
    await engine.dispose()


@pytest.fixture(scope="session")
async def client(database):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    security_middleware._login_attempts.clear()
    yield


async def login(client, username: str, password: str) -> dict:
    r = await client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
async def sa(client):
    return await login(client, settings.SUPER_ADMIN_EMAIL, settings.SUPER_ADMIN_PASSWORD)


class Tenant:
    def __init__(self, client, company_id: int, admin_headers: dict, code: str):
        self.client = client
        self.company_id = company_id
        self.admin = admin_headers
        self.code = code

    async def add_user(self, role: str, password: str = "Passw0rd!x") -> dict:
        name = f"{self.code.lower()}_{role}_{uuid.uuid4().hex[:5]}"
        r = await self.client.post(
            "/api/v1/users",
            headers=self.admin,
            json={"username": name, "email": f"{name}@example.com", "password": password,
                  "full_name_ar": "مستخدم", "full_name_en": "User", "system_role": role},
        )
        assert r.status_code == 200, r.text
        headers = await login(self.client, name, password)
        return {"id": r.json()["id"], "headers": headers, "username": name}

    async def build_unit(self, code: str, headers: dict | None = None) -> dict:
        h = headers or self.admin
        p = await self.client.post("/api/v1/projects", headers=h, json={
            "name_ar": f"مشروع {code}", "name_en": f"Project {code}", "code": f"P-{code}", "city": "Cairo"})
        assert p.status_code == 200, p.text
        b = await self.client.post(f"/api/v1/projects/{p.json()['id']}/buildings", headers=h,
                                   json={"name_ar": "مبنى", "name_en": "B", "code": "B"})
        assert b.status_code == 200, b.text
        f = await self.client.post(f"/api/v1/projects/buildings/{b.json()['id']}/floors", headers=h, json={"floor_number": 1})
        assert f.status_code == 200, f.text
        u = await self.client.post("/api/v1/projects/units", headers=h, json={
            "floor_id": f.json()["id"], "unit_code": code, "unit_number": "1", "unit_type": "apartment",
            "area_sqm": 120, "price": 2000000, "bedrooms": 2, "listing_purpose": "rent"})
        assert u.status_code == 200, u.text
        return {"project_id": p.json()["id"], "floor_id": f.json()["id"], "unit_id": u.json()["id"]}

    async def owner(self, name="Owner", rate=10, freq="monthly") -> int:
        r = await self.client.post("/api/v1/owners", headers=self.admin, json={
            "full_name": name, "commission_rate": rate, "settlement_frequency": freq, "national_id": "29001011234567",
            "bank_account": "1234567890"})
        assert r.status_code == 200, r.text
        return r.json()["id"]


ALL_MODULES = [
    "dashboard", "customers", "leads", "follow_ups", "projects", "reservations", "contracts", "collections", "brokers",
    "finance", "hr", "construction", "procurement", "warehouse", "property", "customer_service", "real_estate_requests",
    "rentals", "owners", "property_expenses", "admin_expenses", "users", "customer_portal", "reports", "branding",
]


@pytest.fixture(scope="session")
async def make_tenant(client, sa):
    plan_id = None

    async def factory(modules: list[str] | None = None) -> Tenant:
        nonlocal plan_id
        if plan_id is None:
            plans = await client.get("/api/v1/super-admin/subscription-plans", headers=sa)
            plan_id = plans.json()[0]["id"]
        code = f"T{uuid.uuid4().hex[:6].upper()}"
        admin_email = f"admin_{code.lower()}@example.com"
        r = await client.post("/api/v1/super-admin/companies", headers=sa, json={
            "name_ar": f"شركة {code}", "name_en": f"Company {code}", "code": code, "plan_id": plan_id,
            "start_trial": False, "enabled_modules": modules or ALL_MODULES, "admin_email": admin_email,
            "admin_password": "Admin!2345"})
        assert r.status_code == 200, r.text
        headers = await login(client, admin_email, "Admin!2345")
        return Tenant(client, r.json()["id"], headers, code)

    return factory
