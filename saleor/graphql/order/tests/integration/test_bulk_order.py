import copy
from decimal import Decimal
from unittest.mock import patch

import graphene
import pytest

from saleor.order import OrderEvents
from saleor.order.models import Order, OrderLine
from saleor.payment.models import TransactionItem

from .....order.calculations import fetch_order_prices_if_expired
from .....plugins.manager import get_plugins_manager
from ....discount.enums import DiscountValueTypeEnum
from ....order.enums import OrderStatusEnum
from ....payment.enums import TransactionActionEnum
from ....payment.tests.mutations.test_transaction_request_action import (
    MUTATION_TRANSACTION_REQUEST_ACTION,
)
from ....tests.utils import get_graphql_content
from ...enums import StockUpdatePolicyEnum
from ..mutations.test_draft_order_complete import DRAFT_ORDER_COMPLETE_MUTATION
from ..mutations.test_fulfillment_return_products import ORDER_FULFILL_RETURN_MUTATION
from ..mutations.test_order_bulk_create import (
    ORDER_BULK_CREATE,
    order_bulk_input,  # noqa: F401
)
from ..mutations.test_order_fulfill import ORDER_FULFILL_MUTATION


@pytest.mark.integration
def test_create_order_from_imported_draft_order(
    staff_api_client,
    permission_manage_orders_import,
    permission_group_manage_orders,
    order_bulk_input,  # noqa: F811
    product,
    channel_USD,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_orders_import)
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    # import draft order from external system
    order = order_bulk_input
    order["status"] = OrderStatusEnum.DRAFT.name
    order["deliveryMethod"] = None
    order["channel"] = channel_USD.slug
    order["currency"] = "USD"
    order["lines"][0]["variantId"] = graphene.Node.to_global_id(
        "ProductVariant", product.variants.first().id
    )
    order["lines"][0]["isShippingRequired"] = False
    order["fulfillments"] = []
    order["transactions"] = []
    order["invoices"] = []
    order["discounts"] = []

    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.UPDATE.name,
    }

    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)
    order_id = content["data"]["orderBulkCreate"]["results"][0]["order"]["id"]

    # complete draft order
    staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, {"id": order_id})

    # then
    db_order = Order.objects.get()
    assert db_order.status == OrderStatusEnum.UNFULFILLED.name.lower()


@pytest.mark.integration
def test_fulfill_imported_order(
    staff_api_client,
    permission_manage_orders_import,
    permission_group_manage_orders,
    order_bulk_input,  # noqa: F811
    product,
    warehouse,
    channel_USD,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_orders_import)
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    # import unfulfilled order from external system
    order = order_bulk_input
    order["status"] = OrderStatusEnum.UNFULFILLED.name
    order["deliveryMethod"] = None
    order["channel"] = channel_USD.slug
    order["currency"] = "USD"
    order["lines"][0]["variantId"] = graphene.Node.to_global_id(
        "ProductVariant", product.variants.first().id
    )
    order["lines"][0]["isShippingRequired"] = False
    order["fulfillments"] = []
    order["transactions"] = []
    order["invoices"] = []
    order["discounts"] = []

    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.UPDATE.name,
    }

    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderBulkCreate"]["results"][0]["order"]
    order_id = data["id"]
    order_line_id = data["lines"][0]["id"]
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)

    # fulfill order
    variables = {
        "order": order_id,
        "input": {
            "lines": [
                {
                    "orderLineId": order_line_id,
                    "stocks": [{"quantity": 5, "warehouse": warehouse_id}],
                },
            ],
        },
    }
    staff_api_client.post_graphql(ORDER_FULFILL_MUTATION, variables)

    # then
    db_order = Order.objects.get()
    assert db_order.status == OrderStatusEnum.FULFILLED.name.lower()


@pytest.mark.integration
@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
def test_return_and_refund_imported_order(
    mocked_is_active,
    staff_api_client,
    permission_manage_orders_import,
    permission_group_manage_orders,
    permission_manage_payments,
    order_bulk_input,  # noqa: F811
    product,
    warehouse,
    channel_USD,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import, permission_manage_payments
    )
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    # import fulfilled order from external system
    order = order_bulk_input
    variant_id = graphene.Node.to_global_id(
        "ProductVariant", product.variants.first().id
    )
    order["status"] = OrderStatusEnum.FULFILLED.name
    order["deliveryMethod"] = None
    order["channel"] = channel_USD.slug
    order["currency"] = "USD"
    order["lines"][0]["variantId"] = variant_id
    order["lines"][0]["isShippingRequired"] = False
    order["fulfillments"][0]["lines"][0]["variantId"] = variant_id
    order["transactions"][0]["amountAuthorized"] = {
        "amount": Decimal(0),
        "currency": "USD",
    }
    order["transactions"][0]["amountCharged"] = {
        "amount": Decimal(120),
        "currency": "USD",
    }
    order["transactions"][0]["availableActions"] = [TransactionActionEnum.REFUND.name]
    order["invoices"] = []
    order["discounts"] = []

    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.UPDATE.name,
    }

    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderBulkCreate"]["results"][0]["order"]
    order_id = data["id"]
    fulfillment_id = data["fulfillments"][0]["lines"][0]["id"]

    # return products
    variables = {
        "order": order_id,
        "input": {
            "refund": False,
            "fulfillmentLines": [
                {
                    "fulfillmentLineId": fulfillment_id,
                    "quantity": 5,
                }
            ],
        },
    }
    staff_api_client.post_graphql(ORDER_FULFILL_RETURN_MUTATION, variables)

    # refund products
    mocked_is_active.side_effect = [True, False]
    transaction = TransactionItem.objects.get()
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.REFUND.name,
        "amount": Decimal(120),
    }
    staff_api_client.post_graphql(MUTATION_TRANSACTION_REQUEST_ACTION, variables)

    # then
    db_order = Order.objects.get()
    assert db_order.status == OrderStatusEnum.RETURNED.name.lower()
    event = db_order.events.last()
    assert event.type == OrderEvents.TRANSACTION_REFUND_REQUESTED


@pytest.mark.integration
def test_filter_imported_orders(
    staff_api_client,
    permission_manage_orders_import,
    permission_group_manage_orders,
    order_bulk_input,  # noqa: F811
    product,
    channel_USD,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_orders_import)
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    # import three orders (fulfilled, partially fulfilled, unfulfilled)
    # from external system
    variant_id = graphene.Node.to_global_id(
        "ProductVariant", product.variants.first().id
    )
    order_1 = order_bulk_input
    order_1["status"] = OrderStatusEnum.FULFILLED.name
    order_1["deliveryMethod"] = None
    order_1["channel"] = channel_USD.slug
    order_1["currency"] = "USD"
    order_1["lines"][0]["variantId"] = variant_id
    order_1["lines"][0]["quantity"] = 2
    order_1["lines"][0]["isShippingRequired"] = False
    order_1["fulfillments"][0]["lines"][0]["variantId"] = variant_id
    order_1["fulfillments"][0]["lines"][0]["quantity"] = 2
    order_1["transactions"] = []
    order_1["invoices"] = []
    order_1["discounts"] = []

    order_2 = copy.deepcopy(order_1)
    order_2["status"] = OrderStatusEnum.PARTIALLY_FULFILLED.name
    order_2["fulfillments"][0]["lines"][0]["quantity"] = 1

    order_3 = copy.deepcopy(order_1)
    order_3["status"] = OrderStatusEnum.UNFULFILLED.name
    order_3["fulfillments"][0]["lines"][0]["quantity"] = 0

    variables = {
        "orders": [order_1, order_2, order_3],
        "stockUpdatePolicy": StockUpdatePolicyEnum.UPDATE.name,
    }

    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)
    results = content["data"]["orderBulkCreate"]["results"]
    order_1_id, order_2_id, order_3_id = (result["order"]["id"] for result in results)

    # filter created orders by partially fulfilled status
    query = """
      query ($filter: OrderFilterInput!, ) {
        orders(first: 5, filter:$filter) {
          totalCount
          edges {
            node {
              id
            }
          }
        }
      }
    """
    response = staff_api_client.post_graphql(
        query, {"filter": {"status": "PARTIALLY_FULFILLED"}}
    )
    content = get_graphql_content(response)
    data_1 = content["data"]["orders"]

    # filter created orders by unfulfilled status
    response = staff_api_client.post_graphql(
        query, {"filter": {"status": "UNFULFILLED"}}
    )
    content = get_graphql_content(response)
    data_2 = content["data"]["orders"]

    # then
    assert data_1["totalCount"] == 1
    assert data_1["edges"][0]["node"]["id"] == order_2_id
    assert data_2["totalCount"] == 1
    assert data_2["edges"][0]["node"]["id"] == order_3_id


@pytest.mark.integration
def test_refresh_order_prices_from_imported_draft_order_with_unit_discount(
    staff_api_client,
    permission_manage_orders_import,
    permission_group_manage_orders,
    order_bulk_input,  # noqa: F811
    product,
    channel_USD,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_orders_import)
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    # import draft order from external system
    order = order_bulk_input
    order["status"] = OrderStatusEnum.DRAFT.name
    order["deliveryMethod"] = None
    order["channel"] = channel_USD.slug
    order["currency"] = "USD"
    order["fulfillments"] = []
    order["transactions"] = []
    order["invoices"] = []
    order["discounts"] = []

    discount_type = DiscountValueTypeEnum.FIXED.name
    discount_value = 10
    discount_reason = "Test discount"
    variant = product.variants.first()
    order["lines"][0]["variantId"] = graphene.Node.to_global_id(
        "ProductVariant", variant.id
    )
    order["lines"][0]["isShippingRequired"] = False
    order["lines"][0]["unitDiscountValue"] = discount_value
    order["lines"][0]["unitDiscountType"] = discount_type
    order["lines"][0]["unitDiscountReason"] = discount_reason

    line_total_price_net = 50
    line_total_price_gross = 60
    order["lines"][0]["totalPrice"]["net"] = line_total_price_net
    order["lines"][0]["totalPrice"]["gross"] = line_total_price_gross

    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.UPDATE.name,
    }

    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["orderBulkCreate"]["results"]
    assert not data[0]["errors"]

    order_response_data = data[0]["order"]

    order_line = order_response_data["lines"][0]
    assert order_line["variant"]["id"] == graphene.Node.to_global_id(
        "ProductVariant", variant.id
    )
    assert order_line["unitDiscountType"] == discount_type
    assert order_line["unitDiscountValue"] == discount_value
    assert order_line["unitDiscountReason"] == discount_reason
    assert order_response_data["total"]["net"]["amount"] == line_total_price_net
    assert order_response_data["total"]["gross"]["amount"] == line_total_price_gross
    assert (
        order_response_data["undiscountedTotal"]["net"]["amount"]
        == order["lines"][0]["undiscountedTotalPrice"]["net"]
    )
    assert (
        order_response_data["undiscountedTotal"]["gross"]["amount"]
        == order["lines"][0]["undiscountedTotalPrice"]["gross"]
    )
    assert order_response_data["shippingPrice"]["gross"]["amount"] == 0
    assert order_response_data["shippingPrice"]["net"]["amount"] == 0

    db_order_line = OrderLine.objects.get()
    assert db_order_line.variant == variant
    assert db_order_line.unit_discount_type == discount_type.lower()
    assert db_order_line.unit_discount_value == discount_value
    assert db_order_line.unit_discount_reason == discount_reason

    assert order_response_data

    # refetch order prices
    order = Order.objects.get()
    order, lines = fetch_order_prices_if_expired(
        order, get_plugins_manager(allow_replica=True), force_update=True
    )

    # then - ensure the order prices are updated, the discount is applied
    line = lines[0]
    assert line.unit_discount_type == discount_type.lower()
    assert line.unit_discount_value == discount_value
    assert line.unit_discount_reason == discount_reason
    assert (
        line.undiscounted_total_price_net_amount - line.total_price_net_amount
    ) / line.quantity == line.unit_discount_amount
    assert order.total_net_amount == line.total_price_net_amount
    assert order.total_gross_amount == line.total_price_gross_amount
