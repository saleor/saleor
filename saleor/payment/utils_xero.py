from decimal import Decimal, InvalidOperation


def get_reconciled_amount(response: dict) -> Decimal:
    raw = response.get("reconciledAmount")
    if raw is None:
        return Decimal(0)
    try:
        return Decimal(str(raw))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(0)
