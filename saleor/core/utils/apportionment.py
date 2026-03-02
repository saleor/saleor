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
