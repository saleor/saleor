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
from .....shipping import IncoTerm
from .....tax.models import TaxClass, TaxClassCountryRate
from .....warehouse.models import Allocation, Stock
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....tests.utils import assert_no_permission, get_graphql_content
from ..utils import assert_proper_webhook_called_once

# NOTE: Line-level tax rounding (Xero-style)
# Total gross is computed as: line_net + round(line_net * tax_rate / 100)
# rather than: unit_gross * quantity.
# This means total_price_gross_amount != unit_price_gross_amount * quantity
# by up to 1 penny. This is intentional to match Xero's rounding behaviour.
# We assert net totals (which are always exact) instead of gross.
# Order-level discounts will be deprecated to avoid compounding rounding issues.

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
        MessageGroupId="example.com:saleorappadditional",
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
        line_1.unit_price_net_amount * line_1.quantity,
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
        line_1.unit_price_net_amount * line_1.quantity,
        currency,
    )
    assert (
        line_1.undiscounted_total_price_net_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity
    )
    assert line_1.unit_discount_amount == new_unit_discount_amount
    assert line_1.unit_discount_type == initial_discount_value_type
    assert line_1.unit_discount_reason == f"Voucher code: {order.voucher_code}"
    assert line_1.unit_discount_value == initial_discount_value

    assert line_2.base_unit_price_amount == line_2.undiscounted_base_unit_price_amount
    assert (
        line_2.total_price_net_amount
        == line_2.undiscounted_base_unit_price_amount * line_2.quantity
    )
    assert (
        line_2.undiscounted_total_price_net_amount
        == line_2.undiscounted_base_unit_price_amount * line_2.quantity
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
    assert order.subtotal_net_amount == (
        line_1.total_price_net_amount + line_2.total_price_net_amount
    )
    assert order.subtotal_gross_amount == (
        line_1.total_price_gross_amount + line_2.total_price_gross_amount
    )
    assert (
        order.total_net_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert order.total_gross_amount == (
        order.subtotal_gross_amount + order.shipping_price_gross_amount
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
        line_1.unit_price_gross_amount * new_quantity, currency
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
        line_1.unit_price_gross_amount * new_quantity, currency
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


ORDER_LINE_UPDATE_WITH_PRICE_MUTATION = """
    mutation OrderLineUpdate($lineId: ID!, $quantity: Int!, $price: PositiveDecimal) {
        orderLineUpdate(id: $lineId, input: {quantity: $quantity, price: $price}) {
            errors {
                field
                message
                code
            }
            orderLine {
                id
                quantity
                unitPrice {
                    gross {
                        amount
                    }
                }
                undiscountedUnitPrice {
                    gross {
                        amount
                    }
                }
            }
        }
    }
"""


def test_order_line_update_with_custom_price_on_draft_order(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    line = order.lines.first()
    original_price = line.unit_price_gross_amount
    new_price = Decimal("99.99")
    assert original_price != new_price

    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"lineId": line_id, "quantity": line.quantity, "price": str(new_price)}

    response = staff_api_client.post_graphql(
        ORDER_LINE_UPDATE_WITH_PRICE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["orderLineUpdate"]

    assert not data["errors"]
    assert data["orderLine"]["quantity"] == line.quantity
    assert Decimal(data["orderLine"]["unitPrice"]["gross"]["amount"]) == pytest.approx(
        new_price, rel=Decimal("0.0001")
    )
    assert Decimal(
        data["orderLine"]["undiscountedUnitPrice"]["gross"]["amount"]
    ) == pytest.approx(new_price, rel=Decimal("0.0001"))

    line.refresh_from_db()
    assert line.unit_price_gross_amount == new_price
    assert line.undiscounted_unit_price_gross_amount == new_price


def test_order_line_update_with_custom_price_on_unconfirmed_order(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])

    line = order.lines.first()
    original_price = line.unit_price_gross_amount
    new_price = Decimal("99.99")
    assert original_price != new_price

    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"lineId": line_id, "quantity": line.quantity, "price": str(new_price)}

    response = staff_api_client.post_graphql(
        ORDER_LINE_UPDATE_WITH_PRICE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["orderLineUpdate"]

    assert not data["errors"]
    assert data["orderLine"]["quantity"] == line.quantity
    assert Decimal(data["orderLine"]["unitPrice"]["gross"]["amount"]) == pytest.approx(
        new_price, rel=Decimal("0.0001")
    )
    assert Decimal(
        data["orderLine"]["undiscountedUnitPrice"]["gross"]["amount"]
    ) == pytest.approx(new_price, rel=Decimal("0.0001"))

    line.refresh_from_db()
    assert line.unit_price_gross_amount == new_price
    assert line.undiscounted_unit_price_gross_amount == new_price


def test_order_line_update_with_custom_price_on_confirmed_order_fails(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.status = OrderStatus.UNFULFILLED
    order.save(update_fields=["status"])

    line = order.lines.first()
    new_price = Decimal("99.99")

    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"lineId": line_id, "quantity": line.quantity, "price": str(new_price)}

    response = staff_api_client.post_graphql(
        ORDER_LINE_UPDATE_WITH_PRICE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["orderLineUpdate"]

    assert data["errors"]
    assert data["errors"][0]["field"] == "price"
    assert data["errors"][0]["code"] == OrderErrorCode.CANNOT_DISCOUNT.name


def test_order_line_update_quantity_without_price_still_works(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    line = order.lines.first()
    original_price = line.unit_price_gross_amount
    original_quantity = line.quantity
    new_quantity = original_quantity + 1

    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"lineId": line_id, "quantity": new_quantity, "price": None}

    response = staff_api_client.post_graphql(
        ORDER_LINE_UPDATE_WITH_PRICE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["orderLineUpdate"]

    assert not data["errors"]
    assert data["orderLine"]["quantity"] == new_quantity

    line.refresh_from_db()
    assert line.quantity == new_quantity
    assert line.unit_price_gross_amount == original_price


def test_order_line_update_both_quantity_and_price(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    line = order.lines.first()
    original_quantity = line.quantity
    new_quantity = original_quantity + 2
    new_price = Decimal("49.99")

    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"lineId": line_id, "quantity": new_quantity, "price": str(new_price)}

    response = staff_api_client.post_graphql(
        ORDER_LINE_UPDATE_WITH_PRICE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["orderLineUpdate"]

    assert not data["errors"]
    assert data["orderLine"]["quantity"] == new_quantity
    assert Decimal(data["orderLine"]["unitPrice"]["gross"]["amount"]) == pytest.approx(
        new_price, rel=Decimal("0.0001")
    )

    line.refresh_from_db()
    assert line.quantity == new_quantity
    assert line.unit_price_gross_amount == new_price


ORDER_LINE_UPDATE_WITH_TAX_CLASS_MUTATION = """
    mutation OrderLineUpdate($lineId: ID!, $quantity: Int!, $taxClassId: ID!) {
        orderLineUpdate(id: $lineId, input: {quantity: $quantity, taxClass: $taxClassId}) {
            errors { field code message }
            orderLine { id }
        }
    }
"""

ORDER_LINE_UPDATE_WITH_INVALID_TAX_CLASS_MUTATION = """
    mutation OrderLineUpdate($lineId: ID!, $quantity: Int!, $taxClassId: ID!) {
        orderLineUpdate(id: $lineId, input: {quantity: $quantity, taxClass: $taxClassId}) {
            errors { field code message }
            orderLine { id }
        }
    }
"""


def test_order_line_update_with_tax_class(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    tax_classes,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    line = order.lines.first()
    override_tax_class = tax_classes[0]
    line.variant.product.tax_class = tax_classes[1]
    line.variant.product.save(update_fields=["tax_class"])

    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    tax_class_id = graphene.Node.to_global_id("TaxClass", override_tax_class.id)

    variables = {
        "lineId": line_id,
        "quantity": line.quantity,
        "taxClassId": tax_class_id,
    }

    # when
    response = staff_api_client.post_graphql(
        ORDER_LINE_UPDATE_WITH_TAX_CLASS_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["orderLineUpdate"]["errors"]

    line.refresh_from_db()
    assert line.tax_class_id == override_tax_class.id
    assert line.tax_class_id != line.variant.product.tax_class_id


def test_order_line_update_with_invalid_tax_class(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    invalid_tax_class_id = graphene.Node.to_global_id("TaxClass", 0)

    variables = {
        "lineId": line_id,
        "quantity": line.quantity,
        "taxClassId": invalid_tax_class_id,
    }

    # when
    response = staff_api_client.post_graphql(
        ORDER_LINE_UPDATE_WITH_INVALID_TAX_CLASS_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["orderLineUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "taxClass"
    assert errors[0]["code"] == OrderErrorCode.NOT_FOUND.name


# ── Mutations that do NOT request unitPrice, so the price-refresh resolver
# ── does not auto-reset should_refresh_prices before we can check it. ──────

ORDER_LINE_UPDATE_QUANTITY_ONLY_MUTATION = """
    mutation OrderLineUpdateQty($lineId: ID!, $quantity: Int!) {
        orderLineUpdate(id: $lineId, input: {quantity: $quantity}) {
            errors { field code message }
            orderLine { id quantity }
        }
    }
"""

ORDER_LINE_UPDATE_TAX_CLASS_NO_PRICE_MUTATION = """
    mutation OrderLineUpdateTaxClass($lineId: ID!, $quantity: Int!, $taxClassId: ID!) {
        orderLineUpdate(id: $lineId, input: {quantity: $quantity, taxClass: $taxClassId}) {
            errors { field code message }
            orderLine { id }
        }
    }
"""


def test_order_line_update_price_sets_base_unit_price(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
):
    # Arrange
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    line = order.lines.first()
    new_price = Decimal("50.00")

    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"lineId": line_id, "quantity": line.quantity, "price": str(new_price)}

    # Act
    response = staff_api_client.post_graphql(
        ORDER_LINE_UPDATE_WITH_PRICE_MUTATION, variables
    )
    content = get_graphql_content(response)

    # Assert
    assert not content["data"]["orderLineUpdate"]["errors"]

    line.refresh_from_db()
    # base_unit_price stores the entered value that the tax engine works from.
    assert line.base_unit_price_amount == new_price
    assert line.undiscounted_base_unit_price_amount == new_price


def test_order_line_update_quantity_only_does_not_set_should_refresh_prices(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
):
    # Arrange
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.should_refresh_prices = False
    order.save(update_fields=["status", "should_refresh_prices"])

    line = order.lines.first()
    new_quantity = line.quantity + 1
    line_id = graphene.Node.to_global_id("OrderLine", line.id)

    # Act – uses a mutation that does NOT request unitPrice, so the resolver
    # cannot reset should_refresh_prices before we assert.
    response = staff_api_client.post_graphql(
        ORDER_LINE_UPDATE_QUANTITY_ONLY_MUTATION,
        {"lineId": line_id, "quantity": new_quantity},
    )
    content = get_graphql_content(response)

    # Assert
    assert not content["data"]["orderLineUpdate"]["errors"]
    assert content["data"]["orderLineUpdate"]["orderLine"]["quantity"] == new_quantity

    order.refresh_from_db()
    # A quantity-only update must not mark prices as stale – the unit price
    # did not change, so no tax recalculation is needed.
    assert order.should_refresh_prices is False


def test_order_line_update_tax_class_sets_should_refresh_prices(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    tax_classes,
):
    # Arrange
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.should_refresh_prices = False
    order.save(update_fields=["status", "should_refresh_prices"])

    line = order.lines.first()
    tax_class = tax_classes[0]
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    tax_class_id = graphene.Node.to_global_id("TaxClass", tax_class.id)

    # Act – uses a mutation that does NOT request unitPrice so the resolver
    # does not auto-reset should_refresh_prices before we can read it.
    response = staff_api_client.post_graphql(
        ORDER_LINE_UPDATE_TAX_CLASS_NO_PRICE_MUTATION,
        {"lineId": line_id, "quantity": line.quantity, "taxClassId": tax_class_id},
    )
    content = get_graphql_content(response)

    # Assert
    assert not content["data"]["orderLineUpdate"]["errors"]

    order.refresh_from_db()
    # Changing the tax class must invalidate prices so the flat-rate tax
    # engine recalculates with the new class's rate.
    assert order.should_refresh_prices is True


def test_order_line_update_tax_class_snapshots_xero_tax_code(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
):
    # given - DDP order with a shipping address in PL (the order fixture default).
    # Changing the tax class should snapshot the PL rate's xero_tax_code.
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.inco_term = IncoTerm.DDP
    order.save(update_fields=["status", "inco_term"])

    new_tax_class = TaxClass.objects.create(name="Reduced PL")
    pl_rate = TaxClassCountryRate.objects.create(
        tax_class=new_tax_class, country="PL", rate=8, xero_tax_code="REDUCEDPL"
    )

    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    tax_class_id = graphene.Node.to_global_id("TaxClass", new_tax_class.id)

    # when
    response = staff_api_client.post_graphql(
        ORDER_LINE_UPDATE_TAX_CLASS_NO_PRICE_MUTATION,
        {"lineId": line_id, "quantity": line.quantity, "taxClassId": tax_class_id},
    )
    content = get_graphql_content(response)

    # then - xero_tax_code and tax_class_country_rate are snapshotted from the PL rate.
    assert not content["data"]["orderLineUpdate"]["errors"]
    line.refresh_from_db()
    assert line.xero_tax_code == "REDUCEDPL"
    assert line.tax_class_country_rate == pl_rate


def test_order_line_update_tax_class_dap_xero_tax_code_is_null(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
):
    # given - DAP order: zero-rated export, so xero_tax_code must be null regardless
    # of what rates exist for the tax class.
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.inco_term = IncoTerm.DAP
    order.save(update_fields=["status", "inco_term"])

    new_tax_class = TaxClass.objects.create(name="Standard")
    TaxClassCountryRate.objects.create(
        tax_class=new_tax_class, country="PL", rate=23, xero_tax_code="OUTPUT2"
    )

    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    tax_class_id = graphene.Node.to_global_id("TaxClass", new_tax_class.id)

    # when
    response = staff_api_client.post_graphql(
        ORDER_LINE_UPDATE_TAX_CLASS_NO_PRICE_MUTATION,
        {"lineId": line_id, "quantity": line.quantity, "taxClassId": tax_class_id},
    )
    content = get_graphql_content(response)

    # then - DAP → no country lookup → xero_tax_code is null.
    assert not content["data"]["orderLineUpdate"]["errors"]
    line.refresh_from_db()
    assert line.xero_tax_code is None
    assert line.tax_class_country_rate is None
