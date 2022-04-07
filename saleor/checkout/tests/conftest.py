from decimal import Decimal

import pytest
from prices import Money

from ...checkout import calculations
from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...discount import DiscountType, DiscountValueType
from ...plugins.manager import get_plugins_manager


@pytest.fixture
def checkout_with_fixed_discount_and_invalid_amount(
    checkout_with_items_and_shipping, discount_info
):
    checkout = checkout_with_items_and_shipping
    value = Decimal(10)
    checkout.discounts.create(
        type=DiscountType.MANUAL,
        value=value,
        value_type=DiscountValueType.FIXED,
        amount=Money(0, checkout.currency),
        name="Discount name",
        translated_name="Zniżka",
        reason="Secoud discount reason",
    )
    return checkout


@pytest.fixture
def checkout_with_fixed_discount_for_more_then_total_and_invalid_amount(
    checkout_with_items_and_shipping, discount_info
):
    checkout = checkout_with_items_and_shipping
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    taxed_total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
        discounts=[discount_info],
    )

    pre_discount_total = taxed_total.gross
    value = Decimal(pre_discount_total.amount + 10)

    checkout.discounts.create(
        value=value,
        value_type=DiscountValueType.FIXED,
        amount=Money(0, checkout.currency),
        name="Discount name",
        translated_name="Zniżka",
        reason="Secoud discount reason",
    )
    return checkout


@pytest.fixture
def checkout_with_percentage_discount_and_invalid_amount(
    checkout_with_items_and_shipping,
):
    checkout = checkout_with_items_and_shipping
    value = Decimal(20)
    checkout.discounts.create(
        type=DiscountType.MANUAL,
        value=value,
        value_type=DiscountValueType.PERCENTAGE,
        amount=Money(0, checkout.currency),
        name="Discount name",
        translated_name="Zniżka",
        reason="Secoud discount reason",
    )
    return checkout


@pytest.fixture
def checkout_with_100_percentage_discount_and_invalid_amount(
    checkout_with_items_and_shipping,
):
    checkout = checkout_with_items_and_shipping
    value = Decimal(100)
    checkout.discounts.create(
        value=value,
        value_type=DiscountValueType.PERCENTAGE,
        amount=Money(0, checkout.currency),
        name="Discount name",
        translated_name="Zniżka",
        reason="Secoud discount reason",
    )
    return checkout
