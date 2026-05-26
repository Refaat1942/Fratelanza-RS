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

Run locally:

```bash
pip install -e ".[backend]"
uvicorn backend.vps_admin.main:app --host 0.0.0.0 --port 8000
```

Production on the VPS should run behind HTTPS using Nginx or Caddy.
