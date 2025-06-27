from decimal import Decimal
from unittest.mock import ANY, patch

import graphene
import pytest
from django.test import override_settings

from .....core.models import EventDelivery
from .....core.prices import quantize_price
from .....core.taxes import zero_money
from .....discount import DiscountType, DiscountValueType, RewardValueType, VoucherType
from .....discount.models import PromotionRule
from .....discount.utils.voucher import (
    create_or_update_voucher_discount_objects_for_order,
)
from .....order import OrderStatus
from .....order import events as order_events
from .....order.actions import call_order_event
from .....order.calculations import fetch_order_prices_if_expired
from .....order.error_codes import OrderErrorCode
from .....order.models import OrderEvent
from .....product.models import Product, ProductVariant
from .....product.utils.variant_prices import update_discounted_prices_for_promotion
from .....product.utils.variants import fetch_variants_for_promotion_rules
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
    reward_value = Decimal(25)
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
        kwargs={"event_delivery_id": order_delivery.id, "telemetry_context": ANY},
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

    # update variant channel listing
    variant_channel_listing = line.variant.channel_listings.get(channel=order.channel)
    new_variant_price = undiscounted_unit_price + Decimal(100)
    variant_channel_listing.price_amount = new_variant_price
    variant_channel_listing.save(update_fields=["price_amount"])

    # update catalogue discount
    rule = discount.promotion_rule
    reward_value = rule.reward_value
    new_reward_value = reward_value + Decimal(10)
    rule.reward_value = new_reward_value
    rule.save(update_fields=["reward_value"])
    fetch_variants_for_promotion_rules(PromotionRule.objects.all())
    update_discounted_prices_for_promotion(Product.objects.all())

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

    assert line_data["unitDiscountType"] == discount.value_type.upper()
    assert line_data["unitDiscountValue"] == discount.value
    assert Decimal(line_data["unitDiscount"]["amount"]) == quantize_price(
        unit_discount, currency
    )


def test_order_line_update_apply_once_per_order_voucher_discount(
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
    tax_configuration_flat_rates,
    voucher,
    plugins_manager,
):
    """Updating the cheapest product line should only update voucher discount amount.

    The voucher discount should use denormalized voucher reward.
    """
    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    currency = order.currency
    tax_rate = Decimal("1.23")

    lines = order.lines.all()
    undiscounted_shipping_price = order.undiscounted_base_shipping_price
    undiscounted_subtotal = zero_money(currency)
    for line in lines:
        undiscounted_subtotal += line.undiscounted_base_unit_price * line.quantity

    # apply voucher apply once per order type
    initial_discount_value_type = DiscountValueType.PERCENTAGE
    voucher.discount_value_type = initial_discount_value_type
    voucher.type = VoucherType.ENTIRE_ORDER
    voucher.apply_once_per_order = True
    voucher.save(update_fields=["discount_value_type", "type", "apply_once_per_order"])
    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    initial_discount_value = voucher_listing.discount_value
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code
    order.save(update_fields=["voucher_code", "voucher_id", "status"])
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    line_1, line_2 = lines
    assert line_1.undiscounted_base_unit_price < line_2.undiscounted_base_unit_price
    discount = line_1.discounts.get()
    initial_discount_amount = (
        line_1.undiscounted_base_unit_price_amount * initial_discount_value / 100
    )
    initial_unit_discount_amount = initial_discount_amount / line_1.quantity
    assert quantize_price(line_1.base_unit_price_amount, currency) == quantize_price(
        line_1.undiscounted_base_unit_price_amount - initial_unit_discount_amount,
        currency,
    )
    assert quantize_price(line_1.total_price_net_amount, currency) == quantize_price(
        line_1.undiscounted_total_price_net_amount - initial_discount_amount,
        currency,
    )
    assert discount.value == initial_discount_value
    assert discount.value_type == DiscountValueType.PERCENTAGE
    assert discount.amount_value == initial_discount_amount

    # update voucher listing value and voucher discount value type
    voucher_listing.discount_value /= 2
    voucher_listing.save(update_fields=["discount_value"])
    assert voucher_listing.discount_value != initial_discount_value
    new_voucher_discount_value_type = DiscountValueType.FIXED
    voucher.discount_value_type = new_voucher_discount_value_type
    voucher.save(update_fields=["discount_value_type"])
    assert initial_discount_value_type != new_voucher_discount_value_type

    # add 1 unit to line 1
    new_quantity = line_1.quantity + 1
    line_1_id = graphene.Node.to_global_id("OrderLine", line_1.id)
    variables = {"lineId": line_1_id, "quantity": new_quantity}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderLineUpdate"]
    assert not data["errors"]

    order.refresh_from_db()
    line_1, line_2 = order.lines.all()
    new_unit_discount_amount = initial_discount_amount / new_quantity

    discount.refresh_from_db()
    assert discount.value == initial_discount_value
    assert discount.value_type == initial_discount_value_type
    assert discount.amount_value == initial_discount_amount
    assert discount.type == DiscountType.VOUCHER
    assert discount.reason == f"Voucher code: {order.voucher_code}"

    assert quantize_price(line_1.base_unit_price_amount, currency) == quantize_price(
        line_1.undiscounted_base_unit_price_amount - new_unit_discount_amount,
        currency,
    )
    assert quantize_price(line_1.total_price_net_amount, currency) == quantize_price(
        line_1.undiscounted_total_price_net_amount - initial_discount_amount,
        currency,
    )
    assert quantize_price(line_1.total_price_gross_amount, currency) == quantize_price(
        line_1.base_unit_price_amount * new_quantity * tax_rate, currency
    )
    assert quantize_price(
        line_1.undiscounted_total_price_gross_amount, currency
    ) == quantize_price(
        line_1.undiscounted_base_unit_price_amount * line_1.quantity * tax_rate,
        currency,
    )
    assert line_1.unit_discount_amount == new_unit_discount_amount
    assert line_1.unit_discount_type == initial_discount_value_type
    assert line_1.unit_discount_reason == f"Voucher code: {order.voucher_code}"
    assert line_1.unit_discount_value == initial_discount_value

    assert line_2.base_unit_price_amount == line_2.undiscounted_base_unit_price_amount
    assert (
        line_2.total_price_gross_amount
        == line_2.undiscounted_base_unit_price_amount * line_2.quantity * tax_rate
    )
    assert (
        line_2.undiscounted_total_price_gross_amount
        == line_2.undiscounted_base_unit_price_amount * line_2.quantity * tax_rate
    )
    assert line_2.unit_discount_amount == 0
    assert line_2.unit_discount_type is None
    assert line_2.unit_discount_reason is None
    assert line_2.unit_discount_value == 0

    assert order.undiscounted_base_shipping_price == undiscounted_shipping_price
    assert order.base_shipping_price == undiscounted_shipping_price
    assert order.shipping_price_net == undiscounted_shipping_price
    assert order.shipping_price_gross == quantize_price(
        undiscounted_shipping_price * tax_rate, currency
    )

    undiscounted_subtotal += line_1.undiscounted_unit_price.net
    assert (
        order.undiscounted_total_net
        == undiscounted_subtotal + undiscounted_shipping_price
    )
    assert (
        order.undiscounted_total_gross
        == (undiscounted_subtotal + undiscounted_shipping_price) * tax_rate
    )
    assert (
        order.subtotal_net_amount
        == undiscounted_subtotal.amount - initial_discount_amount
    )
    assert quantize_price(order.subtotal_gross_amount, currency) == quantize_price(
        order.subtotal_net_amount * tax_rate, currency
    )
    assert (
        order.total_net_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert quantize_price(order.total_gross_amount, currency) == quantize_price(
        (order.undiscounted_total_net_amount - initial_discount_amount) * tax_rate,
        currency,
    )


def test_order_line_update_specific_product_voucher_discount_percentage(
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
    tax_configuration_flat_rates,
    voucher,
    plugins_manager,
):
    """The voucher discount should use denormalized voucher values."""

    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    currency = order.currency
    tax_rate = Decimal("1.23")

    lines = order.lines.all()
    line_1, line_2 = lines
    undiscounted_shipping_price = order.undiscounted_base_shipping_price
    undiscounted_subtotal = zero_money(currency)
    for line in lines:
        undiscounted_subtotal += line.undiscounted_base_unit_price * line.quantity

    # apply specific product voucher
    initial_discount_value_type = DiscountValueType.PERCENTAGE
    voucher.discount_value_type = initial_discount_value_type
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save(update_fields=["discount_value_type", "type"])
    voucher.variants.add(line_1.variant)
    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    initial_discount_value = voucher_listing.discount_value
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code
    order.save(update_fields=["voucher_code", "voucher_id", "status"])
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    line_1, line_2 = lines
    initial_unit_discount = (
        line_1.undiscounted_base_unit_price_amount * initial_discount_value / 100
    )
    assert (
        line_1.base_unit_price_amount
        == line_1.undiscounted_base_unit_price_amount - initial_unit_discount
    )
    discount_amount = initial_unit_discount * line_1.quantity
    discount = line_1.discounts.get()
    assert discount.value == initial_discount_value
    assert discount.value_type == DiscountValueType.PERCENTAGE
    assert discount.amount_value == discount_amount

    # update voucher listing value, discount value type and eligible variants
    voucher_listing.discount_value /= 2
    voucher_listing.save(update_fields=["discount_value"])
    assert voucher_listing.discount_value != initial_discount_value
    new_voucher_discount_value_type = DiscountValueType.FIXED
    voucher.discount_value_type = new_voucher_discount_value_type
    voucher.save(update_fields=["discount_value_type"])
    assert initial_discount_value_type != new_voucher_discount_value_type
    voucher.variants.set([line_2.variant])

    # add 1 unit to line 1
    new_quantity = line_1.quantity + 1
    line_1_id = graphene.Node.to_global_id("OrderLine", line_1.id)
    variables = {"lineId": line_1_id, "quantity": new_quantity}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderLineUpdate"]
    assert not data["errors"]

    order.refresh_from_db()
    line_1, line_2 = order.lines.all()
    new_discount_amount = initial_unit_discount * new_quantity

    discount.refresh_from_db()
    assert discount.value == initial_discount_value
    assert discount.value_type == initial_discount_value_type
    assert discount.amount_value == new_discount_amount
    assert discount.type == DiscountType.VOUCHER
    assert discount.reason == f"Voucher code: {order.voucher_code}"

    assert quantize_price(line_1.base_unit_price_amount, currency) == quantize_price(
        line_1.undiscounted_base_unit_price_amount - initial_unit_discount,
        currency,
    )
    assert quantize_price(line_1.total_price_net_amount, currency) == quantize_price(
        line_1.undiscounted_total_price_net_amount - new_discount_amount,
        currency,
    )
    assert quantize_price(line_1.total_price_gross_amount, currency) == quantize_price(
        line_1.base_unit_price_amount * new_quantity * tax_rate, currency
    )
    assert quantize_price(
        line_1.undiscounted_total_price_gross_amount, currency
    ) == quantize_price(
        line_1.undiscounted_base_unit_price_amount * line_1.quantity * tax_rate,
        currency,
    )
    assert line_1.unit_discount_amount == initial_unit_discount
    assert line_1.unit_discount_type == initial_discount_value_type
    assert line_1.unit_discount_reason == f"Voucher code: {order.voucher_code}"
    assert line_1.unit_discount_value == initial_discount_value

    assert line_2.base_unit_price_amount == line_2.undiscounted_base_unit_price_amount
    assert (
        line_2.total_price_gross_amount
        == line_2.undiscounted_base_unit_price_amount * line_2.quantity * tax_rate
    )
    assert (
        line_2.undiscounted_total_price_gross_amount
        == line_2.undiscounted_base_unit_price_amount * line_2.quantity * tax_rate
    )
    assert line_2.unit_discount_amount == 0
    assert line_2.unit_discount_type is None
    assert line_2.unit_discount_reason is None
    assert line_2.unit_discount_value == 0

    assert order.undiscounted_base_shipping_price == undiscounted_shipping_price
    assert order.base_shipping_price == undiscounted_shipping_price
    assert order.shipping_price_net == undiscounted_shipping_price
    assert order.shipping_price_gross == quantize_price(
        undiscounted_shipping_price * tax_rate, currency
    )

    undiscounted_subtotal += line_1.undiscounted_unit_price.net
    assert (
        order.undiscounted_total_net
        == undiscounted_subtotal + undiscounted_shipping_price
    )
    assert (
        order.undiscounted_total_gross
        == (undiscounted_subtotal + undiscounted_shipping_price) * tax_rate
    )
    assert (
        order.subtotal_net_amount == undiscounted_subtotal.amount - new_discount_amount
    )
    assert quantize_price(order.subtotal_gross_amount, currency) == quantize_price(
        order.subtotal_net_amount * tax_rate, currency
    )
    assert (
        order.total_net_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert quantize_price(order.total_gross_amount, currency) == quantize_price(
        (order.undiscounted_total_net_amount - new_discount_amount) * tax_rate,
        currency,
    )


def test_order_line_update_specific_product_voucher_discount_fixed(
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
    tax_configuration_flat_rates,
    voucher,
    plugins_manager,
):
    """The voucher discount should use denormalized voucher values."""

    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    currency = order.currency
    tax_rate = Decimal("1.23")

    lines = order.lines.all()
    line_1, line_2 = lines
    undiscounted_shipping_price = order.undiscounted_base_shipping_price
    undiscounted_subtotal = zero_money(currency)
    for line in lines:
        undiscounted_subtotal += line.undiscounted_base_unit_price * line.quantity

    # apply specific product voucher
    initial_discount_value_type = DiscountValueType.FIXED
    voucher.discount_value_type = initial_discount_value_type
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save(update_fields=["discount_value_type", "type"])
    voucher.variants.add(line_1.variant)
    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    initial_unit_discount = Decimal(2)
    voucher_listing.discount_value = initial_unit_discount
    voucher_listing.save(update_fields=["discount_value"])
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code
    order.save(update_fields=["voucher_code", "voucher_id", "status"])
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    line_1, line_2 = lines
    assert (
        line_1.base_unit_price_amount
        == line_1.undiscounted_base_unit_price_amount - initial_unit_discount
    )
    discount_amount = initial_unit_discount * line_1.quantity
    discount = line_1.discounts.get()
    assert discount.value == initial_unit_discount
    assert discount.value_type == initial_discount_value_type
    assert discount.amount_value == discount_amount

    # update voucher listing value, discount value type and eligible variants
    voucher_listing.discount_value *= 2
    voucher_listing.save(update_fields=["discount_value"])
    assert voucher_listing.discount_value != initial_unit_discount
    new_voucher_discount_value_type = DiscountValueType.PERCENTAGE
    voucher.discount_value_type = new_voucher_discount_value_type
    voucher.save(update_fields=["discount_value_type"])
    assert initial_discount_value_type != new_voucher_discount_value_type
    voucher.variants.set([line_2.variant])

    # add 1 unit to line 1
    new_quantity = line_1.quantity + 1
    line_1_id = graphene.Node.to_global_id("OrderLine", line_1.id)
    variables = {"lineId": line_1_id, "quantity": new_quantity}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderLineUpdate"]
    assert not data["errors"]

    order.refresh_from_db()
    line_1, line_2 = order.lines.all()
    new_discount_amount = initial_unit_discount * new_quantity

    discount.refresh_from_db()
    assert discount.value == initial_unit_discount
    assert discount.value_type == initial_discount_value_type
    assert discount.amount_value == new_discount_amount
    assert discount.type == DiscountType.VOUCHER
    assert discount.reason == f"Voucher code: {order.voucher_code}"

    assert quantize_price(line_1.base_unit_price_amount, currency) == quantize_price(
        line_1.undiscounted_base_unit_price_amount - initial_unit_discount,
        currency,
    )
    assert quantize_price(line_1.total_price_net_amount, currency) == quantize_price(
        line_1.undiscounted_total_price_net_amount - new_discount_amount,
        currency,
    )
    assert quantize_price(line_1.total_price_gross_amount, currency) == quantize_price(
        line_1.base_unit_price_amount * new_quantity * tax_rate, currency
    )
    assert quantize_price(
        line_1.undiscounted_total_price_gross_amount, currency
    ) == quantize_price(
        line_1.undiscounted_base_unit_price_amount * line_1.quantity * tax_rate,
        currency,
    )
    assert line_1.unit_discount_amount == initial_unit_discount
    assert line_1.unit_discount_type == initial_discount_value_type
    assert line_1.unit_discount_reason == f"Voucher code: {order.voucher_code}"
    assert line_1.unit_discount_value == initial_unit_discount

    assert line_2.base_unit_price_amount == line_2.undiscounted_base_unit_price_amount
    assert (
        line_2.total_price_gross_amount
        == line_2.undiscounted_base_unit_price_amount * line_2.quantity * tax_rate
    )
    assert (
        line_2.undiscounted_total_price_gross_amount
        == line_2.undiscounted_base_unit_price_amount * line_2.quantity * tax_rate
    )
    assert line_2.unit_discount_amount == 0
    assert line_2.unit_discount_type is None
    assert line_2.unit_discount_reason is None
    assert line_2.unit_discount_value == 0

    assert order.undiscounted_base_shipping_price == undiscounted_shipping_price
    assert order.base_shipping_price == undiscounted_shipping_price
    assert order.shipping_price_net == undiscounted_shipping_price
    assert order.shipping_price_gross == quantize_price(
        undiscounted_shipping_price * tax_rate, currency
    )

    undiscounted_subtotal += line_1.undiscounted_unit_price.net
    assert (
        order.undiscounted_total_net
        == undiscounted_subtotal + undiscounted_shipping_price
    )
    assert (
        order.undiscounted_total_gross
        == (undiscounted_subtotal + undiscounted_shipping_price) * tax_rate
    )
    assert (
        order.subtotal_net_amount == undiscounted_subtotal.amount - new_discount_amount
    )
    assert quantize_price(order.subtotal_gross_amount, currency) == quantize_price(
        order.subtotal_net_amount * tax_rate, currency
    )
    assert (
        order.total_net_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert quantize_price(order.total_gross_amount, currency) == quantize_price(
        (order.undiscounted_total_net_amount - new_discount_amount) * tax_rate,
        currency,
    )


def test_order_line_update_specific_product_voucher_discount_multiple_lines(
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
    tax_configuration_flat_rates,
    voucher,
    plugins_manager,
):
    """The voucher discount should use denormalized voucher values."""

    query = ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    currency = order.currency
    tax_rate = Decimal("1.23")

    lines = order.lines.all()
    line_1, line_2 = lines
    undiscounted_shipping_price = order.undiscounted_base_shipping_price
    undiscounted_subtotal = zero_money(currency)
    for line in lines:
        undiscounted_subtotal += line.undiscounted_base_unit_price * line.quantity

    # apply specific product voucher
    initial_discount_value_type = DiscountValueType.FIXED
    voucher.discount_value_type = initial_discount_value_type
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save(update_fields=["discount_value_type", "type"])
    voucher.variants.set([line_1.variant, line_2.variant])
    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    initial_unit_discount = Decimal(2)
    voucher_listing.discount_value = initial_unit_discount
    voucher_listing.save(update_fields=["discount_value"])
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code
    order.save(update_fields=["voucher_code", "voucher_id", "status"])
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    line_1, line_2 = lines
    assert (
        line_1.base_unit_price_amount
        == line_1.undiscounted_base_unit_price_amount - initial_unit_discount
    )
    discount_amount_1 = initial_unit_discount * line_1.quantity
    discount_1 = line_1.discounts.get()
    assert discount_1.value == initial_unit_discount
    assert discount_1.value_type == initial_discount_value_type
    assert discount_1.amount_value == discount_amount_1

    assert (
        line_2.base_unit_price_amount
        == line_2.undiscounted_base_unit_price_amount - initial_unit_discount
    )
    discount_amount_2 = initial_unit_discount * line_2.quantity
    discount_2 = line_2.discounts.get()
    assert discount_2.value == initial_unit_discount
    assert discount_2.value_type == initial_discount_value_type
    assert discount_2.amount_value == discount_amount_2

    # update voucher listing value, discount value type and eligible variants
    voucher_listing.discount_value *= 2
    voucher_listing.save(update_fields=["discount_value"])
    assert voucher_listing.discount_value != initial_unit_discount
    new_voucher_discount_value_type = DiscountValueType.PERCENTAGE
    voucher.discount_value_type = new_voucher_discount_value_type
    voucher.save(update_fields=["discount_value_type"])
    assert initial_discount_value_type != new_voucher_discount_value_type
    voucher.variants.set([])

    # add 1 unit to line 1
    new_quantity_1 = line_1.quantity + 1
    line_1_id = graphene.Node.to_global_id("OrderLine", line_1.id)
    variables = {"lineId": line_1_id, "quantity": new_quantity_1}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderLineUpdate"]
    assert not data["errors"]

    order.refresh_from_db()
    line_1, line_2 = order.lines.all()
    new_discount_amount_1 = initial_unit_discount * new_quantity_1

    discount_1.refresh_from_db()
    assert discount_1.value == initial_unit_discount
    assert discount_1.value_type == initial_discount_value_type
    assert discount_1.amount_value == new_discount_amount_1
    assert discount_1.type == DiscountType.VOUCHER
    assert discount_1.reason == f"Voucher code: {order.voucher_code}"

    assert quantize_price(line_1.base_unit_price_amount, currency) == quantize_price(
        line_1.undiscounted_base_unit_price_amount - initial_unit_discount,
        currency,
    )
    assert quantize_price(line_1.total_price_net_amount, currency) == quantize_price(
        line_1.undiscounted_total_price_net_amount - new_discount_amount_1,
        currency,
    )
    assert quantize_price(line_1.total_price_gross_amount, currency) == quantize_price(
        line_1.base_unit_price_amount * new_quantity_1 * tax_rate, currency
    )
    assert quantize_price(
        line_1.undiscounted_total_price_gross_amount, currency
    ) == quantize_price(
        line_1.undiscounted_base_unit_price_amount * line_1.quantity * tax_rate,
        currency,
    )
    assert line_1.unit_discount_amount == initial_unit_discount
    assert line_1.unit_discount_type == initial_discount_value_type
    assert line_1.unit_discount_reason == f"Voucher code: {order.voucher_code}"
    assert line_1.unit_discount_value == initial_unit_discount

    discount_2.refresh_from_db()
    assert discount_2.value == initial_unit_discount
    assert discount_2.value_type == initial_discount_value_type
    assert discount_2.amount_value == discount_amount_2
    assert discount_2.type == DiscountType.VOUCHER
    assert discount_2.reason == f"Voucher code: {order.voucher_code}"

    assert quantize_price(line_2.base_unit_price_amount, currency) == quantize_price(
        line_2.undiscounted_base_unit_price_amount - initial_unit_discount,
        currency,
    )
    assert quantize_price(line_2.total_price_net_amount, currency) == quantize_price(
        line_2.undiscounted_total_price_net_amount - discount_amount_2,
        currency,
    )
    assert quantize_price(line_2.total_price_gross_amount, currency) == quantize_price(
        line_2.base_unit_price_amount * line_2.quantity * tax_rate, currency
    )
    assert quantize_price(
        line_2.undiscounted_total_price_gross_amount, currency
    ) == quantize_price(
        line_2.undiscounted_base_unit_price_amount * line_2.quantity * tax_rate,
        currency,
    )
    assert line_2.unit_discount_amount == initial_unit_discount
    assert line_2.unit_discount_type == initial_discount_value_type
    assert line_2.unit_discount_reason == f"Voucher code: {order.voucher_code}"
    assert line_2.unit_discount_value == initial_unit_discount

    assert order.undiscounted_base_shipping_price == undiscounted_shipping_price
    assert order.base_shipping_price == undiscounted_shipping_price
    assert order.shipping_price_net == undiscounted_shipping_price
    assert order.shipping_price_gross == quantize_price(
        undiscounted_shipping_price * tax_rate, currency
    )

    undiscounted_subtotal += line_1.undiscounted_unit_price.net
    assert (
        order.undiscounted_total_net
        == undiscounted_subtotal + undiscounted_shipping_price
    )
    assert (
        order.undiscounted_total_gross
        == (undiscounted_subtotal + undiscounted_shipping_price) * tax_rate
    )
    assert (
        order.subtotal_net_amount
        == undiscounted_subtotal.amount - new_discount_amount_1 - discount_amount_2
    )
    assert quantize_price(order.subtotal_gross_amount, currency) == quantize_price(
        order.subtotal_net_amount * tax_rate, currency
    )
    assert (
        order.total_net_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert quantize_price(order.total_gross_amount, currency) == quantize_price(
        (
            order.undiscounted_total_net_amount
            - new_discount_amount_1
            - discount_amount_2
        )
        * tax_rate,
        currency,
    )
