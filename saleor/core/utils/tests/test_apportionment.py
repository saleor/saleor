from saleor.core.utils.apportionment import hamilton


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
