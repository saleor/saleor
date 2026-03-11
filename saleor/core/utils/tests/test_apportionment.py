from decimal import Decimal

import pytest

from saleor.core.utils.apportionment import distribute_cost_proportionally, hamilton


def test_distribute_even_split():
    result = distribute_cost_proportionally(
        Decimal("90.00"), [Decimal(100), Decimal(100), Decimal(100)], "GBP"
    )
    assert result == [Decimal("30.00"), Decimal("30.00"), Decimal("30.00")]
    assert sum(result) == Decimal("90.00")


def test_distribute_thirds_remainder_goes_to_largest_fraction():
    result = distribute_cost_proportionally(
        Decimal("100.00"), [Decimal(1), Decimal(1), Decimal(1)], "GBP"
    )
    assert sum(result) == Decimal("100.00")
    assert sorted(result) == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]


def test_distribute_uneven_weights():
    result = distribute_cost_proportionally(
        Decimal("333.00"),
        [Decimal(400), Decimal(350), Decimal(250)],
        "GBP",
    )
    assert sum(result) == Decimal("333.00")
    assert result[0] == Decimal("133.20")
    assert result[1] == Decimal("116.55")
    assert result[2] == Decimal("83.25")


def test_distribute_zero_total():
    result = distribute_cost_proportionally(
        Decimal(0), [Decimal(100), Decimal(200)], "GBP"
    )
    assert result == [Decimal(0), Decimal(0)]


def test_distribute_zero_weights():
    result = distribute_cost_proportionally(
        Decimal(100), [Decimal(0), Decimal(0)], "GBP"
    )
    assert result == [Decimal(0), Decimal(0)]


def test_distribute_single_bucket_gets_total():
    result = distribute_cost_proportionally(
        Decimal("62.56"), [Decimal("125.12")], "GBP"
    )
    assert result == [Decimal("62.56")]


def test_distribute_two_buckets_sum_exact():
    result = distribute_cost_proportionally(
        Decimal("12.20"), [Decimal("75.28"), Decimal("37.64")], "GBP"
    )
    assert sum(result) == Decimal("12.20")


def test_distribute_jpy_zero_decimal_currency():
    result = distribute_cost_proportionally(
        Decimal(1000), [Decimal(1), Decimal(1), Decimal(1)], "JPY"
    )
    assert sum(result) == Decimal(1000)
    assert all(r == int(r) for r in result)
    assert sorted(result) == [Decimal(333), Decimal(333), Decimal(334)]


def test_distribute_negative_total_raises():
    with pytest.raises(ValueError, match="non-negative"):
        distribute_cost_proportionally(
            Decimal("-10.00"), [Decimal(1), Decimal(1)], "GBP"
        )


def test_distribute_wildly_different_weights():
    result = distribute_cost_proportionally(
        Decimal("100.00"), [Decimal("0.001"), Decimal(999999)], "GBP"
    )
    assert sum(result) == Decimal("100.00")
    assert result[0] == Decimal("0.00")
    assert result[1] == Decimal("100.00")


def test_distribute_many_small_weights():
    weights = [Decimal(1)] * 7
    result = distribute_cost_proportionally(Decimal("10.00"), weights, "GBP")
    assert sum(result) == Decimal("10.00")
    assert all(r >= Decimal("1.42") for r in result)


def test_hamilton_docstring_example():
    result = hamilton({"A": 5, "B": 10, "C": 40}, total=10)
    assert result == {"A": 1, "B": 2, "C": 7}


def test_hamilton_remainder_allocated_by_largest_fraction():
    # 1/3 each, total=10 -> floors are 3,3,3, remainder=1 goes to whichever has highest fraction
    result = hamilton({"A": 1, "B": 1, "C": 1}, total=10)
    assert sum(result.values()) == 10
    assert all(v >= 3 for v in result.values())


def test_hamilton_total_zero():
    assert hamilton({"A": 5, "B": 10}, total=0) == {"A": 0, "B": 0}


def test_hamilton_empty_weights():
    assert hamilton({}, total=10) == {}


def test_hamilton_zero_weights():
    assert hamilton({"A": 0, "B": 0}, total=10) == {"A": 0, "B": 0}


def test_hamilton_total_greater_than_weight_sum():
    # total=100, w_sum=3 — should not raise, should allocate all 100
    result = hamilton({"A": 1, "B": 1, "C": 1}, total=100)
    assert sum(result.values()) == 100
