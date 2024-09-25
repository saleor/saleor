import json
from decimal import Decimal
from unittest.mock import ANY, Mock

import pytest
from freezegun import freeze_time
from prices import Money, TaxedMoney

from ....core.prices import quantize_price
from ....discount import (
    DiscountType,
    DiscountValueType,
    RewardType,
    RewardValueType,
    VoucherType,
)
from ....discount.models import PromotionRule
from ....graphql.core.utils import to_global_id_or_none
from ....order import OrderStatus
from ....order.calculations import fetch_order_prices_if_expired
from ....order.models import Order
from ....order.utils import (
    create_order_discount_for_order,
    update_discount_for_order_line,
)
from ....plugins.manager import get_plugins_manager
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


@pytest.fixture
def subscription_order_calculate_taxes(subscription_webhook):
    return subscription_webhook(
        TAXES_SUBSCRIPTION_QUERY, WebhookEventSyncType.ORDER_CALCULATE_TAXES
    )


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
            },
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_checkout_calculate_taxes_with_free_shipping_voucher(
    checkout_with_voucher_free_shipping,
    webhook_app,
    permission_handle_taxes,
    checkout_with_shipping_address,
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
            },
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_checkout_calculate_taxes_with_pregenerated_payload(
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
    webhook_app,
    permission_handle_taxes,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_voucher
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

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
            },
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_checkout_calculate_taxes_with_shipping_voucher(
    checkout_with_item,
    voucher_free_shipping,
    webhook_app,
    permission_handle_taxes,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.voucher_code = voucher_free_shipping.codes.first()

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
            },
        },
    }


@freeze_time("2020-03-18 12:00:00")
def test_checkout_calculate_taxes_with_order_promotion(
    checkout_with_item_and_order_discount,
    webhook_app,
    permission_handle_taxes,
):
    # given
    checkout = checkout_with_item_and_order_discount
    line = checkout.lines.get()
    line_price = line.variant.channel_listings.get(
        channel=checkout.channel
    ).price_amount
    channel_id = to_global_id_or_none(checkout.channel)
    webhook_app.permissions.add(permission_handle_taxes)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
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
    assert json.loads(deliveries.payload.get_payload()) == {
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
    order.undiscounted_base_shipping_price = expected_shipping_price
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
            "undiscounted_base_shipping_price_amount",
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
    assert json.loads(deliveries.payload.get_payload()) == {
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
    channel_listing = voucher.channel_listings.get()
    channel_listing.discount_value = discount_amount
    channel_listing.save(update_fields=["discount_value"])

    order_discount = order.discounts.first()
    order_discount.value = discount_amount
    order_discount.save(update_fields=["value"])

    order.undiscounted_base_shipping_price = expected_shipping_price
    order.base_shipping_price = expected_shipping_price
    order.shipping_price = TaxedMoney(
        net=expected_shipping_price, gross=expected_shipping_price
    )
    order.save(
        update_fields=[
            "base_shipping_price_amount",
            "shipping_price_net_amount",
            "shipping_price_gross_amount",
            "undiscounted_base_shipping_price_amount",
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
    assert json.loads(deliveries.payload.get_payload()) == {
        "__typename": "CalculateTaxes",
        "taxBase": {
            "address": {"id": to_global_id_or_none(order.shipping_address)},
            "currency": "USD",
            "discounts": [
                {
                    "amount": {"amount": float(discount_amount)},
                    "type": TaxableObjectDiscountType.SUBTOTAL,
                }
            ],
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

    order.undiscounted_base_shipping_price = expected_shipping_price
    order.base_shipping_price = expected_shipping_price
    order.shipping_price = TaxedMoney(
        net=expected_shipping_price, gross=expected_shipping_price
    )
    order.save(
        update_fields=[
            "base_shipping_price_amount",
            "shipping_price_net_amount",
            "shipping_price_gross_amount",
            "undiscounted_base_shipping_price_amount",
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
    assert json.loads(deliveries.payload.get_payload()) == {
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
    order.undiscounted_base_shipping_price = expected_shipping_price
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
            "undiscounted_base_shipping_price_amount",
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
    assert json.loads(deliveries.payload.get_payload()) == {
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
    assert json.loads(deliveries.payload.get_payload()) == {
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
    order_with_lines,
    subscription_calculate_taxes_for_order,
    tax_configuration_tax_app,
):
    # given
    order = order_with_lines
    shipping_price_amount = order.base_shipping_price_amount

    discount_value = Decimal("20")
    order.discounts.create(
        value_type=DiscountValueType.FIXED,
        value=discount_value,
        reason="Discount reason",
    )

    line_1, line_2 = order.lines.all()
    line_1_unit_price = line_1.base_unit_price_amount
    line_2_unit_price = line_2.base_unit_price_amount
    subtotal_amount = (
        line_1_unit_price * line_1.quantity + line_2_unit_price * line_2.quantity
    )
    total_amount = subtotal_amount + shipping_price_amount

    manager = Mock(get_taxes_for_order=Mock(return_value={}))
    fetch_order_prices_if_expired(order, manager, [line_1, line_2], True)

    webhook = subscription_calculate_taxes_for_order
    webhook.subscription_query = TAXES_SUBSCRIPTION_QUERY
    webhook.save(update_fields=["subscription_query"])

    # Manual discount applies both to subtotal and shipping. For tax calculation it
    # requires to be split into subtotal and shipping portion.
    manual_discount_subtotal_portion = subtotal_amount / total_amount * discount_value
    manual_discount_shipping_portion = discount_value - manual_discount_subtotal_portion

    # when
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
                    "amount": {"amount": float(manual_discount_subtotal_portion)},
                    "type": TaxableObjectDiscountType.SUBTOTAL,
                },
                {
                    "amount": {"amount": float(manual_discount_shipping_portion)},
                    "type": TaxableObjectDiscountType.SHIPPING,
                },
            ],
            "channel": {"id": to_global_id_or_none(order.channel)},
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
                    "totalPrice": {
                        "amount": float(line_1_unit_price * line_1.quantity)
                    },
                    "unitPrice": {"amount": float(line_1_unit_price)},
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
                    "totalPrice": {
                        "amount": float(line_2_unit_price * line_2.quantity)
                    },
                    "unitPrice": {"amount": float(line_2_unit_price)},
                    "variantName": line_2.variant_name,
                },
            ],
            "pricesEnteredWithTax": False,
            "shippingPrice": {"amount": float(shipping_price_amount)},
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
    assert json.loads(deliveries.payload.get_payload()) == {
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


def test_order_calculate_taxes_order_promotion(
    order_with_lines,
    order_promotion_with_rule,
    subscription_order_calculate_taxes,
    tax_configuration_tax_app,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    webhook = subscription_order_calculate_taxes
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


def test_order_calculate_taxes_order_voucher_and_manual_discount(
    order_with_lines,
    voucher,
    subscription_order_calculate_taxes,
    tax_configuration_tax_app,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    webhook = subscription_order_calculate_taxes
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


def test_order_calculate_taxes_order_promotion_and_manual_discount(
    order_with_lines,
    order_promotion_with_rule,
    subscription_order_calculate_taxes,
    tax_configuration_tax_app,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    webhook = subscription_order_calculate_taxes
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


def test_order_calculate_taxes_free_shipping_voucher_and_manual_discount_fixed(
    order_with_lines,
    voucher_free_shipping,
    subscription_order_calculate_taxes,
    tax_configuration_tax_app,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    voucher = voucher_free_shipping
    webhook = subscription_order_calculate_taxes
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


def test_order_calculate_taxes_free_shipping_voucher_and_manual_discount_percentage(
    order_with_lines,
    voucher_free_shipping,
    subscription_order_calculate_taxes,
    tax_configuration_tax_app,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    voucher = voucher_free_shipping
    webhook = subscription_order_calculate_taxes
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
