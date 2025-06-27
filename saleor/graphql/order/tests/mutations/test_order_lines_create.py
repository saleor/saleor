import datetime
from datetime import timedelta
from decimal import Decimal
from unittest.mock import ANY, patch

import graphene
import pytest
from django.db.models import Sum
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time

from .....core.models import EventDelivery
from .....core.prices import quantize_price
from .....core.taxes import zero_money
from .....discount import DiscountType, DiscountValueType, RewardValueType, VoucherType
from .....discount.models import OrderLineDiscount, PromotionRule
from .....discount.utils.voucher import (
    create_or_update_voucher_discount_objects_for_order,
)
from .....order import OrderStatus
from .....order import events as order_events
from .....order.actions import call_order_event
from .....order.calculations import fetch_order_prices_if_expired
from .....order.error_codes import OrderErrorCode
from .....order.models import OrderEvent, OrderLine
from .....product.models import Product, ProductVariant
from .....product.utils.variant_prices import update_discounted_prices_for_promotion
from .....product.utils.variants import fetch_variants_for_promotion_rules
from .....warehouse.models import Allocation, Stock
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....tests.utils import assert_no_permission, get_graphql_content
from ..utils import assert_proper_webhook_called_once

ORDER_LINES_CREATE_MUTATION = """
    mutation OrderLinesCreate(
            $orderId: ID!,
            $variantId: ID!,
            $quantity: Int!,
            $forceNewLine: Boolean,
            $price: PositiveDecimal,
        ) {
        orderLinesCreate(id: $orderId,
                input: [
                    {
                        variantId: $variantId,
                        quantity: $quantity,
                        forceNewLine: $forceNewLine,
                        price: $price
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
                saleId
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
                unitDiscount {
                  amount
                }
                isPriceOverridden
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
def test_order_lines_create_with_out_of_stock_webhook(
    product_variant_out_of_stock_webhook_mock,
    order_with_lines,
    permission_group_manage_orders,
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

    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    permission_group_manage_orders,
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

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    staff_api_client.post_graphql(query, variables)
    product_variant_out_of_stock_webhook_mock.assert_called_once_with(
        Stock.objects.all()[3]
    )


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_order_lines_create(
    product_variant_out_of_stock_webhook_mock,
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
    variant_with_many_stocks,
):
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    lines_count = order.lines.count()
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    order.refresh_from_db()
    assert order.lines_count == lines_count + 1

    # mutation should fail when quantity is lower than 1
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": 0}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["errors"]
    assert data["errors"][0]["field"] == "quantity"
    assert data["errors"][0]["variants"] == [variant_id]
    product_variant_out_of_stock_webhook_mock.assert_not_called()


def test_order_lines_create_by_user_no_channel_access(
    order_with_lines,
    permission_group_all_perms_channel_USD_only,
    staff_api_client,
    variant_with_many_stocks,
    channel_PLN,
):
    # given
    query = ORDER_LINES_CREATE_MUTATION
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)

    order = order_with_lines
    order.channel = channel_PLN
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status", "channel"])

    variant = variant_with_many_stocks
    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_by_app(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    order_with_lines,
    permission_manage_orders,
    app_api_client,
    variant_with_many_stocks,
    channel_PLN,
):
    # given
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    lines_count = order.lines.count()
    variant = variant_with_many_stocks
    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["orderLines"][0]["productSku"] == variant.sku
    assert data["orderLines"][0]["productVariantId"] == variant.get_global_id()
    assert data["orderLines"][0]["quantity"] == quantity

    assert OrderEvent.objects.count() == 1
    event = OrderEvent.objects.last()
    assert event.type == order_events.OrderEvents.ADDED_PRODUCTS
    assert len(event.parameters["lines"]) == 1
    line = OrderLine.objects.last()
    assert event.parameters["lines"] == [
        {"item": str(line), "line_pk": str(line.pk), "quantity": quantity}
    ]
    assert_proper_webhook_called_once(
        order,
        OrderStatus.UNCONFIRMED,
        draft_order_updated_webhook_mock,
        order_updated_webhook_mock,
    )
    order.refresh_from_db()
    assert order.lines_count == lines_count + 1


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_order_lines_create_for_just_published_product(
    product_variant_out_of_stock_webhook_mock,
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_group_manage_orders,
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
    product_listing.published_at = datetime.datetime.now(tz=datetime.UTC)
    product_listing.save(update_fields=["published_at"])

    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    permission_group_manage_orders,
    staff_api_client,
):
    query = ORDER_LINES_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    channel = order.channel
    line = order.lines.first()
    variant = line.variant
    variant.channel_listings.filter(channel=channel).update(price_amount=None)
    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    error = content["data"]["orderLinesCreate"]["errors"][0]
    assert error["code"] == OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.name
    assert error["field"] == "input"
    assert error["variants"] == [variant_id]
    order_updated_webhook_mock.assert_not_called()
    draft_order_updated_webhoook_mock.assert_not_called()


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
def test_order_lines_create_when_some_line_has_deleted_product(
    status,
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
):
    query = ORDER_LINES_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    line = order.lines.first()
    line2 = order.lines.last()
    assert line.variant != line2.variant
    line2.variant = None
    line2.save(update_fields=["variant"])
    order.status = status
    order.save(update_fields=["status"])

    variant = line.variant
    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]

    assert data["orderLines"][0]["productSku"] == variant.sku
    assert data["orderLines"][0]["productVariantId"] == variant.get_global_id()
    assert data["orderLines"][0]["quantity"] == line.quantity + quantity


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_with_existing_variant(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_group_manage_orders,
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_with_same_variant_and_force_new_line(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
):
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    lines = order.lines.all()
    lines_count = len(lines)
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    response = staff_api_client.post_graphql(query, variables)

    order.refresh_from_db()
    assert order.lines.count() == lines_count + 1
    assert order.lines_count == lines_count + 1
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


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_when_variant_already_in_multiple_lines(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_group_manage_orders,
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

    lines_count = order.lines.count()

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
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    response = staff_api_client.post_graphql(ORDER_LINES_CREATE_MUTATION, variables)

    order.refresh_from_db()
    assert order.lines.count() == lines_count + 1
    assert order.lines_count == lines_count + 1
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


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_variant_on_promotion(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
    variant_with_many_stocks,
    catalogue_promotion_without_rules,
    promotion_translation_fr,
    promotion_rule_translation_fr,
):
    # given
    query = ORDER_LINES_CREATE_MUTATION

    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])

    variant = variant_with_many_stocks

    reward_value = Decimal(5)
    rule = catalogue_promotion_without_rules.rules.create(
        name="Promotion rule",
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", variant.product.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(order.channel)

    variant_channel_listing = variant.channel_listings.get(channel=order.channel)
    variant_channel_listing.discounted_price_amount = (
        variant_channel_listing.price.amount - reward_value
    )
    variant_channel_listing.save(update_fields=["discounted_price_amount"])

    variant_channel_listing.variantlistingpromotionrule.create(
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=order.channel.currency_code,
    )

    promotion_translation_fr.promotion = catalogue_promotion_without_rules
    promotion_translation_fr.language_code = order.language_code
    promotion_translation_fr.save(update_fields=["promotion", "language_code"])

    promotion_rule_translation_fr.promotion_rule = rule
    promotion_rule_translation_fr.language_code = order.language_code
    promotion_rule_translation_fr.save(
        update_fields=["promotion_rule", "language_code"]
    )

    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    permission_group_manage_orders.user_set.add(staff_api_client.user)

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

    assert (
        line_data["unitPrice"]["gross"]["amount"]
        == variant_channel_listing.price_amount - reward_value
    )
    assert (
        line_data["unitPrice"]["net"]["amount"]
        == variant_channel_listing.price_amount - reward_value
    )
    assert line_data["saleId"] == graphene.Node.to_global_id(
        "Promotion", catalogue_promotion_without_rules.id
    )

    line = order.lines.get(product_sku=variant.sku)
    assert line.sale_id == graphene.Node.to_global_id(
        "Promotion", catalogue_promotion_without_rules.id
    )
    assert line.unit_discount_amount == reward_value
    assert line.unit_discount_value == reward_value
    assert line.unit_discount_reason == f"Promotion: {line.sale_id}"
    assert line.discounts.count() == 1
    discount = line.discounts.first()
    assert discount.promotion_rule == rule
    assert discount.amount_value == reward_value
    assert discount.type == DiscountType.PROMOTION
    assert discount.name == f"{catalogue_promotion_without_rules.name}: {rule.name}"
    assert (
        discount.translated_name
        == f"{promotion_translation_fr.name}: {promotion_rule_translation_fr.name}"
    )


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_order_promotion(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
    variant_with_many_stocks,
    order_promotion_rule,
):
    # given
    query = ORDER_LINES_CREATE_MUTATION

    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    order.lines.all().delete()

    rule = order_promotion_rule
    promotion_id = graphene.Node.to_global_id("Promotion", rule.promotion_id)
    assert rule.reward_value_type == RewardValueType.PERCENTAGE
    assert rule.reward_value == Decimal(25)

    variant = variant_with_many_stocks
    quantity = 5
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variant_channel_listing = variant.channel_listings.get(channel=order.channel)
    expected_discount = round(
        quantity * variant_channel_listing.discounted_price.amount * Decimal(0.25), 2
    )
    expected_unit_discount = round(expected_discount / quantity, 2)

    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

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
    assert line_data["unitDiscount"]["amount"] == 0.00
    assert (
        line_data["unitPrice"]["gross"]["amount"]
        == variant_channel_listing.price_amount - expected_unit_discount
    )
    assert (
        line_data["unitPrice"]["net"]["amount"]
        == variant_channel_listing.price_amount - expected_unit_discount
    )

    line = order.lines.get(product_sku=variant.sku)
    assert line.unit_discount_amount == 0
    assert (
        line.unit_price_gross_amount
        == variant_channel_listing.discounted_price.amount - expected_unit_discount
    )

    assert len(data["order"]["discounts"]) == 1
    discount = data["order"]["discounts"][0]
    assert discount["amount"]["amount"] == expected_discount

    discount = order.discounts.get()
    assert discount.promotion_rule == rule
    assert discount.amount_value == expected_discount
    assert discount.type == DiscountType.ORDER_PROMOTION
    assert discount.reason == f"Promotion: {promotion_id}"


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_gift_promotion(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
    variant_with_many_stocks,
    gift_promotion_rule,
):
    # given
    query = ORDER_LINES_CREATE_MUTATION

    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    order.lines.all().delete()

    rule = gift_promotion_rule
    promotion_id = graphene.Node.to_global_id("Promotion", rule.promotion_id)

    variant = variant_with_many_stocks
    quantity = 5
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

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

    lines = data["orderLines"]
    # gift line is not returned
    assert len(lines) == 1

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


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_with_product_and_variant_not_assigned_to_channel(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    status,
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
    variant,
):
    query = ORDER_LINES_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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

    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    error = content["data"]["orderLinesCreate"]["errors"][0]
    assert error["code"] == OrderErrorCode.PRODUCT_NOT_PUBLISHED.name
    assert error["field"] == "input"
    assert error["variants"] == [variant_id]
    order_updated_webhook_mock.assert_not_called()
    draft_order_updated_webhook_mock.assert_not_called()


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_with_variant_not_assigned_to_channel(
    order_update_webhook_mock,
    draft_order_update_webhook_mock,
    status,
    order_with_lines,
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    shipping_method,
    variant,
    channel_USD,
    graphql_address_data,
):
    query = ORDER_LINES_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    line = order.lines.first()
    assert variant != line.variant
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": 1}
    variant.channel_listings.all().delete()

    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    error = content["data"]["orderLinesCreate"]["errors"][0]
    assert error["code"] == OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.name
    assert error["field"] == "input"
    assert error["variants"] == [variant_id]
    order_update_webhook_mock.assert_not_called()
    draft_order_update_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
def test_order_lines_create_without_sku(
    product_variant_out_of_stock_webhook_mock,
    status,
    order_with_lines,
    permission_group_manage_orders,
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    permission_group_manage_orders,
):
    query = ORDER_LINES_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    line = order.lines.first()
    variant = line.variant
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": 1}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["errors"]
    order_updated_webhook_mock.assert_not_called()
    draft_order_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_with_custom_price(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
):
    # give
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    order_line = order.lines.first()
    old_qty = order_line.quantity

    lines_count = len(order.lines.all())

    variant = order_line.variant
    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    custom_price = 18
    force_new_line = False
    variables = {
        "orderId": order_id,
        "variantId": variant_id,
        "quantity": quantity,
        "price": custom_price,
        "forceNewLine": force_new_line,
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    new_qty = quantity + old_qty
    assert_proper_webhook_called_once(
        order,
        order.status,
        draft_order_updated_webhook_mock,
        order_updated_webhook_mock,
    )
    assert OrderEvent.objects.count() == 1

    event = OrderEvent.objects.last()
    assert event.type == order_events.OrderEvents.ADDED_PRODUCTS
    assert len(event.parameters["lines"]) == 1
    assert len(order.lines.all()) == lines_count

    order_line.refresh_from_db()
    assert order_line.undiscounted_base_unit_price_amount == custom_price
    assert order_line.base_unit_price_amount == custom_price
    assert event.parameters["lines"] == [
        {"item": str(order_line), "line_pk": str(order_line.pk), "quantity": new_qty}
    ]

    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["orderLines"][0]["productSku"] == variant.sku
    assert data["orderLines"][0]["productVariantId"] == variant.get_global_id()
    assert data["orderLines"][0]["quantity"] == new_qty
    assert data["orderLines"][0]["isPriceOverridden"] is True


@patch("saleor.plugins.manager.PluginsManager.draft_order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_lines_create_with_custom_price_force_new_line(
    order_updated_webhook_mock,
    draft_order_updated_webhook_mock,
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
):
    # give
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    order_line = order.lines.first()

    lines_count = len(order.lines.all())

    variant = order_line.variant
    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    custom_price = 18
    force_new_line = True
    variables = {
        "orderId": order_id,
        "variantId": variant_id,
        "quantity": quantity,
        "price": custom_price,
        "forceNewLine": force_new_line,
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    assert_proper_webhook_called_once(
        order,
        order.status,
        draft_order_updated_webhook_mock,
        order_updated_webhook_mock,
    )
    assert OrderEvent.objects.count() == 1
    event = OrderEvent.objects.last()
    assert event.type == order_events.OrderEvents.ADDED_PRODUCTS
    assert len(event.parameters["lines"]) == 1

    order.refresh_from_db()
    assert order.lines.count() == lines_count + 1
    assert order.lines_count == lines_count + 1

    line = OrderLine.objects.last()
    assert line.undiscounted_base_unit_price_amount == custom_price
    assert line.base_unit_price_amount == custom_price
    assert event.parameters["lines"] == [
        {"item": str(line), "line_pk": str(line.pk), "quantity": quantity}
    ]

    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert data["orderLines"][0]["productSku"] == variant.sku
    assert data["orderLines"][0]["productVariantId"] == variant.get_global_id()
    assert data["orderLines"][0]["quantity"] == quantity
    assert data["orderLines"][0]["isPriceOverridden"] is True


def test_order_lines_create_with_custom_price_and_catalogue_discount(
    order_line_on_promotion,
    permission_group_manage_orders,
    staff_api_client,
):
    # give
    query = ORDER_LINES_CREATE_MUTATION
    order_line = order_line_on_promotion
    order = order_line.order
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    old_qty = order_line.quantity

    lines_count = len(order.lines.all())

    variant = order_line.variant
    variant_listings = variant.channel_listings.get(channel=order.channel)
    promotion_rule = variant_listings.promotion_rules.first()
    promotion_rule.variants.add(variant)
    reward_value = promotion_rule.reward_value
    assert promotion_rule.reward_value_type == DiscountValueType.FIXED

    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    custom_price = 18
    force_new_line = False
    variables = {
        "orderId": order_id,
        "variantId": variant_id,
        "quantity": quantity,
        "price": custom_price,
        "forceNewLine": force_new_line,
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)

    new_qty = quantity + old_qty

    order.refresh_from_db()
    assert order.lines.count() == lines_count
    assert order.lines_count == lines_count
    order_line.refresh_from_db()
    data = content["data"]["orderLinesCreate"]
    line_data = data["orderLines"][0]
    assert line_data["productSku"] == variant.sku
    assert line_data["productVariantId"] == variant.get_global_id()
    assert line_data["quantity"] == new_qty
    assert line_data["isPriceOverridden"] is True
    assert line_data["undiscountedUnitPrice"]["gross"]["amount"] == custom_price
    assert line_data["unitPrice"]["gross"]["amount"] == custom_price - reward_value
    assert line_data["unitDiscount"]["amount"] == reward_value


def test_order_lines_create_with_custom_price_force_new_line_and_catalogue_discount(
    order_line_on_promotion,
    permission_group_manage_orders,
    staff_api_client,
):
    # give
    query = ORDER_LINES_CREATE_MUTATION
    order_line = order_line_on_promotion
    order = order_line.order
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    order_line = order.lines.first()
    lines_count = len(order.lines.all())

    variant = order_line.variant
    variant_listings = variant.channel_listings.get(channel=order.channel)
    promotion_rule = variant_listings.promotion_rules.first()
    promotion_rule.variants.add(variant)
    reward_value = promotion_rule.reward_value
    assert promotion_rule.reward_value_type == DiscountValueType.FIXED

    update_discounted_prices_for_promotion(Product.objects.all())

    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    custom_price = 18
    force_new_line = True
    variables = {
        "orderId": order_id,
        "variantId": variant_id,
        "quantity": quantity,
        "price": custom_price,
        "forceNewLine": force_new_line,
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)

    order.refresh_from_db()
    assert order.lines.count() == lines_count + 1
    assert order.lines_count == lines_count + 1
    data = content["data"]["orderLinesCreate"]

    discounted_line_data = data["orderLines"][0]
    assert discounted_line_data["productSku"] == variant.sku
    assert discounted_line_data["productVariantId"] == variant.get_global_id()
    assert discounted_line_data["quantity"] == quantity
    assert discounted_line_data["isPriceOverridden"] is True
    assert (
        discounted_line_data["undiscountedUnitPrice"]["gross"]["amount"] == custom_price
    )
    assert (
        discounted_line_data["unitPrice"]["gross"]["amount"]
        == custom_price - reward_value
    )
    assert discounted_line_data["unitDiscount"]["amount"] == reward_value


def test_order_lines_create_no_shipping_address(
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
    variant_with_many_stocks,
):
    # given
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.shipping_address = None
    order.save(update_fields=["status", "shipping_address"])

    variant = variant_with_many_stocks
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    quantity = 1
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderLinesCreate"]
    assert not data["errors"]
    assert data["orderLines"][0]["productSku"] == variant.sku
    assert data["orderLines"][0]["quantity"] == quantity


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
def test_order_lines_create_triggers_webhooks(
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

    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = status
    order.save(update_fields=["status"])
    line = order.lines.first()
    variant = line.variant
    quantity = 2
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["orderLinesCreate"]["errors"]

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


def test_order_lines_create_with_catalogue_discount_existing_variant(
    order_with_lines_and_catalogue_promotion,
    permission_group_manage_orders,
    staff_api_client,
    tax_configuration_flat_rates,
):
    # given
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines_and_catalogue_promotion
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])
    channel = order.channel
    tax_rate = Decimal("1.23")

    currency = order.currency
    line = order.lines.first()
    variant = line.variant
    old_qty = line.quantity
    lines_count = len(order.lines.all())
    undiscounted_unit_price = line.undiscounted_base_unit_price_amount

    discount = line.discounts.get()
    initial_discount_amount = discount.amount_value
    unit_discount = quantize_price(initial_discount_amount / old_qty, currency)

    # update variant channel listing
    variant_channel_listing = variant.channel_listings.get(channel=channel)
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

    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "orderId": order_id,
        "variantId": variant_id,
        "quantity": quantity,
        "forceNewLine": False,
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    new_qty = quantity + old_qty

    order.refresh_from_db()
    assert order.lines.count() == lines_count
    assert order.lines_count == lines_count
    line.refresh_from_db()
    data = content["data"]["orderLinesCreate"]
    line_data = data["orderLines"][0]
    assert line_data["productSku"] == variant.sku
    assert line_data["quantity"] == new_qty
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
    total_price = unit_price * new_qty
    assert line_data["totalPrice"]["net"]["amount"] == total_price
    assert Decimal(str(line_data["totalPrice"]["gross"]["amount"])) == quantize_price(
        total_price * tax_rate, currency
    )
    assert (
        line_data["undiscountedTotalPrice"]["net"]["amount"]
        == undiscounted_unit_price * new_qty
    )
    assert Decimal(
        str(line_data["undiscountedTotalPrice"]["gross"]["amount"])
    ) == quantize_price(undiscounted_unit_price * new_qty * tax_rate, currency)

    discount.refresh_from_db()
    assert discount.amount_value != initial_discount_amount
    assert discount.amount_value == unit_discount * new_qty


def test_order_lines_create_apply_once_per_order_voucher_new_cheapest_line(
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
    product_variant_list,
    tax_configuration_flat_rates,
    warehouse,
    voucher,
    plugins_manager,
):
    """Adding new line with the cheapest product should update voucher discount.

    The voucher discount should use denormalized voucher reward.
    """
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    channel = order.channel
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
    initial_discount = line_1.discounts.get()
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
    assert initial_discount.value == initial_discount_value
    assert initial_discount.value_type == DiscountValueType.PERCENTAGE
    assert initial_discount.amount_value == initial_discount_amount

    # update voucher listing value and voucher discount value type
    voucher_listing.discount_value /= 2
    voucher_listing.save(update_fields=["discount_value"])
    assert voucher_listing.discount_value != initial_discount_value
    new_voucher_discount_value_type = DiscountValueType.FIXED
    voucher.discount_value_type = new_voucher_discount_value_type
    voucher.save(update_fields=["discount_value_type"])
    assert initial_discount_value_type != new_voucher_discount_value_type

    # prepare new line with the cheapest product
    new_variant = product_variant_list[0]
    new_variant_channel_listing = new_variant.channel_listings.get(channel=channel)
    new_variant_price = line_1.undiscounted_base_unit_price_amount - Decimal(1)
    new_variant_channel_listing.price_amount = new_variant_price
    new_variant_channel_listing.discounted_price_amount = new_variant_price
    new_variant_channel_listing.save(
        update_fields=["price_amount", "discounted_price_amount"]
    )

    quantity = 2
    Stock.objects.create(
        warehouse=warehouse, product_variant=new_variant, quantity=quantity
    )
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", new_variant.id)
    variables = {
        "orderId": order_id,
        "variantId": variant_id,
        "quantity": quantity,
        "forceNewLine": False,
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderLinesCreate"]
    assert not data["errors"]

    order.refresh_from_db()
    line_1, line_2, new_line = order.lines.all()

    with pytest.raises(OrderLineDiscount.DoesNotExist):
        initial_discount.refresh_from_db()

    assert line_1.base_unit_price_amount == line_1.undiscounted_base_unit_price_amount
    assert (
        line_1.total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity * tax_rate
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity * tax_rate
    )
    assert line_1.unit_discount_amount == 0
    assert line_1.unit_discount_type is None
    assert line_1.unit_discount_reason is None
    assert line_1.unit_discount_value == 0

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

    # new discount should be applied to new line with denormalized voucher reward values
    new_discount = new_line.discounts.get()
    new_discount_amount = (
        new_line.undiscounted_base_unit_price_amount * initial_discount_value / 100
    )
    new_unit_discount_amount = new_discount_amount / new_line.quantity
    assert new_discount.value == initial_discount_value
    assert new_discount.amount_value == new_discount_amount
    assert new_discount.value_type == initial_discount_value_type
    assert new_discount.type == DiscountType.VOUCHER
    assert new_discount.reason == f"Voucher code: {order.voucher_code}"

    assert (
        new_line.base_unit_price_amount
        == new_line.undiscounted_base_unit_price_amount - new_unit_discount_amount
    )
    assert (
        new_line.total_price_net_amount
        == new_line.undiscounted_total_price_net_amount - new_discount_amount
    )
    assert quantize_price(
        new_line.total_price_gross_amount, currency
    ) == quantize_price(
        new_line.base_unit_price_amount * new_line.quantity * tax_rate, currency
    )
    assert quantize_price(
        new_line.undiscounted_total_price_gross_amount, currency
    ) == quantize_price(
        new_line.undiscounted_base_unit_price_amount * new_line.quantity * tax_rate,
        currency,
    )
    assert new_line.unit_discount_amount == new_unit_discount_amount
    assert new_line.unit_discount_type == initial_discount_value_type
    assert new_line.unit_discount_reason == f"Voucher code: {order.voucher_code}"
    assert new_line.unit_discount_value == initial_discount_value

    assert order.undiscounted_base_shipping_price == undiscounted_shipping_price
    assert order.base_shipping_price == undiscounted_shipping_price
    assert order.shipping_price_net == undiscounted_shipping_price
    assert order.shipping_price_gross == quantize_price(
        undiscounted_shipping_price * tax_rate, currency
    )

    undiscounted_subtotal += new_line.undiscounted_total_price.net
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
        (order.undiscounted_total_net_amount - new_discount_amount) * tax_rate, currency
    )


def test_order_lines_create_apply_once_per_order_voucher_existing_variant(
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
    tax_configuration_flat_rates,
    voucher,
    plugins_manager,
):
    """Creating line with existing variant should only update voucher discount amount.

    The voucher discount should use denormalized voucher reward.
    """
    query = ORDER_LINES_CREATE_MUTATION
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

    # add 1 unit of line 1 variant
    extra_quantity = 1
    new_quantity = line_1.quantity + extra_quantity
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", line_1.variant.id)
    variables = {
        "orderId": order_id,
        "variantId": variant_id,
        "quantity": extra_quantity,
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderLinesCreate"]
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


def test_order_lines_create_specific_product_voucher_existing_variant(
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
    tax_configuration_flat_rates,
    voucher,
    plugins_manager,
):
    """The order line should be updated with denormalized voucher values."""

    query = ORDER_LINES_CREATE_MUTATION
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

    # add 1 unit of line 1 variant
    extra_quantity = 1
    new_quantity = line_1.quantity + extra_quantity
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", line_1.variant.id)
    variables = {
        "orderId": order_id,
        "variantId": variant_id,
        "quantity": extra_quantity,
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderLinesCreate"]
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


@freeze_time("2020-03-18 12:00:00")
def test_order_lines_create_set_price_expiration_time(
    order_with_lines,
    variant_with_many_stocks,
    permission_group_manage_orders,
    staff_api_client,
):
    # given
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    variant = variant_with_many_stocks
    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    expire_period = order.channel.draft_order_line_price_freeze_period
    assert expire_period is not None
    assert expire_period > 0
    expected_expire_time = timezone.now() + timedelta(hours=expire_period)

    # when
    staff_api_client.post_graphql(query, variables)

    # then
    new_line = OrderLine.objects.get(variant_id=variant.id)
    assert new_line.draft_base_price_expire_at == expected_expire_time


@freeze_time("2020-03-18 12:00:00")
def test_order_lines_create_dont_set_price_expiration_time_when_period_is_none(
    order_with_lines,
    variant_with_many_stocks,
    permission_group_manage_orders,
    staff_api_client,
):
    # given
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    variant = variant_with_many_stocks
    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # change default draft_order_line_price_freeze_period setting to None
    channel = order.channel
    channel.draft_order_line_price_freeze_period = None
    channel.save(update_fields=["draft_order_line_price_freeze_period"])

    # when
    staff_api_client.post_graphql(query, variables)

    # then
    new_line = OrderLine.objects.get(variant_id=variant.id)
    assert new_line.draft_base_price_expire_at is None


@freeze_time("2020-03-18 12:00:00")
def test_order_lines_create_dont_set_price_expiration_time_when_price_overridden(
    order_with_lines,
    variant_with_many_stocks,
    permission_group_manage_orders,
    staff_api_client,
):
    # given
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    variant = variant_with_many_stocks
    quantity = 1
    custom_price = Decimal(5)
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "orderId": order_id,
        "variantId": variant_id,
        "quantity": quantity,
        "price": custom_price,
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    expire_period = order.channel.draft_order_line_price_freeze_period
    assert expire_period is not None
    assert expire_period > 0

    # when
    staff_api_client.post_graphql(query, variables)

    # then
    new_line = OrderLine.objects.get(variant_id=variant.id)
    assert new_line.is_price_overridden is True
    assert new_line.draft_base_price_expire_at is None


@freeze_time("2020-03-18 12:00:00")
def test_order_lines_create_with_existing_variant_dont_set_expiration_date(
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
):
    # given
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    line = order.lines.first()
    variant = line.variant
    old_quantity = line.quantity
    extra_quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "orderId": order_id,
        "variantId": variant_id,
        "quantity": extra_quantity,
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    expire_period = order.channel.draft_order_line_price_freeze_period
    assert expire_period is not None
    assert expire_period > 0

    initial_expire_date = timezone.now() + timedelta(hours=expire_period - 1)
    line.draft_base_price_expire_at = initial_expire_date
    line.save(update_fields=["draft_base_price_expire_at"])

    # when
    staff_api_client.post_graphql(query, variables)

    # then
    line.refresh_from_db()
    assert line.quantity == old_quantity + extra_quantity
    assert line.draft_base_price_expire_at == initial_expire_date


@freeze_time("2020-03-18 12:00:00")
def test_order_lines_create_existing_variant_and_custom_price_unset_expiration_date(
    order_with_lines,
    permission_group_manage_orders,
    staff_api_client,
):
    # given
    query = ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    line = order.lines.first()
    variant = line.variant
    old_quantity = line.quantity
    extra_quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    custom_price = Decimal(5)
    variables = {
        "orderId": order_id,
        "variantId": variant_id,
        "quantity": extra_quantity,
        "price": custom_price,
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    expire_period = order.channel.draft_order_line_price_freeze_period
    assert expire_period is not None
    assert expire_period > 0

    initial_expire_date = timezone.now() + timedelta(hours=expire_period - 1)
    line.draft_base_price_expire_at = initial_expire_date
    line.save(update_fields=["draft_base_price_expire_at"])

    # when
    staff_api_client.post_graphql(query, variables)

    # then
    line.refresh_from_db()
    assert line.quantity == old_quantity + extra_quantity
    assert line.draft_base_price_expire_at is None


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
def test_order_lines_create_sets_product_type_id_for_order_line(
    status,
    order,
    permission_group_manage_orders,
    staff_api_client,
    variant_with_many_stocks,
):
    # given
    query = ORDER_LINES_CREATE_MUTATION
    order.status = status
    order.save(update_fields=["status"])
    variant = variant_with_many_stocks

    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    expected_product_type_id = variant.product.product_type_id

    # when
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["orderLinesCreate"]["errors"]

    order.refresh_from_db()
    assert len(order.lines.all()) == 1
    assert order.lines.first().product_type_id == expected_product_type_id
