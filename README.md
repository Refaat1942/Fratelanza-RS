# FRATELANZA REAL ESTATE PLATFORM

**منصة فراتيلانزا العقارية** — Enterprise-grade cloud SaaS for real estate development companies.

Integrated ERP, CRM, Property Management, Construction, Finance, HR, and Business Intelligence platform designed for Egypt, GCC, and international markets.

## Features

- **Multi-Tenant SaaS** — Super Admin controls multiple companies
- **Arabic RTL + English LTR** — Full bilingual support
- **17 User Roles** — Complete RBAC permission system
- **CRM & Sales Pipeline** — Lead to contract workflow
- **Real Estate Structure** — Projects → Buildings → Floors → Units
- **Reservations & Contracts** — Auto-locking, expiry, approval workflows
- **Installments & Collections** — Payment plans with notifications
- **Broker & Customer Portals** — Self-service access
- **Construction Management** — Phases, tasks, milestones, Gantt
- **Finance & Accounting** — Chart of accounts, journal entries
- **AI Features** — Lead scoring, chat assistant, report summaries
- **Business Intelligence** — Real-time KPI dashboards

## Property management, RBAC & customer demos

* Rental contracts, rent collection, owner settlements, property/admin expenses, offers & requests matching, financial reports
* Server-enforced tenant isolation, custom roles (module × action, data scope, sensitive fields), customer-specific demo tenants

Docs: [Gap analysis](docs/REAL_ESTATE_GAP_ANALYSIS.md) · [Multi-tenant architecture](docs/MULTITENANT_ARCHITECTURE.md) ·
[Implementation plan & accounting rules](docs/IMPLEMENTATION_PLAN.md) · [Roles & permissions](docs/ROLES_AND_PERMISSIONS.md) ·
[Demo setup](docs/DEMO_SETUP.md) · [Migration & deployment](docs/MIGRATION_AND_DEPLOYMENT.md)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, TypeScript, Tailwind CSS, Shadcn-style UI |
| Backend | Python FastAPI |
| Database | PostgreSQL |
| Cache | Redis |
| Auth | JWT + 2FA (TOTP) |
| Storage | Local + AWS S3 Compatible |
| Deploy | Docker, Nginx, Linux VPS |

## Quick Start (Development)

```bash
git clone https://github.com/Refaat1942/Fratelanza-RS.git
cd Fratelanza-RS
cp .env.example .env
docker compose up -d --build
```

## Production Deploy (Hostinger VPS — Port 14136)

**Verified working commands** (does not stop Hub or other VPS projects):

```bash
ssh root@187.124.15.14
cd /opt/fratelanza
git fetch origin && git reset --hard origin/main
bash DEPLOY-VPS.sh
```

First time only:

```bash
git clone https://github.com/Refaat1942/Fratelanza-RS.git /opt/fratelanza
cd /opt/fratelanza
cp .env.production.example .env && nano .env   # set passwords
bash DEPLOY-VPS.sh
```

Verify after deploy:

```bash
curl -s http://127.0.0.1:14136/health    # must show git_commit
docker ps | grep fratelanza_rs_nginx       # must show port 14136
```

Then hard-refresh browser: `Ctrl+Shift+R` on https://rs.fratelanza.com

> **Do not run** `docker compose up -d --build` on the VPS — that is the **dev** compose file and fails on port 5432. Production uses `docker-compose.prod.yml` via `DEPLOY-VPS.sh`.

See [docs/16-hostinger-deployment.md](docs/16-hostinger-deployment.md) for full guide.

### Local development only

```bash
# With Docker (local machine, not VPS)
docker compose up -d --build

# Or locally:
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Access

| Service | URL |
|---------|-----|
| **Live demo (Real Estate)** | https://rs.fratelanza.com/login |
| **RS control (Super Admin)** | https://rs-control.fratelanza.com/super-admin |
| Direct (if domain shows Hub) | http://187.124.15.14:14136/login |
| Fratelanza Hub (different app) | https://hub.fratelanza.com |
| Frontend (local dev) | http://localhost:5173 |
| API (local dev) | http://localhost:8000 |
| API Docs (local dev) | http://localhost:8000/docs |

If `rs.fratelanza.com` opens **Fratelanza Hub** instead of Real Estate, run on the VPS:

```bash
cd /opt/fratelanza && bash scripts/fix-rs-domain.sh
```

## Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Super Admin | admin@fratelanza.com | Admin@123456 |
| Demo Company Admin | admin@demo.fratelanza.com | Demo123456 |

> Change these immediately in production.

## Documentation

| Document | Path |
|----------|------|
| Business Analysis | [docs/01-business-analysis.md](docs/01-business-analysis.md) |
| SRS | [docs/02-srs.md](docs/02-srs.md) |
| Database Design | [docs/03-database-design.md](docs/03-database-design.md) |
| ERD | [docs/04-erd.md](docs/04-erd.md) |
| API Documentation | [docs/05-api-documentation.md](docs/05-api-documentation.md) |
| Folder Structure | [docs/06-folder-structure.md](docs/06-folder-structure.md) |
| Frontend Architecture | [docs/07-frontend-architecture.md](docs/07-frontend-architecture.md) |
| Backend Architecture | [docs/08-backend-architecture.md](docs/08-backend-architecture.md) |
| Security Design | [docs/09-security-design.md](docs/09-security-design.md) |
| UI Design System | [docs/10-ui-design-system.md](docs/10-ui-design-system.md) |
| User Journeys | [docs/11-user-journeys.md](docs/11-user-journeys.md) |
| Dashboard Designs | [docs/12-dashboard-designs.md](docs/12-dashboard-designs.md) |
| Database Schema | [docs/13-database-schema.sql](docs/13-database-schema.sql) |
| Development Roadmap | [docs/14-development-roadmap.md](docs/14-development-roadmap.md) |
| Deployment Guide | [docs/15-production-deployment-guide.md](docs/15-production-deployment-guide.md) |
| **Demo User Manual (EN)** | [docs/DEMO-USER-MANUAL.md](docs/DEMO-USER-MANUAL.md) |
| **Demo User Manual (AR)** | [docs/DEMO-USER-MANUAL-AR.md](docs/DEMO-USER-MANUAL-AR.md) |
| Demo Quick Start Card | [docs/DEMO-QUICK-START.md](docs/DEMO-QUICK-START.md) |

## Project Structure

```
├── backend/          # FastAPI application
├── frontend/         # React application
├── docs/             # Complete documentation
├── nginx/            # Reverse proxy config
├── scripts/          # Setup scripts
└── docker-compose.yml
```

## License

Proprietary — FRATELANZA Real Estate Platform © 2026
