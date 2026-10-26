"""Real-estate business logic (scenarios 19–25)."""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.core.database import AsyncSessionLocal
from app.models.finance import JournalEntry, JournalLine
from app.models.rentals import OutboundMessage, RentalContract, RentReceivable
from app.models.system import Notification
from app.services.rental_service import RentalService, build_periods
from app.services.scheduler_service import run_company_jobs


async def _lease(client, t, unit_id, *, start, end, rent, freq="monthly", owner_id=None, mobile="+201000000777", activate=True):
    r = await client.post("/api/v1/rentals/contracts", headers=t.admin, json={
        "unit_id": unit_id, "owner_id": owner_id, "tenant_name": "مستأجر اختبار", "tenant_mobile": mobile,
        "start_date": start.isoformat(), "end_date": end.isoformat(), "rent_amount": rent, "payment_frequency": freq,
        "activate": activate})
    assert r.status_code == 200, r.text
    return r.json()["id"]


async def _receivables(client, t, contract_id):
    return (await client.get(f"/api/v1/rentals/receivables?contract_id={contract_id}", headers=t.admin)).json()


async def test_19_renewal_preserves_history(client, make_tenant):
    t = await make_tenant()
    u = await t.build_unit("REN-19")
    cid = await _lease(client, t, u["unit_id"], start=date(2025, 1, 1), end=date(2025, 12, 31), rent=10000)
    before = (await client.get(f"/api/v1/rentals/contracts/{cid}", headers=t.admin)).json()
    r = await client.post(f"/api/v1/rentals/contracts/{cid}/renew", headers=t.admin,
                          json={"new_end_date": "2026-12-31", "new_rent_amount": 11500})
    assert r.status_code == 200, r.text
    new_id = r.json()["id"]
    old = (await client.get(f"/api/v1/rentals/contracts/{cid}", headers=t.admin)).json()
    new = (await client.get(f"/api/v1/rentals/contracts/{new_id}", headers=t.admin)).json()
    # old contract keeps its dates, rent and receivables
    assert old["stored_status"] == "renewed"
    assert (old["start_date"], old["end_date"], old["rent_amount"]) == (before["start_date"], before["end_date"], 10000.0)
    assert len(old["receivables"]) == 12 and all(r["amount_due"] == 10000.0 for r in old["receivables"])
    # new contract continues the day after, linked to the old one
    assert new["start_date"] == "2026-01-01" and new["rent_amount"] == 11500.0 and new["renewed_from_id"] == cid
    assert new["renewal_history"][0]["id"] == cid
    assert len(new["unit_tenant_history"]) == 2
    # replacing the tenant also keeps history
    r = await client.post(f"/api/v1/rentals/contracts/{new_id}/replace-tenant", headers=t.admin, json={
        "termination_date": "2026-06-30", "reason": "إخلاء ودي",
        "new_contract": {"unit_id": u["unit_id"], "tenant_name": "مستأجر جديد", "start_date": "2026-07-01",
                         "end_date": "2027-06-30", "rent_amount": 12000}})
    assert r.status_code == 200, r.text
    terminated = (await client.get(f"/api/v1/rentals/contracts/{new_id}", headers=t.admin)).json()
    assert terminated["stored_status"] == "terminated" and terminated["termination_reason"] == "إخلاء ودي"
    # receivables after termination are cancelled, not deleted
    statuses = {r["period_start"]: r["status"] for r in terminated["receivables"]}
    assert statuses["2026-07-01"] == "cancelled" and len(statuses) == 12
    # a second active lease on the same unit is refused
    r = await client.post("/api/v1/rentals/contracts", headers=t.admin, json={
        "unit_id": u["unit_id"], "tenant_name": "Overlap", "start_date": "2026-08-01", "end_date": "2027-01-31",
        "rent_amount": 5000, "activate": True})
    assert r.status_code == 409


async def test_20_receivables_generated_correctly_without_duplicates(client, make_tenant):
    t = await make_tenant()
    u = await t.build_unit("REC-20")
    # quarterly billing, 14 months → 4 full quarters + a 2-month pro-rated tail
    cid = await _lease(client, t, u["unit_id"], start=date(2026, 1, 1), end=date(2027, 2, 28), rent=9000, freq="quarterly")
    recs = await _receivables(client, t, cid)
    assert [r["period_start"] for r in recs] == ["2026-01-01", "2026-04-01", "2026-07-01", "2026-10-01", "2027-01-01"]
    assert [r["amount_due"] for r in recs[:4]] == [27000.0] * 4
    assert recs[4]["period_end"] == "2027-02-28"
    assert abs(recs[4]["amount_due"] - 27000 * 59 / 90) < 0.01
    # retried / concurrent job runs never duplicate
    async with AsyncSessionLocal() as db:
        contract = (await db.execute(select(RentalContract).where(RentalContract.id == cid))).scalar_one()
        assert await RentalService.generate_receivables(db, contract) == 0
        assert await RentalService.generate_receivables(db, contract) == 0
        await run_company_jobs(db, t.company_id)
        await run_company_jobs(db, t.company_id)
        await db.commit()
        count = (await db.execute(select(func.count()).select_from(RentReceivable).where(RentReceivable.rental_contract_id == cid))).scalar()
    assert count == 5
    # the schedule builder itself
    periods = build_periods(date(2026, 1, 31), date(2026, 4, 29), "monthly", Decimal("1000"))
    assert [p["period_start"].isoformat() for p in periods] == ["2026-01-31", "2026-02-28", "2026-03-31"]
    assert [p["amount_due"] for p in periods] == [Decimal("1000.00")] * 3


async def test_21_partial_payments_update_balances(client, make_tenant):
    t = await make_tenant()
    u = await t.build_unit("PAY-21")
    cid = await _lease(client, t, u["unit_id"], start=date(2026, 1, 1), end=date(2026, 12, 31), rent=8000)
    rec = (await _receivables(client, t, cid))[0]
    url = f"/api/v1/rentals/receivables/{rec['id']}"
    assert (await client.post(f"{url}/payments", headers=t.admin, json={"amount": 3000, "paid_on": "2026-01-02"})).status_code == 200
    after = next(r for r in await _receivables(client, t, cid) if r["id"] == rec["id"])
    assert (after["amount_paid"], after["outstanding"], after["status"] in ("partial", "overdue")) == (3000.0, 5000.0, True)
    # over-payment refused
    assert (await client.post(f"{url}/payments", headers=t.admin, json={"amount": 5000.01, "paid_on": "2026-01-03"})).status_code == 400
    # authorised waiver reduces the balance, then the rest is paid
    assert (await client.post(f"{url}/adjustments", headers=t.admin, json={"amount": 1000, "reason": "خصم تأخير صيانة"})).status_code == 200
    assert (await client.post(f"{url}/payments", headers=t.admin, json={"amount": 4000, "paid_on": "2026-01-05"})).status_code == 200
    final = next(r for r in await _receivables(client, t, cid) if r["id"] == rec["id"])
    assert (final["outstanding"], final["status"]) == (0.0, "paid")
    # refund re-opens the balance
    assert (await client.post(f"{url}/refunds", headers=t.admin, json={"amount": 500, "paid_on": "2026-01-06"})).status_code == 200
    refunded = next(r for r in await _receivables(client, t, cid) if r["id"] == rec["id"])
    assert refunded["outstanding"] == 500.0 and refunded["amount_paid"] == 6500.0
    history = (await client.get(f"{url}/payments", headers=t.admin)).json()
    assert [p["kind"] for p in history["payments"]] == ["payment", "payment", "refund"]
    assert history["adjustments"][0]["amount"] == 1000.0


async def test_22_owner_settlement_expenses_and_commission(client, make_tenant):
    t = await make_tenant()
    owner = await t.owner("مالك التسوية", rate=10)
    u = await t.build_unit("SET-22")
    await client.put(f"/api/v1/rentals/units/{u['unit_id']}", headers=t.admin, json={"owner_id": owner})
    cid = await _lease(client, t, u["unit_id"], start=date(2026, 1, 1), end=date(2026, 12, 31), rent=10000)
    recs = await _receivables(client, t, cid)
    for r in recs[:2]:
        await client.post(f"/api/v1/rentals/receivables/{r['id']}/payments", headers=t.admin,
                          json={"amount": 10000, "paid_on": r["due_date"]})
    async def expense(amount, charged_to, approve=True):
        e = (await client.post("/api/v1/property-expenses", headers=t.admin, json={
            "unit_id": u["unit_id"], "expense_date": "2026-01-15", "category": "plumbing", "amount": amount,
            "charged_to": charged_to})).json()["id"]
        if approve:
            assert (await client.post(f"/api/v1/property-expenses/{e}/approve", headers=t.admin)).status_code == 200
        return e
    await expense(1500, "owner")
    await expense(500, "company")          # company-borne → not deducted from the owner
    await expense(700, "owner", approve=False)  # not approved → not deducted
    body = {"owner_id": owner, "period_start": "2026-01-01", "period_end": "2026-02-28"}
    preview = (await client.post("/api/v1/owners/settlements/preview", headers=t.admin, json=body)).json()
    assert (preview["gross_collected"], preview["commission_amount"], preview["expenses_total"], preview["net_payable"]) == (
        20000.0, 2000.0, 1500.0, 16500.0)
    s = (await client.post("/api/v1/owners/settlements", headers=t.admin, json=body)).json()
    assert s["net_payable"] == 16500.0 and s["status"] == "draft"
    assert (await client.post("/api/v1/owners/settlements", headers=t.admin, json=body)).status_code == 409
    # the same collections cannot be settled twice in a later period
    later = (await client.post("/api/v1/owners/settlements/preview", headers=t.admin, json={**body, "period_start": "2026-03-01", "period_end": "2026-03-31"})).json()
    assert later["gross_collected"] == 0.0 and later["expenses_total"] == 0.0
    sid = s["id"]
    assert (await client.post(f"/api/v1/owners/settlements/{sid}/payments", headers=t.admin,
                              json={"amount": 100, "paid_on": "2026-03-05"})).status_code == 400  # must approve first
    await client.post(f"/api/v1/owners/settlements/{sid}/approve", headers=t.admin)
    p1 = await client.post(f"/api/v1/owners/settlements/{sid}/payments", headers=t.admin, json={"amount": 6500, "paid_on": "2026-03-05"})
    assert p1.json()["status"] == "partial" and p1.json()["remaining"] == 10000.0
    assert (await client.post(f"/api/v1/owners/settlements/{sid}/payments", headers=t.admin,
                              json={"amount": 10000.01, "paid_on": "2026-03-06"})).status_code == 400
    p2 = await client.post(f"/api/v1/owners/settlements/{sid}/payments", headers=t.admin, json={"amount": 10000, "paid_on": "2026-03-06"})
    assert p2.json()["status"] == "paid"
    # ledger: owner funds are a liability; only the commission became company revenue
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(
            select(JournalEntry.source_type, func.sum(JournalLine.credit) - func.sum(JournalLine.debit))
            .join(JournalLine, JournalLine.journal_entry_id == JournalEntry.id)
            .where(JournalEntry.company_id == t.company_id).group_by(JournalEntry.source_type))).all()
        from app.models.finance import ChartOfAccount
        balances = dict((await db.execute(
            select(ChartOfAccount.code, func.sum(JournalLine.credit) - func.sum(JournalLine.debit))
            .join(JournalLine, JournalLine.account_id == ChartOfAccount.id)
            .where(ChartOfAccount.company_id == t.company_id).group_by(ChartOfAccount.code))).all())
    assert rows  # entries exist
    assert balances["4200"] == Decimal("2000.00")       # commission income
    assert "4100" not in balances                        # owner rent is never company rental income
    assert balances["2100"] == Decimal("0.00")           # owner liability fully discharged: 20000 − 2000 − 1500 − 16500


async def test_23_same_expense_not_posted_twice(client, make_tenant):
    t = await make_tenant()
    u = await t.build_unit("EXP-23")
    mr = (await client.post("/api/v1/property/maintenance", headers=t.admin, json={"unit_id": u["unit_id"], "title": "Leak"})).json()["id"]
    first = await client.post(f"/api/v1/property-expenses/from-maintenance/{mr}", headers=t.admin,
                              json={"amount": 900, "expense_date": "2026-02-01", "charged_to": "company"})
    assert first.status_code == 200
    dup = await client.post(f"/api/v1/property-expenses/from-maintenance/{mr}", headers=t.admin,
                            json={"amount": 900, "expense_date": "2026-02-01", "charged_to": "company"})
    assert dup.status_code == 409
    eid = first.json()["id"]
    assert (await client.post(f"/api/v1/property-expenses/{eid}/approve", headers=t.admin)).status_code == 200
    assert (await client.post(f"/api/v1/property-expenses/{eid}/approve", headers=t.admin)).status_code == 400
    assert (await client.post(f"/api/v1/property-expenses/{eid}/mark-paid", headers=t.admin, json={"paid_on": "2026-02-02"})).status_code == 200
    assert (await client.post(f"/api/v1/property-expenses/{eid}/mark-paid", headers=t.admin, json={"paid_on": "2026-02-03"})).status_code == 400
    async with AsyncSessionLocal() as db:
        counts = dict((await db.execute(
            select(JournalEntry.source_type, func.count()).where(JournalEntry.company_id == t.company_id, JournalEntry.source_id == eid)
            .group_by(JournalEntry.source_type))).all())
        # direct service retry is idempotent as well
        from app.services.accounting_service import AccountingService

        again = await AccountingService.post(db, t.company_id, source_type="property_expense", source_id=eid,
                                             entry_date=date(2026, 2, 1), description="retry",
                                             lines=[("5100", Decimal("900"), Decimal("0")), ("2300", Decimal("0"), Decimal("900"))])
        await db.commit()
        total = (await db.execute(select(func.count()).select_from(JournalEntry).where(
            JournalEntry.company_id == t.company_id, JournalEntry.source_type == "property_expense"))).scalar()
    assert counts == {"property_expense": 1, "property_expense_payment": 1}
    assert again.description != "retry" and total == 1
    # approved expenses cannot be deleted (would orphan the posting)
    assert (await client.delete(f"/api/v1/property-expenses/{eid}", headers=t.admin)).status_code == 400


async def test_24_dashboard_totals_reconcile(client, make_tenant):
    t = await make_tenant()
    today = date.today()
    units = [await t.build_unit(f"DASH-24-{i}") for i in range(3)]
    start = date(today.year - 1, today.month, 1)
    c1 = await _lease(client, t, units[0]["unit_id"], start=start, end=start + timedelta(days=700), rent=5000)
    await _lease(client, t, units[1]["unit_id"], start=start, end=today + timedelta(days=20), rent=7000)  # expiring
    await _lease(client, t, units[2]["unit_id"], start=today, end=today + timedelta(days=365), rent=3000, activate=False)  # draft
    recs = await _receivables(client, t, c1)
    await client.post(f"/api/v1/rentals/receivables/{recs[0]['id']}/payments", headers=t.admin, json={"amount": 5000, "paid_on": recs[0]["due_date"]})
    await client.post(f"/api/v1/rentals/receivables/{recs[1]['id']}/payments", headers=t.admin, json={"amount": 2000, "paid_on": recs[1]["due_date"]})
    cards = {c["key"]: c["value"] for c in (await client.get("/api/v1/re-dashboard/cards", headers=t.admin)).json()["cards"]}
    all_recs = (await client.get("/api/v1/rentals/receivables", headers=t.admin)).json()
    overdue_sum = round(sum(r["outstanding"] for r in all_recs if r["status"] == "overdue"), 2)
    assert round(cards["overdue_rent"], 2) == overdue_sum > 0
    upcoming = round(sum(r["outstanding"] for r in all_recs if r["status"] in ("pending", "partial")
                         and today <= date.fromisoformat(r["due_date"]) <= today + timedelta(days=30)), 2)
    assert round(cards["upcoming_collections"], 2) == upcoming
    assert cards["active_contracts"] == 2 and cards["expiring_contracts"] == 1
    assert (cards["total_units"], cards["occupied_units"], cards["available_units"]) == (3, 2, 1)
    summary = (await client.get("/api/v1/rentals/summary", headers=t.admin)).json()
    assert round(summary["overdue"], 2) == overdue_sum
    report = (await client.get("/api/v1/re-reports/receivables", headers=t.admin)).json()
    assert round(sum(r["outstanding"] for r in report["rows"] if r["is_overdue"]), 2) == overdue_sum


async def test_25_notifications_follow_schedule(client, make_tenant):
    t = await make_tenant()
    u = await t.build_unit("NOTE-25")
    owner = await t.owner("مالك الإشعار", freq="monthly")
    run_day = date(2026, 11, 28)  # owner (monthly, settlement_day 5): next settlement due 2026-12-05 → 7 days
    # a lease whose next rent is due exactly 3 days after run_day, and that expires 30 days after it
    cid = await _lease(client, t, u["unit_id"], start=date(2026, 1, 1), end=date(2026, 12, 28), rent=6000,
                       owner_id=owner, mobile="+201066600000")
    async with AsyncSessionLocal() as db:
        await db.execute(
            RentReceivable.__table__.update()
            .where(RentReceivable.rental_contract_id == cid, RentReceivable.period_start == date(2026, 12, 1))
            .values(due_date=run_day + timedelta(days=3))
        )
        await db.execute(
            RentReceivable.__table__.update()
            .where(RentReceivable.rental_contract_id == cid, RentReceivable.period_start == date(2026, 11, 1))
            .values(due_date=run_day - timedelta(days=1))
        )
        await db.commit()
        stats1 = await run_company_jobs(db, t.company_id, run_day)
        stats2 = await run_company_jobs(db, t.company_id, run_day)  # retry → no duplicates
        await db.commit()
        keys = [k for (k,) in (await db.execute(select(Notification.dedupe_key).where(Notification.company_id == t.company_id))).all()]
        outbound = (await db.execute(select(OutboundMessage).where(OutboundMessage.company_id == t.company_id))).scalars().all()
    assert stats1["notifications"] > 0 and stats2["notifications"] == 0
    assert any(k.startswith("rent_due:") for k in keys)
    assert any(k.startswith("rent_overdue:") and k.endswith(":1") for k in keys)
    assert any(k == f"contract_expiring:{cid}" for k in keys)
    assert any(k == f"settlement_due:{owner}:2026-11-30" for k in keys)
    assert len(keys) == len(set(keys))  # one admin → each reminder exactly once
    # renter reminder went through the gateway and was only logged (OUTBOUND_MODE=log)
    assert outbound and all(m.status == "logged" and m.recipient == "+201066600000" for m in outbound)
    # no reminders on other days
    async with AsyncSessionLocal() as db:
        quiet = await run_company_jobs(db, t.company_id, run_day + timedelta(days=1))
        await db.rollback()
    assert quiet["notifications"] == 0
