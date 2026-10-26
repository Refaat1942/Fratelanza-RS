# Customer Demo Setup

A demo is an isolated tenant (`companies.is_demo = true`) seeded with fictional but consistent data through the real services, plus a `demo_environments` configuration. It uses the normal screens and APIs.

## Create a demo (UI)

1. Log in as platform super admin (`https://rs-control.fratelanza.com/super-admin`, locally `http://localhost:5173/login` with `SUPER_ADMIN_EMAIL`).
2. Sidebar → **العروض التجريبية** (`/super-admin/demos`) → **نسخة تجريبية جديدة**.
3. Fill prospect name and demo company names (AR/EN), choose a **profile**:
   * إدارة الأملاك (Property Management) · المبيعات والوساطة (Sales & Brokerage) · الإيجارات والتحصيل (Rental & Collections) · نظام عقاري متكامل (Full ERP)
4. Adjust **modules** (pages that exist in the demo), **permitted actions** (export, delete, refund are off by default; permission management can never be enabled) and **dashboard cards**; set the expiry date/time; choose the first user's role.
5. **إنشاء وتعبئة البيانات** → the login and a one-time password are shown. Copy them.
6. Give the prospect `https://rs.fratelanza.com/login` with those credentials. A purple banner marks every page as a demo.

## Create a demo (API)

```bash
TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' \
  -d '{"username":"admin@fratelanza.com","password":"<SUPER_ADMIN_PASSWORD>"}' | jq -r .access_token)

# Customer A: units, rentals, collections, owner settlements, financial reports
curl -s -X POST localhost:8000/api/v1/demos -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{
  "prospect_name": "Customer A", "company_name_ar": "شركة أ التجريبية", "company_name_en": "Customer A Demo",
  "profile": "rental_collections",
  "enabled_modules": ["dashboard","projects","rentals","owners","reports"],
  "valid_days": 14,
  "users": [{"role":"company_admin"},{"role":"collection_officer"}]
}' | jq '.credentials'

# Customer B: properties, leads, sales requests, CRM only
curl -s -X POST localhost:8000/api/v1/demos -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{
  "prospect_name": "Customer B", "company_name_ar": "شركة ب التجريبية", "company_name_en": "Customer B Demo",
  "profile": "sales_brokerage",
  "enabled_modules": ["dashboard","projects","leads","customers","real_estate_requests"]
}' | jq '.credentials'
```

Customer B gets 403 on `/rentals`, `/owners`, `/re-reports/profit_loss`, etc. — by URL in the browser and by direct API call — and 404/403 on any id belonging to another tenant (covered by `tests/test_demo.py::test_18`).

## Configure / operate

| Task | UI (`/super-admin/demos` card) | API |
|---|---|---|
| Change modules, actions, cards, expiry, names | الإعدادات | `PUT /api/v1/demos/{id}` |
| Reset data to baseline | إعادة الضبط | `POST /api/v1/demos/{id}/reset` |
| Revoke immediately | إيقاف | `POST /api/v1/demos/{id}/revoke` |
| Re-enable | إعادة التفعيل | `POST /api/v1/demos/{id}/restore` |
| Add a user with a role | مستخدم إضافي | `POST /api/v1/demos/{id}/users {"role":"accountant"}` |
| Audit events | سجل الأحداث | `GET /api/v1/demos/{id}/audit` |
| Options (profiles, modules, actions, cards) | — | `GET /api/v1/demos/options` |

Inside a demo the demo's company admin can also fine-tune *roles* of demo users (`/roles`) if the `users` module is enabled for the demo.

## Safety guarantees (server-enforced)

* Separate tenant → no access to production rows, files or other demos; demo users are never super admins and get 403 on `/super-admin/*` and `/demos/*`.
* Expired, disabled or revoked demos are rejected at login and on every request (`demo_expired`, `demo_revoked`).
* Allowed actions are enforced in `AccessGuardMiddleware`; exports/deletes/refunds are off unless enabled per demo.
* Outbound email/WhatsApp/SMS → `outbound_messages` with status `suppressed_demo` (`OutboundService`), independent of `OUTBOUND_MODE`.
* AI requests from demo tenants use the local summariser (never OpenAI/Gemini).
* There is no payment-provider integration in the codebase; demo "payments" are internal records only.
* Reset deletes only the demo tenant's business rows (resolved via FKs, `reset_plan()` is tested to cover every table), keeps users, roles, config and the audit trail, and removes the demo's upload folder. Production tenants can't be reset.

## Built-in marketing company

The pre-existing `DEMO` company (`admin@demo.fratelanza.com`) remains a regular tenant. On startup it receives the new property-management modules and, once, fictional owners/leases/settlements so the new screens have data.
