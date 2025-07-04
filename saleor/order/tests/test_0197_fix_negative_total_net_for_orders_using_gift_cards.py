import importlib
from decimal import Decimal

import pytest
from django.apps import apps

# Import with importlib due to inability to import the normal way a module having name
# starting with a number.
migrations = importlib.import_module(
    "saleor.order.migrations.0197_fix_negative_total_net_for_orders_using_gift_cards"
)


@pytest.mark.parametrize(
    (
        "initial_total_net_amount",
        "initial_total_gross_amount",
        "has_gift_cards",
        "expected_total_net_amount",
        "expected_total_gross_amount",
    ),
    [
        ("-2.00", "0.00", True, "0.00", "0.00"),
        ("0.00", "0.00", True, "0.00", "0.00"),
        ("1.00", "2.00", True, "1.00", "2.00"),
        ("-2.00", "0.00", False, "-2.00", "0.00"),
        ("0.00", "0.00", False, "0.00", "0.00"),
        ("1.00", "2.00", False, "1.00", "2.00"),
    ],
)
def test_fix_negative_total_net_for_orders_using_gift_cards_task(
    request,
    initial_total_net_amount,
    initial_total_gross_amount,
    has_gift_cards,
    expected_total_net_amount,
    expected_total_gross_amount,
):
    if has_gift_cards:
        order = request.getfixturevalue("order_with_gift_card")
    else:
        order = request.getfixturevalue("order")

    order.total_net_amount = Decimal(initial_total_net_amount)
    order.total_gross_amount = Decimal(initial_total_gross_amount)
    order.save(update_fields=["total_net_amount", "total_gross_amount"])

    migrations.fix_negative_total_net_for_orders_using_gift_cards(apps, None)

    order.refresh_from_db(fields=["total_net_amount", "total_gross_amount"])

    assert order.total_net_amount == Decimal(expected_total_net_amount)
    assert order.total_gross_amount == Decimal(expected_total_gross_amount)
