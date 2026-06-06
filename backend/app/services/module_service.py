import json
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.platform_modules import (
    ALL_MODULE_KEYS,
    CORE_MODULE_KEYS,
    PLAN_MODULE_DEFAULTS,
    PLATFORM_MODULES,
)
from app.models.tenant import Company, SubscriptionPlan


class ModuleService:
    @staticmethod
    def catalog() -> list[dict]:
        return [
            {
                "key": m["key"],
                "name_en": m["name_en"],
                "name_ar": m["name_ar"],
                "category_en": m["category_en"],
                "category_ar": m["category_ar"],
                "route": m["route"],
                "core": m["core"],
            }
            for m in PLATFORM_MODULES
        ]

    @staticmethod
    def defaults_for_plan(plan_code: Optional[str]) -> list[str]:
        if plan_code and plan_code in PLAN_MODULE_DEFAULTS:
            return list(PLAN_MODULE_DEFAULTS[plan_code])
        return list(ALL_MODULE_KEYS)

    @staticmethod
    def parse_enabled(company: Company, plan: Optional[SubscriptionPlan] = None) -> list[str]:
        if company.enabled_modules:
            try:
                parsed = json.loads(company.enabled_modules)
                if isinstance(parsed, list) and parsed:
                    enabled = set(parsed) | set(CORE_MODULE_KEYS)
                    return [k for k in ALL_MODULE_KEYS if k in enabled]
            except (json.JSONDecodeError, TypeError):
                pass
        if plan and plan.features:
            try:
                data = json.loads(plan.features)
                if isinstance(data, dict) and isinstance(data.get("modules"), list):
                    enabled = set(data["modules"]) | set(CORE_MODULE_KEYS)
                    return [k for k in ALL_MODULE_KEYS if k in enabled]
            except (json.JSONDecodeError, TypeError):
                pass
        if plan and plan.code in PLAN_MODULE_DEFAULTS:
            return ModuleService.defaults_for_plan(plan.code)
        return list(ALL_MODULE_KEYS)

    @staticmethod
    def is_enabled(company: Company, module_key: str, plan: Optional[SubscriptionPlan] = None) -> bool:
        if module_key in CORE_MODULE_KEYS:
            return True
        return module_key in ModuleService.parse_enabled(company, plan)

    @staticmethod
    def module_for_path(path: str) -> Optional[str]:
        """Map API path to module key. Returns None if path is always allowed."""
        skip_prefixes = ("/search", "/notifications", "/auth", "/companies/me/modules", "/companies/me")
        for skip in skip_prefixes:
            if path == skip or path.startswith(skip + "/"):
                if skip == "/companies/me" and (
                    path.startswith("/companies/me/branding") or path.startswith("/companies/me/logo")
                ):
                    break
                return None
        for mod in PLATFORM_MODULES:
            for prefix in mod["api_prefixes"]:
                if path.startswith(prefix):
                    return mod["key"]
        return None

    @staticmethod
    async def set_company_modules(
        db: AsyncSession,
        company: Company,
        module_keys: list[str],
    ) -> list[str]:
        enabled = set(module_keys) | set(CORE_MODULE_KEYS)
        ordered = [k for k in ALL_MODULE_KEYS if k in enabled]
        company.enabled_modules = json.dumps(ordered)
        await db.flush()
        return ordered

    @staticmethod
    def serialize_plan_features(modules: list[str]) -> str:
        return json.dumps({"modules": modules})
