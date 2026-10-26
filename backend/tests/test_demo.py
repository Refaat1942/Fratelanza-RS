"""Demo environments (scenarios 13–18)."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.core.database import AsyncSessionLocal
from app.models.rentals import OutboundMessage, PropertyOwner, RentalContract
from app.services.demo_service import reset_plan


async def _create_demo(client, sa, profile="full_erp", **extra):
    payload = {"prospect_name": "عميل محتمل", "company_name_ar": "شركة تجريبية", "company_name_en": "Demo Co",
               "profile": profile, "users": [{"role": "company_admin"}], **extra}
    r = await client.post("/api/v1/demos", headers=sa, json=payload)
    assert r.status_code == 200, r.text
    demo = r.json()
    assert demo["link_path"].startswith("/demo/") and "credentials" not in demo
    token = demo["link_path"].rsplit("/", 1)[1]
    r = await client.post("/api/v1/auth/demo-link", json={"token": token})
    assert r.status_code == 200, r.text
    return demo, {"Authorization": f"Bearer {r.json()['access_token']}"}


async def test_13_demo_user_only_accesses_assigned_demo_tenant(client, sa, make_tenant):
    prod = await make_tenant()
    pu = await prod.build_unit("PROD-13")
    demo, h = await _create_demo(client, sa)
    units = (await client.get("/api/v1/rentals/units", headers=h)).json()
    assert units and all(u["unit_code"].startswith("PALM-") for u in units)
    assert (await client.put(f"/api/v1/rentals/units/{pu['unit_id']}", headers=h, json={"notes": "x"})).status_code == 404
    me = (await client.get("/api/v1/auth/me/permissions", headers=h)).json()
    assert me["is_demo"] is True and me["company_id"] == demo["company_id"]
    # never platform admin
    assert (await client.get("/api/v1/super-admin/companies", headers=h)).status_code == 403
    assert (await client.get("/api/v1/demos", headers=h)).status_code == 403
    assert (await client.get("/api/v1/super-admin/settings", headers=h)).status_code == 403


async def test_14_demo_data_isolated_from_production(client, sa, make_tenant):
    prod = await make_tenant()
    demo, h = await _create_demo(client, sa)
    prod_owners = (await client.get("/api/v1/owners", headers=prod.admin)).json()
    demo_owners = (await client.get("/api/v1/owners", headers=h)).json()
    assert prod_owners == [] and len(demo_owners) == 4
    async with AsyncSessionLocal() as db:
        demo_rows = (await db.execute(select(func.count()).select_from(PropertyOwner).where(PropertyOwner.company_id == demo["company_id"]))).scalar()
    assert demo_rows == 4
    # realistic data exists: active leases, overdue rent, settlements
    contracts = (await client.get("/api/v1/rentals/contracts", headers=h)).json()
    statuses = {c["status"] for c in contracts}
    assert {"terminated", "draft"} <= statuses and ("active" in statuses or "expiring" in statuses)
    overdue = (await client.get("/api/v1/rentals/receivables?status=overdue", headers=h)).json()
    assert overdue
    assert (await client.get("/api/v1/owners/settlements", headers=h)).json()


async def test_15_demo_never_triggers_external_messages(client, sa):
    demo, h = await _create_demo(client, sa)
    # the seeded demo ran the reminder job; anything it produced must be suppressed
    await client.post("/api/v1/rentals/jobs/run", headers=h)
    async with AsyncSessionLocal() as db:
        msgs = (await db.execute(select(OutboundMessage).where(OutboundMessage.company_id == demo["company_id"]))).scalars().all()
    assert all(m.status == "suppressed_demo" and m.provider == "demo_sink" for m in msgs)
    # exports are disabled by default in demos (bulk-download restriction)
    r = await client.get("/api/v1/re-reports/contracts/export", headers=h)
    assert r.status_code == 403 and r.json()["action"] == "export"
    # destructive actions & refunds are disabled by default
    contracts = (await client.get("/api/v1/rentals/contracts", headers=h)).json()
    draft = next(c for c in contracts if c["status"] == "draft")
    assert (await client.delete(f"/api/v1/rentals/contracts/{draft['id']}", headers=h)).status_code == 403
    paid = next(r for r in (await client.get("/api/v1/rentals/receivables?status=paid", headers=h)).json())
    assert (await client.post(f"/api/v1/rentals/receivables/{paid['id']}/refunds", headers=h,
                              json={"amount": 1, "paid_on": "2026-01-01"})).status_code == 403
    # AI requests are forced to the local provider for demo tenants
    from app.middleware.module_guard import current_access
    from app.services.access_service import AccessContext
    from app.services.llm_client import LLMClient

    token = current_access.set(AccessContext(1, demo["company_id"], None, False, True, ()))
    try:
        assert LLMClient.resolve_provider() == "local"
    finally:
        current_access.reset(token)


async def test_16_expired_or_revoked_demo_rejects_access(client, sa):
    demo, h = await _create_demo(client, sa)
    assert (await client.get("/api/v1/owners", headers=h)).status_code == 200
    await client.post(f"/api/v1/demos/{demo['id']}/revoke", headers=sa)
    r = await client.get("/api/v1/owners", headers=h)
    assert r.status_code == 403 and r.json()["detail"] == "demo_revoked"
    token = demo["link_path"].rsplit("/", 1)[1]
    r = await client.post("/api/v1/auth/demo-link", json={"token": token})
    assert r.status_code == 403 and r.json()["detail"] == "demo_revoked"
    await client.post(f"/api/v1/demos/{demo['id']}/restore", headers=sa)
    assert (await client.get("/api/v1/owners", headers=h)).status_code == 200
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    await client.put(f"/api/v1/demos/{demo['id']}", headers=sa, json={"expires_at": past})
    r = await client.get("/api/v1/owners", headers=h)
    assert r.status_code == 403 and r.json()["detail"] == "demo_expired"
    assert (await client.get("/api/v1/auth/me", headers=h)).status_code == 403
    r = await client.post("/api/v1/auth/demo-link", json={"token": token})
    assert r.status_code == 403 and r.json()["detail"] == "demo_expired"
    # the end date is set in days and can be extended
    await client.put(f"/api/v1/demos/{demo['id']}", headers=sa, json={"valid_days": 5})
    refreshed = (await client.get(f"/api/v1/demos/{demo['id']}", headers=sa)).json()
    assert refreshed["status"] == "active" and refreshed["days_left"] == 5
    # a regenerated link invalidates the old one
    new = (await client.post(f"/api/v1/demos/{demo['id']}/link", headers=sa)).json()
    assert (await client.post("/api/v1/auth/demo-link", json={"token": token})).status_code == 404
    new_token = new["link_path"].rsplit("/", 1)[1]
    assert (await client.post("/api/v1/auth/demo-link", json={"token": new_token})).status_code == 200
    assert (await client.post("/api/v1/auth/demo-link", json={"token": "x" * 32})).status_code == 404


async def test_17_resetting_a_demo_does_not_affect_other_demos(client, sa, make_tenant):
    prod = await make_tenant()
    await prod.owner("Production owner")
    demo_a, ha = await _create_demo(client, sa)
    demo_b, hb = await _create_demo(client, sa)
    # mutate demo A, then reset it
    await client.post("/api/v1/owners", headers=ha, json={"full_name": "Temporary owner"})
    assert len((await client.get("/api/v1/owners", headers=ha)).json()) == 5
    async with AsyncSessionLocal() as db:
        before_b = (await db.execute(select(func.count()).select_from(RentalContract).where(RentalContract.company_id == demo_b["company_id"]))).scalar()
    r = await client.post(f"/api/v1/demos/{demo_a['id']}/reset", headers=sa)
    assert r.status_code == 200, r.text
    assert len((await client.get("/api/v1/owners", headers=ha)).json()) == 4  # back to baseline
    async with AsyncSessionLocal() as db:
        after_b = (await db.execute(select(func.count()).select_from(RentalContract).where(RentalContract.company_id == demo_b["company_id"]))).scalar()
    assert before_b == after_b
    assert len((await client.get("/api/v1/owners", headers=prod.admin)).json()) == 1
    # demo users and audit trail survive the reset
    assert (await client.get("/api/v1/auth/me", headers=ha)).status_code == 200
    audit = (await client.get(f"/api/v1/demos/{demo_a['id']}/audit", headers=sa)).json()
    assert any(a["action"] == "demo_reset" for a in audit)
    # production tenants can never be reset
    from app.services.demo_service import purge_tenant_data

    async with AsyncSessionLocal() as db:
        try:
            await purge_tenant_data(db, prod.company_id)
            raise AssertionError("production purge must be refused")
        except Exception as exc:  # HTTPException
            assert "demo" in str(getattr(exc, "detail", exc)).lower()


async def test_18_each_demo_respects_its_own_configuration(client, sa):
    # Customer A: units, rentals, collections, owner settlements, financial reports
    demo_a, ha = await _create_demo(
        client, sa, profile="rental_collections",
        enabled_modules=["dashboard", "projects", "rentals", "owners", "reports"],
    )
    # Customer B: properties, leads, sales requests, CRM only
    demo_b, hb = await _create_demo(
        client, sa, profile="sales_brokerage",
        enabled_modules=["dashboard", "projects", "leads", "customers", "real_estate_requests"],
    )
    assert (await client.get("/api/v1/rentals/contracts", headers=ha)).status_code == 200
    assert (await client.get("/api/v1/owners/settlements", headers=ha)).status_code == 200
    assert (await client.get("/api/v1/re-reports/profit_loss", headers=ha)).status_code == 200
    assert (await client.get("/api/v1/leads", headers=ha)).status_code == 403
    # B: disabled modules blocked by direct API calls
    for path in ("/api/v1/rentals/contracts", "/api/v1/owners", "/api/v1/owners/settlements", "/api/v1/re-reports/profit_loss",
                 "/api/v1/collections/installments", "/api/v1/hr/employees"):
        assert (await client.get(path, headers=hb)).status_code == 403, path
    assert (await client.get("/api/v1/leads", headers=hb)).status_code == 200
    assert (await client.get("/api/v1/re-requests", headers=hb)).status_code == 200
    # B reusing A's record ids gets nothing
    a_contract = (await client.get("/api/v1/rentals/contracts", headers=ha)).json()[0]["id"]
    assert (await client.get(f"/api/v1/rentals/contracts/{a_contract}", headers=hb)).status_code == 403
    # changing B's config does not affect A
    await client.put(f"/api/v1/demos/{demo_b['id']}", headers=sa, json={"enabled_modules": ["dashboard", "leads"]})
    assert (await client.get("/api/v1/re-requests", headers=hb)).status_code == 403
    assert (await client.get("/api/v1/rentals/contracts", headers=ha)).status_code == 200
    # action configuration: allow export only in A
    await client.put(f"/api/v1/demos/{demo_a['id']}", headers=sa,
                     json={"allowed_actions": ["view", "create", "edit", "approve", "collect", "export", "print"]})
    assert (await client.get("/api/v1/re-reports/contracts/export", headers=ha)).status_code == 200
    # dashboard cards follow the demo configuration
    await client.put(f"/api/v1/demos/{demo_a['id']}", headers=sa, json={"dashboard_cards": ["overdue_rent"]})
    cards = (await client.get("/api/v1/re-dashboard/cards", headers=ha)).json()["cards"]
    assert [c["key"] for c in cards] == ["overdue_rent"]
    # demos can never hand out permission management
    r = await client.put(f"/api/v1/demos/{demo_a['id']}", headers=sa, json={"allowed_actions": ["view", "manage_permissions"]})
    assert r.status_code == 400


def test_reset_plan_covers_every_table():
    plan = reset_plan()
    unresolved = sorted(name for name, how in plan.items() if how == "unresolved")
    assert unresolved == [], f"Tables a demo reset cannot attribute to a tenant: {unresolved}"
