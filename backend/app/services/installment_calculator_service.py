from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from dateutil.relativedelta import relativedelta

from app.models.sales import PaymentPlanType

PLAN_MONTHS: dict[str, int] = {
    PaymentPlanType.MONTHLY.value: 1,
    PaymentPlanType.QUARTERLY.value: 3,
    PaymentPlanType.SEMI_ANNUAL.value: 6,
    PaymentPlanType.ANNUAL.value: 12,
    PaymentPlanType.CUSTOM.value: 1,
}


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def generate_due_dates(start_date: str, count: int, plan_type: str) -> list[str]:
    base = datetime.strptime(start_date, "%Y-%m-%d").date()
    months_step = PLAN_MONTHS.get(plan_type, 3)
    return [(base + relativedelta(months=months_step * i)).isoformat() for i in range(count)]


def _distribute_amount(total: Decimal, slots: int) -> list[Decimal]:
    if slots <= 0:
        return []
    if slots == 1:
        return [money(total)]
    each = money(total / slots)
    amounts: list[Decimal] = []
    running = Decimal("0")
    for i in range(slots):
        if i == slots - 1:
            amounts.append(money(total - running))
        else:
            amounts.append(each)
            running += each
    return amounts


def build_schedule(
    total_price: Decimal,
    down_payment: Decimal,
    plan_type: str,
    number_of_installments: int,
    start_date: str,
    installment_rows: list[dict] | None = None,
) -> dict:
    if down_payment > total_price:
        raise ValueError("Down payment cannot exceed total unit price")
    if number_of_installments < 1:
        raise ValueError("At least one installment is required")

    financed = money(total_price - down_payment)
    dates = generate_due_dates(start_date, number_of_installments, plan_type)

    if not installment_rows:
        amounts = _distribute_amount(financed, number_of_installments)
        installments = [
            {
                "installment_number": i + 1,
                "due_date": dates[i],
                "due_amount": float(amounts[i]),
                "remaining_balance": float(amounts[i]),
                "is_manual": False,
            }
            for i in range(number_of_installments)
        ]
    else:
        installments = recalculate_schedule(
            total_price=total_price,
            down_payment=down_payment,
            plan_type=plan_type,
            start_date=start_date,
            installment_rows=installment_rows,
        )

    schedule_total = sum(Decimal(str(row["due_amount"])) for row in installments)
    return {
        "total_price": float(total_price),
        "down_payment": float(down_payment),
        "financed_amount": float(financed),
        "plan_type": plan_type,
        "number_of_installments": number_of_installments,
        "start_date": start_date,
        "installments": installments,
        "schedule_total": float(money(schedule_total)),
        "balanced": money(schedule_total) == financed,
    }


def recalculate_schedule(
    total_price: Decimal,
    down_payment: Decimal,
    plan_type: str,
    start_date: str,
    installment_rows: list[dict],
) -> list[dict]:
    financed = money(total_price - down_payment)
    count = len(installment_rows)
    if count < 1:
        raise ValueError("Installment rows required")

    dates = generate_due_dates(start_date, count, plan_type)
    manual_total = Decimal("0")
    unlocked_indices: list[int] = []
    draft: list[dict] = []

    for i, row in enumerate(installment_rows):
        num = int(row.get("installment_number", i + 1))
        is_manual = bool(row.get("is_manual", False))
        paid = money(Decimal(str(row.get("paid_amount", 0))))
        locked = is_manual or paid > 0

        if locked:
            amt = money(Decimal(str(row.get("due_amount", 0))))
            manual_total += amt
        else:
            unlocked_indices.append(i)

        draft.append(
            {
                "installment_number": num,
                "due_date": row.get("due_date") or dates[i],
                "due_amount": None,
                "paid_amount": float(paid),
                "remaining_balance": None,
                "is_manual": is_manual,
                "locked": locked,
            }
        )

    if manual_total > financed:
        raise ValueError("Fixed installment amounts exceed the financed balance")

    remaining = financed - manual_total
    auto_amounts = _distribute_amount(remaining, len(unlocked_indices))

    for slot, idx in enumerate(unlocked_indices):
        amt = auto_amounts[slot]
        paid = money(Decimal(str(draft[idx]["paid_amount"])))
        draft[idx]["due_amount"] = float(amt)
        draft[idx]["remaining_balance"] = float(max(amt - paid, Decimal("0")))

    for i, row in enumerate(installment_rows):
        if draft[i]["due_amount"] is not None:
            continue
        amt = money(Decimal(str(row.get("due_amount", 0))))
        paid = money(Decimal(str(row.get("paid_amount", 0))))
        draft[i]["due_amount"] = float(amt)
        draft[i]["remaining_balance"] = float(max(amt - paid, Decimal("0")))

    for item in draft:
        item.pop("locked", None)

    return draft
