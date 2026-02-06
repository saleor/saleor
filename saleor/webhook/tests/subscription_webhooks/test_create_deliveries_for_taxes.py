import json
from unittest.mock import ANY

import pytest
from freezegun import freeze_time

from ....discount.models import PromotionRule
from ....graphql.core.utils import to_global_id_or_none
from ....tax import TaxableObjectDiscountType
from ...event_types import WebhookEventSyncType
from ...models import Webhook
from ...transport.synchronous.transport import (
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
          type
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
            metadata {
              key
              value
            }
            privateMetadata {
              key
              value
            }
            user {
              id
            }
        }
          ... on Order {
            id
            metadata {
              key
              value
            }
            privateMetadata {
              key
              value
            }
            user {
              id
            }
          }
        }
      }
    }
  }
}


"""


@pytest.fixture
def subscription_order_calculate_taxes(subscription_webhook):
    return subscription_webhook(
        TAXES_SUBSCRIPTION_QUERY, WebhookEventSyncType.ORDER_CALCULATE_TAXES
    )


@freeze_time("2020-03-18 12:00:00")
@pytest.mark.parametrize("charge_taxes", [True, False])
def test_checkout_calculate_taxes(
    checkout_ready_to_complete,
    tax_app,
    charge_taxes,
    customer_user,
):
    # given
    webhook = Webhook.objects.create(
        name="Webhook",
        app=tax_app,
        target_url="http://www.example.com/any",
        subscription_query=TAXES_SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    webhook.events.create(event_type=event_type)

    tax_configuration = checkout_ready_to_complete.channel.tax_configuration
    tax_configuration.charge_taxes = charge_taxes
    tax_configuration.save(update_fields=["charge_taxes"])
    tax_configuration.country_exceptions.all().delete()

    checkout_ready_to_complete.user = customer_user
    checkout_ready_to_complete.save(update_fields=["user_id"])

    # when
    deliveries = create_delivery_for_subscription_sync_event(
        event_type, checkout_ready_to_complete, webhook
    )

    # then
    metadata = checkout_ready_to_complete.metadata_storage.metadata
    private_metadata = checkout_ready_to_complete.metadata_storage.private_metadata
    assert json.loads(deliveries.payload.get_payload()) == {
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
                "metadata": [
                    {"key": key, "value": value} for key, value in metadata.items()
                ],
                "privateMetadata": [
                    {"key": key, "value": value}
                    for key, value in private_metadata.items()
                ],
                "user": {
                    "id": to_global_id_or_none(customer_user),
                },
            },
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_checkout_calculate_taxes_with_free_shipping_voucher(
    checkout_with_voucher_free_shipping,
    tax_app,
    checkout_with_shipping_address,
):
    # given
    checkout = checkout_with_voucher_free_shipping
    webhook = Webhook.objects.create(
        name="Webhook",
        app=tax_app,
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
    metadata = checkout.metadata_storage.metadata
    private_metadata = checkout.metadata_storage.private_metadata
    assert json.loads(deliveries.payload.get_payload()) == {
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
                "metadata": [
                    {"key": key, "value": value} for key, value in metadata.items()
                ],
                "privateMetadata": [
                    {"key": key, "value": value}
                    for key, value in private_metadata.items()
                ],
                "user": None,
            },
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_checkout_calculate_taxes_with_pregenerated_payload(
    checkout_with_voucher_free_shipping,
    tax_app,
):
    # given
    checkout = checkout_with_voucher_free_shipping
    webhook = Webhook.objects.create(
        name="Webhook",
        app=tax_app,
        target_url="http://www.example.com/any",
        subscription_query=TAXES_SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    webhook.events.create(event_type=event_type)
    expected_payload = {"payload": "test"}

    # when
    deliveries = create_delivery_for_subscription_sync_event(
        event_type,
        checkout,
        webhook,
        pregenerated_payload=expected_payload,
    )

    # then
    assert json.loads(deliveries.payload.get_payload()) == expected_payload


@freeze_time("2020-03-18 12:00:00")
def test_checkout_calculate_taxes_with_entire_order_voucher(
    checkout_with_voucher,
    tax_app,
    address,
    checkout_delivery,
):
    # given
    checkout = checkout_with_voucher
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout)
    checkout.billing_address = address
    checkout.save()

    webhook = Webhook.objects.create(
        name="Webhook",
        app=tax_app,
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
    metadata = checkout.metadata_storage.metadata
    private_metadata = checkout.metadata_storage.private_metadata
    assert json.loads(deliveries.payload.get_payload()) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": {"id": to_global_id_or_none(address)},
            "currency": "USD",
            "discounts": [
                {"amount": {"amount": 20.0}, "type": TaxableObjectDiscountType.SUBTOTAL}
            ],
            "channel": {"id": to_global_id_or_none(checkout_with_voucher.channel)},
            "lines": [
                {
                    "chargeTaxes": True,
                    "productName": "Test product",
                    "productSku": "123",
                    "quantity": 3,
                    "sourceLine": {
                        "id": to_global_id_or_none(checkout.lines.first()),
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
                "id": to_global_id_or_none(checkout),
                "__typename": "Checkout",
                "metadata": [
                    {"key": key, "value": value} for key, value in metadata.items()
                ],
                "privateMetadata": [
                    {"key": key, "value": value}
                    for key, value in private_metadata.items()
                ],
                "user": None,
            },
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_checkout_calculate_taxes_with_entire_order_voucher_once_per_order(
    voucher,
    checkout_with_voucher,
    tax_app,
    permission_handle_taxes,
):
    # given
    webhook = Webhook.objects.create(
        name="Webhook",
        app=tax_app,
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
    metadata = checkout_with_voucher.metadata_storage.metadata
    private_metadata = checkout_with_voucher.metadata_storage.private_metadata
    assert json.loads(deliveries.payload.get_payload()) == {
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
                "metadata": [
                    {"key": key, "value": value} for key, value in metadata.items()
                ],
                "privateMetadata": [
                    {"key": key, "value": value}
                    for key, value in private_metadata.items()
                ],
                "user": None,
            },
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_checkout_calculate_taxes_with_shipping_voucher(
    checkout_with_item,
    voucher_free_shipping,
    tax_app,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.voucher_code = voucher_free_shipping.codes.first()

    webhook = Webhook.objects.create(
        name="Webhook",
        app=tax_app,
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
    metadata = checkout.metadata_storage.metadata
    private_metadata = checkout.metadata_storage.private_metadata
    assert json.loads(deliveries.payload.get_payload()) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": {"id": to_global_id_or_none(address)},
            "currency": "USD",
            "discounts": [],
            "channel": {"id": to_global_id_or_none(checkout.channel)},
            "lines": [
                {
                    "chargeTaxes": True,
                    "productName": "Test product",
                    "productSku": "123",
                    "quantity": 3,
                    "sourceLine": {
                        "id": to_global_id_or_none(checkout.lines.first()),
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
                "id": to_global_id_or_none(checkout),
                "__typename": "Checkout",
                "metadata": [
                    {"key": key, "value": value} for key, value in metadata.items()
                ],
                "privateMetadata": [
                    {"key": key, "value": value}
                    for key, value in private_metadata.items()
                ],
                "user": None,
            },
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_checkout_calculate_taxes_with_order_promotion(
    checkout_with_item_and_order_discount,
    tax_app,
):
    # given
    checkout = checkout_with_item_and_order_discount
    line = checkout.lines.get()
    line_price = line.variant.channel_listings.get(
        channel=checkout.channel
    ).price_amount
    channel_id = to_global_id_or_none(checkout.channel)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=tax_app,
        target_url="http://www.example.com/any",
        subscription_query=TAXES_SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    webhook.events.create(event_type=event_type)
    discount_amount = PromotionRule.objects.get().reward_value

    # when
    deliveries = create_delivery_for_subscription_sync_event(
        event_type, checkout, webhook
    )

    # then
    metadata = checkout.metadata_storage.metadata
    private_metadata = checkout.metadata_storage.private_metadata
    assert json.loads(deliveries.payload.get_payload()) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": None,
            "currency": "USD",
            "discounts": [
                {
                    "amount": {"amount": float(discount_amount)},
                    "type": TaxableObjectDiscountType.SUBTOTAL,
                }
            ],
            "channel": {"id": channel_id},
            "lines": [
                {
                    "chargeTaxes": True,
                    "productName": "Test product",
                    "productSku": "123",
                    "quantity": line.quantity,
                    "sourceLine": {
                        "id": to_global_id_or_none(line),
                        "__typename": "CheckoutLine",
                    },
                    "totalPrice": {"amount": float(line_price * 3)},
                    "unitPrice": {"amount": float(line_price)},
                    "variantName": "",
                }
            ],
            "pricesEnteredWithTax": True,
            "shippingPrice": {"amount": 0.0},
            "sourceObject": {
                "id": to_global_id_or_none(checkout),
                "__typename": "Checkout",
                "metadata": [
                    {"key": key, "value": value} for key, value in metadata.items()
                ],
                "privateMetadata": [
                    {"key": key, "value": value}
                    for key, value in private_metadata.items()
                ],
                "user": None,
            },
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_checkout_calculate_taxes_empty_checkout(
    checkout,
    tax_app,
):
    # given
    webhook = Webhook.objects.create(
        name="Webhook",
        app=tax_app,
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
    metadata = checkout.metadata_storage.metadata
    private_metadata = checkout.metadata_storage.private_metadata
    assert json.loads(deliveries.payload.get_payload()) == {
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
                "metadata": [
                    {"key": key, "value": value} for key, value in metadata.items()
                ],
                "privateMetadata": [
                    {"key": key, "value": value}
                    for key, value in private_metadata.items()
                ],
                "user": None,
            },
        },
    }
