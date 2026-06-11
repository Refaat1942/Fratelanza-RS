from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.real_estate import Building, Floor, Project, Unit


def _unit_adjustment_percent(unit: Unit) -> float:
    base = getattr(unit, "base_price", None)
    if base is None:
        return 0.0
    base_f = float(base)
    if base_f <= 0:
        return 0.0
    return round((float(unit.price) - base_f) / base_f * 100, 2)


class MasterPlanService:
    @staticmethod
    async def get_master_plan(db: AsyncSession, project_id: int) -> dict | None:
        project = (
            await db.execute(
                select(Project).where(Project.id == project_id, Project.is_deleted == False)
            )
        ).scalar_one_or_none()
        if not project:
            return None

        buildings = (
            await db.execute(
                select(Building)
                .where(Building.project_id == project_id)
                .options(
                    selectinload(Building.floors).selectinload(Floor.units),
                )
                .order_by(Building.code)
            )
        ).scalars().all()

        status_counts: dict[str, int] = defaultdict(int)
        building_payloads = []

        for building in buildings:
            floors_payload = []
            sorted_floors = sorted(building.floors, key=lambda f: f.floor_number, reverse=True)
            for floor in sorted_floors:
                units_payload = []
                active_units = [u for u in floor.units if not u.is_deleted]
                for unit in sorted(active_units, key=lambda u: u.unit_number):
                    status = unit.status.value
                    status_counts[status] += 1
                    base_attr = getattr(unit, "base_price", None)
                    base = float(base_attr if base_attr is not None else unit.price)
                    price = float(unit.price)
                    units_payload.append(
                        {
                            "id": unit.id,
                            "unit_code": unit.unit_code,
                            "unit_number": unit.unit_number,
                            "unit_type": unit.unit_type.value,
                            "status": status,
                            "price": price,
                            "base_price": base,
                            "adjustment_percent": _unit_adjustment_percent(unit),
                            "area_sqm": float(unit.area_sqm),
                            "bedrooms": unit.bedrooms,
                            "is_locked": unit.is_locked,
                        }
                    )
                floors_payload.append(
                    {
                        "id": floor.id,
                        "floor_number": floor.floor_number,
                        "name_en": floor.name_en,
                        "name_ar": floor.name_ar,
                        "units": units_payload,
                    }
                )
            building_payloads.append(
                {
                    "id": building.id,
                    "code": building.code,
                    "name_en": building.name_en,
                    "name_ar": building.name_ar,
                    "floors": floors_payload,
                }
            )

        total_units = sum(status_counts.values())
        return {
            "project": {
                "id": project.id,
                "code": project.code,
                "name_en": project.name_en,
                "name_ar": project.name_ar,
                "city": project.city,
            },
            "buildings": building_payloads,
            "stats": {
                "total": total_units,
                "by_status": dict(status_counts),
                "available": status_counts.get("available", 0),
                "reserved": status_counts.get("reserved", 0),
                "sold": (
                    status_counts.get("sold", 0)
                    + status_counts.get("contracted", 0)
                    + status_counts.get("delivered", 0)
                ),
            },
        }
