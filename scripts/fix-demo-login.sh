#!/bin/bash
# Fix demo company login only — run on VPS
set -e
cd /opt/fratelanza

DEMO_EMAIL="admin@demo.fratelanza.com"
DEMO_PASS="Demo123456"

echo "Fixing demo login..."

docker compose -p fratelanza -f docker-compose.prod.yml exec -T backend python3 << PYEOF
import asyncio
import bcrypt
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.tenant import Company, CompanyStatus
from app.models.users import User, SystemRole, UserStatus

EMAIL = "${DEMO_EMAIL}"
PASSWORD = "${DEMO_PASS}"

def hash_pw(p):
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()

async def fix():
    async with AsyncSessionLocal() as db:
        cr = await db.execute(select(Company).where(Company.code == "DEMO"))
        company = cr.scalar_one_or_none()
        if not company:
            company = Company(
                name_ar="شركة فراتيلانزا للتطوير العقاري",
                name_en="Fratelanza Real Estate Development",
                code="DEMO",
                email="info@fratelanza-demo.com",
                country="Egypt",
                status=CompanyStatus.ACTIVE,
            )
            db.add(company)
            await db.flush()
            print("Created DEMO company")

        r = await db.execute(select(User).where(User.email == EMAIL))
        user = r.scalar_one_or_none()
        if user:
            user.password_hash = hash_pw(PASSWORD)
            user.status = UserStatus.ACTIVE
            user.is_deleted = False
            user.company_id = company.id
            user.system_role = SystemRole.COMPANY_ADMIN
            user.is_super_admin = False
            print("Updated demo user")
        else:
            db.add(User(
                email=EMAIL,
                password_hash=hash_pw(PASSWORD),
                full_name_ar="مدير الشركة",
                full_name_en="Company Administrator",
                system_role=SystemRole.COMPANY_ADMIN,
                company_id=company.id,
                is_super_admin=False,
                status=UserStatus.ACTIVE,
            ))
            print("Created demo user")
        await db.commit()

asyncio.run(fix())
PYEOF

HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:9000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${DEMO_EMAIL}\",\"password\":\"${DEMO_PASS}\"}")

echo ""
if [ "$HTTP" = "200" ]; then
  echo "SUCCESS! Demo login works."
else
  echo "Login test returned HTTP $HTTP — restart backend:"
  echo "  docker compose -p fratelanza -f docker-compose.prod.yml restart backend"
fi
echo ""
echo "  Email:    ${DEMO_EMAIL}"
echo "  Password: ${DEMO_PASS}"
