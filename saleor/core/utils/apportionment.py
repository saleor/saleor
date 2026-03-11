from decimal import ROUND_DOWN, Decimal

from babel.numbers import get_currency_precision


def distribute_cost_proportionally(
    total: Decimal,
    weights: list[Decimal],
    currency: str,
) -> list[Decimal]:
    """Split a monetary total across buckets proportional to weights, summing exactly.

    Uses Hamilton's method (largest-remainder): floor each share to the
    currency's smallest unit, then hand out leftover units to the entries
    whose fractional remainders were largest.

    https://en.wikipedia.org/wiki/Mathematics_of_apportionment
    """
    if total < 0:
        raise ValueError("total must be non-negative")

    weight_sum = sum(weights)
    if not weight_sum or not total:
        return [Decimal(0)] * len(weights)

    precision = get_currency_precision(currency)
    unit = Decimal(10) ** -precision

    exact = [total * w / weight_sum for w in weights]
    floored = [e.quantize(unit, rounding=ROUND_DOWN) for e in exact]

    remainders = [e - f for e, f in zip(exact, floored, strict=False)]
    shortfall = total - sum(floored)
    units = int((shortfall / unit).to_integral_value())

    indices = sorted(range(len(remainders)), key=lambda i: remainders[i], reverse=True)
    for i in indices[:units]:
        floored[i] += unit

    return floored


def hamilton(weights: dict, total: int) -> dict:
    """Distribute total across keys proportional to weights using Hamilton's method.

    https://en.wikipedia.org/wiki/Mathematics_of_apportionment

    eg. weights={A: 5, B: 10, C: 40}, total=10 -> {A: 1, B: 2, C: 7}
    """
    if not weights or total == 0:
        return dict.fromkeys(weights, 0)
    w_sum = sum(weights.values())
    if w_sum == 0:
        return dict.fromkeys(weights, 0)
    quotas = {k: total * v / w_sum for k, v in weights.items()}
    result = {k: int(q) for k, q in quotas.items()}
    remainder = total - sum(result.values())
    for k, _ in sorted(quotas.items(), key=lambda x: x[1] % 1, reverse=True)[
        :remainder
    ]:
        result[k] += 1
    assert sum(result.values()) == total
    return result
