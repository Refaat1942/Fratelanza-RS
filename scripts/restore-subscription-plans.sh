#!/bin/bash
# Restore default subscription plans (Basic, Professional, Enterprise) if missing
set -euo pipefail
cd "${APP_DIR:-/opt/fratelanza}"

echo "Restoring subscription plans..."

docker compose -p fratelanza -f docker-compose.prod.yml exec -T backend python3 << 'PYEOF'
import asyncio
from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.models.tenant import SubscriptionPlan
from app.utils.seed import ensure_default_subscription_plans

async def main():
    async with AsyncSessionLocal() as db:
        before = (await db.execute(select(func.count(SubscriptionPlan.id)))).scalar() or 0
        added = await ensure_default_subscription_plans(db)
        await db.commit()
        after = (await db.execute(select(func.count(SubscriptionPlan.id)))).scalar() or 0
        print(f"Plans before: {before}, added: {added}, total now: {after}")
        result = await db.execute(
            select(SubscriptionPlan).order_by(SubscriptionPlan.sort_order, SubscriptionPlan.id)
        )
        for p in result.scalars().all():
            print(f"  - {p.code}: {p.name_en} (active={p.is_active})")

asyncio.run(main())
PYEOF

echo "Done. Refresh Super Admin → Subscription Plans in your browser."
