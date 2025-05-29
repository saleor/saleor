from decimal import Decimal
from unittest.mock import patch

import pytest
from prices import Money, TaxedMoney

from .....core.postgres import FlatConcatSearchVector
from .....discount.models import OrderDiscount
from .....order import OrderStatus
from .....order.events import (
    draft_order_created_from_replace_event,
    fulfillment_fulfilled_items_event,
    order_added_products_event,
)
from .....order.models import Order, Payment
from .....order.search import prepare_order_search_vector_value
from .....plugins.manager import PluginsManager
from .....tax.calculations.order import update_order_prices_with_flat_rates
from ....tests.utils import get_graphql_content
from .shared_query_fragments import ORDER_FRAGMENT_WITH_WEBHOOK_RELATED_FIELDS

QUERY_ORDERS_WITH_WEBHOOK_RELATED_FIELDS = (
    ORDER_FRAGMENT_WITH_WEBHOOK_RELATED_FIELDS
    + """
query Orders {
  orders(first: 10) {
    edges {
      node {
        ...order
      }
    }
  }
}
"""
)


@patch(
    "saleor.order.calculations.update_order_prices_with_flat_rates",
    wraps=update_order_prices_with_flat_rates,
)
def test_query_orders_when_flat_rates_active(
    mocked_update_order_prices_with_flat_rates,
    order_with_lines,
    tax_configuration_flat_rates,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    order_with_lines.status = OrderStatus.UNCONFIRMED
    order_with_lines.should_refresh_prices = True
    order_with_lines.total_gross_amount = Decimal(0)
    order_with_lines.save()
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(QUERY_ORDERS_WITH_WEBHOOK_RELATED_FIELDS)

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["orders"]["edges"]) == 1
    order_with_lines.refresh_from_db()
    assert not order_with_lines.should_refresh_prices
    assert order_with_lines.total_gross_amount != Decimal(0)
    mocked_update_order_prices_with_flat_rates.assert_called_once()


@patch("saleor.order.calculations.calculate_prices")
@patch("saleor.order.calculations.update_order_prices_with_flat_rates")
def test_query_orders_for_order_with_lines_when_tax_app_active(
    mocked_update_order_prices_with_flat_rates,
    mocked_calculate_prices,
    order_with_lines,
    tax_configuration_tax_app,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    order_with_lines.status = OrderStatus.UNCONFIRMED
    order_with_lines.should_refresh_prices = True
    order_with_lines.total_gross_amount = Decimal(0)
    order_with_lines.save()
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(QUERY_ORDERS_WITH_WEBHOOK_RELATED_FIELDS)

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["orders"]["edges"]) == 1
    order_with_lines.refresh_from_db()

    assert order_with_lines.should_refresh_prices
    assert order_with_lines.total_gross_amount == Decimal(0)

    mocked_update_order_prices_with_flat_rates.assert_not_called()
    mocked_calculate_prices.assert_not_called()


@patch("saleor.order.calculations.calculate_prices")
@patch("saleor.order.calculations.update_order_prices_with_flat_rates")
def test_query_orders_for_order_with_granted_refunds_when_tax_app_active(
    mocked_update_order_prices_with_flat_rates,
    mocked_calculate_prices,
    order_with_lines,
    tax_configuration_tax_app,
    staff_api_client,
    permission_group_manage_orders,
    app,
):
    # given
    order = order_with_lines

    current_reason = "Granted refund reason."
    current_amount = Decimal("10.00")
    granted_refund = order.granted_refunds.create(
        amount_value=current_amount,
        currency=order.currency,
        reason=current_reason,
        app=app,
    )
    order_line = order.lines.first()
    granted_refund.lines.create(order_line=order_line, quantity=1)

    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.total_gross_amount = Decimal(0)
    order.save()
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(QUERY_ORDERS_WITH_WEBHOOK_RELATED_FIELDS)

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["orders"]["edges"]) == 1
    order.refresh_from_db()

    assert order.should_refresh_prices
    assert order.total_gross_amount == Decimal(0)

    mocked_update_order_prices_with_flat_rates.assert_not_called()
    mocked_calculate_prices.assert_not_called()


@patch("saleor.order.calculations.calculate_prices")
@patch("saleor.order.calculations.update_order_prices_with_flat_rates")
def test_query_orders_for_order_with_fulfillments_when_tax_app_active(
    mocked_update_order_prices_with_flat_rates,
    mocked_calculate_prices,
    order_with_lines,
    tax_configuration_tax_app,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    order = order_with_lines
    fulfillment = order.fulfillments.create()
    fulfillment.lines.create(order_line=order_with_lines.lines.first(), quantity=1)

    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.total_gross_amount = Decimal(0)
    order.save()
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(QUERY_ORDERS_WITH_WEBHOOK_RELATED_FIELDS)

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["orders"]["edges"]) == 1
    order.refresh_from_db()

    assert order.should_refresh_prices
    assert order.total_gross_amount == Decimal(0)

    mocked_update_order_prices_with_flat_rates.assert_not_called()
    mocked_calculate_prices.assert_not_called()


@patch("saleor.order.calculations.calculate_prices")
@patch("saleor.order.calculations.update_order_prices_with_flat_rates")
def test_query_orders_for_order_with_events_when_tax_app_active(
    mocked_update_order_prices_with_flat_rates,
    mocked_calculate_prices,
    order_with_lines,
    tax_configuration_tax_app,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    order = order_with_lines
    order_line = order.lines.first()
    fulfillment = order.fulfillments.create()
    fulfillment.lines.create(order_line=order_with_lines.lines.first(), quantity=1)
    fulfillment_fulfilled_items_event(
        order=order,
        user=staff_api_client.user,
        app=None,
        fulfillment_lines=fulfillment.lines.all(),
    )
    order_added_products_event(
        order=order, user=staff_api_client.user, app=None, order_lines=[order_line]
    )
    draft_order_created_from_replace_event(
        draft_order=order,
        original_order=order,
        user=staff_api_client.user,
        app=None,
        lines=[order_line],
    )

    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.total_gross_amount = Decimal(0)
    order.save()
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(QUERY_ORDERS_WITH_WEBHOOK_RELATED_FIELDS)

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["orders"]["edges"]) == 1
    order.refresh_from_db()

    assert order.should_refresh_prices
    assert order.total_gross_amount == Decimal(0)

    mocked_update_order_prices_with_flat_rates.assert_not_called()
    mocked_calculate_prices.assert_not_called()


@patch.object(PluginsManager, "excluded_shipping_methods_for_order")
def test_query_orders_with_active_filter_shipping_methods_webhook(
    mocked_webhook_handler,
    settings,
    order_with_lines,
    tax_configuration_flat_rates,
    staff_api_client,
    permission_group_manage_orders,
):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    # given
    order_with_lines.status = OrderStatus.UNCONFIRMED
    order_with_lines.should_refresh_prices = True
    order_with_lines.total_gross_amount = Decimal(0)
    order_with_lines.save()
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(QUERY_ORDERS_WITH_WEBHOOK_RELATED_FIELDS)

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["orders"]["edges"]) == 1
    order_with_lines.refresh_from_db()
    assert not order_with_lines.should_refresh_prices
    assert order_with_lines.total_gross_amount != Decimal(0)
    mocked_webhook_handler.assert_not_called()


ORDERS_QUERY_WITH_SEARCH = """
  query ($search: String) {
    orders(first: 10, search:$search) {
      totalCount
      edges {
        node {
          id
        }
      }
    }
  }
"""


@pytest.mark.parametrize(
    ("search_value", "count"),
    [
        ("discount name", 2),
        ("Some other", 1),
        ("translated", 1),
        ("test@mirumee.com", 1),
        ("Leslie", 1),
        ("Wade", 1),
        ("", 3),
        ("ExternalID", 1),
        ("SKU_A", 1),
    ],
)
def test_orders_query_with_search(
    search_value,
    count,
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    channel_USD,
    product,
    variant,
):
    # given
    orders = Order.objects.bulk_create(
        [
            Order(
                user=customer_user,
                user_email="test@mirumee.com",
                channel=channel_USD,
            ),
            Order(
                user_email="user_email1@example.com",
                channel=channel_USD,
            ),
            Order(
                user_email="user_email2@example.com",
                channel=channel_USD,
            ),
        ]
    )

    OrderDiscount.objects.bulk_create(
        [
            OrderDiscount(
                order=orders[0],
                name="Some discount name",
                value=Decimal("1"),
                amount_value=Decimal("1"),
                translated_name="translated",
            ),
            OrderDiscount(
                order=orders[2],
                name="Some other discount name",
                value=Decimal("10"),
                amount_value=Decimal("10"),
                translated_name="PL_name",
            ),
        ]
    )
    order_with_payment = orders[1]
    payment = Payment.objects.create(
        order=order_with_payment, psp_reference="ExternalID"
    )
    payment.transactions.create(gateway_response={}, is_success=True)

    order_with_orderline = orders[2]
    channel = order_with_orderline.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    unit_price = TaxedMoney(net=net, gross=gross)
    order_with_orderline.lines.create(
        product_name=str(product),
        variant_name=str(variant),
        product_sku=variant.sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=3,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * 3,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * 3,
        tax_rate=Decimal("0.23"),
    )
    for order in orders:
        order.search_vector = FlatConcatSearchVector(
            *prepare_order_search_vector_value(order)
        )
    Order.objects.bulk_update(orders, ["search_vector"])

    variables = {"search": search_value}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_WITH_SEARCH, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == count
