# Project Folder Structure
# FRATELANZA REAL ESTATE PLATFORM

```
fratelanza-platform/
├── docs/                          # Documentation
│   ├── 01-business-analysis.md
│   ├── 02-srs.md
│   ├── 03-database-design.md
│   ├── 04-erd.md
│   ├── 05-api-documentation.md
│   ├── 06-folder-structure.md
│   ├── 07-frontend-architecture.md
│   ├── 08-backend-architecture.md
│   ├── 09-security-design.md
│   ├── 10-ui-design-system.md
│   ├── 11-user-journeys.md
│   ├── 12-dashboard-designs.md
│   ├── 13-database-schema.sql
│   ├── 14-development-roadmap.md
│   └── 15-production-deployment-guide.md
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py            # Auth dependencies
│   │   │   └── v1/
│   │   │       ├── endpoints/     # API route handlers
│   │   │       └── router.py      # Route aggregator
│   │   ├── core/
│   │   │   ├── config.py          # Settings
│   │   │   ├── database.py        # SQLAlchemy engine
│   │   │   └── security.py        # JWT, passwords, 2FA
│   │   ├── models/                # SQLAlchemy ORM models
│   │   ├── schemas/               # Pydantic schemas
│   │   ├── services/              # Business logic
│   │   ├── utils/                 # Seed, helpers
│   │   └── main.py                # FastAPI app
│   ├── alembic/                   # DB migrations
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                # Reusable UI components
│   │   │   ├── layout/            # Sidebar, Header, Layout
│   │   │   └── dashboard/         # Chart components
│   │   ├── pages/
│   │   │   ├── auth/              # Login
│   │   │   ├── super-admin/       # Super Admin pages
│   │   │   └── company/           # Company module pages
│   │   ├── stores/                # Zustand state
│   │   ├── locales/               # i18n translations
│   │   ├── lib/                   # API client, utils
│   │   ├── types/                 # TypeScript types
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── i18n.ts
│   ├── package.json
│   └── Dockerfile
├── nginx/
│   └── nginx.conf
├── scripts/
├── docker-compose.yml
├── .env.example
└── README.md
```
