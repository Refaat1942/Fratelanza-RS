"""Multi-tenant isolation (scenarios 1–7)."""

from datetime import date, timedelta

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.rentals import RentReceivable
from app.services.scheduler_service import run_company_jobs


async def _lease(client, tenant, unit_id, owner_id=None, start=None, months=12, rent=10000, activate=True):
    start = start or date.today().replace(day=1)
    end = date(start.year + months // 12, start.month, 1) - timedelta(days=1)
    r = await client.post("/api/v1/rentals/contracts", headers=tenant.admin, json={
        "unit_id": unit_id, "owner_id": owner_id, "tenant_name": "مستأجر", "tenant_mobile": "+201000000999",
        "tenant_id_number": "29912312345678", "start_date": start.isoformat(), "end_date": end.isoformat(),
        "rent_amount": rent, "activate": activate})
    assert r.status_code == 200, r.text
    return r.json()["id"]


async def test_1_tenant_cannot_list_other_tenants_properties(client, make_tenant):
    a, b = await make_tenant(), await make_tenant()
    await a.build_unit("A-ISO-1")
    await b.build_unit("B-ISO-1")
    board = (await client.get("/api/v1/projects/units/board", headers=a.admin)).json()
    codes = {u["unit_code"] for units in board.values() for u in units}
    assert "A-ISO-1" in codes and "B-ISO-1" not in codes
    projects = (await client.get("/api/v1/projects", headers=a.admin)).json()["items"]
    assert all(p["company_id"] == a.company_id for p in projects)
    rental_units = (await client.get("/api/v1/rentals/units", headers=a.admin)).json()
    assert {u["unit_code"] for u in rental_units} == {"A-ISO-1"}


async def test_2_tenant_cannot_retrieve_other_tenant_unit_by_id(client, make_tenant):
    a, b = await make_tenant(), await make_tenant()
    bu = await b.build_unit("B-ISO-2")
    # direct unit endpoints
    assert (await client.put(f"/api/v1/rentals/units/{bu['unit_id']}", headers=a.admin, json={"notes": "x"})).status_code == 404
    assert (await client.delete(f"/api/v1/projects/units/{bu['unit_id']}", headers=a.admin)).status_code == 404
    # nested route through B's project
    assert (await client.get(f"/api/v1/projects/{bu['project_id']}/units", headers=a.admin)).status_code == 404
    # cannot attach a unit to B's floor
    r = await client.post("/api/v1/projects/units", headers=a.admin, json={
        "floor_id": bu["floor_id"], "unit_code": "HIJACK", "unit_number": "9", "unit_type": "apartment", "area_sqm": 1, "price": 1})
    assert r.status_code == 404


async def test_3_tenant_cannot_modify_or_delete_other_tenant_contract(client, make_tenant):
    a, b = await make_tenant(), await make_tenant()
    bu = await b.build_unit("B-ISO-3")
    cid = await _lease(client, b, bu["unit_id"], activate=False)
    assert (await client.get(f"/api/v1/rentals/contracts/{cid}", headers=a.admin)).status_code == 404
    assert (await client.put(f"/api/v1/rentals/contracts/{cid}", headers=a.admin, json={"notes": "pwn"})).status_code == 404
    assert (await client.post(f"/api/v1/rentals/contracts/{cid}/terminate", headers=a.admin,
                              json={"termination_date": date.today().isoformat(), "reason": "nope"})).status_code == 404
    assert (await client.delete(f"/api/v1/rentals/contracts/{cid}", headers=a.admin)).status_code == 404
    # still intact for B
    assert (await client.get(f"/api/v1/rentals/contracts/{cid}", headers=b.admin)).json()["stored_status"] == "draft"


async def test_4_tenant_cannot_access_other_customers_or_financial_reports(client, make_tenant):
    a, b = await make_tenant(), await make_tenant()
    r = await client.post("/api/v1/customers", headers=b.admin, json={
        "full_name_ar": "عميل ب", "full_name_en": "Customer B", "mobile": "+201234567890"})
    cust_b = r.json()["id"]
    assert (await client.get(f"/api/v1/customers/{cust_b}", headers=a.admin)).status_code in (403, 404)
    assert (await client.get(f"/api/v1/customers/{cust_b}/timeline", headers=a.admin)).status_code == 404
    listed = (await client.get("/api/v1/customers", headers=a.admin)).json()["items"]
    assert cust_b not in {c["id"] for c in listed}
    # B has collections; A's financial report must not include them
    bu = await b.build_unit("B-ISO-4")
    cid = await _lease(client, b, bu["unit_id"], rent=7777)
    recs = (await client.get(f"/api/v1/rentals/receivables?contract_id={cid}", headers=b.admin)).json()
    await client.post(f"/api/v1/rentals/receivables/{recs[0]['id']}/payments", headers=b.admin,
                      json={"amount": 7777, "paid_on": date.today().isoformat()})
    report_a = (await client.get("/api/v1/re-reports/collections", headers=a.admin)).json()
    assert report_a["rows"] == []
    report_b = (await client.get("/api/v1/re-reports/collections", headers=b.admin)).json()
    assert report_b["totals"]["collected"] == 7777.0
    # A cannot read B's settlement or receivable payments by id
    assert (await client.get(f"/api/v1/rentals/receivables/{recs[0]['id']}/payments", headers=a.admin)).status_code == 404


async def test_5_cross_tenant_relations_rejected(client, make_tenant):
    a, b = await make_tenant(), await make_tenant()
    au = await a.build_unit("A-ISO-5")
    owner_b = await b.owner("Owner B")
    cust_b = (await client.post("/api/v1/customers", headers=b.admin, json={
        "full_name_ar": "مستأجر ب", "full_name_en": "Renter B", "mobile": "+201234567891"})).json()["id"]
    # A's unit + B's owner
    r = await client.post("/api/v1/rentals/contracts", headers=a.admin, json={
        "unit_id": au["unit_id"], "owner_id": owner_b, "tenant_name": "x", "start_date": "2026-01-01",
        "end_date": "2026-12-31", "rent_amount": 1000})
    assert r.status_code == 404
    # A's unit + B's customer as renter
    r = await client.post("/api/v1/rentals/contracts", headers=a.admin, json={
        "unit_id": au["unit_id"], "tenant_customer_id": cust_b, "start_date": "2026-01-01", "end_date": "2026-12-31",
        "rent_amount": 1000})
    assert r.status_code == 404
    # B's customer in A's reservation, lead and maintenance request
    assert (await client.post("/api/v1/reservations", headers=a.admin, json={
        "customer_id": cust_b, "unit_id": au["unit_id"], "deposit_amount": 1, "reservation_date": "2026-01-01",
        "expiry_date": "2026-02-01"})).status_code == 404
    assert (await client.post("/api/v1/leads", headers=a.admin, json={
        "full_name": "Lead X", "mobile": "+201000000001", "customer_id": cust_b})).status_code == 404
    assert (await client.post("/api/v1/property/maintenance", headers=a.admin, json={
        "unit_id": au["unit_id"], "customer_id": cust_b, "title": "Leak"})).status_code == 404
    # a role of tenant B cannot be assigned inside tenant A
    role_b = (await client.post("/api/v1/roles", headers=b.admin, json={
        "name_ar": "دور", "name_en": "Role B", "permissions": {"customers": ["view"]}})).json()["id"]
    user_a = await a.add_user("sales_agent")
    assert (await client.put(f"/api/v1/roles/assignments/{user_a['id']}", headers=a.admin,
                             json={"role_ids": [role_b]})).status_code == 404


async def test_6_exports_and_background_jobs_are_tenant_scoped(client, make_tenant):
    a, b = await make_tenant(), await make_tenant()
    await client.post("/api/v1/customers", headers=a.admin, json={"full_name_ar": "تصدير أ", "full_name_en": "ExportA", "mobile": "+201111111111"})
    await client.post("/api/v1/customers", headers=b.admin, json={"full_name_ar": "تصدير ب", "full_name_en": "ExportB", "mobile": "+201111111112"})
    csv_a = (await client.get("/api/v1/exports/customers?format=csv", headers=a.admin)).text
    assert "ExportA" in csv_a and "ExportB" not in csv_a
    # background job for A must not touch B's contracts
    au, bu = await a.build_unit("A-ISO-6"), await b.build_unit("B-ISO-6")
    ca = await _lease(client, a, au["unit_id"])
    cb = await _lease(client, b, bu["unit_id"])
    async with AsyncSessionLocal() as db:
        await db.execute(RentReceivable.__table__.delete().where(RentReceivable.rental_contract_id.in_([ca, cb])))
        await db.commit()
        await run_company_jobs(db, a.company_id)
        await db.commit()
        count_a = len((await db.execute(select(RentReceivable).where(RentReceivable.rental_contract_id == ca))).scalars().all())
        count_b = len((await db.execute(select(RentReceivable).where(RentReceivable.rental_contract_id == cb))).scalars().all())
    assert count_a == 12
    assert count_b == 0
    # the per-tenant job endpoint only affects the caller's tenant
    stats = (await client.post("/api/v1/rentals/jobs/run", headers=a.admin)).json()
    assert stats["receivables_created"] == 0


async def test_7_cache_and_file_access_do_not_leak(client, make_tenant):
    a, b = await make_tenant(), await make_tenant()
    up = await client.post("/api/v1/files", headers=b.admin, data={"category": "expenses"},
                           files={"file": ("receipt.pdf", b"%PDF-1.4 tenant b secret", "application/pdf")})
    assert up.status_code == 200, up.text
    url = up.json()["url"]
    assert url.startswith(f"/uploads/tenants/{b.company_id}/")
    assert (await client.get(url)).status_code == 401  # anonymous
    assert (await client.get(url, headers=a.admin)).status_code == 404  # other tenant
    assert (await client.get(url, headers=b.admin)).content.startswith(b"%PDF")
    # path traversal is rejected
    assert (await client.get("/uploads/../app/main.py", headers=b.admin)).status_code == 404
    # tenant A cannot attach B's file to its own expense
    au = await a.build_unit("A-ISO-7")
    r = await client.post("/api/v1/property-expenses", headers=a.admin, json={
        "unit_id": au["unit_id"], "expense_date": date.today().isoformat(), "category": "other", "amount": 10,
        "charged_to": "company", "attachment_url": url})
    assert r.status_code == 400
    # dashboard cards (cached permission context) differ per tenant and never mix data
    bu = await b.build_unit("B-ISO-7")
    await _lease(client, b, bu["unit_id"])
    cards_a = {c["key"]: c["value"] for c in (await client.get("/api/v1/re-dashboard/cards", headers=a.admin)).json()["cards"]}
    cards_b = {c["key"]: c["value"] for c in (await client.get("/api/v1/re-dashboard/cards", headers=b.admin)).json()["cards"]}
    assert cards_a["active_contracts"] == 0
    assert cards_b["active_contracts"] == 1
