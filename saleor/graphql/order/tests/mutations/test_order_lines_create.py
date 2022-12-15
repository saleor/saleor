from datetime import datetime
from unittest.mock import patch

import graphene
import pytest
import pytz
from django.db.models import Sum

from .....order import OrderStatus
from .....order import events as order_events
from .....order.error_codes import OrderErrorCode
from .....order.models import OrderEvent, OrderLine
from .....product.models import ProductVariant
from .....warehouse.models import Allocation, Stock
from ....tests.utils import assert_no_permission, get_graphql_content
from ..utils import assert_proper_webhook_called_once

ORDER_LINES_CREATE_MUTATION = """
    mutation OrderLinesCreate(
            $orderId: ID!, $variantId: ID!, $quantity: Int!, $forceNewLine: Boolean
        ) {
        orderLinesCreate(id: $orderId,
                input: [
                    {
                        variantId: $variantId,
                        quantity: $quantity,
                        forceNewLine: $forceNewLine
                    }
                ]) {

            errors {
                field
                code
                message
                variants
            }
            orderLines {
                id
                quantity
                productSku
                productVariantId
                unitPrice {
                    gross {
                        amount
                        currency
                    }
                    net {
                        amount
                        currency
                    }
                }
            }
            order {
                total {
                    gross {
                        amount
                    }
                }
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_order_lines_create_with_out_of_stock_webhook(
    product_variant_out_of_stock_webhook_mock,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
):
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    line = order.lines.first()
    variant = line.variant
    quantity = 2
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    staff_api_client.post_graphql(query, variables)

    quantity_allocated = Allocation.objects.aggregate(Sum("quantity_allocated"))[
        "quantity_allocated__sum"
    ]
    stock_quantity = Allocation.objects.aggregate(Sum("stock__quantity"))[
        "stock__quantity__sum"
    ]
    assert quantity_allocated == stock_quantity
    product_variant_out_of_stock_webhook_mock.assert_called_once_with(
        Stock.objects.first()
    )


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_order_lines_create_for_variant_with_many_stocks_with_out_of_stock_webhook(
    product_variant_out_of_stock_webhook_mock,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
    variant_with_many_stocks,
):
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    variant = variant_with_many_stocks
    quantity = 4
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    staff_api_client.post_graphql(query, variables)
    product_variant_out_of_stock_webhook_mock.assert_called_once_with(
        Stock.objects.all()[3]
    )


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_order_lines_create(
    product_variant_out_of_stock_webhook_mock,
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
    variant_with_many_stocks,
):
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    variant = variant_with_many_stocks
    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    # mutation should fail without proper permissions
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)
    order_updated_webhook_mock.assert_not_called()
    draft_order_updated_webhook_mock.assert_not_called()
    assert not OrderEvent.objects.exists()

    # assign permissions
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query, variables)
    assert_proper_webhook_called_once(
        order, status, draft_order_updated_webhook_mock, order_updated_webhook_mock
    )
    assert OrderEvent.objects.count() == 1
    event = OrderEvent.objects.last()
    assert event.type == order_events.OrderEvents.ADDED_PRODUCTS
    assert len(event.parameters["lines"]) == 1
    line = OrderLine.objects.last()
    assert event.parameters["lines"] == [
        {"item": str(line), "line_pk": str(line.pk), "quantity": quantity}
    ]

    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["orderLines"][0]["productSku"] == variant.sku
    assert data["orderLines"][0]["productVariantId"] == variant.get_global_id()
    assert data["orderLines"][0]["quantity"] == quantity

    # mutation should fail when quantity is lower than 1
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": 0}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["errors"]
    assert data["errors"][0]["field"] == "quantity"
    assert data["errors"][0]["variants"] == [variant_id]
    product_variant_out_of_stock_webhook_mock.assert_not_called()


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_order_lines_create_for_just_published_product(
    product_variant_out_of_stock_webhook_mock,
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
    variant_with_many_stocks,
):
    # given
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    variant = variant_with_many_stocks
    product_listing = variant.product.channel_listings.get(channel=order.channel)
    product_listing.published_at = datetime.now(pytz.utc)
    product_listing.save(update_fields=["published_at"])

    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    assert_proper_webhook_called_once(
        order, status, draft_order_updated_webhook_mock, order_updated_webhook_mock
    )
    assert OrderEvent.objects.count() == 1
    assert OrderEvent.objects.last().type == order_events.OrderEvents.ADDED_PRODUCTS
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["orderLines"][0]["productSku"] == variant.sku
    assert data["orderLines"][0]["productVariantId"] == variant.get_global_id()
    assert data["orderLines"][0]["quantity"] == quantity


@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_with_unavailable_variant(
    order_updated_webhook_mock,
    draft_order_updated_webhoook_mock,
    draft_order,
    permission_manage_orders,
    staff_api_client,
):
    query = ORDER_LINES_CREATE_MUTATION
    order = draft_order
    channel = order.channel
    line = order.lines.first()
    variant = line.variant
    variant.channel_listings.filter(channel=channel).update(price_amount=None)
    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["orderLinesCreate"]["errors"][0]
    assert error["code"] == OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.name
    assert error["field"] == "input"
    assert error["variants"] == [variant_id]
    order_updated_webhook_mock.assert_not_called()
    draft_order_updated_webhoook_mock.assert_not_called()


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_with_existing_variant(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
):
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    line = order.lines.first()
    variant = line.variant
    old_quantity = line.quantity
    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    # mutation should fail without proper permissions
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)
    assert not OrderEvent.objects.exists()
    order_updated_webhook_mock.assert_not_called()
    draft_order_updated_webhook_mock.assert_not_called()

    # assign permissions
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query, variables)
    assert OrderEvent.objects.count() == 1
    assert OrderEvent.objects.last().type == order_events.OrderEvents.ADDED_PRODUCTS
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["orderLines"][0]["productSku"] == variant.sku
    assert data["orderLines"][0]["productVariantId"] == variant.get_global_id()
    assert data["orderLines"][0]["quantity"] == old_quantity + quantity
    assert_proper_webhook_called_once(
        order, status, draft_order_updated_webhook_mock, order_updated_webhook_mock
    )


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_with_same_variant_and_force_new_line(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
):
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    lines = order.lines.all()
    assert len(lines) == 2
    line = lines[0]
    variant = line.variant

    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "orderId": order_id,
        "variantId": variant_id,
        "quantity": quantity,
        "forceNewLine": True,
    }

    # mutation should fail without proper permissions
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)
    assert not OrderEvent.objects.exists()
    order_updated_webhook_mock.assert_not_called()
    draft_order_updated_webhook_mock.assert_not_called()

    # assign permissions
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    response = staff_api_client.post_graphql(query, variables)
    assert order.lines.count() == 3
    assert OrderEvent.objects.count() == 1
    assert OrderEvent.objects.last().type == order_events.OrderEvents.ADDED_PRODUCTS
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["orderLines"][0]["productSku"] == variant.sku
    assert data["orderLines"][0]["productVariantId"] == variant.get_global_id()
    assert data["orderLines"][0]["quantity"] == quantity
    assert_proper_webhook_called_once(
        order, status, draft_order_updated_webhook_mock, order_updated_webhook_mock
    )


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_when_variant_already_in_multiple_lines(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
):
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])

    line = order.lines.first()
    variant = line.variant

    # copy line and add to order
    line.id = None
    line.save()

    assert order.lines.count() == 3

    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "orderId": order_id,
        "variantId": variant_id,
        "quantity": quantity,
        "forceNewLine": True,
    }

    # assign permissions
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    response = staff_api_client.post_graphql(ORDER_LINES_CREATE_MUTATION, variables)

    assert order.lines.count() == 4
    assert OrderEvent.objects.count() == 1
    assert OrderEvent.objects.last().type == order_events.OrderEvents.ADDED_PRODUCTS
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["orderLines"][0]["productSku"] == variant.sku
    assert data["orderLines"][0]["productVariantId"] == variant.get_global_id()
    assert data["orderLines"][0]["quantity"] == quantity
    assert_proper_webhook_called_once(
        order, status, draft_order_updated_webhook_mock, order_updated_webhook_mock
    )


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_variant_on_sale(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
    variant_with_many_stocks,
    sale,
):
    # given
    query = ORDER_LINES_CREATE_MUTATION

    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])

    variant = variant_with_many_stocks
    sale.variants.add(variant)

    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    assert_proper_webhook_called_once(
        order, status, draft_order_updated_webhook_mock, order_updated_webhook_mock
    )
    assert OrderEvent.objects.count() == 1
    assert OrderEvent.objects.last().type == order_events.OrderEvents.ADDED_PRODUCTS
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    line_data = data["orderLines"][0]
    assert line_data["productSku"] == variant.sku
    assert line_data["quantity"] == quantity
    assert line_data["quantity"] == quantity
    variant_channel_listing = variant.channel_listings.get(channel=order.channel)
    sale_channel_listing = sale.channel_listings.first()
    assert (
        line_data["unitPrice"]["gross"]["amount"]
        == variant_channel_listing.price_amount - sale_channel_listing.discount_value
    )
    assert (
        line_data["unitPrice"]["net"]["amount"]
        == variant_channel_listing.price_amount - sale_channel_listing.discount_value
    )

    line = order.lines.get(product_sku=variant.sku)
    assert line.sale_id == graphene.Node.to_global_id("Sale", sale.id)
    assert line.unit_discount_amount == sale_channel_listing.discount_value
    assert line.unit_discount_value == sale_channel_listing.discount_value
    assert (
        line.unit_discount_reason
        == f"Sale: {graphene.Node.to_global_id('Sale', sale.id)}"
    )


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_with_product_and_variant_not_assigned_to_channel(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
    variant,
):
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    line = order.lines.first()
    assert variant != line.variant
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": 1}
    variant.product.channel_listings.all().delete()
    variant.channel_listings.all().delete()

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["orderLinesCreate"]["errors"][0]
    assert error["code"] == OrderErrorCode.PRODUCT_NOT_PUBLISHED.name
    assert error["field"] == "input"
    assert error["variants"] == [variant_id]
    order_updated_webhook_mock.assert_not_called()
    draft_order_updated_webhook_mock.assert_not_called()


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_with_variant_not_assigned_to_channel(
    order_update_webhook_mock,
    draft_order_update_webhook_mock,
    status,
    order_with_lines,
    staff_api_client,
    permission_manage_orders,
    customer_user,
    shipping_method,
    variant,
    channel_USD,
    graphql_address_data,
):
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    line = order.lines.first()
    assert variant != line.variant
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": 1}
    variant.channel_listings.all().delete()

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["orderLinesCreate"]["errors"][0]
    assert error["code"] == OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.name
    assert error["field"] == "input"
    assert error["variants"] == [variant_id]
    order_update_webhook_mock.assert_not_called()
    draft_order_update_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
def test_order_lines_create_without_sku(
    product_variant_out_of_stock_webhook_mock,
    status,
    order_with_lines,
    permission_manage_orders,
    staff_api_client,
    variant_with_many_stocks,
):
    ProductVariant.objects.update(sku=None)
    order_with_lines.lines.update(product_sku=None)

    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    variant = variant_with_many_stocks
    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    # mutation should fail without proper permissions
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)
    assert not OrderEvent.objects.exists()

    # assign permissions
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query, variables)
    assert OrderEvent.objects.count() == 1
    assert OrderEvent.objects.last().type == order_events.OrderEvents.ADDED_PRODUCTS
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["orderLines"][0]["productSku"] is None
    assert data["orderLines"][0]["productVariantId"] == variant.get_global_id()
    assert data["orderLines"][0]["quantity"] == quantity

    # mutation should fail when quantity is lower than 1
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": 0}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["errors"]
    assert data["errors"][0]["field"] == "quantity"
    assert data["errors"][0]["variants"] == [variant_id]
    product_variant_out_of_stock_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_invalid_order_when_creating_lines(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    order_with_lines,
    staff_api_client,
    permission_manage_orders,
):
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    line = order.lines.first()
    variant = line.variant
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": 1}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["errors"]
    order_updated_webhook_mock.assert_not_called()
    draft_order_updated_webhook_mock.assert_not_called()
