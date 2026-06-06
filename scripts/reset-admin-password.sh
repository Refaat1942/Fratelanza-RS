#!/bin/bash
# Reset Super Admin password on running VPS
set -e
cd /opt/fratelanza

PASSWORD="${1:-$(cat LOGIN_PASSWORD.txt 2>/dev/null || grep SUPER_ADMIN_PASSWORD .env | cut -d= -f2)}"
EMAIL="${SUPER_ADMIN_EMAIL:-admin@fratelanza.com}"

if [ -z "$PASSWORD" ]; then
  echo "Usage: bash scripts/reset-admin-password.sh YOUR_PASSWORD"
  exit 1
fi

echo "Resetting password for ${EMAIL}..."

docker compose -p fratelanza -f docker-compose.prod.yml exec -T backend python3 << PYEOF
import asyncio
import bcrypt
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.users import User

async def reset():
    password = "${PASSWORD}"
    email = "${EMAIL}"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            user.password_hash = hashed
            await db.commit()
            print("Password updated for", email)
        else:
            print("User not found:", email)

asyncio.run(reset())
PYEOF

echo "Done. Login with:"
echo "  Email:    ${EMAIL}"
echo "  Password: ${PASSWORD}"
