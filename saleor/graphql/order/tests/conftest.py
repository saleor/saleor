from decimal import Decimal
from functools import partial

import pytest
from prices import Money, fixed_discount, percentage_discount

from ....discount import DiscountValueType


@pytest.fixture
def draft_order_with_many_fixed_discount_order(draft_order_with_fixed_discount_order):
    value = Decimal("10")
    draft_order = draft_order_with_fixed_discount_order
    previous_total = draft_order.total
    discount = partial(fixed_discount, discount=Money(value, draft_order.currency))
    draft_order.total = discount(draft_order.total)
    draft_order.discounts.create(
        value_type=DiscountValueType.FIXED,
        value=value,
        reason="Secoud discount reason",
        amount=(previous_total - draft_order.total).gross,
    )
    draft_order.save()
    return draft_order


@pytest.fixture
def draft_order_with_fixed_and_percentage_discount_order(
    draft_order_with_fixed_discount_order,
):
    value = Decimal("10")
    draft_order = draft_order_with_fixed_discount_order
    previous_total = draft_order.total
    discount = partial(percentage_discount, percentage=value)
    draft_order.total = discount(draft_order.total)
    draft_order.discounts.create(
        value_type=DiscountValueType.PERCENTAGE,
        value=value,
        reason="Secoud discount reason",
        amount=(previous_total - draft_order.total).gross,
    )
    draft_order.save()
    return draft_order


@pytest.fixture
def draft_order_with_percentage_and_fixed_discount_order(
    draft_order,
):
    value = Decimal("10")
    discount = partial(percentage_discount, percentage=value)
    draft_order.total = discount(draft_order.total)
    draft_order.discounts.create(
        value_type=DiscountValueType.PERCENTAGE,
        value=value,
        reason="Secoud discount reason",
        amount=(draft_order.undiscounted_total - draft_order.total).gross,
    )

    value = Decimal("20")
    previous_total = draft_order.total
    discount = partial(fixed_discount, discount=Money(value, draft_order.currency))
    draft_order.total = discount(draft_order.total)
    draft_order.discounts.create(
        value_type=DiscountValueType.FIXED,
        value=value,
        reason="Discount reason",
        amount=(previous_total - draft_order.total).gross,
    )

    draft_order.save()
    return draft_order


@pytest.fixture
def draft_order_with_many_percentage_discount_order(
    draft_order,
):
    value = Decimal("10")
    discount = partial(percentage_discount, percentage=value)
    draft_order.total = discount(draft_order.total)
    draft_order.discounts.create(
        value_type=DiscountValueType.PERCENTAGE,
        value=value,
        reason="Secoud discount reason",
        amount=(draft_order.undiscounted_total - draft_order.total).gross,
    )

    value = Decimal("20")
    previous_total = draft_order.total
    discount = partial(percentage_discount, percentage=value)
    draft_order.total = discount(draft_order.total)
    draft_order.discounts.create(
        value_type=DiscountValueType.PERCENTAGE,
        value=value,
        reason="Discount reason",
        amount=(previous_total - draft_order.total).gross,
    )

    draft_order.save()
    return draft_order
