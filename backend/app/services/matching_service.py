"""Match customer requirements (want to buy / rent) with offers and listed units.

Each criterion yields ``match``, ``mismatch`` or ``unknown`` (information missing on either side).
Unknown is never counted as a match — the result shows what still has to be confirmed.
A mismatch on a *required* criterion excludes the candidate.
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.real_estate import Building, Floor, Project, Unit, UnitStatus
from app.models.rentals import PropertyRequest

CRITERIA: list[dict] = [
    {"key": "purpose", "name_ar": "الغرض (بيع/إيجار)", "name_en": "Purpose (sale/rent)", "required": True},
    {"key": "property_type", "name_ar": "نوع العقار", "name_en": "Property type", "required": True},
    {"key": "location", "name_ar": "الموقع", "name_en": "Location", "required": False},
    {"key": "budget", "name_ar": "الميزانية", "name_en": "Budget", "required": False},
    {"key": "area", "name_ar": "المساحة", "name_en": "Area", "required": False},
    {"key": "rooms", "name_ar": "عدد الغرف", "name_en": "Rooms", "required": False},
    {"key": "floor", "name_ar": "الدور", "name_en": "Floor", "required": False},
    {"key": "finishing", "name_ar": "التشطيب", "name_en": "Finishing", "required": False},
    {"key": "furnishing", "name_ar": "الفرش", "name_en": "Furnishing", "required": False},
]
CRITERIA_KEYS = [c["key"] for c in CRITERIA]
REQUIRED = {c["key"] for c in CRITERIA if c["required"]}

COUNTERPART = {"request_buy": "offer_sale", "request_rent": "offer_rent", "offer_sale": "request_buy", "offer_rent": "request_rent"}


def _norm(value: Optional[str]) -> Optional[str]:
    return value.strip().lower() if isinstance(value, str) and value.strip() else None


def _range_check(lo, hi, value) -> str:
    if value is None or (lo is None and hi is None):
        return "unknown"
    value = Decimal(str(value))
    if lo is not None and value < Decimal(str(lo)):
        return "mismatch"
    if hi is not None and value > Decimal(str(hi)):
        return "mismatch"
    return "match"


def _ranges_overlap(lo1, hi1, lo2, hi2) -> str:
    if (lo1 is None and hi1 is None) or (lo2 is None and hi2 is None):
        return "unknown"
    lo1 = Decimal(str(lo1)) if lo1 is not None else Decimal("-1e18")
    hi1 = Decimal(str(hi1)) if hi1 is not None else Decimal("1e18")
    lo2 = Decimal(str(lo2)) if lo2 is not None else Decimal("-1e18")
    hi2 = Decimal(str(hi2)) if hi2 is not None else Decimal("1e18")
    return "match" if lo1 <= hi2 and lo2 <= hi1 else "mismatch"


def _eq(a, b) -> str:
    a, b = (_norm(a) if isinstance(a, str) else a), (_norm(b) if isinstance(b, str) else b)
    if a is None or b is None:
        return "unknown"
    return "match" if a == b else "mismatch"


def _evaluate(request: PropertyRequest, candidate: dict, criteria: list[str]) -> dict:
    results: dict[str, str] = {}
    for key in criteria:
        if key == "purpose":
            results[key] = "match" if candidate["purpose_ok"] else "mismatch"
        elif key == "property_type":
            results[key] = _eq(request.property_type, candidate.get("property_type"))
        elif key == "location":
            city = _eq(request.city, candidate.get("city"))
            if city == "match" and request.district and candidate.get("district"):
                city = _eq(request.district, candidate.get("district"))
            results[key] = city
        elif key == "budget":
            if candidate.get("price") is not None:
                results[key] = _range_check(request.price_min, request.price_max, candidate["price"])
            else:
                results[key] = _ranges_overlap(request.price_min, request.price_max, candidate.get("price_min"), candidate.get("price_max"))
        elif key == "area":
            if candidate.get("area") is not None:
                results[key] = _range_check(request.area_min, request.area_max, candidate["area"])
            else:
                results[key] = _ranges_overlap(request.area_min, request.area_max, candidate.get("area_min"), candidate.get("area_max"))
        elif key == "rooms":
            if request.rooms is None or candidate.get("rooms") is None:
                results[key] = "unknown"
            else:
                results[key] = "match" if int(candidate["rooms"]) >= int(request.rooms) else "mismatch"
        elif key == "floor":
            results[key] = _eq(request.floor, candidate.get("floor"))
        elif key == "finishing":
            results[key] = _eq(request.finishing, candidate.get("finishing"))
        elif key == "furnishing":
            results[key] = _eq(request.furnishing_status, candidate.get("furnishing_status"))
    return results


class MatchingService:
    @staticmethod
    async def find_matches(
        db: AsyncSession,
        company_id: int,
        request: PropertyRequest,
        criteria: Optional[list[str]] = None,
        min_score: float = 0.0,
    ) -> list[dict]:
        criteria = [c for c in (criteria or CRITERIA_KEYS) if c in CRITERIA_KEYS]
        for required in REQUIRED:
            if required not in criteria:
                criteria.append(required)
        target_kind = COUNTERPART.get(request.kind)
        candidates: list[dict] = []

        offers = (
            await db.execute(
                select(PropertyRequest).where(
                    PropertyRequest.company_id == company_id,
                    PropertyRequest.kind == target_kind,
                    PropertyRequest.status == "open",
                    PropertyRequest.is_deleted == False,  # noqa: E712
                    PropertyRequest.id != request.id,
                )
            )
        ).scalars().all()
        for o in offers:
            single_price = o.price_min if o.price_min is not None and o.price_min == o.price_max else None
            candidates.append(
                {
                    "source": "request" if o.kind.startswith("request") else "offer",
                    "id": o.id,
                    "title": f"{o.property_type or ''} — {o.city or ''} {o.district or ''}".strip(" —"),
                    "contact_name": o.customer_name,
                    "contact_mobile": o.customer_mobile,
                    "purpose_ok": True,
                    "property_type": o.property_type,
                    "city": o.city,
                    "district": o.district,
                    "price": single_price,
                    "price_min": o.price_min,
                    "price_max": o.price_max,
                    "area": o.area_min if o.area_min is not None and o.area_min == o.area_max else None,
                    "area_min": o.area_min,
                    "area_max": o.area_max,
                    "rooms": o.rooms,
                    "floor": o.floor,
                    "finishing": o.finishing,
                    "furnishing_status": o.furnishing_status,
                }
            )

        # Requests are also matched against the tenant's own listed units
        if request.kind in ("request_buy", "request_rent"):
            wanted = ("sale", "both") if request.kind == "request_buy" else ("rent", "both")
            units = (
                await db.execute(
                    select(Unit, Floor, Project)
                    .join(Floor, Unit.floor_id == Floor.id)
                    .join(Building, Floor.building_id == Building.id)
                    .join(Project, Building.project_id == Project.id)
                    .where(
                        Unit.company_id == company_id,
                        Unit.is_deleted == False,  # noqa: E712
                        Unit.listing_purpose.in_(wanted),
                        Unit.status == UnitStatus.AVAILABLE,
                        Unit.occupancy_status == "vacant",
                    )
                )
            ).all()
            for unit, floor, project in units:
                candidates.append(
                    {
                        "source": "unit",
                        "id": unit.id,
                        "title": f"{unit.unit_code} — {project.name_ar}",
                        "contact_name": None,
                        "contact_mobile": None,
                        "purpose_ok": True,
                        "property_type": unit.unit_type.value,
                        "city": project.city,
                        "district": None,
                        # For rent requests the comparable price is the monthly rent, which is not
                        # stored on the unit — leave unknown rather than compare a sale price.
                        "price": unit.price if request.kind == "request_buy" else None,
                        "area": unit.area_sqm,
                        "rooms": unit.bedrooms,
                        "floor": floor.floor_number,
                        "finishing": unit.finishing,
                        "furnishing_status": unit.furnishing_status,
                    }
                )

        labels = {c["key"]: c for c in CRITERIA}
        matches = []
        for cand in candidates:
            results = _evaluate(request, cand, criteria)
            if any(results.get(k) == "mismatch" for k in REQUIRED):
                continue
            matched = [k for k, v in results.items() if v == "match"]
            mismatched = [k for k, v in results.items() if v == "mismatch"]
            unknown = [k for k, v in results.items() if v == "unknown"]
            evaluated = len(matched) + len(mismatched)
            score = round(len(matched) / len(criteria), 2) if criteria else 0.0
            if score < min_score or evaluated == 0:
                continue
            matches.append(
                {
                    "source": cand["source"],
                    "id": cand["id"],
                    "title": cand["title"],
                    "contact_name": cand["contact_name"],
                    "contact_mobile": cand["contact_mobile"],
                    "score": score,
                    "matched": [{"key": k, "name_ar": labels[k]["name_ar"], "name_en": labels[k]["name_en"]} for k in matched],
                    "mismatched": [{"key": k, "name_ar": labels[k]["name_ar"], "name_en": labels[k]["name_en"]} for k in mismatched],
                    "unknown": [{"key": k, "name_ar": labels[k]["name_ar"], "name_en": labels[k]["name_en"]} for k in unknown],
                }
            )
        matches.sort(key=lambda m: (-m["score"], len(m["mismatched"])))
        return matches
