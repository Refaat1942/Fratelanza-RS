import json

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.customer_portal_features import (
    ALL_PORTAL_FEATURE_KEYS,
    CORE_PORTAL_FEATURE_KEYS,
    PORTAL_FEATURES,
)
from app.models.tenant import Company
from app.services.module_service import ModuleService


class CustomerPortalFeatureService:
    @staticmethod
    def catalog() -> list[dict]:
        return list(PORTAL_FEATURES)

    @staticmethod
    def defaults() -> list[str]:
        return list(ALL_PORTAL_FEATURE_KEYS)

    @staticmethod
    def parse_enabled(company: Company) -> list[str]:
        if company.customer_portal_features:
            try:
                parsed = json.loads(company.customer_portal_features)
                if isinstance(parsed, list):
                    enabled = set(parsed) | set(CORE_PORTAL_FEATURE_KEYS)
                    return [k for k in ALL_PORTAL_FEATURE_KEYS if k in enabled]
            except json.JSONDecodeError:
                pass
        return list(ALL_PORTAL_FEATURE_KEYS)

    @staticmethod
    def is_enabled(company: Company, feature_key: str) -> bool:
        return feature_key in CustomerPortalFeatureService.parse_enabled(company)

    @staticmethod
    def assert_portal_module(company: Company, plan=None) -> None:
        enabled_modules = ModuleService.parse_enabled(company, plan)
        if "customer_portal" not in enabled_modules:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Buyer portal is not enabled for this company",
            )

    @staticmethod
    def assert_feature(company: Company, feature_key: str) -> None:
        if not CustomerPortalFeatureService.is_enabled(company, feature_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Portal feature '{feature_key}' is disabled",
            )

    @staticmethod
    async def set_company_features(
        db: AsyncSession,
        company: Company,
        feature_keys: list[str],
    ) -> list[str]:
        allowed = set(ALL_PORTAL_FEATURE_KEYS)
        enabled = set(feature_keys) & allowed
        enabled |= set(CORE_PORTAL_FEATURE_KEYS)
        ordered = [k for k in ALL_PORTAL_FEATURE_KEYS if k in enabled]
        company.customer_portal_features = json.dumps(ordered)
        await db.flush()
        return ordered

    @staticmethod
    def filter_dashboard(data: dict, enabled: set[str]) -> dict:
        result = dict(data)
        if "contracts" not in enabled:
            result["contracts"] = []
        if "phases" not in enabled:
            result["construction_phases"] = []
        summary = dict(result.get("summary") or {})
        if "installments" not in enabled:
            summary["upcoming_installments"] = 0
        if "receipts" not in enabled:
            summary["receipts_count"] = 0
        if "contracts" not in enabled:
            summary["contracts_count"] = 0
        result["summary"] = summary
        return result
