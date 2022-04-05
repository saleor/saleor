from decimal import Decimal
from functools import partial

import pytest
from prices import Money, fixed_discount, percentage_discount

from ...checkout import calculations
from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...discount import DiscountType, DiscountValueType
from ...plugins.manager import get_plugins_manager


@pytest.fixture
def checkout_with_fixed_discount(checkout_with_items_and_shipping, discount_info):
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

    value = Decimal(10)
    pre_discount_total = taxed_total.gross
    discount = partial(fixed_discount, discount=Money(value, checkout.currency))
    post_discount_total = discount(pre_discount_total)

    checkout.discounts.create(
        type=DiscountType.MANUAL,
        value=value,
        value_type=DiscountValueType.FIXED,
        amount=(pre_discount_total - post_discount_total),
        name="Discount name",
        translated_name="Zniżka",
        reason="Secoud discount reason",
    )
    return checkout


@pytest.fixture
def checkout_with_fixed_discount_for_more_then_total(
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
    discount = partial(fixed_discount, discount=Money(value, checkout.currency))
    post_discount_total = discount(pre_discount_total)

    checkout.discounts.create(
        value=value,
        value_type=DiscountValueType.FIXED,
        amount=(pre_discount_total - post_discount_total),
        name="Discount name",
        translated_name="Zniżka",
        reason="Secoud discount reason",
    )
    return checkout


@pytest.fixture
def checkout_with_percentage_discount(checkout_with_items_and_shipping, discount_info):
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

    value = Decimal(20)
    pre_discount_total = taxed_total.gross
    discount = partial(percentage_discount, percentage=value)
    post_discount_total = discount(pre_discount_total)

    checkout.discounts.create(
        type=DiscountType.MANUAL,
        value=value,
        value_type=DiscountValueType.PERCENTAGE,
        amount=(pre_discount_total - post_discount_total),
        name="Discount name",
        translated_name="Zniżka",
        reason="Secoud discount reason",
    )
    return checkout


@pytest.fixture
def checkout_with_100_percentage_discount(
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

    value = Decimal(100)
    pre_discount_total = taxed_total.gross
    discount = partial(percentage_discount, percentage=value)
    post_discount_total = discount(pre_discount_total)

    checkout.discounts.create(
        value=value,
        value_type=DiscountValueType.PERCENTAGE,
        amount=(pre_discount_total - post_discount_total),
        name="Discount name",
        translated_name="Zniżka",
        reason="Secoud discount reason",
    )
    return checkout
