"""Username-only, case-sensitive login shared by staff, super admin and buyers."""

from app.core.config import settings


async def test_super_admin_logs_in_with_username(client):
    r = await client.post("/api/v1/auth/login", json={"username": settings.SUPER_ADMIN_USERNAME, "password": settings.SUPER_ADMIN_PASSWORD})
    assert r.status_code == 200
    assert settings.SUPER_ADMIN_USERNAME == "superadmin" and settings.SUPER_ADMIN_PASSWORD == "123456"


async def test_login_is_case_sensitive_and_not_by_email(client, make_tenant):
    t = await make_tenant()
    r = await client.post("/api/v1/users", headers=t.admin, json={
        "username": f"Sara.{t.code}", "password": "Secret123", "full_name_ar": "سارة", "full_name_en": "Sara",
        "email": f"sara_{t.code.lower()}@example.com"})
    assert r.status_code == 200, r.text
    assert r.json()["username"] == f"Sara.{t.code}"  # stored exactly as typed
    ok = await client.post("/api/v1/auth/login", json={"username": f"Sara.{t.code}", "password": "Secret123"})
    assert ok.status_code == 200
    for wrong in (f"sara.{t.code.lower()}", f"SARA.{t.code}", f"sara_{t.code.lower()}@example.com"):
        r = await client.post("/api/v1/auth/login", json={"username": wrong, "password": "Secret123"})
        assert r.status_code == 401, wrong


async def test_buyer_uses_same_login_endpoint_without_email(client, make_tenant):
    t = await make_tenant()
    r = await client.post("/api/v1/users", headers=t.admin, json={
        "username": f"Buyer{t.code}", "password": "Buyer123", "full_name_ar": "مشتري", "full_name_en": "Buyer",
        "system_role": "customer"})
    assert r.status_code == 200, r.text
    assert r.json()["email"] is None
    tokens = await client.post("/api/v1/auth/login", json={"username": f"Buyer{t.code}", "password": "Buyer123"})
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens.json()['access_token']}"})
    assert me.json()["system_role"] == "customer"
