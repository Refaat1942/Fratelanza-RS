# Commercial Deployment Model

This product can be sold as an EXE without asking customers to install SQL
Server.

## Recommended model

```text
Customer EXE
  -> HTTPS
  -> Fratelanza VPS API
  -> Separate database per customer on the VPS
```

Each customer receives:

- EXE installer
- Client ID
- Installation ID
- Per-customer API key
- Branding/logo settings

The customer does **not** receive a database password and does **not** install
SQL Server.

## Separate database per customer

The VPS admin backend should map:

```text
CUST-001 -> fratelanza_cust_001
CUST-002 -> fratelanza_cust_002
CUST-003 -> fratelanza_cust_003
```

The EXE only knows its `client_id`, `installation_id`, and API key. The VPS API
decides which customer database is used.

## Offline control

Real-time remote control is impossible when the customer has no internet. The
commercial pattern is cached control:

1. EXE contacts your VPS while online.
2. VPS returns license state and `offline_allow_until`.
3. EXE stores the trusted policy locally.
4. If internet is down, EXE can run only until the cached offline expiry.
5. If the customer is suspended while offline, the EXE will block them when the
   cached period expires or immediately when it reconnects.

Recommended grace periods:

- Subscription customers: 24-72 hours
- High-trust customers: 7 days
- Trial customers: 0-24 hours

## Customer `.env` for EXE-only cloud deployment

```env
FRATELANZA_DATA_MODE=hybrid_offline
FRATELANZA_REMOTE_ENABLED=true
FRATELANZA_REMOTE_API_BASE_URL=https://your-domain.com/api
FRATELANZA_REMOTE_API_KEY=<customer-secret-key>
FRATELANZA_REMOTE_CLIENT_ID=CUST-001
FRATELANZA_REMOTE_INSTALLATION_ID=CUST-001-PC-001
FRATELANZA_REMOTE_DISABLE=true
FRATELANZA_REMOTE_OFFLINE_GRACE_HOURS=72
```

## Current API coverage

The desktop app can now switch repository composition by data mode:

- `local_sql`: modules use local SQL Server repositories.
- `cloud_api`: modules use the VPS API.
- `hybrid_offline`: modules use the VPS API, with cached license policy for
  temporary offline startup.

The VPS scaffold exposes API routes for:

- Login
- Products, categories, brands, units, stock adjustments
- Customers and suppliers
- Expenses, revenues, cashboxes, expense categories
- Sales invoices
- Reports and low-stock alerts
- Company profile and taxes

The scaffold uses in-memory tenant data so the contract is testable quickly.
Before production, replace that storage with real per-customer databases on the
VPS using each customer's `database_key`.

## Important

Do not expose SQL Server directly to customer EXEs over the public internet.
Use the VPS API as the secure middle layer.
