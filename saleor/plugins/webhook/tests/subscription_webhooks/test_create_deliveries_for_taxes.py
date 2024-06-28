import json
from decimal import Decimal
from functools import partial
from unittest.mock import ANY

import pytest
from freezegun import freeze_time
from prices import Money, TaxedMoney, fixed_discount

from .....core.prices import quantize_price
from .....discount import DiscountValueType, VoucherType
from .....graphql.core.utils import to_global_id_or_none
from .....order import OrderStatus
from .....order.calculations import fetch_order_prices_if_expired
from .....order.models import Order
from .....order.utils import update_discount_for_order_line
from .....plugins.manager import get_plugins_manager
from .....tests.fixtures import recalculate_order
from .....webhook.event_types import WebhookEventSyncType
from .....webhook.models import Webhook
from .....webhook.transport.synchronous.transport import (
    create_delivery_for_subscription_sync_event,
)

TAXES_SUBSCRIPTION_QUERY = """
subscription {
  event {
    __typename
    ... on CalculateTaxes {
      taxBase {
        pricesEnteredWithTax
        currency
        shippingPrice {
          amount
        }
        address {
          id
        }
        channel {
            id
        }

        discounts {
          amount {
            amount
          }
        }

        lines {
          quantity
          chargeTaxes
          productName
          variantName
          productSku
          unitPrice {
            amount
          }

          totalPrice {
            amount
          }
          sourceLine {
            __typename
            ... on CheckoutLine {
              id
            }
            ... on OrderLine {
              id
            }
          }
        }
        sourceObject {
          __typename
          ... on Checkout {
            id
          }
          ... on Order {
            id
          }
        }
      }
    }
  }
}


"""


@freeze_time("2020-03-18 12:00:00")
@pytest.mark.parametrize("charge_taxes", [True, False])
def test_checkout_calculate_taxes(
    checkout_ready_to_complete,
    webhook_app,
    permission_handle_taxes,
    charge_taxes,
):
    # given
    webhook_app.permissions.add(permission_handle_taxes)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        target_url="http://www.example.com/any",
        subscription_query=TAXES_SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    webhook.events.create(event_type=event_type)

    tax_configuration = checkout_ready_to_complete.channel.tax_configuration
    tax_configuration.charge_taxes = charge_taxes
    tax_configuration.save(update_fields=["charge_taxes"])
    tax_configuration.country_exceptions.all().delete()

    # when
    deliveries = create_delivery_for_subscription_sync_event(
        event_type, checkout_ready_to_complete, webhook
    )

    # then
    assert json.loads(deliveries.payload.payload) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": {
                "id": to_global_id_or_none(checkout_ready_to_complete.shipping_address)
            },
            "currency": "USD",
            "discounts": [],
            "channel": {"id": to_global_id_or_none(checkout_ready_to_complete.channel)},
            "lines": [
                {
                    "productName": "Test product",
                    "productSku": "123",
                    "quantity": 3,
                    "sourceLine": {
                        "id": to_global_id_or_none(
                            checkout_ready_to_complete.lines.first()
                        ),
                        "__typename": "CheckoutLine",
                    },
                    "chargeTaxes": charge_taxes,
                    "totalPrice": {"amount": 30.0},
                    "unitPrice": {"amount": 10.0},
                    "variantName": "",
                }
            ],
            "pricesEnteredWithTax": True,
            "shippingPrice": {"amount": 10.0},
            "sourceObject": {
                "id": to_global_id_or_none(checkout_ready_to_complete),
                "__typename": "Checkout",
            },
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_checkout_calculate_taxes_with_free_shipping_voucher(
    checkout_with_voucher_free_shipping,
    webhook_app,
    permission_handle_taxes,
):
    # given
    checkout = checkout_with_voucher_free_shipping
    webhook_app.permissions.add(permission_handle_taxes)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        target_url="http://www.example.com/any",
        subscription_query=TAXES_SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    webhook.events.create(event_type=event_type)

    # when
    deliveries = create_delivery_for_subscription_sync_event(
        event_type, checkout, webhook
    )

    # then
    assert json.loads(deliveries.payload.payload) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": {"id": to_global_id_or_none(checkout.shipping_address)},
            "currency": "USD",
            "discounts": [],
            "channel": {"id": to_global_id_or_none(checkout.channel)},
            "lines": ANY,
            "pricesEnteredWithTax": True,
            "shippingPrice": {"amount": 0.0},
            "sourceObject": {
                "id": to_global_id_or_none(checkout),
                "__typename": "Checkout",
            },
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_checkout_calculate_taxes_with_entire_order_voucher(
    checkout_with_voucher,
    webhook_app,
    permission_handle_taxes,
):
    # given
    webhook_app.permissions.add(permission_handle_taxes)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        target_url="http://www.example.com/any",
        subscription_query=TAXES_SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    webhook.events.create(event_type=event_type)

    # when
    deliveries = create_delivery_for_subscription_sync_event(
        event_type, checkout_with_voucher, webhook
    )

    # then
    assert json.loads(deliveries.payload.payload) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": None,
            "currency": "USD",
            "discounts": [{"amount": {"amount": 20.0}}],
            "channel": {"id": to_global_id_or_none(checkout_with_voucher.channel)},
            "lines": [
                {
                    "chargeTaxes": True,
                    "productName": "Test product",
                    "productSku": "123",
                    "quantity": 3,
                    "sourceLine": {
                        "id": to_global_id_or_none(checkout_with_voucher.lines.first()),
                        "__typename": "CheckoutLine",
                    },
                    "totalPrice": {"amount": 30.0},
                    "unitPrice": {"amount": 10.0},
                    "variantName": "",
                }
            ],
            "pricesEnteredWithTax": True,
            "shippingPrice": {"amount": 0.0},
            "sourceObject": {
                "id": to_global_id_or_none(checkout_with_voucher),
                "__typename": "Checkout",
            },
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_checkout_calculate_taxes_with_entire_order_voucher_once_per_order(
    voucher,
    checkout_with_voucher,
    webhook_app,
    permission_handle_taxes,
):
    # given
    webhook_app.permissions.add(permission_handle_taxes)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        target_url="http://www.example.com/any",
        subscription_query=TAXES_SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    webhook.events.create(event_type=event_type)
    voucher.apply_once_per_order = True
    voucher.save()

    # when
    deliveries = create_delivery_for_subscription_sync_event(
        event_type, checkout_with_voucher, webhook
    )

    # then
    assert json.loads(deliveries.payload.payload) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": None,
            "currency": "USD",
            "discounts": [],
            "channel": {"id": to_global_id_or_none(checkout_with_voucher.channel)},
            "lines": [
                {
                    "chargeTaxes": True,
                    "productName": "Test product",
                    "productSku": "123",
                    "quantity": 3,
                    "sourceLine": {
                        "id": to_global_id_or_none(checkout_with_voucher.lines.first()),
                        "__typename": "CheckoutLine",
                    },
                    "totalPrice": {"amount": 20.0},
                    "unitPrice": {"amount": 6.67},
                    "variantName": "",
                }
            ],
            "pricesEnteredWithTax": True,
            "shippingPrice": {"amount": 0.0},
            "sourceObject": {
                "id": to_global_id_or_none(checkout_with_voucher),
                "__typename": "Checkout",
            },
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_checkout_calculate_taxes_with_shipping_voucher(
    checkout_with_voucher,
    voucher,
    webhook_app,
    permission_handle_taxes,
):
    # given
    voucher.type = VoucherType.SHIPPING
    webhook_app.permissions.add(permission_handle_taxes)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        target_url="http://www.example.com/any",
        subscription_query=TAXES_SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    webhook.events.create(event_type=event_type)

    # when
    deliveries = create_delivery_for_subscription_sync_event(
        event_type, checkout_with_voucher, webhook
    )

    # then
    assert json.loads(deliveries.payload.payload) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": None,
            "currency": "USD",
            "discounts": [{"amount": {"amount": 20.0}}],
            "channel": {"id": to_global_id_or_none(checkout_with_voucher.channel)},
            "lines": [
                {
                    "chargeTaxes": True,
                    "productName": "Test product",
                    "productSku": "123",
                    "quantity": 3,
                    "sourceLine": {
                        "id": to_global_id_or_none(checkout_with_voucher.lines.first()),
                        "__typename": "CheckoutLine",
                    },
                    "totalPrice": {"amount": 30.0},
                    "unitPrice": {"amount": 10.0},
                    "variantName": "",
                }
            ],
            "pricesEnteredWithTax": True,
            "shippingPrice": {"amount": 0.0},
            "sourceObject": {
                "id": to_global_id_or_none(checkout_with_voucher),
                "__typename": "Checkout",
            },
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_checkout_calculate_taxes_empty_checkout(
    checkout,
    webhook_app,
    permission_handle_taxes,
):
    # given
    webhook_app.permissions.add(permission_handle_taxes)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        target_url="http://www.example.com/any",
        subscription_query=TAXES_SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    webhook.events.create(event_type=event_type)

    # when
    deliveries = create_delivery_for_subscription_sync_event(
        event_type, checkout, webhook
    )

    # then
    assert json.loads(deliveries.payload.payload) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": None,
            "channel": {"id": to_global_id_or_none(checkout.channel)},
            "currency": "USD",
            "discounts": [],
            "lines": [],
            "pricesEnteredWithTax": True,
            "shippingPrice": {"amount": 0.0},
            "sourceObject": {
                "id": to_global_id_or_none(checkout),
                "__typename": "Checkout",
            },
        },
    }


@freeze_time("2020-03-18 12:00:00")
@pytest.mark.parametrize("charge_taxes", [True, False])
def test_order_calculate_taxes(
    order_line, webhook_app, permission_handle_taxes, shipping_zone, charge_taxes
):
    # given
    order = order_line.order
    expected_shipping_price = Money("2.00", order.currency)
    order.base_shipping_price = expected_shipping_price
    order.shipping_price = TaxedMoney(
        net=expected_shipping_price, gross=expected_shipping_price
    )
    order.save(
        update_fields=[
            "base_shipping_price_amount",
            "shipping_price_net_amount",
            "shipping_price_gross_amount",
        ]
    )
    shipping_method = shipping_zone.shipping_methods.first()
    order.shipping_method = shipping_method
    webhook_app.permissions.add(permission_handle_taxes)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        target_url="http://www.example.com/any",
        subscription_query=TAXES_SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventSyncType.ORDER_CALCULATE_TAXES
    webhook.events.create(event_type=event_type)

    tax_configuration = order.channel.tax_configuration
    tax_configuration.charge_taxes = charge_taxes
    tax_configuration.save(update_fields=["charge_taxes"])
    tax_configuration.country_exceptions.all().delete()

    # when
    deliveries = create_delivery_for_subscription_sync_event(event_type, order, webhook)

    # then
    shipping_price_amount = shipping_method.channel_listings.get(
        channel=order.channel
    ).price.amount
    shipping_price_amount = quantize_price(shipping_price_amount, order.currency)
    assert expected_shipping_price != shipping_price_amount
    assert json.loads(deliveries.payload.payload) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": {"id": to_global_id_or_none(order.shipping_address)},
            "currency": "USD",
            "discounts": [],
            "channel": {"id": to_global_id_or_none(order.channel)},
            "lines": [
                {
                    "chargeTaxes": charge_taxes,
                    "productName": "Test product",
                    "productSku": "SKU_A",
                    "quantity": 3,
                    "sourceLine": {
                        "__typename": "OrderLine",
                        "id": to_global_id_or_none(order_line),
                    },
                    "totalPrice": {"amount": 36.9},
                    "unitPrice": {"amount": 12.3},
                    "variantName": "SKU_A",
                }
            ],
            "pricesEnteredWithTax": True,
            "shippingPrice": {"amount": expected_shipping_price.amount},
            "sourceObject": {
                "__typename": "Order",
                "id": to_global_id_or_none(order),
            },
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_draft_order_calculate_taxes_line_discount(
    order_line,
    webhook_app,
    permission_handle_taxes,
    shipping_zone,
    voucher_specific_product_type,
):
    # given
    order = order_line.order
    expected_shipping_price = Money("2.00", order.currency)
    order.base_shipping_price = expected_shipping_price
    order.shipping_price = TaxedMoney(
        net=expected_shipping_price, gross=expected_shipping_price
    )
    order.status = OrderStatus.DRAFT
    order.save(
        update_fields=[
            "base_shipping_price_amount",
            "shipping_price_net_amount",
            "shipping_price_gross_amount",
            "status",
        ]
    )

    discount_value = Decimal("5")
    update_discount_for_order_line(
        order_line, order, "test discount", DiscountValueType.FIXED, discount_value
    )
    manager = get_plugins_manager(allow_replica=False)
    fetch_order_prices_if_expired(order, manager, order.lines.all(), True)

    shipping_method = shipping_zone.shipping_methods.first()
    order.shipping_method = shipping_method
    webhook_app.permissions.add(permission_handle_taxes)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        target_url="http://www.example.com/any",
        subscription_query=TAXES_SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventSyncType.ORDER_CALCULATE_TAXES
    webhook.events.create(event_type=event_type)

    # when
    deliveries = create_delivery_for_subscription_sync_event(event_type, order, webhook)

    # then
    expected_total_price_amount = (
        order_line.undiscounted_base_unit_price_amount - discount_value
    ) * order_line.quantity
    assert json.loads(deliveries.payload.payload) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": {"id": to_global_id_or_none(order.shipping_address)},
            "currency": "USD",
            "discounts": [],
            "channel": {"id": to_global_id_or_none(order.channel)},
            "lines": [
                {
                    "chargeTaxes": True,
                    "productName": order_line.product_name,
                    "productSku": "SKU_A",
                    "quantity": order_line.quantity,
                    "sourceLine": {
                        "__typename": "OrderLine",
                        "id": to_global_id_or_none(order_line),
                    },
                    "totalPrice": {"amount": float(expected_total_price_amount)},
                    "unitPrice": {
                        "amount": float(
                            expected_total_price_amount / order_line.quantity
                        )
                    },
                    "variantName": order_line.variant_name,
                }
            ],
            "pricesEnteredWithTax": True,
            "shippingPrice": {"amount": float(expected_shipping_price.amount)},
            "sourceObject": {
                "__typename": "Order",
                "id": to_global_id_or_none(order),
            },
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_draft_order_calculate_taxes_entire_order_voucher(
    draft_order_with_voucher, subscription_calculate_taxes_for_order, shipping_zone
):
    # given
    order = draft_order_with_voucher
    webhook = subscription_calculate_taxes_for_order
    expected_shipping_price = Money("2.00", order.currency)

    voucher = draft_order_with_voucher.voucher
    voucher.type = VoucherType.ENTIRE_ORDER
    voucher.save(update_fields=["type"])

    discount_amount = Decimal("10")
    order_discount = order.discounts.first()
    order_discount.value = discount_amount
    order_discount.save(update_fields=["value"])

    order.base_shipping_price = expected_shipping_price
    order.shipping_price = TaxedMoney(
        net=expected_shipping_price, gross=expected_shipping_price
    )
    order.save(
        update_fields=[
            "base_shipping_price_amount",
            "shipping_price_net_amount",
            "shipping_price_gross_amount",
        ]
    )

    manager = get_plugins_manager(allow_replica=False)
    fetch_order_prices_if_expired(order, manager, order.lines.all(), True)

    shipping_method = shipping_zone.shipping_methods.first()
    order.shipping_method = shipping_method

    webhook.subscription_query = TAXES_SUBSCRIPTION_QUERY
    webhook.save(update_fields=["subscription_query"])

    # when
    deliveries = create_delivery_for_subscription_sync_event(
        WebhookEventSyncType.ORDER_CALCULATE_TAXES, order, webhook
    )

    # then
    assert json.loads(deliveries.payload.payload) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": {"id": to_global_id_or_none(order.shipping_address)},
            "currency": "USD",
            "discounts": [{"amount": {"amount": float(discount_amount)}}],
            "channel": {"id": to_global_id_or_none(order.channel)},
            "lines": [
                {
                    "chargeTaxes": True,
                    "productName": line.product_name,
                    "productSku": line.product_sku,
                    "quantity": line.quantity,
                    "sourceLine": {
                        "__typename": "OrderLine",
                        "id": to_global_id_or_none(line),
                    },
                    "totalPrice": {
                        "amount": float(line.base_unit_price_amount * line.quantity)
                    },
                    "unitPrice": {"amount": float(line.base_unit_price_amount)},
                    "variantName": line.variant_name,
                }
                for line in order.lines.all()
            ],
            "pricesEnteredWithTax": True,
            "shippingPrice": {"amount": float(expected_shipping_price.amount)},
            "sourceObject": {
                "__typename": "Order",
                "id": to_global_id_or_none(order),
            },
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_draft_order_calculate_taxes_apply_once_per_order_voucher(
    draft_order_with_voucher, subscription_calculate_taxes_for_order, shipping_zone
):
    # given
    order = draft_order_with_voucher
    webhook = subscription_calculate_taxes_for_order
    expected_shipping_price = Money("2.00", order.currency)

    voucher = draft_order_with_voucher.voucher
    voucher.type = VoucherType.ENTIRE_ORDER
    voucher.apply_once_per_order = True
    voucher.save(update_fields=["type", "apply_once_per_order"])

    discount_amount = Decimal("10")
    order_discount = order.discounts.first()
    order_discount.value = discount_amount
    order_discount.save(update_fields=["value"])

    order.base_shipping_price = expected_shipping_price
    order.shipping_price = TaxedMoney(
        net=expected_shipping_price, gross=expected_shipping_price
    )
    order.save(
        update_fields=[
            "base_shipping_price_amount",
            "shipping_price_net_amount",
            "shipping_price_gross_amount",
        ]
    )

    manager = get_plugins_manager(allow_replica=False)
    fetch_order_prices_if_expired(order, manager, order.lines.all(), True)

    shipping_method = shipping_zone.shipping_methods.first()
    order.shipping_method = shipping_method

    webhook.subscription_query = TAXES_SUBSCRIPTION_QUERY
    webhook.save(update_fields=["subscription_query"])

    # when
    deliveries = create_delivery_for_subscription_sync_event(
        WebhookEventSyncType.ORDER_CALCULATE_TAXES, order, webhook
    )

    # then
    assert json.loads(deliveries.payload.payload) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": {"id": to_global_id_or_none(order.shipping_address)},
            "currency": "USD",
            "discounts": [],
            "channel": {"id": to_global_id_or_none(order.channel)},
            "lines": [
                {
                    "chargeTaxes": True,
                    "productName": line.product_name,
                    "productSku": line.product_sku,
                    "quantity": line.quantity,
                    "sourceLine": {
                        "__typename": "OrderLine",
                        "id": to_global_id_or_none(line),
                    },
                    "totalPrice": {
                        "amount": float(
                            round(line.base_unit_price_amount * line.quantity, 2)
                        )
                    },
                    "unitPrice": {
                        "amount": float(round(line.base_unit_price_amount, 2))
                    },
                    "variantName": line.variant_name,
                }
                for line in order.lines.all()
            ],
            "pricesEnteredWithTax": True,
            "shippingPrice": {"amount": float(expected_shipping_price.amount)},
            "sourceObject": {
                "__typename": "Order",
                "id": to_global_id_or_none(order),
            },
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_order_calculate_taxes_specific_product_voucher(
    order_line,
    subscription_calculate_taxes_for_order,
    shipping_zone,
    voucher_specific_product_type,
):
    # given
    order = order_line.order
    webhook = subscription_calculate_taxes_for_order
    expected_shipping_price = Money("2.00", order.currency)
    order.base_shipping_price = expected_shipping_price
    order.shipping_price = TaxedMoney(
        net=expected_shipping_price, gross=expected_shipping_price
    )
    order.status = OrderStatus.DRAFT
    order.voucher = voucher_specific_product_type
    order.voucher_code = voucher_specific_product_type.codes.first().code
    order.save(
        update_fields=[
            "base_shipping_price_amount",
            "shipping_price_net_amount",
            "shipping_price_gross_amount",
            "voucher_code",
            "voucher",
            "status",
        ]
    )

    voucher_specific_product_type.discount_value_type = DiscountValueType.FIXED
    voucher_specific_product_type.save(update_fields=["discount_value_type"])

    voucher_listing = voucher_specific_product_type.channel_listings.get(
        channel=order.channel
    )
    unit_discount_amount = Decimal("2")
    voucher_listing.discount_value = unit_discount_amount
    voucher_listing.save(update_fields=["discount_value"])
    voucher_specific_product_type.variants.add(order_line.variant)

    manager = get_plugins_manager(allow_replica=False)
    fetch_order_prices_if_expired(order, manager, order.lines.all(), True)

    shipping_method = shipping_zone.shipping_methods.first()
    order.shipping_method = shipping_method

    webhook.subscription_query = TAXES_SUBSCRIPTION_QUERY
    webhook.save(update_fields=["subscription_query"])

    # when
    deliveries = create_delivery_for_subscription_sync_event(
        WebhookEventSyncType.ORDER_CALCULATE_TAXES, order, webhook
    )

    # then
    expected_total_price_amount = (
        order_line.undiscounted_base_unit_price_amount - unit_discount_amount
    ) * order_line.quantity
    assert json.loads(deliveries.payload.payload) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": {"id": to_global_id_or_none(order.shipping_address)},
            "currency": "USD",
            "discounts": [],
            "channel": {"id": to_global_id_or_none(order.channel)},
            "lines": [
                {
                    "chargeTaxes": True,
                    "productName": order_line.product_name,
                    "productSku": "SKU_A",
                    "quantity": order_line.quantity,
                    "sourceLine": {
                        "__typename": "OrderLine",
                        "id": to_global_id_or_none(order_line),
                    },
                    "totalPrice": {"amount": float(expected_total_price_amount)},
                    "unitPrice": {
                        "amount": float(
                            expected_total_price_amount / order_line.quantity
                        )
                    },
                    "variantName": order_line.variant_name,
                }
            ],
            "pricesEnteredWithTax": True,
            "shippingPrice": {"amount": float(expected_shipping_price.amount)},
            "sourceObject": {
                "__typename": "Order",
                "id": to_global_id_or_none(order),
            },
        },
    }


@freeze_time("2020-03-18 12:00:00")
@pytest.mark.parametrize("charge_taxes", [True, False])
def test_draft_order_calculate_taxes_free_shipping_voucher(
    draft_order_with_free_shipping_voucher,
    subscription_calculate_taxes_for_order,
    shipping_zone,
    charge_taxes,
):
    # given
    order = draft_order_with_free_shipping_voucher
    webhook = subscription_calculate_taxes_for_order
    shipping_method = shipping_zone.shipping_methods.first()
    order.shipping_method = shipping_method

    webhook.subscription_query = TAXES_SUBSCRIPTION_QUERY
    webhook.save(update_fields=["subscription_query"])

    # when
    deliveries = create_delivery_for_subscription_sync_event(
        WebhookEventSyncType.ORDER_CALCULATE_TAXES, order, webhook
    )

    # then
    assert json.loads(deliveries.payload.payload) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": {"id": to_global_id_or_none(order.shipping_address)},
            "currency": "USD",
            "discounts": [],
            "channel": {"id": to_global_id_or_none(order.channel)},
            "lines": ANY,
            "pricesEnteredWithTax": True,
            "shippingPrice": {"amount": 0.0},
            "sourceObject": {
                "__typename": "Order",
                "id": to_global_id_or_none(order),
            },
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_order_calculate_taxes_with_manual_discount(
    order_line,
    subscription_calculate_taxes_for_order,
):
    # given
    order = order_line.order
    order.total = order_line.total_price + order.shipping_price
    order.undiscounted_total = order.total
    order.save()

    value = Decimal("20")
    discount = partial(fixed_discount, discount=Money(value, order.currency))
    order.total = discount(order.total)
    order.save()
    order.discounts.create(
        value_type=DiscountValueType.FIXED,
        value=value,
        reason="Discount reason",
        amount=(order.undiscounted_total - order.total).gross,
    )
    recalculate_order(order)
    order.refresh_from_db()

    webhook = subscription_calculate_taxes_for_order
    webhook.subscription_query = TAXES_SUBSCRIPTION_QUERY
    webhook.save(update_fields=["subscription_query"])

    # when
    deliveries = create_delivery_for_subscription_sync_event(
        WebhookEventSyncType.ORDER_CALCULATE_TAXES, order, webhook
    )

    # then
    assert json.loads(deliveries.payload.payload) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": {"id": to_global_id_or_none(order.shipping_address)},
            "currency": "USD",
            "discounts": [{"amount": {"amount": 20.0}}],
            "channel": {"id": to_global_id_or_none(order.channel)},
            "lines": [
                {
                    "chargeTaxes": True,
                    "productName": "Test product",
                    "productSku": "SKU_A",
                    "quantity": 3,
                    "sourceLine": {
                        "__typename": "OrderLine",
                        "id": to_global_id_or_none(order_line),
                    },
                    "totalPrice": {"amount": 36.9},
                    "unitPrice": {"amount": 12.3},
                    "variantName": "SKU_A",
                }
            ],
            "pricesEnteredWithTax": True,
            "shippingPrice": {"amount": 0.0},
            "sourceObject": {"__typename": "Order", "id": to_global_id_or_none(order)},
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_order_calculate_taxes_empty_order(
    order, webhook_app, permission_handle_taxes, channel_USD
):
    # given
    order = Order.objects.create(channel=channel_USD, currency="USD")
    webhook_app.permissions.add(permission_handle_taxes)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        target_url="http://www.example.com/any",
        subscription_query=TAXES_SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventSyncType.ORDER_CALCULATE_TAXES
    webhook.events.create(event_type=event_type)

    # when
    deliveries = create_delivery_for_subscription_sync_event(event_type, order, webhook)

    # then
    assert json.loads(deliveries.payload.payload) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": None,
            "currency": "USD",
            "discounts": [],
            "lines": [],
            "pricesEnteredWithTax": True,
            "shippingPrice": {"amount": 0.0},
            "channel": {"id": to_global_id_or_none(order.channel)},
            "sourceObject": {
                "__typename": "Order",
                "id": to_global_id_or_none(order),
            },
        },
    }
