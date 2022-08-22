import json
from decimal import Decimal
from functools import partial

from freezegun import freeze_time
from prices import Money, fixed_discount

from .....discount import DiscountValueType
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
def test_checkout_calculate_taxes(
    checkout_ready_to_complete,
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
            "lines": [
                {
                    "chargeTaxes": True,
                    "productName": "Test product",
                    "productSku": "123",
                    "quantity": 3,
                    "sourceLine": {
                        "id": to_global_id_or_none(
                            checkout_ready_to_complete.lines.first()
                        ),
                        "__typename": "CheckoutLine",
                    },
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
def test_order_calculate_taxes(
    order_line,
    webhook_app,
    permission_handle_taxes,
):

    # given
    order = order_line.order
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
            "discounts": [],
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
        amount=(order.undiscounted_total - order.total).gross,  # type: ignore
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
            "sourceObject": {
                "__typename": "Order",
                "id": to_global_id_or_none(order),
            },
        },
    }
