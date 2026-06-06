# Backend Architecture
# FRATELANZA REAL ESTATE PLATFORM

## Tech Stack
- **Python 3.12** + **FastAPI**
- **SQLAlchemy 2.0** (async) + **PostgreSQL**
- **Alembic** for migrations
- **Redis** for caching
- **Pydantic v2** for validation
- **JWT** (python-jose) for auth
- **Boto3** for S3 storage

## Layered Architecture

```
API Endpoints → Services → Models → Database
     ↓              ↓
  Schemas       Business Logic
  (Pydantic)    (Validation, Rules)
```

## Directory Responsibilities

| Layer | Path | Purpose |
|-------|------|---------|
| Endpoints | `api/v1/endpoints/` | HTTP handlers, request/response |
| Dependencies | `api/deps.py` | Auth, RBAC, audit injection |
| Services | `services/` | Business logic, transactions |
| Models | `models/` | SQLAlchemy ORM entities |
| Schemas | `schemas/` | Pydantic request/response DTOs |
| Core | `core/` | Config, DB, security |

## Multi-Tenancy

- `company_id` column on tenant-scoped tables
- `get_company_user` dependency enforces isolation
- Super Admin bypasses company filter
- All list endpoints filter by company unless super admin

## Authentication Flow

1. `POST /auth/login` → verify password → issue access + refresh JWT
2. Access token: 30 min expiry, contains user_id, role, company_id
3. Refresh token: 7 day expiry
4. Optional 2FA via TOTP (pyotp)

## RBAC

17 system roles defined in `SystemRole` enum:
- Permission model: `module.action` (e.g., `customers.create`)
- Role-permission mapping via `role_permissions` table
- `require_roles()` dependency for endpoint protection

## Key Business Rules

### Reservation
- Check unit availability before create
- Lock unit on reservation
- Auto-expire on `expiry_date`

### Lead Scoring
- AI service scores based on data completeness and stage
- Auto-updated on create/update

### Audit
- All auth events logged
- IP and user-agent captured

## Async Database

```python
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine)
```

## Startup
- Auto-create tables via `Base.metadata.create_all`
- Seed super admin, plans, demo company
