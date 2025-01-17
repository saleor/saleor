from decimal import Decimal
from unittest.mock import patch

import graphene
import pytest
from django.test import override_settings

from .....core.models import EventDelivery
from .....core.prices import quantize_price
from .....discount import DiscountType, RewardValueType
from .....order import OrderStatus
from .....order import events as order_events
from .....order.actions import call_order_event
from .....order.error_codes import OrderErrorCode
from .....order.models import OrderEvent
from .....product.models import ProductVariant
from .....warehouse.models import Allocation, Stock
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....tests.utils import assert_no_permission, get_graphql_content
from ..utils import assert_proper_webhook_called_once

ORDER_LINE_UPDATE_MUTATION = """
    mutation OrderLineUpdate($lineId: ID!, $quantity: Int!) {
        orderLineUpdate(id: $lineId, input: {quantity: $quantity}) {
            errors {
                field
                message
                code
            }
            orderLine {
                id
                quantity
                unitDiscount {
                  amount
                }
                unitDiscountType
                unitDiscountValue
                isGift
                                totalPrice {
                    gross {
                        amount
                    }
                    net {
                        amount
                    }
                }
                undiscountedTotalPrice {
                    gross {
                        amount
                    }
                    net {
                        amount
                    }
                }
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
                undiscountedUnitPrice {
                    gross {
                        amount
                    }
                    net {
                        amount
                    }
                }
            }
            order {
                total {
                    gross {
                        amount
                    }
                }
                discounts {
                    amount {
                        amount
                    }
                }
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_order_line_update_with_out_of_stock_webhook_for_two_lines_success_scenario(
    out_of_stock_mock,
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
):
    # given
    Stock.objects.update(quantity=5)
    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    first_line, second_line = order.lines.all()
    new_quantity = 5

    first_line_id = graphene.Node.to_global_id("OrderLine", first_line.id)
    second_line_id = graphene.Node.to_global_id("OrderLine", second_line.id)

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    variables = {"lineId": first_line_id, "quantity": new_quantity}
    staff_api_client.post_graphql(query, variables)
    variables = {"lineId": second_line_id, "quantity": new_quantity}
    staff_api_client.post_graphql(query, variables)

    # then
    assert out_of_stock_mock.call_count == 2
    out_of_stock_mock.assert_called_with(Stock.objects.last())


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_order_line_update_with_out_of_stock_webhook_success_scenario(
    out_of_stock_mock,
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
):
    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    line = order.lines.first()
    new_quantity = 5
    line_id = graphene.Node.to_global_id("OrderLine", line.id)

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {"lineId": line_id, "quantity": new_quantity}
    staff_api_client.post_graphql(query, variables)

    out_of_stock_mock.assert_called_once_with(Stock.objects.first())


@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
def test_order_line_update_with_back_in_stock_webhook_fail_scenario(
    product_variant_back_in_stock_webhook_mock,
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
):
    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    line = order.lines.first()
    new_quantity = 1
    line_id = graphene.Node.to_global_id("OrderLine", line.id)

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {"lineId": line_id, "quantity": new_quantity}
    staff_api_client.post_graphql(query, variables)

    product_variant_back_in_stock_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
def test_order_line_update_with_back_in_stock_webhook_called_once_success_scenario(
    back_in_stock_mock,
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
):
    first_allocated = Allocation.objects.first()
    first_allocated.quantity_allocated = 5
    first_allocated.save()

    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    line = order.lines.first()
    new_quantity = 1
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"lineId": line_id, "quantity": new_quantity}

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    staff_api_client.post_graphql(query, variables)
    back_in_stock_mock.assert_called_once_with(first_allocated.stock)


@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
def test_order_line_update_with_back_in_stock_webhook_called_twice_success_scenario(
    product_variant_back_in_stock_webhook_mock,
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
):
    first_allocation = Allocation.objects.first()
    first_allocation.quantity_allocated = 5
    first_allocation.save()

    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    first_line, second_line = order.lines.all()
    new_quantity = 1
    first_line_id = graphene.Node.to_global_id("OrderLine", first_line.id)
    second_line_id = graphene.Node.to_global_id("OrderLine", second_line.id)

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {"lineId": first_line_id, "quantity": new_quantity}
    staff_api_client.post_graphql(query, variables)

    variables = {"lineId": second_line_id, "quantity": new_quantity}
    staff_api_client.post_graphql(query, variables)

    assert product_variant_back_in_stock_webhook_mock.call_count == 2
    product_variant_back_in_stock_webhook_mock.assert_called_with(Stock.objects.last())


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_line_update(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
    staff_user,
):
    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    line = order.lines.first()
    new_quantity = 1
    removed_quantity = 2
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"lineId": line_id, "quantity": new_quantity}

    # Ensure the line has the expected quantity
    assert line.quantity == 3

    # No event should exist yet
    assert not OrderEvent.objects.exists()

    # mutation should fail without proper permissions
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)
    order_updated_webhook_mock.assert_not_called()
    draft_order_updated_webhook_mock.assert_not_called()

    # assign permissions
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLineUpdate"]
    assert data["orderLine"]["quantity"] == new_quantity
    assert_proper_webhook_called_once(
        order, status, draft_order_updated_webhook_mock, order_updated_webhook_mock
    )
    removed_items_event = OrderEvent.objects.last()  # type: OrderEvent
    assert removed_items_event.type == order_events.OrderEvents.REMOVED_PRODUCTS
    assert removed_items_event.user == staff_user
    assert removed_items_event.parameters == {
        "lines": [
            {"quantity": removed_quantity, "line_pk": str(line.pk), "item": str(line)}
        ]
    }

    # mutation should fail when quantity is lower than 1
    variables = {"lineId": line_id, "quantity": 0}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLineUpdate"]
    assert data["errors"]
    assert data["errors"][0]["field"] == "quantity"


@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_line_update_no_allocation(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
    staff_user,
):
    # given
    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    line = order.lines.first()
    line.allocations.all().delete()
    new_quantity = 1
    removed_quantity = 2
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"lineId": line_id, "quantity": new_quantity}

    # when
    # No event should exist yet
    assert not OrderEvent.objects.exists()

    # assign permissions
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderLineUpdate"]
    assert data["orderLine"]["quantity"] == new_quantity
    assert_proper_webhook_called_once(
        order,
        order.status,
        draft_order_updated_webhook_mock,
        order_updated_webhook_mock,
    )
    removed_items_event = OrderEvent.objects.last()  # type: OrderEvent
    assert removed_items_event.type == order_events.OrderEvents.REMOVED_PRODUCTS
    assert removed_items_event.user == staff_user
    assert removed_items_event.parameters == {
        "lines": [
            {"quantity": removed_quantity, "line_pk": str(line.pk), "item": str(line)}
        ]
    }


def test_order_line_update_by_user_no_channel_access(
    order_with_lines,
    permission_group_all_perms_channel_USD_only,
    staff_api_client,
    staff_user,
    channel_PLN,
):
    # given
    query = ORDER_LINE_UPDATE_MUTATION
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.channel = channel_PLN
    order.save(update_fields=["status", "channel"])

    line = order.lines.first()
    new_quantity = 1
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"lineId": line_id, "quantity": new_quantity}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_line_update_by_app(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    order_with_lines,
    permission_manage_orders,
    app_api_client,
    channel_PLN,
):
    # given
    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.channel = channel_PLN
    order.save(update_fields=["status", "channel"])

    line = order.lines.first()
    new_quantity = 1
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"lineId": line_id, "quantity": new_quantity}

    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderLineUpdate"]
    assert data["orderLine"]["quantity"] == new_quantity
    assert_proper_webhook_called_once(
        order,
        order.status,
        draft_order_updated_webhook_mock,
        order_updated_webhook_mock,
    )
    removed_items_event = OrderEvent.objects.last()  # type: OrderEvent
    assert removed_items_event.type == order_events.OrderEvents.REMOVED_PRODUCTS
    assert removed_items_event.app == app_api_client.app
    assert removed_items_event.user is None


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
def test_order_line_update_without_sku(
    status,
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
    staff_user,
):
    ProductVariant.objects.update(sku=None)

    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    line = order.lines.first()
    new_quantity = 1
    removed_quantity = 2
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"lineId": line_id, "quantity": new_quantity}

    # Ensure the line has the expected quantity
    assert line.quantity == 3

    # No event should exist yet
    assert not OrderEvent.objects.exists()

    # mutation should fail without proper permissions
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)

    # assign permissions
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLineUpdate"]
    assert data["orderLine"]["quantity"] == new_quantity

    removed_items_event = OrderEvent.objects.last()  # type: OrderEvent
    assert removed_items_event.type == order_events.OrderEvents.REMOVED_PRODUCTS
    assert removed_items_event.user == staff_user
    assert removed_items_event.parameters == {
        "lines": [
            {"quantity": removed_quantity, "line_pk": str(line.pk), "item": str(line)}
        ]
    }

    line.refresh_from_db()
    assert line.product_sku
    assert line.product_variant_id == line.variant.get_global_id()

    # mutation should fail when quantity is lower than 1
    variables = {"lineId": line_id, "quantity": 0}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLineUpdate"]
    assert data["errors"]
    assert data["errors"][0]["field"] == "quantity"


@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_invalid_order_when_updating_lines(
    order_update_webhook_mock,
    draft_order_update_webhook_mock,
    order_with_lines,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    query = ORDER_LINE_UPDATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"lineId": line_id, "quantity": 1}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderLineUpdate"]
    assert data["errors"]
    order_update_webhook_mock.assert_not_called()
    draft_order_update_webhook_mock.assert_not_called()


def test_order_line_update_quantity_gift(
    order_with_lines,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    query = ORDER_LINE_UPDATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    line = order.lines.first()
    line.is_gift = True
    line.save(update_fields=["is_gift"])
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"lineId": line_id, "quantity": 1}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderLineUpdate"]
    assert not data["orderLine"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == OrderErrorCode.NON_EDITABLE_GIFT_LINE.name


def test_order_line_update_order_promotion(
    draft_order,
    staff_api_client,
    permission_group_manage_orders,
    order_promotion_rule,
):
    # given
    query = ORDER_LINE_UPDATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order

    rule = order_promotion_rule
    promotion_id = graphene.Node.to_global_id("Promotion", rule.promotion_id)
    reward_value = Decimal("25")
    assert rule.reward_value == reward_value
    assert rule.reward_value_type == RewardValueType.PERCENTAGE

    order.lines.last().delete()
    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variant = line.variant
    variant_channel_listing = variant.channel_listings.get(channel=order.channel)
    quantity = 4
    undiscounted_subtotal = quantity * variant_channel_listing.discounted_price_amount
    expected_discount = round(reward_value / 100 * undiscounted_subtotal, 2)

    variables = {"lineId": line_id, "quantity": quantity}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderLineUpdate"]

    discounts = data["order"]["discounts"]
    assert len(discounts) == 1
    assert discounts[0]["amount"]["amount"] == expected_discount

    discount_db = order.discounts.get()
    assert discount_db.promotion_rule == rule
    assert discount_db.amount_value == expected_discount
    assert discount_db.type == DiscountType.ORDER_PROMOTION
    assert discount_db.reason == f"Promotion: {promotion_id}"


def test_order_line_update_gift_promotion(
    draft_order,
    staff_api_client,
    permission_group_manage_orders,
    gift_promotion_rule,
):
    # given
    query = ORDER_LINE_UPDATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    rule = gift_promotion_rule
    promotion_id = graphene.Node.to_global_id("Promotion", rule.promotion_id)

    order.lines.last().delete()
    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    quantity = 4

    variables = {"lineId": line_id, "quantity": quantity}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderLineUpdate"]

    line = data["orderLine"]
    assert line["quantity"] == quantity
    assert line["unitDiscount"]["amount"] == 0
    assert line["unitDiscountValue"] == 0

    gift_line_db = order.lines.get(is_gift=True)
    gift_price = gift_line_db.variant.channel_listings.get(
        channel=order.channel
    ).price_amount
    assert gift_line_db.unit_discount_amount == gift_price
    assert gift_line_db.unit_price_gross_amount == Decimal(0)

    assert not data["order"]["discounts"]

    discount = gift_line_db.discounts.get()
    assert discount.promotion_rule == rule
    assert discount.amount_value == gift_price
    assert discount.type == DiscountType.ORDER_PROMOTION
    assert discount.reason == f"Promotion: {promotion_id}"


@pytest.mark.parametrize(
    ("status", "webhook_event"),
    [
        (OrderStatus.DRAFT, WebhookEventAsyncType.DRAFT_ORDER_UPDATED),
        (OrderStatus.UNCONFIRMED, WebhookEventAsyncType.ORDER_UPDATED),
    ],
)
@patch(
    "saleor.graphql.order.mutations.utils.call_order_event",
    wraps=call_order_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_order_line_update_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_order_event,
    setup_order_webhooks,
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
    settings,
    status,
    webhook_event,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        order_webhook,
    ) = setup_order_webhooks(webhook_event)

    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    order.should_refresh_prices = True
    order.status = status
    order.save(update_fields=["status", "should_refresh_prices"])
    first_line, second_line = order.lines.all()
    new_quantity = 5

    first_line_id = graphene.Node.to_global_id("OrderLine", first_line.id)

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {"lineId": first_line_id, "quantity": new_quantity}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["orderLineUpdate"]["errors"]

    # confirm that event delivery was generated for each async webhook.
    order_delivery = EventDelivery.objects.get(webhook_id=order_webhook.id)
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": order_delivery.id},
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 2
    assert not EventDelivery.objects.exclude(webhook_id=order_webhook.id).exists()

    tax_delivery_call, filter_shipping_call = (
        mocked_send_webhook_request_sync.mock_calls
    )

    tax_delivery = tax_delivery_call.args[0]
    assert tax_delivery.webhook_id == tax_webhook.id

    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    )

    assert wrapped_call_order_event.called


def test_order_line_update_catalogue_discount(
    order_with_lines_and_catalogue_promotion,
    permission_group_manage_orders,
    staff_api_client,
    tax_configuration_flat_rates,
):
    # give
    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines_and_catalogue_promotion
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])
    tax_rate = Decimal(1.23)

    currency = order.currency
    line = order.lines.first()
    old_quantity = line.quantity
    lines_count = len(order.lines.all())
    undiscounted_unit_price = line.undiscounted_base_unit_price_amount

    discount = line.discounts.get()
    initial_discount_amount = discount.amount_value
    unit_discount = quantize_price(initial_discount_amount / old_quantity, currency)

    new_quantity = 4
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"lineId": line_id, "quantity": new_quantity}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)

    assert order.lines.count() == lines_count
    line.refresh_from_db()
    line_data = content["data"]["orderLineUpdate"]["orderLine"]
    assert line_data["quantity"] == new_quantity
    unit_price = undiscounted_unit_price - unit_discount
    assert line_data["unitPrice"]["net"]["amount"] == unit_price
    assert Decimal(str(line_data["unitPrice"]["gross"]["amount"])) == quantize_price(
        unit_price * tax_rate, currency
    )
    assert (
        line_data["undiscountedUnitPrice"]["net"]["amount"] == undiscounted_unit_price
    )
    assert Decimal(
        str(line_data["undiscountedUnitPrice"]["gross"]["amount"])
    ) == quantize_price(undiscounted_unit_price * tax_rate, currency)
    total_price = unit_price * new_quantity
    assert line_data["totalPrice"]["net"]["amount"] == total_price
    assert Decimal(str(line_data["totalPrice"]["gross"]["amount"])) == quantize_price(
        total_price * tax_rate, currency
    )
    assert (
        line_data["undiscountedTotalPrice"]["net"]["amount"]
        == undiscounted_unit_price * new_quantity
    )
    assert Decimal(
        str(line_data["undiscountedTotalPrice"]["gross"]["amount"])
    ) == quantize_price(undiscounted_unit_price * new_quantity * tax_rate, currency)

    discount.refresh_from_db()
    assert discount.amount_value != initial_discount_amount
    assert discount.amount_value == unit_discount * new_quantity
