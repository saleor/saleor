from unittest import mock

import pytest
from promise import Promise

from .....order import OrderStatus
from .....order.webhooks.exclude_shipping import ExcludedShippingMethod
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

ORDER_QUERY_SHIPPING_METHOD = """
query OrderQuery($id: ID) {
  order(id: $id) {
    shippingMethods {
      id
      name
      active
      message
    }
    availableShippingMethods {
      id
      name
      active
      message
    }
  }
}
"""


@mock.patch(
    "saleor.order.webhooks.exclude_shipping.excluded_shipping_methods_for_order"
)
def test_order_shipping_methods(
    mocked_webhook,
    staff_api_client,
    order_with_lines,
    permission_group_manage_orders,
    settings,
):
    # given
    order_with_lines.status = OrderStatus.UNCONFIRMED
    order_with_lines.save(update_fields=["status"])
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    webhook_reason = "spanish-inquisition"
    excluded_shipping_method_id = str(order_with_lines.shipping_method.id)
    mocked_webhook.return_value = Promise.resolve(
        [ExcludedShippingMethod(excluded_shipping_method_id, webhook_reason)]
    )
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    # when
    response = staff_api_client.post_graphql(
        ORDER_QUERY_SHIPPING_METHOD,
        variables={"id": to_global_id_or_none(order_with_lines)},
    )
    content = get_graphql_content(response)
    order_data = content["data"]["order"]

    shipping_methods = order_data["shippingMethods"]
    # then
    assert len(shipping_methods) == 1
    assert not shipping_methods[0]["active"]
    assert shipping_methods[0]["message"] == webhook_reason


@mock.patch(
    "saleor.order.webhooks.exclude_shipping.excluded_shipping_methods_for_order"
)
def test_draft_order_shipping_methods(
    mocked_webhook,
    staff_api_client,
    order_with_lines,
    permission_group_manage_orders,
    settings,
):
    # given
    order_with_lines.status = OrderStatus.DRAFT
    order_with_lines.save(update_fields=["status"])
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    webhook_reason = "spanish-inquisition"
    excluded_shipping_method_id = str(order_with_lines.shipping_method.id)
    mocked_webhook.return_value = Promise.resolve(
        [ExcludedShippingMethod(excluded_shipping_method_id, webhook_reason)]
    )
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(
        ORDER_QUERY_SHIPPING_METHOD,
        variables={"id": to_global_id_or_none(order_with_lines)},
    )
    content = get_graphql_content(response)
    order_data = content["data"]["order"]

    shipping_methods = order_data["shippingMethods"]
    # then
    assert len(shipping_methods) == 1
    assert not shipping_methods[0]["active"]
    assert shipping_methods[0]["message"] == webhook_reason


@pytest.mark.parametrize(
    "order_status",
    [
        OrderStatus.UNFULFILLED,
        OrderStatus.PARTIALLY_FULFILLED,
        OrderStatus.FULFILLED,
        OrderStatus.CANCELED,
        OrderStatus.EXPIRED,
        OrderStatus.RETURNED,
        OrderStatus.PARTIALLY_RETURNED,
    ],
)
@mock.patch(
    "saleor.order.webhooks.exclude_shipping.excluded_shipping_methods_for_order"
)
def test_order_shipping_methods_skips_sync_webhook_for_non_editable_statuses(
    mocked_webhook,
    order_status,
    staff_api_client,
    order_with_lines,
    permission_group_manage_orders,
    settings,
):
    # given
    order_with_lines.status = order_status
    order_with_lines.save(update_fields=["status"])
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(
        ORDER_QUERY_SHIPPING_METHOD,
        variables={"id": to_global_id_or_none(order_with_lines)},
    )
    content = get_graphql_content(response)
    order_data = content["data"]["order"]

    shipping_methods = order_data["shippingMethods"]

    # then
    assert not mocked_webhook.called
    assert len(shipping_methods) == 1
    assert shipping_methods[0]["active"]


@pytest.mark.parametrize(
    ("webhook_response", "expected_count"),
    [
        (lambda s: [ExcludedShippingMethod(str(s.id), "")], 0),
        (lambda s: [], 1),
    ],
)
@mock.patch(
    "saleor.order.webhooks.exclude_shipping.excluded_shipping_methods_for_order"
)
def test_order_available_shipping_methods(
    mocked_webhook,
    staff_api_client,
    order_with_lines,
    permission_group_manage_orders,
    settings,
    webhook_response,
    expected_count,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    order_with_lines.status = OrderStatus.UNCONFIRMED
    order_with_lines.save(update_fields=["status"])
    shipping_method = order_with_lines.shipping_method

    def respond(*args, **kwargs):
        return Promise.resolve(webhook_response(shipping_method))

    mocked_webhook.side_effect = respond
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    # when
    response = staff_api_client.post_graphql(
        ORDER_QUERY_SHIPPING_METHOD,
        variables={"id": to_global_id_or_none(order_with_lines)},
    )
    content = get_graphql_content(response)
    order_data = content["data"]["order"]

    # then
    assert len(order_data["availableShippingMethods"]) == expected_count
