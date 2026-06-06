#!/bin/bash
# Reset BOTH login accounts to known passwords — run on VPS
set -e
cd /opt/fratelanza

SUPER_EMAIL="admin@fratelanza.com"
SUPER_PASS="Admin@Fratelanza2026"
DEMO_EMAIL="admin@demo.fratelanza.com"
DEMO_PASS="Demo123456"

echo "============================================"
echo " Resetting ALL login accounts..."
echo "============================================"

# Ensure latest code + bcrypt fix
git pull origin main 2>/dev/null || true
docker compose -p fratelanza -f docker-compose.prod.yml up -d --build backend
sleep 10

docker compose -p fratelanza -f docker-compose.prod.yml exec -T backend python3 << PYEOF
import asyncio
import bcrypt
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.users import User, SystemRole, UserStatus

SUPER_EMAIL = "${SUPER_EMAIL}"
SUPER_PASS = "${SUPER_PASS}"
DEMO_EMAIL = "${DEMO_EMAIL}"
DEMO_PASS = "${DEMO_PASS}"

def hash_pw(p):
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()

async def reset():
    async with AsyncSessionLocal() as db:
        # Super Admin
        r = await db.execute(select(User).where(User.email == SUPER_EMAIL))
        u = r.scalar_one_or_none()
        if u:
            u.password_hash = hash_pw(SUPER_PASS)
            u.status = UserStatus.ACTIVE
            u.is_deleted = False
            print("Updated Super Admin:", SUPER_EMAIL)
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
            print("Created Super Admin:", SUPER_EMAIL)

        # Demo Company Admin
        r = await db.execute(select(User).where(User.email == DEMO_EMAIL))
        u = r.scalar_one_or_none()
        if u:
            u.password_hash = hash_pw(DEMO_PASS)
            u.status = UserStatus.ACTIVE
            u.is_deleted = False
            print("Updated Demo Admin:", DEMO_EMAIL)
        else:
            from app.models.tenant import Company
            cr = await db.execute(select(Company).where(Company.code == "DEMO"))
            company = cr.scalar_one_or_none()
            cid = company.id if company else None
            db.add(User(
                email=DEMO_EMAIL,
                password_hash=hash_pw(DEMO_PASS),
                full_name_ar="مدير الشركة",
                full_name_en="Company Administrator",
                system_role=SystemRole.COMPANY_ADMIN,
                company_id=cid,
                is_super_admin=False,
                status=UserStatus.ACTIVE,
            ))
            print("Created Demo Admin:", DEMO_EMAIL)

        await db.commit()

asyncio.run(reset())
PYEOF

# Save passwords to file
cat > /opt/fratelanza/LOGINS.txt << EOF
============================================
 FRATELANZA LOGIN DETAILS
============================================

SUPER ADMIN (control panel):
  URL:      https://rs.fratelanza.com
  Email:    ${SUPER_EMAIL}
  Password: ${SUPER_PASS}

COMPANY ADMIN (full platform):
  URL:      https://rs.fratelanza.com
  Email:    ${DEMO_EMAIL}
  Password: ${DEMO_PASS}

============================================
EOF

echo "${SUPER_PASS}" > /opt/fratelanza/LOGIN_PASSWORD.txt

# Test login via API
echo ""
echo "Testing login..."
HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:9000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${SUPER_EMAIL}\",\"password\":\"${SUPER_PASS}\"}")

if [ "$HTTP" = "200" ]; then
  echo "✓ Super Admin login: OK"
else
  echo "✗ Super Admin login test failed (HTTP $HTTP)"
fi

HTTP2=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:9000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${DEMO_EMAIL}\",\"password\":\"${DEMO_PASS}\"}")

if [ "$HTTP2" = "200" ]; then
  echo "✓ Demo Company login: OK"
else
  echo "✗ Demo login failed (HTTP $HTTP2) — run: bash scripts/fix-demo-login.sh"
fi

cat /opt/fratelanza/LOGINS.txt
