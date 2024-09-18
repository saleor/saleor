import json
from decimal import Decimal
from unittest.mock import Mock

import pytest

from saleor.discount import (
    DiscountType,
    DiscountValueType,
    RewardType,
    RewardValueType,
    VoucherType,
)
from saleor.graphql.core.utils import to_global_id_or_none
from saleor.order import OrderStatus
from saleor.order.calculations import fetch_order_prices_if_expired
from saleor.order.utils import create_order_discount_for_order
from saleor.tax import TaxableObjectDiscountType, TaxCalculationStrategy
from saleor.webhook.event_types import WebhookEventSyncType
from saleor.webhook.tests.subscription_webhooks.test_create_deliveries_for_taxes import (
    TAXES_SUBSCRIPTION_QUERY,
)
from saleor.webhook.transport.synchronous.transport import (
    create_delivery_for_subscription_sync_event,
)


@pytest.fixture
def order_with_lines(order_with_lines):
    order_with_lines.status = OrderStatus.UNCONFIRMED
    return order_with_lines


@pytest.fixture
def channel_USD(channel_USD):
    tc = channel_USD.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = False
    tc.tax_calculation_strategy = TaxCalculationStrategy.TAX_APP
    tc.tax_app_id = "avatax.app"
    tc.save()
    return channel_USD


@pytest.fixture
def subscription_calculate_taxes_for_order(subscription_webhook):
    return subscription_webhook(
        TAXES_SUBSCRIPTION_QUERY, WebhookEventSyncType.ORDER_CALCULATE_TAXES
    )


def test_fetch_order_prices_catalogue_promotion(
    order_with_lines_and_catalogue_promotion,
    subscription_calculate_taxes_for_order,
):
    # given
    order = order_with_lines_and_catalogue_promotion
    webhook = subscription_calculate_taxes_for_order
    channel = order.channel
    shipping_price_amount = order.base_shipping_price_amount

    line_1, line_2 = order.lines.all()
    line_1_unit_price = line_1.variant.channel_listings.get().discounted_price_amount
    line_2_unit_price = line_2.base_unit_price_amount

    manager = Mock(get_taxes_for_order=Mock(return_value={}))

    # when
    fetch_order_prices_if_expired(order, manager, None, True)
    deliveries = create_delivery_for_subscription_sync_event(
        WebhookEventSyncType.ORDER_CALCULATE_TAXES, order, webhook
    )

    # then
    assert json.loads(deliveries.payload.get_payload()) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": {"id": to_global_id_or_none(order.shipping_address)},
            "currency": "USD",
            "discounts": [],
            "channel": {"id": to_global_id_or_none(channel)},
            "lines": [
                {
                    "chargeTaxes": True,
                    "productName": line_1.product_name,
                    "productSku": line_1.product_sku,
                    "quantity": line_1.quantity,
                    "sourceLine": {
                        "__typename": "OrderLine",
                        "id": to_global_id_or_none(line_1),
                    },
                    "totalPrice": {"amount": line_1_unit_price * line_1.quantity},
                    "unitPrice": {"amount": line_1_unit_price},
                    "variantName": line_1.variant_name,
                },
                {
                    "chargeTaxes": True,
                    "productName": line_2.product_name,
                    "productSku": line_2.product_sku,
                    "quantity": line_2.quantity,
                    "sourceLine": {
                        "__typename": "OrderLine",
                        "id": to_global_id_or_none(line_2),
                    },
                    "totalPrice": {"amount": line_2_unit_price * line_2.quantity},
                    "unitPrice": {"amount": line_2_unit_price},
                    "variantName": line_2.variant_name,
                },
            ],
            "pricesEnteredWithTax": False,
            "shippingPrice": {"amount": shipping_price_amount},
            "sourceObject": {"__typename": "Order", "id": to_global_id_or_none(order)},
        },
    }


def test_fetch_order_prices_order_promotion(
    order_with_lines, order_promotion_with_rule, subscription_calculate_taxes_for_order
):
    # given
    order = order_with_lines
    webhook = subscription_calculate_taxes_for_order
    channel = order.channel
    shipping_price_amount = order.base_shipping_price_amount

    line_1, line_2 = order.lines.all()
    line_1_unit_price = line_1.base_unit_price_amount
    line_2_unit_price = line_2.base_unit_price_amount

    promotion = order_promotion_with_rule
    rule = promotion.rules.get()
    rule.order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 10}}}
    }
    rule.save(update_fields=["order_predicate"])
    reward_value = Decimal(5)
    assert rule.reward_value == reward_value
    assert rule.reward_value_type == RewardValueType.FIXED
    assert rule.reward_type == RewardType.SUBTOTAL_DISCOUNT

    manager = Mock(get_taxes_for_order=Mock(return_value={}))

    # when
    fetch_order_prices_if_expired(order, manager, None, True)
    deliveries = create_delivery_for_subscription_sync_event(
        WebhookEventSyncType.ORDER_CALCULATE_TAXES, order, webhook
    )

    # then
    assert json.loads(deliveries.payload.get_payload()) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": {"id": to_global_id_or_none(order.shipping_address)},
            "currency": "USD",
            "discounts": [
                {
                    "amount": {"amount": reward_value},
                    "type": TaxableObjectDiscountType.SUBTOTAL,
                }
            ],
            "channel": {"id": to_global_id_or_none(channel)},
            "lines": [
                {
                    "chargeTaxes": True,
                    "productName": line_1.product_name,
                    "productSku": line_1.product_sku,
                    "quantity": line_1.quantity,
                    "sourceLine": {
                        "__typename": "OrderLine",
                        "id": to_global_id_or_none(line_1),
                    },
                    "totalPrice": {"amount": line_1_unit_price * line_1.quantity},
                    "unitPrice": {"amount": line_1_unit_price},
                    "variantName": line_1.variant_name,
                },
                {
                    "chargeTaxes": True,
                    "productName": line_2.product_name,
                    "productSku": line_2.product_sku,
                    "quantity": line_2.quantity,
                    "sourceLine": {
                        "__typename": "OrderLine",
                        "id": to_global_id_or_none(line_2),
                    },
                    "totalPrice": {"amount": line_2_unit_price * line_2.quantity},
                    "unitPrice": {"amount": line_2_unit_price},
                    "variantName": line_2.variant_name,
                },
            ],
            "pricesEnteredWithTax": False,
            "shippingPrice": {"amount": shipping_price_amount},
            "sourceObject": {"__typename": "Order", "id": to_global_id_or_none(order)},
        },
    }


def test_fetch_order_prices_order_promotion_and_manual_discount(
    order_with_lines, order_promotion_with_rule, subscription_calculate_taxes_for_order
):
    # given
    order = order_with_lines
    webhook = subscription_calculate_taxes_for_order
    channel = order.channel
    shipping_price_amount = order.base_shipping_price_amount

    line_1, line_2 = order.lines.all()
    line_1_unit_price = line_1.base_unit_price_amount
    line_2_unit_price = line_2.base_unit_price_amount
    subtotal_amount = (
        line_1_unit_price * line_1.quantity + line_2_unit_price * line_2.quantity
    )
    total_amount = subtotal_amount + shipping_price_amount

    promotion = order_promotion_with_rule
    rule = promotion.rules.get()
    rule.order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 10}}}
    }
    rule.save(update_fields=["order_predicate"])
    assert rule.reward_type == RewardType.SUBTOTAL_DISCOUNT

    manual_reward = Decimal(10)
    create_order_discount_for_order(
        order=order,
        reason="Manual discount",
        value_type=DiscountValueType.FIXED,
        value=manual_reward,
        type=DiscountType.MANUAL,
    )

    subtotal_manual_reward_portion = (subtotal_amount / total_amount) * manual_reward
    shipping_manual_reward_portion = manual_reward - subtotal_manual_reward_portion

    manager = Mock(get_taxes_for_order=Mock(return_value={}))

    # when
    fetch_order_prices_if_expired(order, manager, None, True)
    deliveries = create_delivery_for_subscription_sync_event(
        WebhookEventSyncType.ORDER_CALCULATE_TAXES, order, webhook
    )

    # then
    manual_discount = order.discounts.get(type=DiscountType.MANUAL)
    assert manual_discount.amount_value == manual_reward
    assert not order.discounts.filter(type=DiscountType.ORDER_PROMOTION).first()

    assert json.loads(deliveries.payload.get_payload()) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": {"id": to_global_id_or_none(order.shipping_address)},
            "currency": "USD",
            "discounts": [
                {
                    "amount": {"amount": subtotal_manual_reward_portion},
                    "type": TaxableObjectDiscountType.SUBTOTAL,
                },
                {
                    "amount": {"amount": shipping_manual_reward_portion},
                    "type": TaxableObjectDiscountType.SHIPPING,
                },
            ],
            "channel": {"id": to_global_id_or_none(channel)},
            "lines": [
                {
                    "chargeTaxes": True,
                    "productName": line_1.product_name,
                    "productSku": line_1.product_sku,
                    "quantity": line_1.quantity,
                    "sourceLine": {
                        "__typename": "OrderLine",
                        "id": to_global_id_or_none(line_1),
                    },
                    "totalPrice": {"amount": line_1_unit_price * line_1.quantity},
                    "unitPrice": {"amount": line_1_unit_price},
                    "variantName": line_1.variant_name,
                },
                {
                    "chargeTaxes": True,
                    "productName": line_2.product_name,
                    "productSku": line_2.product_sku,
                    "quantity": line_2.quantity,
                    "sourceLine": {
                        "__typename": "OrderLine",
                        "id": to_global_id_or_none(line_2),
                    },
                    "totalPrice": {"amount": line_2_unit_price * line_2.quantity},
                    "unitPrice": {"amount": line_2_unit_price},
                    "variantName": line_2.variant_name,
                },
            ],
            "pricesEnteredWithTax": False,
            "shippingPrice": {"amount": shipping_price_amount},
            "sourceObject": {"__typename": "Order", "id": to_global_id_or_none(order)},
        },
    }


def test_fetch_order_prices_entire_order_voucher(
    order_with_lines, voucher, subscription_calculate_taxes_for_order
):
    # given
    order = order_with_lines
    webhook = subscription_calculate_taxes_for_order
    channel = order.channel
    shipping_price_amount = order.base_shipping_price_amount

    line_1, line_2 = order.lines.all()
    line_1_unit_price = line_1.base_unit_price_amount
    line_2_unit_price = line_2.base_unit_price_amount

    order.voucher = voucher
    order.save(update_fields=["voucher_id"])
    voucher_reward_value = voucher.channel_listings.get().discount_value

    manager = Mock(get_taxes_for_order=Mock(return_value={}))

    # when
    fetch_order_prices_if_expired(order, manager, None, True)
    deliveries = create_delivery_for_subscription_sync_event(
        WebhookEventSyncType.ORDER_CALCULATE_TAXES, order, webhook
    )

    # then
    voucher_discount = order.discounts.get(type=DiscountType.VOUCHER)
    assert voucher_discount.amount_value == voucher_reward_value

    assert json.loads(deliveries.payload.get_payload()) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": {"id": to_global_id_or_none(order.shipping_address)},
            "currency": "USD",
            "discounts": [
                {
                    "amount": {"amount": voucher_reward_value},
                    "type": TaxableObjectDiscountType.SUBTOTAL,
                }
            ],
            "channel": {"id": to_global_id_or_none(channel)},
            "lines": [
                {
                    "chargeTaxes": True,
                    "productName": line_1.product_name,
                    "productSku": line_1.product_sku,
                    "quantity": line_1.quantity,
                    "sourceLine": {
                        "__typename": "OrderLine",
                        "id": to_global_id_or_none(line_1),
                    },
                    "totalPrice": {"amount": line_1_unit_price * line_1.quantity},
                    "unitPrice": {"amount": line_1_unit_price},
                    "variantName": line_1.variant_name,
                },
                {
                    "chargeTaxes": True,
                    "productName": line_2.product_name,
                    "productSku": line_2.product_sku,
                    "quantity": line_2.quantity,
                    "sourceLine": {
                        "__typename": "OrderLine",
                        "id": to_global_id_or_none(line_2),
                    },
                    "totalPrice": {"amount": line_2_unit_price * line_2.quantity},
                    "unitPrice": {"amount": line_2_unit_price},
                    "variantName": line_2.variant_name,
                },
            ],
            "pricesEnteredWithTax": False,
            "shippingPrice": {"amount": shipping_price_amount},
            "sourceObject": {"__typename": "Order", "id": to_global_id_or_none(order)},
        },
    }


def test_fetch_order_prices_entire_order_voucher_and_manual_discount(
    order_with_lines, voucher, subscription_calculate_taxes_for_order
):
    # given
    order = order_with_lines
    webhook = subscription_calculate_taxes_for_order
    channel = order.channel
    shipping_price_amount = order.base_shipping_price_amount

    line_1, line_2 = order.lines.all()
    line_1_unit_price = line_1.base_unit_price_amount
    line_2_unit_price = line_2.base_unit_price_amount
    subtotal_amount = (
        line_1_unit_price * line_1.quantity + line_2_unit_price * line_2.quantity
    )
    total_amount = subtotal_amount + shipping_price_amount

    assert voucher.type == VoucherType.ENTIRE_ORDER
    order.voucher = voucher
    order.save(update_fields=["voucher_id"])

    manual_reward = Decimal(10)
    create_order_discount_for_order(
        order=order,
        reason="Manual discount",
        value_type=DiscountValueType.FIXED,
        value=manual_reward,
        type=DiscountType.MANUAL,
    )

    subtotal_manual_reward_portion = (subtotal_amount / total_amount) * manual_reward
    shipping_manual_reward_portion = manual_reward - subtotal_manual_reward_portion

    manager = Mock(get_taxes_for_order=Mock(return_value={}))

    # when
    fetch_order_prices_if_expired(order, manager, None, True)
    deliveries = create_delivery_for_subscription_sync_event(
        WebhookEventSyncType.ORDER_CALCULATE_TAXES, order, webhook
    )

    # then
    manual_discount = order.discounts.get(type=DiscountType.MANUAL)
    assert manual_discount.amount_value == manual_reward
    assert not order.discounts.filter(type=DiscountType.VOUCHER).first()

    assert json.loads(deliveries.payload.get_payload()) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": {"id": to_global_id_or_none(order.shipping_address)},
            "currency": "USD",
            "discounts": [
                {
                    "amount": {"amount": subtotal_manual_reward_portion},
                    "type": TaxableObjectDiscountType.SUBTOTAL,
                },
                {
                    "amount": {"amount": shipping_manual_reward_portion},
                    "type": TaxableObjectDiscountType.SHIPPING,
                },
            ],
            "channel": {"id": to_global_id_or_none(channel)},
            "lines": [
                {
                    "chargeTaxes": True,
                    "productName": line_1.product_name,
                    "productSku": line_1.product_sku,
                    "quantity": line_1.quantity,
                    "sourceLine": {
                        "__typename": "OrderLine",
                        "id": to_global_id_or_none(line_1),
                    },
                    "totalPrice": {"amount": line_1_unit_price * line_1.quantity},
                    "unitPrice": {"amount": line_1_unit_price},
                    "variantName": line_1.variant_name,
                },
                {
                    "chargeTaxes": True,
                    "productName": line_2.product_name,
                    "productSku": line_2.product_sku,
                    "quantity": line_2.quantity,
                    "sourceLine": {
                        "__typename": "OrderLine",
                        "id": to_global_id_or_none(line_2),
                    },
                    "totalPrice": {"amount": line_2_unit_price * line_2.quantity},
                    "unitPrice": {"amount": line_2_unit_price},
                    "variantName": line_2.variant_name,
                },
            ],
            "pricesEnteredWithTax": False,
            "shippingPrice": {"amount": shipping_price_amount},
            "sourceObject": {"__typename": "Order", "id": to_global_id_or_none(order)},
        },
    }


def test_fetch_order_prices_free_shipping_voucher_and_manual_discount_fixed(
    order_with_lines, voucher_free_shipping, subscription_calculate_taxes_for_order
):
    # given
    order = order_with_lines
    voucher = voucher_free_shipping
    webhook = subscription_calculate_taxes_for_order
    channel = order.channel
    shipping_price_amount = order.base_shipping_price_amount

    line_1, line_2 = order.lines.all()
    line_1_unit_price = line_1.base_unit_price_amount
    line_2_unit_price = line_2.base_unit_price_amount

    assert voucher.type == VoucherType.SHIPPING
    order.voucher = voucher
    order.save(update_fields=["voucher_id"])

    manual_reward = Decimal(10)
    create_order_discount_for_order(
        order=order,
        reason="Manual discount",
        value_type=DiscountValueType.FIXED,
        value=manual_reward,
        type=DiscountType.MANUAL,
    )

    # Since shipping is free, whole manual discount should be applied to subtotal
    subtotal_manual_reward_portion = manual_reward

    manager = Mock(get_taxes_for_order=Mock(return_value={}))

    # when
    fetch_order_prices_if_expired(order, manager, None, True)
    deliveries = create_delivery_for_subscription_sync_event(
        WebhookEventSyncType.ORDER_CALCULATE_TAXES, order, webhook
    )

    # then
    manual_discount = order.discounts.get(type=DiscountType.MANUAL)
    assert manual_discount.amount_value == subtotal_manual_reward_portion
    voucher_discount = order.discounts.get(type=DiscountType.VOUCHER)
    assert voucher_discount.amount_value == shipping_price_amount

    assert json.loads(deliveries.payload.get_payload()) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": {"id": to_global_id_or_none(order.shipping_address)},
            "currency": "USD",
            "discounts": [
                {
                    "amount": {"amount": subtotal_manual_reward_portion},
                    "type": TaxableObjectDiscountType.SUBTOTAL,
                },
            ],
            "channel": {"id": to_global_id_or_none(channel)},
            "lines": [
                {
                    "chargeTaxes": True,
                    "productName": line_1.product_name,
                    "productSku": line_1.product_sku,
                    "quantity": line_1.quantity,
                    "sourceLine": {
                        "__typename": "OrderLine",
                        "id": to_global_id_or_none(line_1),
                    },
                    "totalPrice": {"amount": line_1_unit_price * line_1.quantity},
                    "unitPrice": {"amount": line_1_unit_price},
                    "variantName": line_1.variant_name,
                },
                {
                    "chargeTaxes": True,
                    "productName": line_2.product_name,
                    "productSku": line_2.product_sku,
                    "quantity": line_2.quantity,
                    "sourceLine": {
                        "__typename": "OrderLine",
                        "id": to_global_id_or_none(line_2),
                    },
                    "totalPrice": {"amount": line_2_unit_price * line_2.quantity},
                    "unitPrice": {"amount": line_2_unit_price},
                    "variantName": line_2.variant_name,
                },
            ],
            "pricesEnteredWithTax": False,
            "shippingPrice": {"amount": 0},
            "sourceObject": {"__typename": "Order", "id": to_global_id_or_none(order)},
        },
    }


def test_fetch_order_prices_free_shipping_voucher_and_manual_discount_percentage(
    order_with_lines, voucher_free_shipping, subscription_calculate_taxes_for_order
):
    # given
    order = order_with_lines
    voucher = voucher_free_shipping
    webhook = subscription_calculate_taxes_for_order
    channel = order.channel
    shipping_price_amount = order.base_shipping_price_amount

    line_1, line_2 = order.lines.all()
    line_1_unit_price = line_1.base_unit_price_amount
    line_2_unit_price = line_2.base_unit_price_amount

    subtotal_amount = (
        line_1_unit_price * line_1.quantity + line_2_unit_price * line_2.quantity
    )
    total_amount = subtotal_amount + shipping_price_amount

    assert voucher.type == VoucherType.SHIPPING
    order.voucher = voucher
    order.save(update_fields=["voucher_id"])
    total_amount -= shipping_price_amount

    manual_reward = Decimal(10)
    create_order_discount_for_order(
        order=order,
        reason="Manual discount",
        value_type=DiscountValueType.PERCENTAGE,
        value=manual_reward,
        type=DiscountType.MANUAL,
    )

    # Since shipping is free, whole manual discount should be applied to subtotal
    subtotal_manual_reward_portion = manual_reward / 100 * total_amount

    manager = Mock(get_taxes_for_order=Mock(return_value={}))

    # when
    fetch_order_prices_if_expired(order, manager, None, True)
    deliveries = create_delivery_for_subscription_sync_event(
        WebhookEventSyncType.ORDER_CALCULATE_TAXES, order, webhook
    )

    # then
    manual_discount = order.discounts.get(type=DiscountType.MANUAL)
    assert manual_discount.amount_value == subtotal_manual_reward_portion
    voucher_discount = order.discounts.get(type=DiscountType.VOUCHER)
    assert voucher_discount.amount_value == shipping_price_amount

    assert json.loads(deliveries.payload.get_payload()) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": {"id": to_global_id_or_none(order.shipping_address)},
            "currency": "USD",
            "discounts": [
                {
                    "amount": {"amount": subtotal_manual_reward_portion},
                    "type": TaxableObjectDiscountType.SUBTOTAL,
                },
            ],
            "channel": {"id": to_global_id_or_none(channel)},
            "lines": [
                {
                    "chargeTaxes": True,
                    "productName": line_1.product_name,
                    "productSku": line_1.product_sku,
                    "quantity": line_1.quantity,
                    "sourceLine": {
                        "__typename": "OrderLine",
                        "id": to_global_id_or_none(line_1),
                    },
                    "totalPrice": {"amount": line_1_unit_price * line_1.quantity},
                    "unitPrice": {"amount": line_1_unit_price},
                    "variantName": line_1.variant_name,
                },
                {
                    "chargeTaxes": True,
                    "productName": line_2.product_name,
                    "productSku": line_2.product_sku,
                    "quantity": line_2.quantity,
                    "sourceLine": {
                        "__typename": "OrderLine",
                        "id": to_global_id_or_none(line_2),
                    },
                    "totalPrice": {"amount": line_2_unit_price * line_2.quantity},
                    "unitPrice": {"amount": line_2_unit_price},
                    "variantName": line_2.variant_name,
                },
            ],
            "pricesEnteredWithTax": False,
            "shippingPrice": {"amount": 0},
            "sourceObject": {"__typename": "Order", "id": to_global_id_or_none(order)},
        },
    }
