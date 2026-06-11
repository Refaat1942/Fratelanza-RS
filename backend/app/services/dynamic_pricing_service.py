from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.construction import ConstructionPhase
from app.models.pricing import PricingRule, PricingTriggerType
from app.models.real_estate import Building, Floor, Project, Unit, UnitStatus

MAX_TOTAL_ADJUSTMENT_PERCENT = Decimal("50")

SOLD_STATUSES = {
    UnitStatus.RESERVED,
    UnitStatus.CONTRACTED,
    UnitStatus.SOLD,
    UnitStatus.DELIVERED,
}


class DynamicPricingService:
    @staticmethod
    def _quantize_price(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def ensure_base_price(unit: Unit) -> Decimal:
        if unit.base_price is None:
            unit.base_price = unit.price
        return unit.base_price

    @staticmethod
    async def get_project_id_for_unit(db: AsyncSession, unit_id: int) -> Optional[int]:
        row = (
            await db.execute(
                select(Building.project_id)
                .join(Floor, Floor.building_id == Building.id)
                .join(Unit, Unit.floor_id == Floor.id)
                .where(Unit.id == unit_id)
            )
        ).scalar_one_or_none()
        return row

    @staticmethod
    async def sales_volume_percent(db: AsyncSession, project_id: int) -> Decimal:
        counts = (
            await db.execute(
                select(Unit.status, func.count())
                .join(Floor, Unit.floor_id == Floor.id)
                .join(Building, Floor.building_id == Building.id)
                .where(Building.project_id == project_id, Unit.is_deleted == False)
                .group_by(Unit.status)
            )
        ).all()
        total = sum(c for _, c in counts)
        if total == 0:
            return Decimal("0")
        sold = sum(c for status, c in counts if status in SOLD_STATUSES)
        return DynamicPricingService._quantize_price(Decimal(sold * 100) / Decimal(total))

    @staticmethod
    async def construction_progress_percent(db: AsyncSession, project_id: int) -> Decimal:
        avg_val = (
            await db.execute(
                select(func.avg(ConstructionPhase.progress_percent)).where(
                    ConstructionPhase.project_id == project_id
                )
            )
        ).scalar()
        if avg_val is None:
            return Decimal("0")
        return DynamicPricingService._quantize_price(Decimal(str(avg_val)))

    @staticmethod
    def tier_adjustment(
        rules: list[PricingRule],
        trigger_type: PricingTriggerType,
        metric_percent: Decimal,
    ) -> Decimal:
        matching = [
            r
            for r in rules
            if r.is_active
            and r.trigger_type == trigger_type
            and metric_percent >= Decimal(r.threshold_percent)
        ]
        if not matching:
            return Decimal("0")
        return max(r.adjustment_percent for r in matching)

    @staticmethod
    async def load_rules(
        db: AsyncSession,
        company_id: int,
        project_id: Optional[int] = None,
    ) -> list[PricingRule]:
        query = select(PricingRule).where(
            PricingRule.company_id == company_id,
            PricingRule.is_active == True,
        )
        if project_id is not None:
            query = query.where(
                (PricingRule.project_id == project_id) | (PricingRule.project_id.is_(None))
            )
        result = await db.execute(query.order_by(PricingRule.sort_order, PricingRule.threshold_percent))
        return list(result.scalars().all())

    @staticmethod
    async def compute_adjustment_percent(
        db: AsyncSession,
        company_id: int,
        project_id: int,
    ) -> dict:
        sales_pct = await DynamicPricingService.sales_volume_percent(db, project_id)
        construction_pct = await DynamicPricingService.construction_progress_percent(db, project_id)
        rules = await DynamicPricingService.load_rules(db, company_id, project_id)

        sales_adj = DynamicPricingService.tier_adjustment(
            rules, PricingTriggerType.SALES_VOLUME, sales_pct
        )
        construction_adj = DynamicPricingService.tier_adjustment(
            rules, PricingTriggerType.CONSTRUCTION_PROGRESS, construction_pct
        )
        total = min(sales_adj + construction_adj, MAX_TOTAL_ADJUSTMENT_PERCENT)

        return {
            "project_id": project_id,
            "sales_volume_percent": float(sales_pct),
            "construction_progress_percent": float(construction_pct),
            "sales_adjustment_percent": float(sales_adj),
            "construction_adjustment_percent": float(construction_adj),
            "total_adjustment_percent": float(total),
            "active_rules_count": len(rules),
        }

    @staticmethod
    async def recalculate_project_prices(
        db: AsyncSession,
        company_id: int,
        project_id: int,
        *,
        commit: bool = False,
    ) -> dict:
        metrics = await DynamicPricingService.compute_adjustment_percent(db, company_id, project_id)
        total_adj = Decimal(str(metrics["total_adjustment_percent"]))
        multiplier = Decimal("1") + (total_adj / Decimal("100"))

        units = (
            await db.execute(
                select(Unit)
                .join(Floor, Unit.floor_id == Floor.id)
                .join(Building, Floor.building_id == Building.id)
                .where(
                    Building.project_id == project_id,
                    Unit.is_deleted == False,
                    Unit.status == UnitStatus.AVAILABLE,
                    Unit.is_locked == False,
                )
            )
        ).scalars().all()

        updated = 0
        for unit in units:
            base = DynamicPricingService.ensure_base_price(unit)
            unit.price = DynamicPricingService._quantize_price(base * multiplier)
            updated += 1

        if commit:
            await db.commit()
        else:
            await db.flush()

        return {**metrics, "units_updated": updated}

    @staticmethod
    async def recalculate_for_unit(db: AsyncSession, unit_id: int) -> Optional[dict]:
        project_id = await DynamicPricingService.get_project_id_for_unit(db, unit_id)
        if not project_id:
            return None
        project = (
            await db.execute(select(Project).where(Project.id == project_id))
        ).scalar_one_or_none()
        if not project:
            return None
        return await DynamicPricingService.recalculate_project_prices(
            db, project.company_id, project_id
        )
