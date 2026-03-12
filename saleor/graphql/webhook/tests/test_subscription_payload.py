from decimal import Decimal

import graphene
import pytest
from django.test import override_settings
from django.utils import timezone

from ....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....webhook.models import Webhook
from ..subscription_payload import (
    generate_payload_from_subscription,
    generate_payload_promise_from_subscription,
    generate_pre_save_payloads,
    get_pre_save_payload_key,
    initialize_request,
)


def test_initialize_request(app):
    # when
    request = initialize_request(app=app)

    # then
    assert request.dataloaders == {}
    assert request.request_time is not None


def test_initialize_request_pass_params(app):
    # given
    dataloaders = {"test": "test"}
    request_time = timezone.now()

    # when
    request = initialize_request(
        app=app, dataloaders=dataloaders, request_time=request_time
    )

    # then
    assert request.dataloaders is dataloaders
    assert request.request_time is request_time


SUBSCRIPTION_QUERY = """
    subscription {
        event {
            ... on ProductVariantUpdated {
                productVariant {
                    name
                }
            }
        }
    }
"""


@override_settings(ENABLE_LIMITING_WEBHOOKS_FOR_IDENTICAL_PAYLOADS=False)
def test_generate_pre_save_payloads_disabled_with_env(webhook_app, variant):
    # given
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED
    webhook.events.create(event_type=event_type)

    # when
    pre_save_payloads = generate_pre_save_payloads(
        [webhook],
        [variant],
        WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED,
        None,
        timezone.now(),
    )

    # then
    assert pre_save_payloads == {}


@override_settings(ENABLE_LIMITING_WEBHOOKS_FOR_IDENTICAL_PAYLOADS=True)
def test_generate_pre_save_payloads_no_subscription_query(webhook_app, variant):
    # given
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=None,
    )
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED
    webhook.events.create(event_type=event_type)

    # when
    pre_save_payloads = generate_pre_save_payloads(
        [webhook],
        [variant],
        WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED,
        None,
        timezone.now(),
    )

    # then
    assert pre_save_payloads == {}


@override_settings(ENABLE_LIMITING_WEBHOOKS_FOR_IDENTICAL_PAYLOADS=True)
def test_generate_pre_save_payloads(webhook_app, variant):
    # given
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED
    webhook.events.create(event_type=event_type)

    # when
    pre_save_payloads = generate_pre_save_payloads(
        [webhook],
        [variant],
        WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED,
        None,
        timezone.now(),
    )

    # then
    key = get_pre_save_payload_key(webhook, variant)
    assert key in pre_save_payloads
    assert pre_save_payloads[key]


def test_generate_payload_from_subscription(checkout, subscription_webhook, app):
    # given
    query = """
    subscription {
      event {
        ... on CalculateTaxes {
          taxBase {
            sourceObject {
              ... on Checkout {
                id
              }
            }
          }
        }
      }
    }
    """
    webhook = subscription_webhook(
        query,
        WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
    )
    app = webhook.app
    request = initialize_request(app=app)
    checkout_global_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    payload = generate_payload_from_subscription(
        event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        subscribable_object=checkout,
        subscription_query=webhook.subscription_query,
        request=request,
    )

    # then
    assert payload["taxBase"]["sourceObject"]["id"] == checkout_global_id


def test_generate_payload_from_subscription_missing_permissions(
    gift_card, subscription_gift_card_created_webhook, permission_manage_gift_card
):
    # given

    webhook = subscription_gift_card_created_webhook
    app = webhook.app
    app.permissions.remove(permission_manage_gift_card)
    request = initialize_request(app=app, requestor=app, sync_event=False)

    # when
    payload = generate_payload_from_subscription(
        event_type=WebhookEventAsyncType.GIFT_CARD_CREATED,
        subscribable_object=gift_card,
        subscription_query=webhook.subscription_query,
        request=request,
    )

    # then
    error_code = "PermissionDenied"
    assert "errors" in payload.keys()
    assert not payload["giftCard"]
    error = payload["errors"][0]
    assert error["extensions"]["exception"]["code"] == error_code


def test_generate_payload_from_subscription_circular_call(
    checkout, subscription_webhook, permission_handle_taxes
):
    # given
    query = """
    subscription {
      event {
        ... on CalculateTaxes {
          taxBase {
            sourceObject {
              ...on Checkout{
                totalPrice {
                  gross {
                    amount
                  }
                }
              }
            }
          }
        }
      }
    }
    """

    webhook = subscription_webhook(
        query,
        WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
    )
    app = webhook.app
    request = initialize_request(app=app, requestor=app, sync_event=True)

    # when
    payload = generate_payload_from_subscription(
        event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        subscribable_object=checkout,
        subscription_query=webhook.subscription_query,
        request=request,
    )
    # then
    error_code = "CircularSubscriptionSyncEvent"
    assert list(payload.keys()) == ["errors"]
    error = payload["errors"][0]
    assert (
        error["message"] == "Resolving this field is not allowed in synchronous events."
    )
    assert error["extensions"]["exception"]["code"] == error_code


def test_generate_payload_from_subscription_unable_to_build_payload(
    checkout, subscription_webhook
):
    # given
    query = """
    subscription {
      event {
        ... on OrderCalculateTaxes {
          taxBase {
            sourceObject {
              ...on Checkout{
                totalPrice {
                  gross {
                    amount
                  }
                }
              }
            }
          }
        }
      }
    }
    """

    webhook = subscription_webhook(
        query,
        WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
    )
    app = webhook.app
    request = initialize_request(app=app, requestor=app, sync_event=True)

    # when
    payload = generate_payload_from_subscription(
        event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        subscribable_object=checkout,
        subscription_query=webhook.subscription_query,
        request=request,
    )
    # then
    assert payload is None


def test_generate_payload_promise_from_subscription(
    checkout,
    subscription_webhook,
):
    # given
    query = """
    subscription {
      event {
        ... on CalculateTaxes {
          taxBase {
            sourceObject {
              ... on Checkout {
                id
              }
            }
          }
        }
      }
    }
    """
    webhook = subscription_webhook(
        query,
        WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
    )
    app = webhook.app
    request = initialize_request(app=app)
    checkout_global_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    payload = generate_payload_promise_from_subscription(
        event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        subscribable_object=checkout,
        subscription_query=webhook.subscription_query,
        request=request,
    )

    # then
    payload = payload.get()
    assert payload["taxBase"]["sourceObject"]["id"] == checkout_global_id


def test_generate_payload_promise_from_subscription_missing_permissions(
    gift_card, subscription_gift_card_created_webhook, permission_manage_gift_card
):
    # given

    webhook = subscription_gift_card_created_webhook
    app = webhook.app
    app.permissions.remove(permission_manage_gift_card)
    request = initialize_request(app=app, requestor=app, sync_event=False)

    # when
    payload = generate_payload_promise_from_subscription(
        event_type=WebhookEventAsyncType.GIFT_CARD_CREATED,
        subscribable_object=gift_card,
        subscription_query=webhook.subscription_query,
        request=request,
    )

    # then
    payload = payload.get()
    error_code = "PermissionDenied"
    assert "errors" in payload.keys()
    assert not payload["giftCard"]
    error = payload["errors"][0]
    assert error["extensions"]["exception"]["code"] == error_code


def test_generate_payload_promise_from_subscription_circular_call(
    checkout, subscription_webhook, permission_handle_taxes
):
    # given
    query = """
    subscription {
      event {
        ... on CalculateTaxes {
          taxBase {
            sourceObject {
              ...on Checkout{
                totalPrice {
                  gross {
                    amount
                  }
                }
              }
            }
          }
        }
      }
    }
    """

    webhook = subscription_webhook(
        query,
        WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
    )
    app = webhook.app
    request = initialize_request(app=app, requestor=app, sync_event=True)

    # when
    payload = generate_payload_promise_from_subscription(
        event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        subscribable_object=checkout,
        subscription_query=webhook.subscription_query,
        request=request,
    )
    # then
    payload = payload.get()
    error_code = "CircularSubscriptionSyncEvent"
    assert list(payload.keys()) == ["errors"]
    error = payload["errors"][0]
    assert (
        error["message"] == "Resolving this field is not allowed in synchronous events."
    )
    assert error["extensions"]["exception"]["code"] == error_code


def test_generate_payload_promise_from_subscription_unable_to_build_payload(
    checkout, subscription_webhook
):
    # given
    query = """
    subscription {
      event {
        ... on OrderCalculateTaxes {
          taxBase {
            sourceObject {
              ...on Checkout{
                totalPrice {
                  gross {
                    amount
                  }
                }
              }
            }
          }
        }
      }
    }
    """

    webhook = subscription_webhook(
        query,
        WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
    )
    app = webhook.app
    request = initialize_request(app=app, requestor=app, sync_event=True)

    # when
    payload = generate_payload_promise_from_subscription(
        event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        subscribable_object=checkout,
        subscription_query=webhook.subscription_query,
        request=request,
    )
    # then
    payload = payload.get()
    assert payload is None


XERO_ORDER_CONFIRMED_QUERY = """
    subscription {
      event {
        ... on XeroOrderConfirmed {
          order { id xeroBankAccountCode }
          calculatedAmounts {
            depositAmount { amount currency }
            shippingXeroTaxCode
            lines {
              orderLineId
              quantity
              productSku
              xeroTaxCode
              unitPriceGross { amount currency }
              unitPriceNet { amount currency }
            }
          }
        }
      }
    }
"""


def test_xero_order_confirmed_calculated_amounts_serializes_as_decimal(
    order, app, webhook_app
):
    # given - order with deposit_required and a known total
    order.currency = "USD"
    order.xero_bank_account_code = "XERO-001"
    order.deposit_required = True
    order.deposit_percentage = Decimal("10.00")
    order.total_gross_amount = Decimal("1000.00")
    order.save(
        update_fields=[
            "currency",
            "xero_bank_account_code",
            "deposit_required",
            "deposit_percentage",
            "total_gross_amount",
        ]
    )

    request = initialize_request(app=app)

    # when
    payload = generate_payload_from_subscription(
        event_type=WebhookEventSyncType.XERO_ORDER_CONFIRMED,
        subscribable_object=order,
        subscription_query=XERO_ORDER_CONFIRMED_QUERY,
        request=request,
    )

    # then - depositAmount reflects the required deposit (10% of total_gross_amount)
    assert "errors" not in payload
    assert payload["order"] is not None
    assert payload["order"]["id"] is not None
    assert payload["order"]["xeroBankAccountCode"] == "XERO-001"
    assert payload["calculatedAmounts"]["depositAmount"]["amount"] == 100.0
    assert payload["calculatedAmounts"]["depositAmount"]["currency"] == "USD"
    # lines list is always present (may be empty if order has no lines in test fixture)
    assert isinstance(payload["calculatedAmounts"]["lines"], list)


def test_xero_order_confirmed_deposit_amount_is_zero_when_no_payment_recorded(
    order, app
):
    # given - order confirmed before any Xero payment has been reconciled
    order.currency = "GBP"
    order.deposit_percentage = Decimal(30)
    order.save(update_fields=["currency", "deposit_percentage"])

    request = initialize_request(app=app)

    # when
    payload = generate_payload_from_subscription(
        event_type=WebhookEventSyncType.XERO_ORDER_CONFIRMED,
        subscribable_object=order,
        subscription_query=XERO_ORDER_CONFIRMED_QUERY,
        request=request,
    )

    # then - no Xero payments recorded yet, so depositAmount is 0
    assert "errors" not in payload
    assert payload["calculatedAmounts"]["depositAmount"]["amount"] == 0.0
    assert payload["calculatedAmounts"]["depositAmount"]["currency"] == "GBP"
    # lines are always present even with zero deposit
    assert isinstance(payload["calculatedAmounts"]["lines"], list)


def test_xero_order_confirmed_lines_use_stored_amounts(order_with_lines, app):
    # given - set known stored amounts on order lines
    order = order_with_lines
    order.currency = "GBP"
    order.save(update_fields=["currency"])

    first_line = order.lines.first()
    first_line.unit_price_gross_amount = Decimal("200.00")
    first_line.unit_price_net_amount = Decimal("166.67")
    first_line.xero_tax_code = "OUTPUT2"
    first_line.save(
        update_fields=[
            "unit_price_gross_amount",
            "unit_price_net_amount",
            "xero_tax_code",
        ]
    )

    request = initialize_request(app=app)

    # when
    payload = generate_payload_from_subscription(
        event_type=WebhookEventSyncType.XERO_ORDER_CONFIRMED,
        subscribable_object=order,
        subscription_query=XERO_ORDER_CONFIRMED_QUERY,
        request=request,
    )

    # then - stored values come through exactly, no calculations engine involved
    assert "errors" not in payload
    lines = payload["calculatedAmounts"]["lines"]
    assert len(lines) == order.lines.count()

    first = next(line for line in lines if line["orderLineId"] == str(first_line.pk))
    assert first["quantity"] == first_line.quantity
    assert first["xeroTaxCode"] == "OUTPUT2"
    assert first["unitPriceGross"]["amount"] == pytest.approx(200.0)
    assert first["unitPriceGross"]["currency"] == "GBP"
    assert first["unitPriceNet"]["amount"] == pytest.approx(166.67, rel=1e-3)
    assert first["unitPriceNet"]["currency"] == "GBP"
    assert first["productSku"] == first_line.product_sku


XERO_FULFILLMENT_CREATED_QUERY = """
    subscription {
      event {
        ... on XeroFulfillmentCreated {
          fulfillment { id }
          calculatedAmounts {
            proformaAmount { amount currency }
            depositAmount { amount currency }
            shippingCost { amount currency }
            shippingNet { amount currency }
            shippingXeroTaxCode
            lines {
              orderLineId
              quantity
              productName
              variantName
              productSku
              xeroTaxCode
              unitPriceNet { amount currency }
              unitPriceGross { amount currency }
              totalPriceNet { amount currency }
              totalPriceGross { amount currency }
            }
          }
        }
      }
    }
"""


def test_xero_fulfillment_created_calculated_amounts_serializes_as_decimal(
    fulfillment, app
):
    # given
    order = fulfillment.order
    order.shipping_price_gross_amount = Decimal("120.00")
    order.shipping_price_net_amount = Decimal("100.00")
    order.shipping_tax_rate = Decimal("0.20")
    order.shipping_xero_tax_code = "OUTPUT2"
    order.currency = "USD"
    order.save(
        update_fields=[
            "shipping_price_gross_amount",
            "shipping_price_net_amount",
            "shipping_tax_rate",
            "shipping_xero_tax_code",
            "currency",
        ]
    )
    fulfillment.deposit_allocated_amount = Decimal("50.00")
    fulfillment.shipping_allocated_net_amount = Decimal("100.00")
    fulfillment.save(
        update_fields=["deposit_allocated_amount", "shipping_allocated_net_amount"]
    )

    for line in fulfillment.lines.all():
        ol = line.order_line
        ol.unit_price_gross_amount = Decimal("100.00")
        ol.unit_price_net_amount = Decimal("80.00")
        ol.total_price_gross_amount = Decimal("100.00") * ol.quantity
        ol.total_price_net_amount = Decimal("80.00") * ol.quantity
        ol.save(
            update_fields=[
                "unit_price_gross_amount",
                "unit_price_net_amount",
                "total_price_gross_amount",
                "total_price_net_amount",
            ]
        )

    lines_gross = sum(
        Decimal("100.00") * line.quantity for line in fulfillment.lines.all()
    )

    request = initialize_request(app=app)

    # when
    payload = generate_payload_from_subscription(
        event_type=WebhookEventSyncType.XERO_FULFILLMENT_CREATED,
        subscribable_object=fulfillment,
        subscription_query=XERO_FULFILLMENT_CREATED_QUERY,
        request=request,
    )

    # then - no errors, amounts are numeric and correct
    assert "errors" not in payload
    amounts = payload["calculatedAmounts"]
    assert amounts["shippingCost"]["amount"] == 120.0
    assert amounts["shippingCost"]["currency"] == "USD"
    assert amounts["shippingNet"]["amount"] == 100.0
    assert amounts["shippingNet"]["currency"] == "USD"
    assert amounts["shippingXeroTaxCode"] == "OUTPUT2"
    expected_proforma = float(lines_gross + Decimal("120.00") - Decimal("50.00"))
    assert amounts["proformaAmount"]["amount"] == expected_proforma
    assert amounts["proformaAmount"]["currency"] == "USD"
    assert amounts["depositAmount"]["amount"] == 50.0
    assert amounts["depositAmount"]["currency"] == "USD"
    assert len(amounts["lines"]) > 0
    for line in amounts["lines"]:
        assert line["unitPriceGross"]["amount"] == pytest.approx(100.0)
        assert line["unitPriceNet"]["amount"] == pytest.approx(80.0)


def test_xero_fulfillment_created_partial_fulfillment_splits_shipping_proportionally(
    order_with_lines, app
):
    # given - partial fulfillment covering only the first order line
    order = order_with_lines
    order.shipping_price_gross_amount = Decimal("12.00")
    order.shipping_price_net_amount = Decimal("10.00")
    order.shipping_tax_rate = Decimal("0.20")
    order.shipping_xero_tax_code = "OUTPUT2"
    order.currency = "GBP"
    order.save(
        update_fields=[
            "shipping_price_gross_amount",
            "shipping_price_net_amount",
            "shipping_tax_rate",
            "shipping_xero_tax_code",
            "currency",
        ]
    )

    all_lines = list(order.lines.all())
    for line in all_lines:
        line.unit_price_gross_amount = Decimal("50.00")
        line.unit_price_net_amount = Decimal("40.00")
        line.total_price_gross_amount = Decimal("50.00")
        line.total_price_net_amount = Decimal("40.00")
        line.quantity = 1
        line.save(
            update_fields=[
                "unit_price_gross_amount",
                "unit_price_net_amount",
                "total_price_gross_amount",
                "total_price_net_amount",
                "quantity",
            ]
        )

    # Only the first line is in this fulfillment
    n_lines = len(all_lines)
    shipping_net_share = (Decimal("10.00") / n_lines).quantize(Decimal("0.01"))
    partial = order.fulfillments.create()
    partial.lines.create(order_line=all_lines[0], quantity=1)
    partial.deposit_allocated_amount = Decimal("5.00")
    partial.shipping_allocated_net_amount = shipping_net_share
    partial.save(
        update_fields=["deposit_allocated_amount", "shipping_allocated_net_amount"]
    )

    request = initialize_request(app=app)

    # when
    payload = generate_payload_from_subscription(
        event_type=WebhookEventSyncType.XERO_FULFILLMENT_CREATED,
        subscribable_object=partial,
        subscription_query=XERO_FULFILLMENT_CREATED_QUERY,
        request=request,
    )

    # then
    assert "errors" not in payload
    amounts = payload["calculatedAmounts"]

    expected_shipping_net = shipping_net_share
    expected_shipping_gross = (shipping_net_share * Decimal("1.20")).quantize(
        Decimal("0.01")
    )

    assert amounts["shippingCost"]["amount"] == pytest.approx(
        float(expected_shipping_gross)
    )
    assert amounts["shippingNet"]["amount"] == pytest.approx(
        float(expected_shipping_net)
    )
    # Shipping must be strictly less than the full amount for a partial fulfillment
    assert amounts["shippingCost"]["amount"] < 12.0

    fulfillment_lines_total = Decimal("50.00")
    expected_proforma = float(
        fulfillment_lines_total + expected_shipping_gross - Decimal("5.00")
    )
    assert amounts["proformaAmount"]["amount"] == pytest.approx(expected_proforma)


def test_xero_fulfillment_created_line_amounts_use_stored_values(fulfillment, app):
    # given - set known stored amounts on a fulfillment line
    order = fulfillment.order
    order.currency = "GBP"
    order.save(update_fields=["currency"])

    first_fl = fulfillment.lines.first()
    ol = first_fl.order_line
    ol.unit_price_gross_amount = Decimal("200.00")
    ol.unit_price_net_amount = Decimal("166.67")
    ol.total_price_gross_amount = Decimal("200.00") * ol.quantity
    ol.total_price_net_amount = Decimal("166.67") * ol.quantity
    ol.xero_tax_code = "OUTPUT2"
    ol.save(
        update_fields=[
            "unit_price_gross_amount",
            "unit_price_net_amount",
            "total_price_gross_amount",
            "total_price_net_amount",
            "xero_tax_code",
        ]
    )

    request = initialize_request(app=app)

    # when
    payload = generate_payload_from_subscription(
        event_type=WebhookEventSyncType.XERO_FULFILLMENT_CREATED,
        subscribable_object=fulfillment,
        subscription_query=XERO_FULFILLMENT_CREATED_QUERY,
        request=request,
    )

    # then - stored values come through exactly
    assert "errors" not in payload
    lines = payload["calculatedAmounts"]["lines"]
    assert len(lines) > 0

    first = next(line for line in lines if line["orderLineId"] == str(ol.pk))
    assert first["quantity"] == first_fl.quantity
    assert first["xeroTaxCode"] == "OUTPUT2"
    assert first["unitPriceGross"]["amount"] == pytest.approx(200.0)
    assert first["unitPriceGross"]["currency"] == "GBP"
    assert first["unitPriceNet"]["amount"] == pytest.approx(166.67, rel=1e-3)
    assert first["unitPriceNet"]["currency"] == "GBP"
    assert first["totalPriceGross"]["amount"] == pytest.approx(
        200.0 * first_fl.quantity
    )
    assert first["totalPriceNet"]["amount"] == pytest.approx(
        166.67 * first_fl.quantity, rel=1e-3
    )


FULFILLMENT_APPROVED_XERO_FIELDS_QUERY = """
    subscription {
      event {
        ... on FulfillmentApproved {
          fulfillment {
            privateMetadata { key value }
            depositAllocatedAmount { amount currency }
          }
          order {
            privateMetadata { key value }
            shippingPrice { gross { amount currency } }
            shippingTaxRate
          }
        }
      }
    }
"""


def test_fulfillment_approved_exposes_xero_fields(fulfillment, webhook_app):
    # given
    order = fulfillment.order
    order.shipping_price_gross_amount = Decimal("60.00")
    order.currency = "GBP"
    order.store_value_in_private_metadata({"xeroDepositPrepaymentId": "prepay-123"})
    order.save(
        update_fields=[
            "shipping_price_gross_amount",
            "currency",
            "private_metadata",
        ]
    )
    fulfillment.deposit_allocated_amount = Decimal("25.00")
    fulfillment.store_value_in_private_metadata(
        {"xeroProformaPrepaymentId": "proforma-456"}
    )
    fulfillment.save(update_fields=["deposit_allocated_amount", "private_metadata"])

    request = initialize_request(app=webhook_app)

    # when
    payload = generate_payload_promise_from_subscription(
        event_type=WebhookEventAsyncType.FULFILLMENT_APPROVED,
        subscribable_object={"fulfillment": fulfillment, "notify_customer": True},
        subscription_query=FULFILLMENT_APPROVED_XERO_FIELDS_QUERY,
        request=request,
    ).get()

    # then
    assert "errors" not in payload
    assert payload["fulfillment"] is not None
    assert payload["order"] is not None

    f = payload["fulfillment"]
    assert f["depositAllocatedAmount"]["amount"] == 25.0
    assert f["depositAllocatedAmount"]["currency"] == "GBP"
    assert any(m["key"] == "xeroProformaPrepaymentId" for m in f["privateMetadata"])

    o = payload["order"]
    assert o["shippingPrice"]["gross"]["amount"] == 60.0
    assert o["shippingPrice"]["gross"]["currency"] == "GBP"
    assert o["shippingTaxRate"] is not None
    assert any(m["key"] == "xeroDepositPrepaymentId" for m in o["privateMetadata"])
