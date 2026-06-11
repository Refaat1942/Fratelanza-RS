# AGENTS.md

## Cursor Cloud specific instructions

This repo runs as a Docker Compose stack. Use **`sudo docker compose`** for all compose commands on Cloud Agent VMs.

### Services

| Service | URL | Notes |
|---------|-----|-------|
| Frontend (dev) | http://localhost:5173 | Vite dev server in `fratelanza_frontend` |
| Backend API | http://localhost:8000 | FastAPI; docs at `/docs` |
| Postgres | localhost:5432 | Seeded on backend startup |

### Demo login

- Username: `admin@demo.fratelanza.com`
- Password: `Demo123456`

Auth expects **`username`** (not `email`) in `POST /api/v1/auth/login`.

### Common commands

```bash
sudo docker compose up -d --build          # start / rebuild stack
sudo docker compose logs -f backend        # backend logs
sudo docker exec fratelanza_frontend npm run build   # frontend typecheck + build
```

If the backend cannot reach Postgres after startup, restart Docker then recreate containers:

```bash
sudo service docker restart
sudo docker compose down && sudo docker compose up -d --build
```

### Warehouse / inventory module

- API prefix: `/api/v1/warehouse`
- Key endpoints: `/items`, `/equipment`, `/transfers`, `/movements`, `/equipment/transfers`
- UI route: `/warehouse` — tabs: Raw Materials, Heavy Equipment, Stock Transfers

Seed data includes central depot `WH-CENTRAL`, site store `WH-SITE-001`, demo cement transfer `TRF-DEMO-001`, and sample excavator/crane.
