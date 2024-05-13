from unittest.mock import patch

import graphene
import pytest
from django.db.models import Sum

from .....order import OrderStatus
from .....order import events as order_events
from .....order.error_codes import OrderErrorCode
from .....order.models import OrderEvent
from .....warehouse.models import Stock
from ....tests.utils import assert_no_permission, get_graphql_content
from ..utils import assert_proper_webhook_called_once

ORDER_LINE_DELETE_MUTATION = """
    mutation OrderLineDelete($id: ID!) {
        orderLineDelete(id: $id) {
            errors {
                field
                message
                code
            }
            orderLine {
                id
            }
            order {
                id
                total{
                    gross{
                        currency
                        amount
                    }
                    net {
                        currency
                        amount
                    }
                }
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
def test_order_line_remove_with_back_in_stock_webhook(
    back_in_stock_webhook_mock,
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    Stock.objects.update(quantity=3)
    first_stock = Stock.objects.first()
    assert (
        first_stock.quantity
        - (
            first_stock.allocations.aggregate(Sum("quantity_allocated"))[
                "quantity_allocated__sum"
            ]
            or 0
        )
    ) == 0

    query = ORDER_LINE_DELETE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])

    line = order.lines.first()

    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"id": line_id}

    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLineDelete"]
    assert OrderEvent.objects.count() == 1
    assert OrderEvent.objects.last().type == order_events.OrderEvents.REMOVED_PRODUCTS
    assert data["orderLine"]["id"] == line_id
    assert line not in order.lines.all()
    first_stock.refresh_from_db()
    assert (
        first_stock.quantity
        - (
            first_stock.allocations.aggregate(Sum("quantity_allocated"))[
                "quantity_allocated__sum"
            ]
            or 0
        )
    ) == 3
    back_in_stock_webhook_mock.assert_called_once_with(Stock.objects.first())


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_line_remove(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
):
    query = ORDER_LINE_DELETE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"id": line_id}

    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLineDelete"]
    assert OrderEvent.objects.count() == 1
    assert OrderEvent.objects.last().type == order_events.OrderEvents.REMOVED_PRODUCTS
    assert data["orderLine"]["id"] == line_id
    assert line not in order.lines.all()
    assert_proper_webhook_called_once(
        order, status, draft_order_updated_webhook_mock, order_updated_webhook_mock
    )


@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_line_remove_no_line_allocations(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
):
    # given
    query = ORDER_LINE_DELETE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    line = order.lines.first()
    line.allocations.all().delete()
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"id": line_id}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderLineDelete"]
    assert OrderEvent.objects.count() == 1
    assert OrderEvent.objects.last().type == order_events.OrderEvents.REMOVED_PRODUCTS
    assert data["orderLine"]["id"] == line_id
    assert line not in order.lines.all()
    assert_proper_webhook_called_once(
        order,
        order.status,
        draft_order_updated_webhook_mock,
        order_updated_webhook_mock,
    )


def test_order_line_remove_by_usr_no_channel_access(
    order_with_lines,
    permission_group_all_perms_channel_USD_only,
    staff_api_client,
    channel_PLN,
):
    # given
    query = ORDER_LINE_DELETE_MUTATION
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.channel = channel_PLN
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status", "channel"])
    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"id": line_id}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_line_remove_by_app(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    order_with_lines,
    permission_manage_orders,
    app_api_client,
    channel_PLN,
):
    # given
    query = ORDER_LINE_DELETE_MUTATION
    order = order_with_lines
    order.channel = channel_PLN
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status", "channel"])
    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"id": line_id}

    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderLineDelete"]
    assert OrderEvent.objects.count() == 1
    assert OrderEvent.objects.last().type == order_events.OrderEvents.REMOVED_PRODUCTS
    assert data["orderLine"]["id"] == line_id
    assert line not in order.lines.all()
    assert_proper_webhook_called_once(
        order,
        OrderStatus.UNCONFIRMED,
        draft_order_updated_webhook_mock,
        order_updated_webhook_mock,
    )


@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_invalid_order_when_removing_lines(
    order_update_webhook_mock,
    draft_order_update_webhook_mock,
    staff_api_client,
    order_with_lines,
    permission_group_manage_orders,
):
    query = ORDER_LINE_DELETE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"id": line_id}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLineDelete"]
    assert data["errors"]
    order_update_webhook_mock.assert_not_called()
    draft_order_update_webhook_mock.assert_not_called()


def test_draft_order_properly_recalculate_total_after_shipping_product_removed(
    staff_api_client,
    draft_order,
    permission_group_manage_orders,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    line = order.lines.get(product_sku="SKU_AA")
    line.is_shipping_required = True
    line.save()

    query = ORDER_LINE_DELETE_MUTATION
    line_2 = order.lines.get(product_sku="SKU_B")
    line_2_id = graphene.Node.to_global_id("OrderLine", line_2.id)
    variables = {"id": line_2_id}

    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLineDelete"]

    order.refresh_from_db()
    assert data["order"]["total"]["net"]["amount"] == float(
        line.total_price_net_amount
    ) + float(order.shipping_price_net_amount)


def test_order_line_delete_non_removable_gift(
    draft_order,
    permission_group_manage_orders,
    staff_api_client,
):
    # given
    query = ORDER_LINE_DELETE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    line = order.lines.first()
    line.is_gift = True
    line.save(update_fields=["is_gift"])
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"id": line_id}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderLineDelete"]
    assert not data["orderLine"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == OrderErrorCode.NON_REMOVABLE_GIFT_LINE.name
