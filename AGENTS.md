# AGENTS.md

## Cursor Cloud specific instructions

### Product overview

Fratelanza Real Estate Platform is a multi-tenant SaaS (FastAPI backend + React/Vite frontend + PostgreSQL). Primary local dev uses **Docker Compose** from the repo root.

### Starting services

Docker must be running (`sudo service docker start`). Then from `/workspace`:

```bash
cp -n .env.example .env   # first time only
sudo docker compose up -d --build
```

| Service | URL |
|---------|-----|
| Frontend (dev) | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |
| Nginx proxy (optional) | http://localhost:80 |

Default credentials: `admin@demo.fratelanza.com` / `Demo123456` (company admin) or `admin@fratelanza.com` / `Admin@123456` (super admin).

### Common commands

| Task | Command |
|------|---------|
| Service status | `sudo docker compose ps` |
| Backend logs | `sudo docker compose logs -f backend` |
| Frontend build | `sudo docker compose exec frontend npm run build` |
| Frontend lint | `sudo docker compose exec frontend npm run lint` |

### Gotchas

- **ESLint config missing**: `npm run lint` fails because there is no `eslint.config.js` (ESLint 9 flat config). The `lint` script exists in `frontend/package.json` but is not wired up yet.
- **No automated backend tests**: There is no `pytest` suite or test files in `backend/`.
- **Redis is required by Docker Compose** (`backend` depends on Redis healthcheck) but is not used in application code yet.
- **Login API field**: Auth expects JSON `{"username": "...", "password": "..."}` (not `email`).
- **Hot reload**: Backend and frontend source are volume-mounted; code changes reload without rebuild. Re-run `sudo docker compose up -d --build` after changing `requirements.txt` or `package.json`.
- **sudo for Docker**: The `ubuntu` user is not in the `docker` group in this VM; prefix Docker commands with `sudo`.

### Manual (non-Docker) alternative

See [README.md](README.md): run PostgreSQL locally, `pip install -r backend/requirements.txt` + `uvicorn`, and `npm install && npm run dev` in `frontend/`. Update `DATABASE_URL` in `.env` to point at `localhost` instead of `postgres`.
