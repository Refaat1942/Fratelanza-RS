"""Permissions (scenarios 8–12) plus privilege-escalation and lock-out guards."""


async def test_8_user_without_permission_cannot_call_restricted_api(client, make_tenant):
    t = await make_tenant()
    agent = await t.add_user("sales_agent")
    # sales agent template has no rentals / owners / finance / hr access
    for path in ("/api/v1/rentals/contracts", "/api/v1/owners", "/api/v1/finance/accounts", "/api/v1/hr/employees",
                 "/api/v1/admin-expenses", "/api/v1/roles"):
        r = await client.get(path, headers=agent["headers"])
        assert r.status_code == 403, (path, r.text)
        assert r.json()["detail"] == "permission_denied"
    # but can use CRM
    assert (await client.get("/api/v1/customers", headers=agent["headers"])).status_code == 200


async def test_9_read_only_user_cannot_create_edit_delete(client, make_tenant):
    t = await make_tenant()
    role = (await client.post("/api/v1/roles/from-template", headers=t.admin, json={"template": "auditor"})).json()
    auditor = await t.add_user("sales_agent")
    r = await client.put(f"/api/v1/roles/assignments/{auditor['id']}", headers=t.admin, json={"role_ids": [role["id"]]})
    assert r.status_code == 200, r.text
    h = auditor["headers"]
    assert (await client.get("/api/v1/customers", headers=h)).status_code == 200
    assert (await client.get("/api/v1/owners", headers=h)).status_code == 200
    assert (await client.post("/api/v1/customers", headers=h, json={
        "full_name_ar": "ممنوع", "full_name_en": "Nope", "mobile": "+201299999999"})).status_code == 403
    cust = (await client.post("/api/v1/customers", headers=t.admin, json={
        "full_name_ar": "عميل", "full_name_en": "Cust", "mobile": "+201299999998"})).json()["id"]
    assert (await client.put(f"/api/v1/customers/{cust}", headers=h, json={"city": "x"})).status_code == 403
    assert (await client.delete(f"/api/v1/customers/{cust}", headers=h)).status_code == 403
    assert (await client.post("/api/v1/owners", headers=h, json={"full_name": "Owner"})).status_code == 403


async def test_10_payroll_user_cannot_see_owner_data(client, make_tenant):
    t = await make_tenant()
    owner_id = await t.owner("Owner Secret")
    hr = await t.add_user("sales_agent")
    await client.put(f"/api/v1/users/{hr['id']}", headers=t.admin, json={"system_role": "hr_manager"})
    hr_h = hr["headers"]
    await client.post("/api/v1/hr/employees", headers=t.admin, json={
        "employee_code": "E1", "full_name_ar": "موظف", "full_name_en": "Emp", "salary": 10000})
    employees = (await client.get("/api/v1/hr/employees", headers=hr_h)).json()
    assert employees[0]["salary"] == 10000.0  # HR sees salaries
    assert (await client.get("/api/v1/owners", headers=hr_h)).status_code == 403
    assert (await client.get(f"/api/v1/owners/{owner_id}", headers=hr_h)).status_code == 403
    # Grant owners:view separately → still no bank details or national ID (field groups not granted)
    role = (await client.post("/api/v1/roles", headers=t.admin, json={
        "name_ar": "رواتب + ملاك", "name_en": "Payroll plus owners", "data_scope": "all", "field_access": ["salaries"],
        "permissions": {"dashboard": ["view"], "hr": ["view", "create", "edit", "collect"], "owners": ["view"]}})).json()
    await client.put(f"/api/v1/roles/assignments/{hr['id']}", headers=t.admin, json={"role_ids": [role["id"]]})
    owner = (await client.get(f"/api/v1/owners/{owner_id}", headers=hr_h)).json()
    assert owner["bank_account"].startswith("••••") and owner["national_id"].startswith("••••")
    assert owner["commission_rate"] is None
    # a sales agent never sees salaries
    agent = await t.add_user("sales_agent")
    assert (await client.get("/api/v1/hr/employees", headers=agent["headers"])).status_code == 403


async def test_11_disabled_module_inaccessible_through_api(client, make_tenant):
    t = await make_tenant(["dashboard", "customers", "leads", "projects", "users", "real_estate_requests"])
    for path in ("/api/v1/rentals/contracts", "/api/v1/owners", "/api/v1/hr/employees", "/api/v1/finance/accounts",
                 "/api/v1/collections/installments", "/api/v1/property-expenses"):
        r = await client.get(path, headers=t.admin)  # even the company admin
        assert r.status_code == 403, (path, r.text)
        assert "not enabled" in r.json()["detail"]
    assert (await client.get("/api/v1/re-requests", headers=t.admin)).status_code == 200
    # report endpoints cannot be used as a side door into disabled modules
    assert (await client.get("/api/v1/reports/hr_employees", headers=t.admin)).status_code == 403
    assert (await client.get("/api/v1/re-reports/contracts", headers=t.admin)).status_code == 403


async def test_12_permission_changes_apply_without_deploy(client, make_tenant, sa):
    t = await make_tenant()
    user = await t.add_user("sales_agent")
    h = user["headers"]
    assert (await client.get("/api/v1/owners", headers=h)).status_code == 403
    role = (await client.post("/api/v1/roles", headers=t.admin, json={
        "name_ar": "عرض الملاك", "name_en": "Owners viewer", "permissions": {"owners": ["view"], "dashboard": ["view"]}})).json()
    await client.put(f"/api/v1/roles/assignments/{user['id']}", headers=t.admin, json={"role_ids": [role["id"]]})
    assert (await client.get("/api/v1/owners", headers=h)).status_code == 200  # same token, next request
    # revoke by editing the role
    await client.put(f"/api/v1/roles/{role['id']}", headers=t.admin, json={
        "name_ar": "عرض الملاك", "name_en": "Owners viewer", "permissions": {"dashboard": ["view"]}})
    assert (await client.get("/api/v1/owners", headers=h)).status_code == 403
    # super admin disables a module for the tenant → immediately enforced
    r = await client.put(f"/api/v1/modules/company/{t.company_id}", headers=sa,
                         json={"enabled_modules": ["dashboard", "users", "customers"]})
    assert r.status_code == 200, r.text
    assert (await client.get("/api/v1/leads", headers=t.admin)).status_code == 403


async def test_no_privilege_escalation_via_user_or_role_api(client, make_tenant):
    t = await make_tenant()
    manager = await t.add_user("sales_agent")
    # admin gives the manager user-management rights but not permission management
    role = (await client.post("/api/v1/roles", headers=t.admin, json={
        "name_ar": "إدارة مستخدمين", "name_en": "User clerk",
        "permissions": {"users": ["view", "create", "edit"], "dashboard": ["view"], "customers": ["view"]}})).json()
    await client.put(f"/api/v1/roles/assignments/{manager['id']}", headers=t.admin, json={"role_ids": [role["id"]]})
    h = manager["headers"]
    r = await client.post("/api/v1/users", headers=h, json={
        "username": f"evil_{t.code.lower()}", "email": f"evil_{t.code.lower()}@x.com", "password": "Passw0rd!",
        "full_name_ar": "شرير", "full_name_en": "Evil", "system_role": "company_admin"})
    assert r.status_code == 403
    assert (await client.put(f"/api/v1/users/{manager['id']}", headers=h, json={"system_role": "company_admin"})).status_code == 403
    assert (await client.post("/api/v1/roles", headers=h, json={
        "name_ar": "كل شيء", "name_en": "All", "permissions": {"finance": ["view"]}})).status_code == 403
    # tenant user cannot change its own company status / limits through branding
    r = await client.put("/api/v1/companies/me/branding", headers=t.admin, json={"status": "active", "storage_limit_mb": 999999})
    assert r.status_code == 200
    company = (await client.get("/api/v1/companies/me", headers=t.admin)).json()
    assert company["storage_limit_mb"] != 999999
    # tenant users cannot trigger platform-wide seeding
    assert (await client.post("/api/v1/dashboard/reseed-demo", headers=t.admin)).status_code == 403
    # an admin cannot grant what they do not hold (e.g. modules disabled for the tenant are filtered)
    assert (await client.post("/api/v1/roles", headers=t.admin, json={
        "name_ar": "سيء", "name_en": "bad role", "permissions": {"nonexistent": ["view"]}})).status_code == 400


async def test_lockout_of_last_admin_is_prevented(client, make_tenant, sa):
    t = await make_tenant()
    me = (await client.get("/api/v1/auth/me", headers=t.admin)).json()
    # cannot demote / suspend / delete the only admin
    assert (await client.put(f"/api/v1/users/{me['id']}", headers=t.admin, json={"system_role": "sales_agent"})).status_code == 400
    assert (await client.post(f"/api/v1/users/{me['id']}/suspend", headers=t.admin)).status_code == 400
    # cannot strip the only admin via a custom role without manage_permissions
    weak = (await client.post("/api/v1/roles", headers=t.admin, json={
        "name_ar": "ضعيف", "name_en": "Weak", "permissions": {"dashboard": ["view"]}})).json()
    assert (await client.put(f"/api/v1/roles/assignments/{me['id']}", headers=t.admin,
                             json={"role_ids": [weak["id"]]})).status_code == 400
    # still an admin afterwards
    assert (await client.get("/api/v1/roles", headers=t.admin)).status_code == 200
    # the platform super admin cannot be suspended when it is the last one
    sa_me = (await client.get("/api/v1/auth/me", headers=sa)).json()
    assert (await client.post(f"/api/v1/users/{sa_me['id']}/suspend", headers=sa)).status_code == 400


async def test_data_scope_own_records_only(client, make_tenant):
    t = await make_tenant()
    a1, a2 = await t.add_user("sales_agent"), await t.add_user("sales_agent")
    c1 = (await client.post("/api/v1/customers", headers=a1["headers"], json={
        "full_name_ar": "عميل وكيل 1", "full_name_en": "Agent1 cust", "mobile": "+201300000001", "national_id": "29901010101010"})).json()
    ids_a2 = {c["id"] for c in (await client.get("/api/v1/customers", headers=a2["headers"])).json()["items"]}
    assert c1["id"] not in ids_a2
    assert (await client.get(f"/api/v1/customers/{c1['id']}", headers=a2["headers"])).status_code == 404
    # the owner agent sees it, but the national ID is masked for agents (no identity field group)
    mine = (await client.get(f"/api/v1/customers/{c1['id']}", headers=a1["headers"])).json()
    assert mine["national_id"].startswith("••••")
    assert (await client.get(f"/api/v1/customers/{c1['id']}", headers=t.admin)).json()["national_id"] == "29901010101010"
    # a masked value round-tripped by the UI never overwrites the real one
    await client.put(f"/api/v1/customers/{c1['id']}", headers=a1["headers"], json={"national_id": mine["national_id"], "city": "Giza"})
    assert (await client.get(f"/api/v1/customers/{c1['id']}", headers=t.admin)).json()["national_id"] == "29901010101010"


async def test_effective_permissions_endpoint(client, make_tenant):
    t = await make_tenant()
    agent = await t.add_user("sales_agent")
    perms = (await client.get("/api/v1/auth/me/permissions", headers=agent["headers"])).json()
    assert perms["data_scope"] == "own"
    assert "rentals" not in perms["permissions"]
    assert "create" in perms["permissions"]["customers"]
    review = (await client.get(f"/api/v1/roles/assignments/{agent['id']}", headers=t.admin)).json()
    assert review["effective"]["permissions"] == perms["permissions"]
