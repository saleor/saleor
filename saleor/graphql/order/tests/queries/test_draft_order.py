from decimal import Decimal
from unittest.mock import patch

from .....order import OrderStatus
from .....order.events import (
    draft_order_created_from_replace_event,
    fulfillment_fulfilled_items_event,
    order_added_products_event,
)
from .....order.models import Order
from .....plugins.manager import PluginsManager
from .....tax.calculations.order import update_order_prices_with_flat_rates
from ....tests.utils import assert_no_permission, get_graphql_content
from .shared_query_fragments import ORDER_FRAGMENT_WITH_WEBHOOK_RELATED_FIELDS

DRAFT_ORDER_QUERY = """
    query DraftOrdersQuery {
        draftOrders(first: 10) {
            edges {
                node {
                    id
                    number
                }
            }
        }
    }
"""


def test_draft_order_query(
    staff_api_client, permission_group_manage_orders, order, draft_order_list
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_QUERY)

    # then
    edges = get_graphql_content(response)["data"]["draftOrders"]["edges"]

    assert len(edges) == Order.objects.drafts().count()


def test_query_draft_orders_by_user_with_access_to_all_channels(
    staff_api_client,
    permission_group_all_perms_all_channels,
    draft_orders_in_different_channels,
):
    # given
    permission_group_all_perms_all_channels.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_QUERY)

    # then
    edges = get_graphql_content(response)["data"]["draftOrders"]["edges"]

    assert len(edges) == len(draft_orders_in_different_channels)


def test_query_draft_orders_by_user_with_restricted_access_to_channels(
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    draft_orders_in_different_channels,
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_QUERY)

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["draftOrders"]["edges"]) == 1
    assert content["data"]["draftOrders"]["edges"][0]["node"]["number"] == str(
        draft_orders_in_different_channels[0].number
    )


def test_query_draft_orders_by_user_with_restricted_access_to_channels_no_acc_channels(
    staff_api_client,
    permission_group_all_perms_without_any_channel,
    draft_orders_in_different_channels,
):
    # given
    permission_group_all_perms_without_any_channel.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_QUERY)

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["draftOrders"]["edges"]) == 0


def test_query_draft_orders_by_app(
    app_api_client, permission_manage_orders, draft_orders_in_different_channels
):
    # when
    response = app_api_client.post_graphql(
        DRAFT_ORDER_QUERY, permissions=(permission_manage_orders,)
    )

    # then
    edges = get_graphql_content(response)["data"]["draftOrders"]["edges"]

    assert len(edges) == len(draft_orders_in_different_channels)


def test_query_draft_orders_by_customer(
    user_api_client, draft_orders_in_different_channels
):
    # when
    response = user_api_client.post_graphql(DRAFT_ORDER_QUERY)

    # then
    assert_no_permission(response)


QUERY_DRAFT_ORDERS_WITH_WEBHOOK_RELATED_FIELDS = (
    ORDER_FRAGMENT_WITH_WEBHOOK_RELATED_FIELDS
    + """
query DraftOrders {
  draftOrders(first: 10) {
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
    order_with_lines.status = OrderStatus.DRAFT
    order_with_lines.should_refresh_prices = True
    order_with_lines.total_gross_amount = Decimal(0)
    order_with_lines.save()
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(
        QUERY_DRAFT_ORDERS_WITH_WEBHOOK_RELATED_FIELDS
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["draftOrders"]["edges"]) == 1
    order_with_lines.refresh_from_db()
    assert not order_with_lines.should_refresh_prices
    assert order_with_lines.total_gross_amount != Decimal(0)
    mocked_update_order_prices_with_flat_rates.assert_called_once()


@patch("saleor.order.calculations._recalculate_prices")
@patch("saleor.order.calculations.update_order_prices_with_flat_rates")
def test_query_orders_for_order_with_lines_when_tax_app_active(
    mocked_update_order_prices_with_flat_rates,
    mocked__recalculate_prices,
    order_with_lines,
    tax_configuration_tax_app,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    order_with_lines.status = OrderStatus.DRAFT
    order_with_lines.should_refresh_prices = True
    order_with_lines.total_gross_amount = Decimal(0)
    order_with_lines.save()
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(
        QUERY_DRAFT_ORDERS_WITH_WEBHOOK_RELATED_FIELDS
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["draftOrders"]["edges"]) == 1
    order_with_lines.refresh_from_db()

    assert order_with_lines.should_refresh_prices
    assert order_with_lines.total_gross_amount == Decimal(0)

    mocked_update_order_prices_with_flat_rates.assert_not_called()
    mocked__recalculate_prices.assert_not_called()


@patch("saleor.order.calculations._recalculate_prices")
@patch("saleor.order.calculations.update_order_prices_with_flat_rates")
def test_query_orders_for_order_with_granted_refunds_when_tax_app_active(
    mocked_update_order_prices_with_flat_rates,
    mocked__recalculate_prices,
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

    order.status = OrderStatus.DRAFT
    order.should_refresh_prices = True
    order.total_gross_amount = Decimal(0)
    order.save()
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(
        QUERY_DRAFT_ORDERS_WITH_WEBHOOK_RELATED_FIELDS
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["draftOrders"]["edges"]) == 1
    order.refresh_from_db()

    assert order.should_refresh_prices
    assert order.total_gross_amount == Decimal(0)

    mocked_update_order_prices_with_flat_rates.assert_not_called()
    mocked__recalculate_prices.assert_not_called()


@patch("saleor.order.calculations._recalculate_prices")
@patch("saleor.order.calculations.update_order_prices_with_flat_rates")
def test_query_orders_for_order_with_fulfillments_when_tax_app_active(
    mocked_update_order_prices_with_flat_rates,
    mocked__recalculate_prices,
    order_with_lines,
    tax_configuration_tax_app,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    order = order_with_lines
    fulfillment = order.fulfillments.create()
    fulfillment.lines.create(order_line=order_with_lines.lines.first(), quantity=1)

    order.status = OrderStatus.DRAFT
    order.should_refresh_prices = True
    order.total_gross_amount = Decimal(0)
    order.save()
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(
        QUERY_DRAFT_ORDERS_WITH_WEBHOOK_RELATED_FIELDS
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["draftOrders"]["edges"]) == 1
    order.refresh_from_db()

    assert order.should_refresh_prices
    assert order.total_gross_amount == Decimal(0)

    mocked_update_order_prices_with_flat_rates.assert_not_called()
    mocked__recalculate_prices.assert_not_called()


@patch("saleor.order.calculations._recalculate_prices")
@patch("saleor.order.calculations.update_order_prices_with_flat_rates")
def test_query_orders_for_order_with_events_when_tax_app_active(
    mocked_update_order_prices_with_flat_rates,
    mocked__recalculate_prices,
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

    order.status = OrderStatus.DRAFT
    order.should_refresh_prices = True
    order.total_gross_amount = Decimal(0)
    order.save()
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(
        QUERY_DRAFT_ORDERS_WITH_WEBHOOK_RELATED_FIELDS
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["draftOrders"]["edges"]) == 1
    order.refresh_from_db()

    assert order.should_refresh_prices
    assert order.total_gross_amount == Decimal(0)

    mocked_update_order_prices_with_flat_rates.assert_not_called()
    mocked__recalculate_prices.assert_not_called()


@patch.object(PluginsManager, "excluded_shipping_methods_for_order")
def test_query_draft_orders_with_active_filter_shipping_methods_webhook(
    mocked_webhook_handler,
    settings,
    order_with_lines,
    tax_configuration_flat_rates,
    staff_api_client,
    permission_group_manage_orders,
):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    # given
    order_with_lines.status = OrderStatus.DRAFT
    order_with_lines.should_refresh_prices = True
    order_with_lines.total_gross_amount = Decimal(0)
    order_with_lines.save()
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(
        QUERY_DRAFT_ORDERS_WITH_WEBHOOK_RELATED_FIELDS
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["draftOrders"]["edges"]) == 1
    order_with_lines.refresh_from_db()
    assert not order_with_lines.should_refresh_prices
    assert order_with_lines.total_gross_amount != Decimal(0)
    mocked_webhook_handler.assert_not_called()
