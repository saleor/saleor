from decimal import Decimal
from unittest import mock

from prices import Money

from ....shipping.interface import ShippingMethodData
from ...webhooks.exclude_shipping import excluded_shipping_methods_for_order


@mock.patch("saleor.order.webhooks.exclude_shipping._get_excluded_shipping_data")
def test_excluded_shipping_methods_for_order_run_webhook_when_shipping_methods_provided(
    mocked_get_excluded_shipping_data, draft_order
):
    # given
    shipping_method = ShippingMethodData(
        id="123",
        price=Money(Decimal("10.59"), "USD"),
    )

    non_empty_shipping_methods = [shipping_method]

    # when
    excluded_shipping_methods_for_order(
        order=draft_order,
        available_shipping_methods=non_empty_shipping_methods,
        allow_replica=False,
        requestor=None,
    ).get()

    # then
    mocked_get_excluded_shipping_data.assert_called_once()


@mock.patch("saleor.order.webhooks.exclude_shipping._get_excluded_shipping_data")
def test_excluded_shipping_methods_for_order_dont_run_webhook_on_missing_shipping_methods(
    mocked_get_excluded_shipping_data, draft_order
):
    # given
    empty_shipping_methods = []

    # when
    excluded_shipping_methods_for_order(
        order=draft_order,
        available_shipping_methods=empty_shipping_methods,
        allow_replica=False,
        requestor=None,
    ).get()

    # then
    mocked_get_excluded_shipping_data.assert_not_called()
