# Fratelanza VPS Admin Backend

This scaffold is the control plane for selling the EXE without installing SQL
Server on each customer device.

Responsibilities:

- Register customers.
- Assign one separate database key per customer.
- Register installations.
- Store license state: active, suspended, expired.
- Return branding and database assignment to the desktop EXE.
- Enforce offline grace policy through heartbeat responses.
- Persist customer/license data on the VPS.
- Store a separate SQLite database file for each customer database key.

Run locally:

```bash
pip install -e ".[backend]"
uvicorn backend.vps_admin.main:app --host 0.0.0.0 --port 8000
```

Production on the VPS should run behind HTTPS using Nginx or Caddy.

One-command VPS deployment:

```bash
curl -fsSL https://raw.githubusercontent.com/Refaat1942/Fratelanza-LMP/cursor/fratelanza-business-suite-becb/scripts/deploy_vps_api.sh | bash
```

Environment:

```env
FRATELANZA_ADMIN_KEY=<your-private-admin-key>
FRATELANZA_VPS_DATA_ROOT=/opt/fratelanza/data
```
