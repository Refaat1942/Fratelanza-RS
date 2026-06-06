import json

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.platform_modules import ALL_MODULE_KEYS, CORE_MODULE_KEYS
from app.models.tenant import SubscriptionPlan
from app.schemas.subscription import SubscriptionPlanUpdate
from app.services.module_service import ModuleService


class SubscriptionService:
    @staticmethod
    def plan_to_dict(plan: SubscriptionPlan) -> dict:
        modules = ModuleService.defaults_for_plan(plan.code)
        if plan.features:
            try:
                data = json.loads(plan.features)
                if isinstance(data, dict) and isinstance(data.get("modules"), list):
                    enabled = set(data["modules"]) | set(CORE_MODULE_KEYS)
                    modules = [k for k in ALL_MODULE_KEYS if k in enabled]
            except (json.JSONDecodeError, TypeError):
                pass
        return {
            "id": plan.id,
            "name_ar": plan.name_ar,
            "name_en": plan.name_en,
            "code": plan.code,
            "price_monthly": plan.price_monthly,
            "price_yearly": plan.price_yearly,
            "max_users": plan.max_users,
            "max_projects": plan.max_projects,
            "max_storage_mb": plan.max_storage_mb,
            "enabled_modules": modules,
            "is_active": plan.is_active,
        }

    @staticmethod
    async def get_plan(db: AsyncSession, plan_id: int) -> SubscriptionPlan:
        result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
        plan = result.scalar_one_or_none()
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        return plan

    @staticmethod
    async def update_plan(db: AsyncSession, plan_id: int, data: SubscriptionPlanUpdate) -> SubscriptionPlan:
        plan = await SubscriptionService.get_plan(db, plan_id)
        payload = data.model_dump(exclude_unset=True)
        modules = payload.pop("enabled_modules", None)
        for field, value in payload.items():
            setattr(plan, field, value)
        if modules is not None:
            enabled = set(modules) | set(CORE_MODULE_KEYS)
            ordered = [k for k in ALL_MODULE_KEYS if k in enabled]
            plan.features = ModuleService.serialize_plan_features(ordered)
        await db.flush()
        return plan
