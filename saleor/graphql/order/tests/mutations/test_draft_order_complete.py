from datetime import datetime, timedelta
from unittest.mock import patch

import graphene
import pytz
from django.db.models import Sum

from .....core.taxes import zero_taxed_money
from .....order import OrderOrigin, OrderStatus
from .....order import events as order_events
from .....order.error_codes import OrderErrorCode
from .....order.models import OrderEvent
from .....plugins.base_plugin import ExcludedShippingMethod
from .....product.models import ProductVariant
from .....warehouse.models import Allocation, PreorderAllocation, Stock
from .....warehouse.tests.utils import get_available_quantity_for_stock
from ....payment.types import PaymentChargeStatusEnum
from ....tests.utils import get_graphql_content

DRAFT_ORDER_COMPLETE_MUTATION = """
    mutation draftComplete($id: ID!) {
        draftOrderComplete(id: $id) {
            errors {
                field
                code
                message
                variants
            }
            order {
                status
                origin
                paymentStatus
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_draft_order_complete(
    product_variant_out_of_stock_webhook_mock,
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order,
):
    order = draft_order

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.DRAFT.upper()
    assert order.search_vector

    for line in order.lines.all():
        allocation = line.allocations.get()
        assert allocation.quantity_allocated == line.quantity_unfulfilled

    # ensure there are only 2 events with correct types
    event_params = {
        "user": staff_user,
        "type__in": [
            order_events.OrderEvents.PLACED_FROM_DRAFT,
            order_events.OrderEvents.CONFIRMED,
        ],
        "parameters": {},
    }
    matching_events = OrderEvent.objects.filter(**event_params)
    assert matching_events.count() == 2
    assert matching_events[0].type != matching_events[1].type
    assert not OrderEvent.objects.exclude(**event_params).exists()
    product_variant_out_of_stock_webhook_mock.assert_called_once_with(
        Stock.objects.last()
    )


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_draft_order_complete_0_total(
    product_variant_out_of_stock_webhook_mock,
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order,
):
    """Ensure the payment status is FULLY_CHARGED when the total order price is 0."""
    order = draft_order
    price = zero_taxed_money(order.currency)
    order.shipping_price = price
    order.total = price
    order.save(
        update_fields=[
            "shipping_price_net_amount",
            "shipping_price_gross_amount",
            "total_net_amount",
            "total_gross_amount",
        ]
    )

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.DRAFT.upper()
    payment_charge_status = PaymentChargeStatusEnum.FULLY_CHARGED
    assert data["paymentStatus"] == payment_charge_status.name
    assert order.search_vector

    for line in order.lines.all():
        allocation = line.allocations.get()
        assert allocation.quantity_allocated == line.quantity_unfulfilled

    # ensure there are only 2 events with correct types
    event_params = {
        "user": staff_user,
        "type__in": [
            order_events.OrderEvents.PLACED_FROM_DRAFT,
            order_events.OrderEvents.CONFIRMED,
        ],
        "parameters": {},
    }
    matching_events = OrderEvent.objects.filter(**event_params)
    assert matching_events.count() == 2
    assert matching_events[0].type != matching_events[1].type
    assert not OrderEvent.objects.exclude(**event_params).exists()
    product_variant_out_of_stock_webhook_mock.assert_called_once_with(
        Stock.objects.last()
    )


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_draft_order_complete_without_sku(
    product_variant_out_of_stock_webhook_mock,
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order,
):
    ProductVariant.objects.update(sku=None)
    draft_order.lines.update(product_sku=None)

    order = draft_order

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.DRAFT.upper()

    for line in order.lines.all():
        allocation = line.allocations.get()
        assert allocation.quantity_allocated == line.quantity_unfulfilled

    # ensure there are only 2 events with correct types
    event_params = {
        "user": staff_user,
        "type__in": [
            order_events.OrderEvents.PLACED_FROM_DRAFT,
            order_events.OrderEvents.CONFIRMED,
        ],
        "parameters": {},
    }
    matching_events = OrderEvent.objects.filter(**event_params)
    assert matching_events.count() == 2
    assert matching_events[0].type != matching_events[1].type
    assert not OrderEvent.objects.exclude(**event_params).exists()
    product_variant_out_of_stock_webhook_mock.assert_called_once_with(
        Stock.objects.last()
    )


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_draft_order_complete_with_out_of_stock_webhook(
    product_variant_out_of_stock_webhook_mock,
    staff_api_client,
    permission_manage_orders,
    draft_order,
):
    order = draft_order
    first_line = order.lines.first()
    first_line.quantity = 5
    first_line.save()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )

    total_stock = Stock.objects.aggregate(Sum("quantity"))["quantity__sum"]
    total_allocation = Allocation.objects.filter(order_line__order=order).aggregate(
        Sum("quantity_allocated")
    )["quantity_allocated__sum"]
    assert total_stock == total_allocation
    assert product_variant_out_of_stock_webhook_mock.call_count == 2
    product_variant_out_of_stock_webhook_mock.assert_called_with(Stock.objects.last())


def test_draft_order_from_reissue_complete(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order,
):
    order = draft_order
    order.origin = OrderOrigin.REISSUE
    order.save(update_fields=["origin"])

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.REISSUE.upper()

    for line in order.lines.all():
        allocation = line.allocations.get()
        assert allocation.quantity_allocated == line.quantity_unfulfilled

    # ensure there are only 2 events with correct types
    event_params = {
        "user": staff_user,
        "type__in": [
            order_events.OrderEvents.PLACED_FROM_DRAFT,
            order_events.OrderEvents.CONFIRMED,
        ],
        "parameters": {},
    }
    matching_events = OrderEvent.objects.filter(**event_params)
    assert matching_events.count() == 2
    assert matching_events[0].type != matching_events[1].type
    assert not OrderEvent.objects.exclude(**event_params).exists()


def test_draft_order_complete_with_inactive_channel(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order,
):
    order = draft_order
    channel = order.channel
    channel.is_active = False
    channel.save()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]
    assert data["errors"][0]["code"] == OrderErrorCode.CHANNEL_INACTIVE.name
    assert data["errors"][0]["field"] == "channel"


def test_draft_order_complete_with_unavailable_variant(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order,
):
    order = draft_order
    variant = order.lines.first().variant
    variant.channel_listings.filter(channel=order.channel).delete()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]
    assert data["errors"][0]["code"] == OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.name
    assert data["errors"][0]["field"] == "lines"
    assert data["errors"][0]["variants"] == [variant_id]


def test_draft_order_complete_channel_without_shipping_zones(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order,
):
    order = draft_order
    order.channel.shipping_zones.clear()

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]

    assert len(data["errors"]) == 3
    assert {error["code"] for error in data["errors"]} == {
        OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name,
        OrderErrorCode.INSUFFICIENT_STOCK.name,
    }
    assert {error["field"] for error in data["errors"]} == {"shipping", "lines"}


def test_draft_order_complete_product_without_inventory_tracking(
    staff_api_client,
    shipping_method,
    permission_manage_orders,
    staff_user,
    draft_order_without_inventory_tracking,
):
    order = draft_order_without_inventory_tracking
    order.shipping_method = shipping_method
    order.save()

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]

    assert not content["data"]["draftOrderComplete"]["errors"]

    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.DRAFT.upper()

    assert not Allocation.objects.filter(order_line__order=order).exists()

    # ensure there are only 2 events with correct types
    event_params = {
        "user": staff_user,
        "type__in": [
            order_events.OrderEvents.PLACED_FROM_DRAFT,
            order_events.OrderEvents.CONFIRMED,
        ],
        "parameters": {},
    }
    matching_events = OrderEvent.objects.filter(**event_params)
    assert matching_events.count() == 2
    assert matching_events[0].type != matching_events[1].type
    assert not OrderEvent.objects.exclude(**event_params).exists()


def test_draft_order_complete_not_available_shipping_method(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order,
):
    # given
    order = draft_order
    order.channel.shipping_zones.clear()

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]

    assert len(data["errors"]) == 3
    assert {error["code"] for error in data["errors"]} == {
        OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name,
        OrderErrorCode.INSUFFICIENT_STOCK.name,
    }
    assert {error["field"] for error in data["errors"]} == {"shipping", "lines"}


@patch("saleor.plugins.manager.PluginsManager.excluded_shipping_methods_for_order")
def test_draft_order_complete_with_excluded_shipping_method(
    mocked_webhook,
    draft_order,
    shipping_method,
    staff_api_client,
    permission_manage_orders,
    settings,
):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    webhook_reason = "archives-are-incomplete"
    mocked_webhook.return_value = [
        ExcludedShippingMethod(str(shipping_method.id), webhook_reason)
    ]
    order = draft_order
    order.status = OrderStatus.DRAFT
    order.shipping_method = shipping_method
    order.save()
    query = DRAFT_ORDER_COMPLETE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]
    assert (
        data["errors"][0]["code"] == OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
    )
    assert data["errors"][0]["field"] == "shipping"


@patch("saleor.plugins.manager.PluginsManager.excluded_shipping_methods_for_order")
def test_draft_order_complete_with_not_excluded_shipping_method(
    mocked_webhook,
    draft_order,
    shipping_method,
    staff_api_client,
    permission_manage_orders,
    settings,
):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    webhook_reason = "archives-are-incomplete"
    other_shipping_method_id = "1337"
    assert other_shipping_method_id != shipping_method.id
    mocked_webhook.return_value = [
        ExcludedShippingMethod(other_shipping_method_id, webhook_reason)
    ]
    order = draft_order
    order.status = OrderStatus.DRAFT
    order.shipping_method = shipping_method
    order.save()
    query = DRAFT_ORDER_COMPLETE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]
    assert len(data["errors"]) == 0


def test_draft_order_complete_out_of_stock_variant(
    staff_api_client, permission_manage_orders, staff_user, draft_order
):
    order = draft_order

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    line_1, _ = order.lines.order_by("-quantity").all()
    stock_1 = Stock.objects.get(product_variant=line_1.variant)
    line_1.quantity = get_available_quantity_for_stock(stock_1) + 1
    line_1.save(update_fields=["quantity"])

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["draftOrderComplete"]["errors"][0]
    order.refresh_from_db()
    assert order.status == OrderStatus.DRAFT
    assert order.origin == OrderOrigin.DRAFT

    assert error["field"] == "lines"
    assert error["code"] == OrderErrorCode.INSUFFICIENT_STOCK.name


def test_draft_order_complete_existing_user_email_updates_user_field(
    staff_api_client, draft_order, customer_user, permission_manage_orders
):
    order = draft_order
    order.user_email = customer_user.email
    order.user = None
    order.save()
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert "errors" not in content
    order.refresh_from_db()
    assert order.user == customer_user


def test_draft_order_complete_anonymous_user_email_sets_user_field_null(
    staff_api_client, draft_order, permission_manage_orders
):
    order = draft_order
    order.user_email = "anonymous@example.com"
    order.user = None
    order.save()
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert "errors" not in content
    order.refresh_from_db()
    assert order.user is None


def test_draft_order_complete_anonymous_user_no_email(
    staff_api_client, draft_order, permission_manage_orders
):
    order = draft_order
    order.user_email = ""
    order.user = None
    order.save()
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    assert data["status"] == OrderStatus.UNFULFILLED.upper()


def test_draft_order_complete_drops_shipping_address(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order,
    address,
):
    order = draft_order
    order.shipping_address = address.get_copy()
    order.billing_address = address.get_copy()
    order.save()
    order.lines.update(is_shipping_required=False)

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()

    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.DRAFT.upper()
    assert order.shipping_address is None


def test_draft_order_complete_unavailable_for_purchase(
    staff_api_client, permission_manage_orders, staff_user, draft_order
):
    # given
    order = draft_order

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    product = order.lines.first().variant.product
    product.channel_listings.update(
        available_for_purchase_at=datetime.now(pytz.UTC) + timedelta(days=5)
    )

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    error = content["data"]["draftOrderComplete"]["errors"][0]
    order.refresh_from_db()
    assert order.status == OrderStatus.DRAFT
    assert order.origin == OrderOrigin.DRAFT

    assert error["field"] == "lines"
    assert error["code"] == OrderErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE.name


def test_draft_order_complete_preorders(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order_with_preorder_lines,
):
    order = draft_order_with_preorder_lines

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no preorder allocation were created
    assert not PreorderAllocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.DRAFT.upper()

    for line in order.lines.all():
        preorder_allocation = line.preorder_allocations.get()
        assert preorder_allocation.quantity == line.quantity_unfulfilled

    # ensure there are only 2 events with correct types
    event_params = {
        "user": staff_user,
        "type__in": [
            order_events.OrderEvents.PLACED_FROM_DRAFT,
            order_events.OrderEvents.CONFIRMED,
        ],
        "parameters": {},
    }
    matching_events = OrderEvent.objects.filter(**event_params)
    assert matching_events.count() == 2
    assert matching_events[0].type != matching_events[1].type
    assert not OrderEvent.objects.exclude(**event_params).exists()


def test_draft_order_complete_insufficient_stock_preorders(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order_with_preorder_lines,
    channel_USD,
):
    order = draft_order_with_preorder_lines

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    line = order.lines.order_by("-quantity").first()
    channel_listing = line.variant.channel_listings.get(channel_id=channel_USD.id)
    line.quantity = channel_listing.preorder_quantity_threshold + 1
    line.save()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["draftOrderComplete"]["errors"][0]
    order.refresh_from_db()
    assert order.status == OrderStatus.DRAFT
    assert order.origin == OrderOrigin.DRAFT

    assert error["field"] == "lines"
    assert error["code"] == OrderErrorCode.INSUFFICIENT_STOCK.name


def test_draft_order_complete_not_draft_order(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
):
    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]
    assert data["errors"][0]["code"] == OrderErrorCode.INVALID.name
    assert data["errors"][0]["field"] == "id"


def test_draft_order_complete_display_gross_prices(
    staff_api_client,
    permission_manage_orders,
    draft_order,
):
    # given
    order = draft_order
    channel = order.channel
    tax_config = channel.tax_configuration

    # Change the current display_gross_prices to the opposite of what is set in the
    # order.display_gross_prices.
    new_display_gross_prices = not order.display_gross_prices

    tax_config.display_gross_prices = new_display_gross_prices
    tax_config.save()
    tax_config.country_exceptions.all().delete()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not content["data"]["draftOrderComplete"]["errors"]
    order.refresh_from_db()
    assert order.display_gross_prices == new_display_gross_prices
