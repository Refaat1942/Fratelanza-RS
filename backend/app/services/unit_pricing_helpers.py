from app.models.real_estate import Unit
from app.schemas.project import UnitResponse


def unit_adjustment_percent(unit: Unit) -> float:
    base = unit.base_price or unit.price
    if not base or float(base) <= 0:
        return 0.0
    return round((float(unit.price) - float(base)) / float(base) * 100, 2)


def unit_to_response(unit: Unit) -> dict:
    data = UnitResponse.model_validate(unit).model_dump()
    data["adjustment_percent"] = unit_adjustment_percent(unit)
    if data.get("base_price") is None:
        data["base_price"] = float(unit.price)
    return data
