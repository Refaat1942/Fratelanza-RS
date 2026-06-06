#!/bin/bash
# Fix BOTH logins — updates database AND .env so restarts don't break passwords
set -e
cd /opt/fratelanza

SUPER_EMAIL="admin@fratelanza.com"
SUPER_PASS="Admin@Fratelanza2026"
DEMO_EMAIL="admin@demo.fratelanza.com"
DEMO_PASS="Demo123456"

echo "============================================"
echo " Fixing Super Admin + Demo logins"
echo "============================================"

# Update .env so future restarts keep same super admin password
if [ -f .env ]; then
  grep -q "^SUPER_ADMIN_EMAIL=" .env && sed -i "s|^SUPER_ADMIN_EMAIL=.*|SUPER_ADMIN_EMAIL=${SUPER_EMAIL}|" .env || echo "SUPER_ADMIN_EMAIL=${SUPER_EMAIL}" >> .env
  grep -q "^SUPER_ADMIN_PASSWORD=" .env && sed -i "s|^SUPER_ADMIN_PASSWORD=.*|SUPER_ADMIN_PASSWORD=${SUPER_PASS}|" .env || echo "SUPER_ADMIN_PASSWORD=${SUPER_PASS}" >> .env
  echo "✓ Updated .env passwords"
fi

git pull origin main 2>/dev/null || true

docker compose -p fratelanza -f docker-compose.prod.yml exec -T backend python3 << PYEOF
import asyncio
import bcrypt
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.tenant import Company, CompanyStatus
from app.models.users import User, SystemRole, UserStatus

SUPER_EMAIL = "${SUPER_EMAIL}"
SUPER_PASS = "${SUPER_PASS}"
DEMO_EMAIL = "${DEMO_EMAIL}"
DEMO_PASS = "${DEMO_PASS}"

def hash_pw(p):
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()

async def fix():
    async with AsyncSessionLocal() as db:
        # Super Admin
        r = await db.execute(select(User).where(User.email == SUPER_EMAIL))
        u = r.scalar_one_or_none()
        if u:
            u.password_hash = hash_pw(SUPER_PASS)
            u.status = UserStatus.ACTIVE
            u.is_deleted = False
            u.is_super_admin = True
            print("Fixed Super Admin")
        else:
            db.add(User(
                email=SUPER_EMAIL,
                password_hash=hash_pw(SUPER_PASS),
                full_name_ar="مدير النظام",
                full_name_en="Super Administrator",
                system_role=SystemRole.SUPER_ADMIN,
                is_super_admin=True,
                status=UserStatus.ACTIVE,
            ))
            print("Created Super Admin")

        # Demo company + admin
        cr = await db.execute(select(Company).where(Company.code == "DEMO"))
        company = cr.scalar_one_or_none()
        if not company:
            company = Company(
                name_ar="شركة فراتيلانزا",
                name_en="Fratelanza Demo",
                code="DEMO",
                country="Egypt",
                status=CompanyStatus.ACTIVE,
            )
            db.add(company)
            await db.flush()

        r = await db.execute(select(User).where(User.email == DEMO_EMAIL))
        u = r.scalar_one_or_none()
        if u:
            u.password_hash = hash_pw(DEMO_PASS)
            u.status = UserStatus.ACTIVE
            u.is_deleted = False
            u.company_id = company.id
            u.is_super_admin = False
            print("Fixed Demo Admin")
        else:
            db.add(User(
                email=DEMO_EMAIL,
                password_hash=hash_pw(DEMO_PASS),
                full_name_ar="مدير الشركة",
                full_name_en="Company Admin",
                system_role=SystemRole.COMPANY_ADMIN,
                company_id=company.id,
                is_super_admin=False,
                status=UserStatus.ACTIVE,
            ))
            print("Created Demo Admin")

        await db.commit()

asyncio.run(fix())
PYEOF

docker compose -p fratelanza -f docker-compose.prod.yml restart backend
sleep 8

# Test both
for pair in "${SUPER_EMAIL}:${SUPER_PASS}:Super Admin" "${DEMO_EMAIL}:${DEMO_PASS}:Demo"; do
  IFS=':' read -r em pw label <<< "$pair"
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:9000/api/v1/auth/login \
    -H "Content-Type: application/json" -d "{\"email\":\"${em}\",\"password\":\"${pw}\"}")
  if [ "$HTTP" = "200" ]; then echo "✓ ${label}: OK"; else echo "✗ ${label}: FAILED (HTTP $HTTP)"; fi
done

cat > /opt/fratelanza/LOGINS.txt << EOF
============================================
 FRATELANZA — LOGIN DETAILS
============================================

SUPER ADMIN (control panel):
  URL:      https://rs.fratelanza.com
  Email:    ${SUPER_EMAIL}
  Password: ${SUPER_PASS}

DEMO COMPANY (full platform):
  URL:      https://rs.fratelanza.com
  Email:    ${DEMO_EMAIL}
  Password: ${DEMO_PASS}

============================================
EOF

cat /opt/fratelanza/LOGINS.txt
