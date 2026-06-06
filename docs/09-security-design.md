# Security Design
# FRATELANZA REAL ESTATE PLATFORM

## 1. Authentication

### JWT Tokens
- **Access Token**: HS256, 30-minute expiry
- **Refresh Token**: 7-day expiry, type-validated
- Payload: `sub`, `exp`, `type`, `role`, `company_id`, `is_super_admin`

### Password Security
- bcrypt hashing via passlib
- Minimum 8 characters for resets
- Super Admin can force password reset

### Two-Factor Authentication
- TOTP (RFC 6238) via pyotp
- Per-user secret stored encrypted
- Required on login when enabled

## 2. Authorization (RBAC)

### Role Hierarchy
```
Super Admin (platform-wide)
  └── Company Admin (company-wide)
       └── Department roles (scoped permissions)
            └── Customer/Broker (portal access)
```

### Permission Model
- Format: `{module}.{action}` (e.g., `contracts.approve`)
- Checked at API endpoint level
- Super Admin has implicit all permissions

## 3. Data Protection

### Multi-Tenant Isolation
- Application-level `company_id` filtering
- Super Admin is only role with cross-company access
- No direct database cross-tenant queries for company users

### Encryption
- Passwords: bcrypt
- JWT secrets: environment variables
- Data at rest: PostgreSQL + encrypted volumes
- Data in transit: TLS via Nginx

## 4. Audit & Monitoring

### Audit Logs
- Login/logout events
- CRUD operations on sensitive entities
- IP address and user-agent captured
- Super Admin can view all logs

### Activity Logs
- Customer timeline events
- Lead activity tracking

## 5. API Security

- CORS restricted to configured origins
- Bearer token required for all protected endpoints
- Input validation via Pydantic schemas
- File upload size limit: 100MB (Nginx)

## 6. Infrastructure Security

- Docker container isolation
- Non-root service accounts (production)
- Environment secrets via `.env` (not committed)
- Redis not exposed publicly in production
- PostgreSQL accessible only within Docker network

## 7. IP Restrictions

- Configurable per company (future)
- Super Admin can block IP ranges

## 8. Backup & Recovery

- PostgreSQL volume backups
- Point-in-time recovery support
- Super Admin backup/restore endpoints (planned)

## 9. Security Headers (Nginx)

```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Strict-Transport-Security: max-age=31536000
```

## 10. Threat Model

| Threat | Control |
|--------|---------|
| Brute force login | Rate limiting (planned), account suspension |
| Token theft | Short expiry, HTTPS only |
| SQL injection | SQLAlchemy parameterized queries |
| XSS | React auto-escaping, CSP headers |
| CSRF | JWT stateless auth (no cookies) |
| Data leak between tenants | company_id enforcement |
