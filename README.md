# FRATELANZA REAL ESTATE PLATFORM

منصة SaaS لإدارة شركات التطوير العقاري، المبيعات، العملاء، الوحدات، الحجوزات، العقود، التحصيل، الوسطاء، خدمة العملاء، الإنشاءات، المشتريات، المخازن، المالية، الموارد البشرية، والذكاء التجاري.

Primary language: Arabic (RTL)  
Secondary language: English (LTR)

## What is included

- Enterprise product blueprint and SRS in `docs/FRATELANZA_PLATFORM_BLUEPRINT.md`
- FastAPI backend scaffold in `backend/`
- React + TypeScript + Tailwind frontend scaffold in `frontend/`
- PostgreSQL, Redis, backend, frontend, and Nginx Docker stack
- Multi-company tenancy model with Super Admin visibility
- RBAC roles and permissions for platform, company, sales, finance, projects, brokers, and customers
- Database models for companies, branches, users, customers, projects, buildings, floors, units, leads, reservations, contracts, installments, payments, brokers, tickets, audit logs, and notifications
- Bilingual UI shell with RTL/LTR language switching
- API documentation outline and OpenAPI-ready endpoints

## Repository structure

```text
.
├── backend/                  # Python FastAPI application
├── frontend/                 # React TypeScript application
├── docs/                     # Business, SRS, ERD, API, security, deployment docs
├── infrastructure/           # Nginx and deployment assets
├── docker-compose.yml        # Local production-like stack
└── README.md
```

## Quick start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Full stack with Docker

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

Default services:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- OpenAPI docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Demo credentials

The seed script is intentionally left as an implementation hook. Create a Super Admin user with:

```bash
cd backend
python -m app.scripts.create_super_admin --email owner@fratelanza.com --password "ChangeMe123!"
```

## Security baseline

- JWT access tokens
- Password hashing with Argon2
- Company-level data isolation
- Super Admin cross-company access
- RBAC permission matrix
- Audit log model for sensitive actions
- CORS allow-list configuration
- 2FA-ready user model
- Storage abstraction for local and S3-compatible providers

## Roadmap

The current implementation is a production-oriented scaffold: architecture, schemas, APIs, UI shell, infrastructure, and module boundaries are in place. The next build iterations should deepen each domain with workflow automation, approval engines, real integrations (email/SMS/WhatsApp/e-signature), reporting query optimization, and automated tests around tenant isolation and financial calculations.
