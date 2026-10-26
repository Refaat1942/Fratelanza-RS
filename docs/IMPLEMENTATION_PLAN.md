# Implementation Plan & Status

Order followed (from the brief) and the state of each phase on branch `claude/trusting-cori-5kyh9o`.

| # | Phase | Status | Main files |
|---|---|---|---|
| 1 | Inspection & baseline | Done — backend boots/seeds on Postgres 16; `tsc` + `vite build` pass; no tests or ESLint config existed | REAL_ESTATE_GAP_ANALYSIS.md |
| 2 | Tenant model, migrations, isolation | Done | `models/tenant.py`, `alembic/`, `core/tenant.py`, 17 IDOR fixes |
| 3 | Auth & permission enforcement | Done | `core/permissions.py`, `services/access_service.py`, `middleware/module_guard.py`, `endpoints/roles.py`, `endpoints/users.py` |
| 4 | Tenant-aware RE & accounting | Done | `models/rentals.py`, `services/accounting_service.py` |
| 5 | Rental contracts & schedules | Done | `services/rental_service.py`, `endpoints/rentals.py` |
| 6 | Owner settlements & expenses | Done | `services/settlement_service.py`, `services/expense_service.py`, `endpoints/owners.py`, `property_expenses.py`, `admin_expenses.py`, `services/payroll_service.py` |
| 7 | Customer demos | Done | `services/demo_service.py`, `endpoints/demos.py`, `services/outbound_service.py` |
| 8 | Dashboard & UI permissions | Done | `services/re_dashboard_service.py`, frontend `stores/permissionsStore.ts`, `ModuleRoute`, `Sidebar` |
| 9 | Notifications, reports, exports | Done | `services/scheduler_service.py`, `services/re_reports_service.py`, `endpoints/re_reports.py` |
| 10 | Security hardening & tests | Done — 32 integration tests | `backend/tests/` |
| 11 | Docs & deployment | Done | `docs/*.md`, `.env*.example` |

Remaining work is listed at the end of REAL_ESTATE_GAP_ANALYSIS.md.

## Accounting rules

Cash basis for rent; accrual for expenses and payroll. Chart codes are created per tenant on first use (`SYSTEM_ACCOUNTS`).

| Event | Debit | Credit | Source key (unique per tenant) |
|---|---|---|---|
| Lease activated with deposit | 1100 Cash | 2200 Tenant deposits (liability — never revenue) | `rental_deposit:<contract>` |
| Rent collected, unit has an owner | 1100 Cash | **2100 Owner payables** (funds held for owner) | `rent_payment:<payment>` |
| Rent collected, company-owned unit | 1100 Cash | 4100 Rental income | `rent_payment:<payment>` |
| Rent refund | 2100 / 4100 | 1100 | `rent_refund:<refund>` |
| Waiver (authorised) | — reduces the receivable; no cash, no posting | | `rent_adjustments` row + audit |
| Property expense approved, charged to owner | 2100 Owner payables | 2300 Accounts payable | `property_expense:<id>` |
| Property expense approved, charged to company | 5100 Maintenance expense | 2300 | `property_expense:<id>` |
| Property expense paid | 2300 | 1100 | `property_expense_payment:<id>` |
| Settlement approved | 2100 | **4200 Commission income** (only now is company revenue recognised) | `owner_settlement_commission:<id>` |
| Owner payout | 2100 | 1100 | `owner_settlement_payment:<payment>` |
| Admin expense recorded | 5200 Admin expense | 2300 | `admin_expense:<id>` (reversal on delete: `admin_expense_reversal:<id>`) |
| Admin expense paid | 2300 | 1100 | per payment |
| Payroll run generated | 5300 Salaries (gross) | 2400 Salaries payable (net) + 2500 Social insurance (11 %) | `payroll_run:<id>` |
| Salary payment | 2400 | 1100 | `payroll_payment:<id>` |

**Settlement formula**: `net = Σ(unsettled payments − refunds on the owner's contracts paid ≤ period_end) − Σ(commission per contract: contract.commission_rate or owner.commission_rate) − Σ(approved owner-charged expenses ≤ period_end not yet settled) + authorised adjustments`. Included rows are stamped with `settlement_id`, so nothing is counted twice; cancelling a draft releases them. Adjustments require `owners.approve`. After the cycle the owner-payable account nets to zero (asserted in `test_22`).

**Company P&L** (`re_reports_service.profit_loss_totals`): revenue = commissions of approved/paid settlements (by period end) + rent on company-owned units; expenses = admin expenses + approved company-charged property expenses + payroll gross. Owner funds are never revenue.

## Receivables & schedule rules
`rent_amount` is monthly; periods follow `payment_frequency`, anchored on the start date (no day drift); a final short period is pro-rated by days. Due date = period start. Generation is `INSERT … ON CONFLICT DO NOTHING` on `(contract, period_start)`. Overdue is derived (`due_date < today` in the tenant's timezone with balance > 0). Renewal creates a new contract from the day after the old end date; the old one keeps its dates/rent/receivables and becomes `renewed`. Termination cancels unpaid receivables starting after the termination date.

## Reminder schedule (daily job, tenant timezone)
* rent due in exactly 3 days → in-app to users who can view rentals + WhatsApp record to the renter;
* overdue 1, 7 and 30 days → in-app;
* lease ends in 30 days → users who can edit rentals;
* owner settlement due in 7 days (period end + `settlement_day`) → users who can view owners.
Deduplicated by `(user_id, dedupe_key)`.
