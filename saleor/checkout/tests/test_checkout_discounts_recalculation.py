from functools import partial
from unittest.mock import patch

import pytest
from prices import Money, percentage_discount

from ...checkout import calculations
from ...plugins.manager import get_plugins_manager
from ..fetch import fetch_checkout_info, fetch_checkout_lines
from ..utils import _recalculate_checkout_discounts, recalculate_checkout_discounts


@patch("saleor.checkout.utils._recalculate_checkout_discount")
@patch("saleor.checkout.utils._recalculate_checkout_discounts")
def test_recalculate_checkout_discounts_with_assigned_discounts(
    _recalculate_checkout_discounts_mock,
    _recalculate_checkout_discount_mock,
    checkout_with_fixed_discount_and_invalid_amount,
):
    # given
    checkout = checkout_with_fixed_discount_and_invalid_amount
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    # when
    recalculate_checkout_discounts(manager, checkout_info, lines, None)

    # then
    _recalculate_checkout_discounts_mock.assert_called_once_with(
        manager, checkout_info, lines, None
    )
    _recalculate_checkout_discount_mock.assert_not_called()


@patch("saleor.checkout.utils._recalculate_checkout_discount")
@patch("saleor.checkout.utils._recalculate_checkout_discounts")
def test_recalculate_checkout_discounts_without_assigned_discounts(
    _recalculate_checkout_discounts_mock,
    _recalculate_checkout_discount_mock,
    checkout_with_items_and_shipping,
):
    # given
    checkout = checkout_with_items_and_shipping
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    # when
    recalculate_checkout_discounts(manager, checkout_info, lines, None)

    # then
    _recalculate_checkout_discounts_mock.assert_not_called()
    _recalculate_checkout_discount_mock.assert_called_once_with(
        manager, checkout_info, lines, None
    )


@pytest.mark.skip("Not Implemented Yet")
def test_recalculate_checkout_discounts_fixed_discount(
    checkout_with_fixed_discount_and_invalid_amount,
):
    # given
    checkout = checkout_with_fixed_discount_and_invalid_amount
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    # when
    _recalculate_checkout_discounts(manager, checkout_info, lines, None)

    # then
    checkout.refresh_from_db()
    discount = checkout.discounts.get()
    assert discount.amount == Money(discount.value, checkout.currency)


@pytest.mark.skip("Not Implemented Yet")
def test_recalculate_checkout_discounts_fixed_discount_for_more_then_total(
    checkout_with_fixed_discount_for_more_then_total_and_invalid_amount, discount_info
):
    # given
    checkout = checkout_with_fixed_discount_for_more_then_total_and_invalid_amount
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

    # when
    _recalculate_checkout_discounts(manager, checkout_info, lines, None)

    # then
    checkout.refresh_from_db()
    discount = checkout.discounts.get()
    assert discount.amount == taxed_total.gross


@pytest.mark.skip("Not Implemented Yet")
def test_recalculate_checkout_discounts_percentage_discount(
    checkout_with_percentage_discount_and_invalid_amount, discount_info
):
    # given
    checkout = checkout_with_percentage_discount_and_invalid_amount
    discount = checkout.discounts.get()
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
    discount_partial = partial(percentage_discount, percentage=discount.value)
    post_discount_total = discount_partial(pre_discount_total)

    # when
    _recalculate_checkout_discounts(manager, checkout_info, lines, None)

    # then
    discount.refresh_from_db()
    assert (
        discount.amount
        == pre_discount_total - post_discount_total
        == round(pre_discount_total * 0.2, 2)
    )


@pytest.mark.skip("Not Implemented Yet")
def test_recalculate_checkout_discounts_100_percentage_discount(
    checkout_with_100_percentage_discount_and_invalid_amount, discount_info
):
    # given
    checkout = checkout_with_100_percentage_discount_and_invalid_amount
    discount = checkout.discounts.get()
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

    # when
    _recalculate_checkout_discounts(manager, checkout_info, lines, None)

    # then
    discount.refresh_from_db()
    assert discount.amount == pre_discount_total
