import json
from decimal import Decimal
from functools import partial
from unittest.mock import ANY

import pytest
from freezegun import freeze_time
from prices import Money, fixed_discount

from .....core.prices import quantize_price
from .....discount import DiscountValueType, VoucherType
from .....graphql.core.utils import to_global_id_or_none
from .....order.models import Order
from .....tests.fixtures import recalculate_order
from .....webhook.event_types import WebhookEventSyncType
from .....webhook.models import Webhook
from ...tasks import create_delivery_for_subscription_sync_event

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
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
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
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
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
def test_checkout_calculate_taxes_with_voucher(
    checkout_with_voucher,
    webhook_app,
    permission_handle_taxes,
):
    # given
    webhook_app.permissions.add(permission_handle_taxes)
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
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
def test_checkout_calculate_taxes_with_shipping_voucher(
    checkout_with_voucher,
    voucher,
    webhook_app,
    permission_handle_taxes,
):
    # given
    voucher.type = VoucherType.SHIPPING
    webhook_app.permissions.add(permission_handle_taxes)
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
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
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
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
    order.save()
    shipping_method = shipping_zone.shipping_methods.first()
    order.shipping_method = shipping_method
    webhook_app.permissions.add(permission_handle_taxes)
    event_type = WebhookEventSyncType.ORDER_CALCULATE_TAXES
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
def test_order_calculate_taxes_with_discounts(
    order_line,
    webhook_app,
    permission_handle_taxes,
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

    webhook_app.permissions.add(permission_handle_taxes)
    event_type = WebhookEventSyncType.ORDER_CALCULATE_TAXES
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
    event_type = WebhookEventSyncType.ORDER_CALCULATE_TAXES
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
