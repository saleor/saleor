import pytest

from ...mutations.utils import (
    CheckoutLineData,
    group_quantity_and_custom_prices_by_variants,
)


@pytest.mark.parametrize(
    "lines, expected",
    [
        (
            [
                {"quantity": 6, "variant_id": "abc", "price": 1.22},
                {"quantity": 6, "variant_id": "abc"},
                {"quantity": 1, "variant_id": "def", "price": 33.2},
                {"quantity": 1, "variant_id": "def", "price": 10},
            ],
            [
                CheckoutLineData(
                    quantity=12,
                    quantity_to_update=True,
                    custom_price=1.22,
                    custom_price_to_update=True,
                ),
                CheckoutLineData(
                    quantity=2,
                    quantity_to_update=True,
                    custom_price=10,
                    custom_price_to_update=True,
                ),
            ],
        ),
        (
            [
                {"quantity": 8, "variant_id": "ghi"},
                {"quantity": 2, "variant_id": "ghi"},
                {"quantity": 6, "variant_id": "abc"},
                {"quantity": 1, "variant_id": "def"},
                {"quantity": 6, "variant_id": "abc"},
                {"quantity": 1, "variant_id": "def"},
                {"quantity": 8, "variant_id": "ghi"},
                {"quantity": 2, "variant_id": "ghi"},
                {"quantity": 922, "variant_id": "xyz"},
                {"quantity": 6, "variant_id": "abc"},
                {"quantity": 1, "variant_id": "def"},
                {"quantity": 6, "variant_id": "abc"},
                {"quantity": 1, "variant_id": "def"},
                {"quantity": 1000, "variant_id": "jkl"},
                {"quantity": 999, "variant_id": "zzz"},
            ],
            [
                CheckoutLineData(
                    quantity=quantity,
                    quantity_to_update=True,
                    custom_price=None,
                    custom_price_to_update=False,
                )
                for quantity in [20, 24, 4, 922, 1000, 999]
            ],
        ),
        (
            [
                {"quantity": 100, "variant_id": name}
                for name in (l1 + l2 for l1 in "abcdef" for l2 in "ghijkl")
            ],
            [
                CheckoutLineData(
                    quantity=100,
                    quantity_to_update=True,
                    custom_price=None,
                    custom_price_to_update=False,
                )
            ]
            * 36,
        ),
    ],
)
def test_group_by_variants(lines, expected):
    assert expected == group_quantity_and_custom_prices_by_variants(lines)
