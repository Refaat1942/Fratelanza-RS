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

You can also ship the customer EXE with `config/customer_cloud.toml`, which is
prepared for VPS mode and does not require local SQL Server values.

## Your laptop Admin EXE

Your laptop should run the admin console, not the customer business database.

Development command:

```bash
fratelanza-admin
```

Environment for your laptop:

```env
FRATELANZA_ADMIN_API_BASE_URL=https://your-vps-domain.com
FRATELANZA_ADMIN_KEY=<your-private-admin-key>
```

The admin console can:

- Create customers.
- Generate/store customer API keys.
- Assign each customer a database key.
- Suspend/reactivate licenses.
- Show the VPS database path for a customer.

## VPS storage

Set this on the VPS:

```env
FRATELANZA_ADMIN_KEY=<your-private-admin-key>
FRATELANZA_VPS_DATA_ROOT=/opt/fratelanza/data
```

The backend stores:

```text
/opt/fratelanza/data/admin.sqlite3
/opt/fratelanza/data/tenants/customer_001.sqlite3
/opt/fratelanza/data/tenants/customer_002.sqlite3
```

So every customer has a separate database file on your VPS.

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

The current scaffold persists customer/license records and per-customer business
data into SQLite files on the VPS. For larger deployments, these SQLite files
can later be replaced by PostgreSQL databases while keeping the same API shape.

## Important

Do not expose SQL Server directly to customer EXEs over the public internet.
Use the VPS API as the secure middle layer.
