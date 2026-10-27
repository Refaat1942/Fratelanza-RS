# API Documentation
# FRATELANZA REAL ESTATE PLATFORM

**Base URL**: `http://localhost:8000/api/v1`  
**Auth**: Bearer JWT Token  
**Interactive Docs**: `/docs` (Swagger) | `/redoc`

## Authentication

### POST /auth/login
```json
{ "username": "superadmin", "password": "123456" }
```
Response: `{ "access_token", "refresh_token", "token_type": "bearer" }`

### POST /auth/refresh
```json
{ "refresh_token": "..." }
```

### GET /auth/me
Returns current user profile.

## Super Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /super-admin/companies | List all companies |
| POST | /super-admin/companies | Create company |
| PUT | /super-admin/companies/{id} | Update company |
| POST | /super-admin/companies/{id}/suspend | Suspend company |
| GET | /super-admin/subscription-plans | List plans |
| GET | /super-admin/audit-logs | View audit logs |

## Companies

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /companies/me | Current company profile |
| GET | /companies/{id} | Get company |
| POST | /companies/{id}/branches | Create branch |

## Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /users | List users |
| POST | /users/{id}/suspend | Suspend user |
| POST | /users/{id}/activate | Activate user |
| POST | /users/{id}/reset-password | Reset password (Super Admin) |

## Customers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /customers | List customers (paginated, searchable) |
| POST | /customers | Create customer |
| GET | /customers/{id} | Get customer |
| PUT | /customers/{id} | Update customer |
| GET | /customers/{id}/timeline | Activity timeline |

## CRM & Leads

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /leads | List leads (filter by stage) |
| POST | /leads | Create lead (auto AI scoring) |
| PUT | /leads/{id} | Update lead |

## Projects & Units

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /projects | List projects |
| POST | /projects | Create project |
| GET | /projects/{id}/units | List project units |
| POST | /projects/units | Create unit |

## Reservations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /reservations | List reservations |
| POST | /reservations | Create (locks unit) |
| POST | /reservations/{id}/approve | Approve reservation |

## Dashboard & BI

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /dashboard/super-admin | Super Admin KPIs |
| GET | /dashboard/company | Company dashboard |

## Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /search?q={query} | Global search |

## AI

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /ai/chat | AI chat assistant |
| GET | /ai/report-summary | AI report summary |

## Response Format

### Paginated
```json
{ "items": [], "total": 100, "page": 1, "page_size": 20, "pages": 5 }
```

### Error
```json
{ "detail": "Error message" }
```

## Status Codes
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 422: Validation Error
