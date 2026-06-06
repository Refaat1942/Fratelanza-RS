#!/bin/bash
# Fix BOTH logins — updates database AND .env
set -e
cd /opt/fratelanza

SUPER_EMAIL="admin@fratelanza.com"
SUPER_PASS="SuperAdmin2026"
DEMO_EMAIL="admin@demo.fratelanza.com"
DEMO_PASS="Demo123456"

echo "============================================"
echo " Fixing Super Admin + Demo logins"
echo "============================================"

# Update .env
if [ -f .env ]; then
  grep -q "^SUPER_ADMIN_EMAIL=" .env && sed -i "s|^SUPER_ADMIN_EMAIL=.*|SUPER_ADMIN_EMAIL=${SUPER_EMAIL}|" .env || echo "SUPER_ADMIN_EMAIL=${SUPER_EMAIL}" >> .env
  grep -q "^SUPER_ADMIN_PASSWORD=" .env && sed -i "s|^SUPER_ADMIN_PASSWORD=.*|SUPER_ADMIN_PASSWORD=${SUPER_PASS}|" .env || echo "SUPER_ADMIN_PASSWORD=${SUPER_PASS}" >> .env
  echo "✓ Updated .env"
fi

git pull origin main 2>/dev/null || true

# Rebuild backend with latest code
docker compose -p fratelanza -f docker-compose.prod.yml up -d --build backend
sleep 15

docker compose -p fratelanza -f docker-compose.prod.yml exec -T backend python3 << 'PYEOF'
import asyncio
import bcrypt
from sqlalchemy import select, or_
from app.core.database import AsyncSessionLocal
from app.models.tenant import Company, CompanyStatus
from app.models.users import User, SystemRole, UserStatus

SUPER_EMAIL = "admin@fratelanza.com"
SUPER_PASS = "SuperAdmin2026"
DEMO_EMAIL = "admin@demo.fratelanza.com"
DEMO_PASS = "Demo123456"

def hash_pw(p):
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()

def verify(p, h):
    return bcrypt.checkpw(p.encode(), h.encode())

async def fix():
    async with AsyncSessionLocal() as db:
        # Find super admin by email OR is_super_admin flag
        r = await db.execute(
            select(User).where(
                or_(User.email == SUPER_EMAIL, User.is_super_admin == True)
            )
        )
        users = r.scalars().all()
        super_user = None
        for u in users:
            if u.email == SUPER_EMAIL or u.is_super_admin:
                super_user = u
                break

        if super_user:
            super_user.email = SUPER_EMAIL
            super_user.password_hash = hash_pw(SUPER_PASS)
            super_user.status = UserStatus.ACTIVE
            super_user.is_deleted = False
            super_user.is_super_admin = True
            super_user.system_role = SystemRole.SUPER_ADMIN
            ok = verify(SUPER_PASS, super_user.password_hash)
            print(f"Fixed Super Admin: {SUPER_EMAIL} (verify={ok})")
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
            print(f"Created Super Admin: {SUPER_EMAIL}")

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

        r2 = await db.execute(select(User).where(User.email == DEMO_EMAIL))
        demo = r2.scalar_one_or_none()
        if demo:
            demo.password_hash = hash_pw(DEMO_PASS)
            demo.status = UserStatus.ACTIVE
            demo.is_deleted = False
            demo.company_id = company.id
            demo.is_super_admin = False
            demo.system_role = SystemRole.COMPANY_ADMIN
            ok = verify(DEMO_PASS, demo.password_hash)
            print(f"Fixed Demo Admin: {DEMO_EMAIL} (verify={ok})")
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
            print(f"Created Demo Admin: {DEMO_EMAIL}")

        await db.commit()

asyncio.run(fix())
PYEOF

sleep 3

# Test logins (separate curl calls — no shell parsing issues)
echo ""
echo "Testing logins..."

HTTP1=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:9000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@fratelanza.com","password":"SuperAdmin2026"}')

HTTP2=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:9000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@demo.fratelanza.com","password":"Demo123456"}')

[ "$HTTP1" = "200" ] && echo "✓ Super Admin: OK" || echo "✗ Super Admin: FAILED (HTTP $HTTP1)"
[ "$HTTP2" = "200" ] && echo "✓ Demo: OK" || echo "✗ Demo: FAILED (HTTP $HTTP2)"

cat > /opt/fratelanza/LOGINS.txt << EOF
============================================
 FRATELANZA — LOGIN DETAILS
============================================

SUPER ADMIN (control panel):
  URL:      https://rs.fratelanza.com
  Email:    admin@fratelanza.com
  Password: SuperAdmin2026

DEMO COMPANY (full platform):
  URL:      https://rs.fratelanza.com
  Email:    admin@demo.fratelanza.com
  Password: Demo123456

============================================
EOF

echo ""
cat /opt/fratelanza/LOGINS.txt
