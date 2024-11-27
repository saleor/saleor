import json
import logging
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from stripe.stripe_object import StripeObject

from .....checkout.calculations import calculate_checkout_total_with_gift_cards
from .....checkout.complete_checkout import complete_checkout
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....order.actions import order_charged, order_refunded, order_voided
from .....payment.models import Transaction
from .....plugins.manager import get_plugins_manager
from .....tests import race_condition
from .... import ChargeStatus, TransactionKind
from ....utils import price_to_minor_unit
from ..consts import (
    AUTHORIZED_STATUS,
    FAILED_STATUSES,
    PROCESSING_STATUS,
    SUCCESS_STATUS,
    WEBHOOK_AUTHORIZED_EVENT,
    WEBHOOK_CANCELED_EVENT,
    WEBHOOK_FAILED_EVENT,
    WEBHOOK_PROCESSING_EVENT,
    WEBHOOK_SUCCESS_EVENT,
)
from ..webhooks import (
    _channel_slug_is_different_from_payment_channel_slug,
    _finalize_checkout,
    _process_payment_with_checkout,
    _update_payment_with_new_transaction,
    handle_authorized_payment_intent,
    handle_failed_payment_intent,
    handle_processing_payment_intent,
    handle_refund,
    handle_successful_payment_intent,
    update_payment_method_details_from_intent,
)


@patch(
    "saleor.payment.gateways.stripe.webhooks.complete_checkout", wraps=complete_checkout
)
@patch("saleor.payment.gateways.stripe.webhooks.update_payment_method")
def test_handle_successful_payment_intent_for_checkout(
    _wrapped_update_payment_method,
    wrapped_checkout_complete,
    payment_stripe_for_checkout,
    checkout_with_items,
    stripe_plugin,
    channel_USD,
):
    payment = payment_stripe_for_checkout
    payment.to_confirm = True
    payment.save()
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )
    plugin = stripe_plugin()
    payment_intent = StripeObject(id="ABC", last_response={})
    payment_intent["amount_received"] = price_to_minor_unit(
        payment.total, payment.currency
    )
    payment_intent["setup_future_usage"] = None
    payment_intent["currency"] = payment.currency
    payment_intent["status"] = SUCCESS_STATUS
    payment_intent["payment_method"] = StripeObject()

    handle_successful_payment_intent(payment_intent, plugin.config, channel_USD.slug)

    payment.refresh_from_db()

    assert wrapped_checkout_complete.called
    assert payment.checkout_id is None
    assert payment.order
    assert payment.order.checkout_token == str(checkout_with_items.token)
    transaction = payment.transactions.get(kind=TransactionKind.CAPTURE)
    assert transaction.token == payment_intent.id


@patch(
    "saleor.payment.gateways.stripe.webhooks.complete_checkout", wraps=complete_checkout
)
@patch("saleor.payment.gateway.refund")
def test_handle_successful_payment_intent_for_checkout_inactive_payment(
    refund_mock,
    wrapped_checkout_complete,
    inactive_payment_stripe_for_checkout,
    checkout_with_items,
    stripe_plugin,
    channel_USD,
):
    payment = inactive_payment_stripe_for_checkout
    payment.to_confirm = True
    payment.save()
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )
    plugin = stripe_plugin()
    payment_intent = StripeObject(id="ABC", last_response={})
    payment_intent["amount_received"] = price_to_minor_unit(
        payment.total, payment.currency
    )
    payment_intent["setup_future_usage"] = None
    payment_intent["currency"] = payment.currency
    payment_intent["status"] = SUCCESS_STATUS

    handle_successful_payment_intent(payment_intent, plugin.config, channel_USD.slug)
    payment.refresh_from_db()

    assert refund_mock.called
    assert not wrapped_checkout_complete.called


@patch("saleor.payment.gateway.refund")
@patch("saleor.checkout.complete_checkout._get_order_data")
def test_handle_successful_payment_intent_when_order_creation_raises_exception(
    order_data_mock,
    refund_mock,
    payment_stripe_for_checkout,
    checkout_with_items,
    stripe_plugin,
    channel_USD,
    stripe_payment_intent,
):
    order_data_mock.side_effect = ValidationError("Test error")
    payment = payment_stripe_for_checkout
    payment.to_confirm = True
    payment.save()
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.CAPTURE,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )
    plugin = stripe_plugin()

    handle_successful_payment_intent(
        stripe_payment_intent, plugin.config, channel_USD.slug
    )

    payment.refresh_from_db()
    assert not payment.order
    assert refund_mock.called


@pytest.mark.parametrize(
    ("metadata", "called"),
    [({f"key{i}": f"value{i}" for i in range(5)}, True), ({}, False)],
)
@patch(
    "saleor.payment.gateways.stripe.webhooks.complete_checkout", wraps=complete_checkout
)
@patch("saleor.payment.gateways.stripe.webhooks.update_payment_method")
def test_handle_successful_payment_intent_with_metadata(
    wrapped_update_payment_method,
    _wrapped_checkout_complete,
    payment_stripe_for_order,
    stripe_plugin,
    channel_USD,
    metadata,
    called,
):
    # given
    payment = payment_stripe_for_order
    current_metadata = {"currentkey": "currentvalue"}
    payment.metadata = metadata
    payment.charge_status = ChargeStatus.PENDING
    payment.save()
    plugin = stripe_plugin()
    payment_intent = StripeObject(id="token", last_response={})
    payment_intent["amount_received"] = price_to_minor_unit(
        payment.total, payment.currency
    )
    payment_intent["metadata"] = current_metadata
    payment_intent["charges"] = {"data": [{"payment_method_details": {"type": "card"}}]}
    payment_intent["amount"] = payment.total
    payment_intent["currency"] = payment.currency
    payment_intent["payment_method"] = StripeObject()

    # when
    handle_successful_payment_intent(payment_intent, plugin.config, channel_USD.slug)

    # then
    if not called:
        assert wrapped_update_payment_method.call_count == 0
    else:
        wrapped_update_payment_method.assert_called_once_with(
            plugin.config.connection_params["secret_api_key"],
            payment_intent.payment_method,
            metadata,
        )


@patch(
    "saleor.payment.gateways.stripe.webhooks.complete_checkout", wraps=complete_checkout
)
@patch("saleor.payment.gateways.stripe.webhooks.update_payment_method")
def test_handle_successful_payment_intent_for_order(
    _wrapped_update_payment_method,
    wrapped_checkout_complete,
    payment_stripe_for_order,
    stripe_plugin,
    channel_USD,
):
    payment = payment_stripe_for_order
    plugin = stripe_plugin()
    payment_intent = StripeObject(id="ABC", last_response={})
    payment_intent["amount"] = payment.total
    payment_intent["currency"] = payment.currency
    payment_intent["capture_method"] = "automatic"
    payment_intent["payment_method"] = StripeObject()

    handle_successful_payment_intent(payment_intent, plugin.config, channel_USD.slug)

    assert wrapped_checkout_complete.called is False


@patch(
    "saleor.payment.gateways.stripe.webhooks.complete_checkout", wraps=complete_checkout
)
@patch("saleor.payment.gateways.stripe.webhooks.update_payment_method")
def test_handle_successful_payment_intent_for_order_with_auth_payment(
    _wrapped_update_payment_method,
    wrapped_checkout_complete,
    payment_stripe_for_order,
    stripe_plugin,
    channel_USD,
):
    payment = payment_stripe_for_order

    plugin = stripe_plugin()

    payment_intent = StripeObject(id="token", last_response={})
    payment_intent["amount_received"] = price_to_minor_unit(
        payment.total, payment.currency
    )
    payment_intent["currency"] = payment.currency
    payment_intent["setup_future_usage"] = None
    payment_intent["status"] = SUCCESS_STATUS
    payment_intent["payment_method"] = StripeObject()

    handle_successful_payment_intent(payment_intent, plugin.config, channel_USD.slug)

    payment.refresh_from_db()

    assert payment.is_active
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.captured_amount == payment.total
    assert payment.transactions.filter(kind=TransactionKind.CAPTURE).exists()
    assert wrapped_checkout_complete.called is False


@patch(
    "saleor.payment.gateways.stripe.webhooks.complete_checkout", wraps=complete_checkout
)
@patch("saleor.payment.gateways.stripe.webhooks.update_payment_method")
def test_handle_successful_payment_intent_for_order_with_pending_payment(
    _wrapped_update_payment_method,
    wrapped_checkout_complete,
    payment_stripe_for_order,
    stripe_plugin,
    channel_USD,
):
    payment = payment_stripe_for_order
    transaction = payment.transactions.first()
    transaction.kind = TransactionKind.PENDING
    transaction.save()

    plugin = stripe_plugin()

    payment_intent = StripeObject(id="token", last_response={})
    payment_intent["amount_received"] = price_to_minor_unit(
        payment.total, payment.currency
    )
    payment_intent["currency"] = payment.currency
    payment_intent["setup_future_usage"] = None
    payment_intent["status"] = SUCCESS_STATUS
    payment_intent["payment_method"] = StripeObject()

    handle_successful_payment_intent(payment_intent, plugin.config, channel_USD.slug)

    payment.refresh_from_db()

    assert payment.is_active
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.captured_amount == payment.total
    assert payment.transactions.filter(kind=TransactionKind.CAPTURE).exists()
    assert wrapped_checkout_complete.called is False


@pytest.mark.parametrize("called", [True, False])
@patch(
    "saleor.payment.gateways.stripe.webhooks._process_payment_with_checkout",
    wraps=_process_payment_with_checkout,
)
@patch("saleor.payment.gateways.stripe.webhooks.update_payment_method")
def test_handle_successful_payment_intent_different_checkout_channel_slug(
    _wrapped_update_payment_method,
    wrapped_process_payment_with_checkout,
    payment_stripe_for_checkout,
    checkout_with_items,
    stripe_plugin,
    channel_USD,
    channel_PLN,
    called,
):
    # given
    channel = channel_USD if called else channel_PLN
    payment = payment_stripe_for_checkout
    payment.to_confirm = True
    payment.save()
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )
    plugin = stripe_plugin()
    payment_intent = StripeObject(id="ABC", last_response={})
    payment_intent["amount_received"] = price_to_minor_unit(
        payment.total, payment.currency
    )
    payment_intent["setup_future_usage"] = None
    payment_intent["currency"] = payment.currency
    payment_intent["status"] = SUCCESS_STATUS
    payment_intent["payment_method"] = StripeObject()

    # when
    handle_successful_payment_intent(payment_intent, plugin.config, channel.slug)

    # then
    assert wrapped_process_payment_with_checkout.called == called


@pytest.mark.parametrize("called", [True, False])
@patch("saleor.payment.gateways.stripe.webhooks.order_charged", wraps=order_charged)
@patch("saleor.payment.gateways.stripe.webhooks.update_payment_method")
def test_handle_successful_payment_intent_different_order_channel_slug(
    _wrapped_update_payment_method,
    wrapped_order_charged,
    payment_stripe_for_order,
    stripe_plugin,
    channel_USD,
    channel_PLN,
    called,
):
    # given
    channel = channel_USD if called else channel_PLN
    payment = payment_stripe_for_order
    plugin = stripe_plugin()
    payment_intent = StripeObject(id="token", last_response={})
    payment_intent["amount_received"] = payment.total
    payment_intent["currency"] = payment.currency
    payment_intent["capture_method"] = "automatic"
    payment_intent["setup_future_usage"] = None
    payment_intent["payment_method"] = StripeObject()

    # when
    handle_successful_payment_intent(payment_intent, plugin.config, channel.slug)

    # then
    assert wrapped_order_charged.called == called


@patch("saleor.checkout.complete_checkout.gateway.payment_refund_or_void")
@patch("saleor.checkout.complete_checkout.gateway.process_payment")
@patch("saleor.payment.gateways.stripe.webhooks.order_charged", wraps=order_charged)
@patch("saleor.payment.gateways.stripe.webhooks.update_payment_method")
def test_handle_successful_payment_intent_checkout_with_voucher_ongoing_completing(
    _wrapped_update_payment_method,
    wrapped_order_charged,
    wrapped_process_payment,
    wrapped_payment_refund_or_void,
    payment_stripe_for_checkout,
    voucher_free_shipping,
    stripe_plugin,
    channel_USD,
    customer_user,
    success_gateway_response,
):
    # given
    channel = channel_USD
    payment = payment_stripe_for_checkout
    checkout = payment.checkout

    wrapped_process_payment.return_value = success_gateway_response

    checkout.voucher_code = voucher_free_shipping.codes.first().code
    checkout.save(update_fields=["voucher_code"])

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    address = customer_user.default_billing_address
    total = calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )

    # set voucher usage limit to 1
    voucher_free_shipping.usage_limit = 1
    voucher_free_shipping.save(update_fields=["usage_limit"])

    plugin = stripe_plugin()
    payment_intent = StripeObject(id="token", last_response={})
    payment_intent["amount_received"] = payment.total
    payment_intent["currency"] = payment.currency
    payment_intent["capture_method"] = "automatic"
    payment_intent["setup_future_usage"] = None
    payment_intent["payment_method"] = StripeObject()

    Transaction.objects.create(
        payment=payment_stripe_for_checkout,
        action_required=False,
        kind=TransactionKind.AUTH,
        token=payment_intent.id,
        is_success=True,
        amount=total.gross.amount,
        currency=total.gross.currency,
        error="",
        gateway_response={},
        action_required_data={},
    )

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    def call_webhook_success_event(*args, **kwargs):
        handle_successful_payment_intent(payment_intent, plugin.config, channel.slug)

    with race_condition.RunAfter(
        "saleor.checkout.complete_checkout._process_payment", call_webhook_success_event
    ):
        order_from_checkout, action_required, _ = complete_checkout(
            checkout_info=checkout_info,
            lines=lines,
            manager=manager,
            payment_data={},
            store_source=False,
            user=customer_user,
            app=None,
        )

    # then
    assert wrapped_order_charged.called is False
    assert order_from_checkout
    wrapped_payment_refund_or_void.assert_not_called()
    code = voucher_free_shipping.codes.first()
    assert code.used == 1


@patch(
    "saleor.payment.gateways.stripe.webhooks.complete_checkout", wraps=complete_checkout
)
@patch("saleor.payment.gateways.stripe.webhooks.update_payment_method")
def test_handle_authorized_payment_intent_for_checkout(
    _wrapped_update_payment_method,
    wrapped_checkout_complete,
    payment_stripe_for_checkout,
    checkout_with_items,
    stripe_plugin,
    channel_USD,
):
    payment = payment_stripe_for_checkout
    payment.to_confirm = True
    payment.save()
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )
    plugin = stripe_plugin()
    payment_intent = StripeObject(id="ABC", last_response={})
    payment_intent["amount"] = price_to_minor_unit(payment.total, payment.currency)
    payment_intent["currency"] = payment.currency
    payment_intent["status"] = AUTHORIZED_STATUS
    payment_intent["payment_method"] = StripeObject()
    handle_authorized_payment_intent(payment_intent, plugin.config, channel_USD.slug)

    payment.refresh_from_db()

    assert wrapped_checkout_complete.called
    assert payment.checkout_id is None
    assert not payment.cc_brand
    assert not payment.cc_last_digits
    assert not payment.cc_exp_year
    assert not payment.cc_exp_month
    assert not payment.payment_method_type
    assert payment.order
    assert payment.order.checkout_token == str(checkout_with_items.token)
    transaction = payment.transactions.get(kind=TransactionKind.AUTH)
    assert transaction.token == payment_intent.id


@patch(
    "saleor.payment.gateways.stripe.webhooks.complete_checkout", wraps=complete_checkout
)
def test_handle_authorized_payment_intent_for_checkout_with_payment_details(
    wrapped_checkout_complete,
    payment_stripe_for_checkout,
    checkout_with_items,
    stripe_plugin,
    channel_USD,
    stripe_payment_intent_with_details,
):
    intent = stripe_payment_intent_with_details
    payment = payment_stripe_for_checkout
    payment.to_confirm = True
    payment.save()
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )
    plugin = stripe_plugin()
    intent["amount"] = price_to_minor_unit(payment.total, payment.currency)
    intent["currency"] = payment.currency
    intent["status"] = AUTHORIZED_STATUS
    handle_authorized_payment_intent(intent, plugin.config, channel_USD.slug)

    payment.refresh_from_db()

    assert wrapped_checkout_complete.called
    assert payment.checkout_id is None
    assert payment.cc_brand == "visa"
    assert payment.cc_last_digits == "3220"
    assert payment.cc_exp_year == 2030
    assert payment.cc_exp_month == 3
    assert payment.payment_method_type == "card"
    assert payment.order
    assert payment.order.checkout_token == str(checkout_with_items.token)
    transaction = payment.transactions.get(kind=TransactionKind.AUTH)
    assert transaction.token == intent.id


@patch("saleor.payment.gateway.void")
def test_handle_authorized_payment_intent_for_checkout_inactive_payment(
    void_mock,
    inactive_payment_stripe_for_checkout,
    checkout_with_items,
    stripe_plugin,
    channel_USD,
):
    payment = inactive_payment_stripe_for_checkout
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )
    plugin = stripe_plugin()
    payment_intent = StripeObject(id="ABC", last_response={})
    payment_intent["amount"] = price_to_minor_unit(payment.total, payment.currency)
    payment_intent["currency"] = payment.currency
    payment_intent["status"] = AUTHORIZED_STATUS

    handle_authorized_payment_intent(payment_intent, plugin.config, channel_USD.slug)
    payment.refresh_from_db()

    assert void_mock.called


@patch("saleor.checkout.complete_checkout._get_order_data")
@patch("saleor.payment.gateway.void")
def test_handle_authorized_payment_intent_when_order_creation_raises_exception(
    void_mock,
    order_data_mock,
    payment_stripe_for_checkout,
    checkout_with_items,
    stripe_plugin,
    channel_USD,
    stripe_payment_intent,
):
    order_data_mock.side_effect = ValidationError("Test error")
    payment = payment_stripe_for_checkout
    payment.to_confirm = True
    payment.save()
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )
    plugin = stripe_plugin()

    handle_authorized_payment_intent(
        stripe_payment_intent, plugin.config, channel_USD.slug
    )

    payment.refresh_from_db()

    assert not payment.order
    assert void_mock.called


@patch(
    "saleor.payment.gateways.stripe.webhooks.complete_checkout", wraps=complete_checkout
)
@patch("saleor.payment.gateways.stripe.webhooks.update_payment_method")
def test_handle_authorized_payment_intent_for_order(
    _wrapped_update_payment_method,
    wrapped_checkout_complete,
    payment_stripe_for_order,
    checkout_with_items,
    stripe_plugin,
    channel_USD,
):
    payment = payment_stripe_for_order
    plugin = stripe_plugin()
    payment_intent = StripeObject(id="ABC", last_response={})
    payment_intent["amount"] = payment.total
    payment_intent["currency"] = payment.currency
    payment_intent["status"] = AUTHORIZED_STATUS
    handle_authorized_payment_intent(payment_intent, plugin.config, channel_USD.slug)

    assert wrapped_checkout_complete.called is False


@patch(
    "saleor.payment.gateways.stripe.webhooks.complete_checkout", wraps=complete_checkout
)
@patch("saleor.payment.gateways.stripe.webhooks.update_payment_method")
def test_handle_authorized_payment_intent_for_processing_order_payment(
    _wrapped_update_payment_method,
    wrapped_checkout_complete,
    payment_stripe_for_order,
    checkout_with_items,
    stripe_plugin,
    channel_USD,
):
    payment = payment_stripe_for_order
    payment.charge_status = ChargeStatus.PENDING
    plugin = stripe_plugin()
    payment_intent = StripeObject(id="ABC", last_response={})
    payment_intent["amount"] = payment.total
    payment_intent["currency"] = payment.currency
    payment_intent["status"] = AUTHORIZED_STATUS
    handle_authorized_payment_intent(payment_intent, plugin.config, channel_USD.slug)

    assert wrapped_checkout_complete.called is False


@pytest.mark.parametrize(
    ("metadata", "called"), [({"key": "value"}, True), ({}, False)]
)
@patch(
    "saleor.payment.gateways.stripe.webhooks.complete_checkout", wraps=complete_checkout
)
@patch("saleor.payment.gateways.stripe.webhooks.update_payment_method")
def test_handle_authorized_payment_intent_with_metadata(
    wrapped_update_payment_method,
    _wrapped_checkout_complete,
    payment_stripe_for_order,
    checkout_with_items,
    stripe_plugin,
    channel_USD,
    metadata,
    called,
):
    # given
    payment = payment_stripe_for_order
    current_metadata = {"currentkey": "currentvalue"}
    payment.metadata = metadata
    payment.charge_status = ChargeStatus.PENDING
    payment.save()
    plugin = stripe_plugin()
    payment_intent = StripeObject(id="token", last_response={})
    payment_intent["metadata"] = current_metadata
    payment_intent["payment_method"] = StripeObject()
    payment_intent["charges"] = {"data": [{"payment_method_details": {"type": "card"}}]}
    payment_intent["amount"] = payment.total
    payment_intent["currency"] = payment.currency

    # when
    handle_authorized_payment_intent(payment_intent, plugin.config, channel_USD.slug)

    # then
    if not called:
        assert wrapped_update_payment_method.call_count == 0
    else:
        wrapped_update_payment_method.assert_called_with(
            plugin.config.connection_params["secret_api_key"],
            payment_intent.payment_method,
            metadata,
        )


@pytest.mark.parametrize("called", [True, False])
@patch(
    "saleor.payment.gateways.stripe.webhooks._update_payment_with_new_transaction",
    wraps=_update_payment_with_new_transaction,
)
@patch("saleor.payment.gateways.stripe.webhooks.update_payment_method")
def test_handle_authorized_payment_intent_different_order_channel_slug(
    _wrapped_update_payment_method,
    wrapped_update_payment_with_new_transaction,
    channel_PLN,
    payment_stripe_for_order,
    checkout_with_items,
    stripe_plugin,
    channel_USD,
    called,
):
    # given
    channel = channel_USD if called else channel_PLN
    payment = payment_stripe_for_order
    payment.charge_status = ChargeStatus.PENDING
    payment.checkout = None
    payment.save()
    plugin = stripe_plugin()
    payment_intent = StripeObject(id="token", last_response={})
    payment_intent["amount"] = payment.total
    payment_intent["currency"] = payment.currency
    payment_intent["status"] = AUTHORIZED_STATUS
    payment_intent["payment_method"] = StripeObject()

    # when
    handle_authorized_payment_intent(payment_intent, plugin.config, channel.slug)

    # then
    assert wrapped_update_payment_with_new_transaction.called == called


@pytest.mark.parametrize("called", [True, False])
@patch(
    "saleor.payment.gateways.stripe.webhooks._process_payment_with_checkout",
    wraps=_process_payment_with_checkout,
)
@patch("saleor.payment.gateways.stripe.webhooks.update_payment_method")
def test_handle_authorized_payment_intent_different_checkout_channel_slug(
    _wrapped_update_payment_method,
    wrapped_process_payment_with_checkout,
    payment_stripe_for_checkout,
    stripe_plugin,
    channel_USD,
    channel_PLN,
    called,
):
    # given
    channel = channel_USD if called else channel_PLN
    payment = payment_stripe_for_checkout
    payment.to_confirm = True
    payment.save()
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )
    plugin = stripe_plugin()
    payment_intent = StripeObject(id="ABC", last_response={})
    payment_intent["amount"] = price_to_minor_unit(payment.total, payment.currency)
    payment_intent["currency"] = payment.currency
    payment_intent["status"] = AUTHORIZED_STATUS
    payment_intent["payment_method"] = StripeObject()

    # when
    handle_authorized_payment_intent(payment_intent, plugin.config, channel.slug)

    # then
    assert wrapped_process_payment_with_checkout.called == called


@patch(
    "saleor.payment.gateways.stripe.webhooks.complete_checkout", wraps=complete_checkout
)
def test_handle_processing_payment_intent_for_order(
    wrapped_checkout_complete,
    payment_stripe_for_order,
    checkout_with_items,
    stripe_plugin,
    channel_USD,
):
    payment = payment_stripe_for_order
    plugin = stripe_plugin()
    payment_intent = StripeObject(id="ABC", last_response={})
    payment_intent["amount"] = payment.total
    payment_intent["currency"] = payment.currency
    payment_intent["status"] = PROCESSING_STATUS
    handle_processing_payment_intent(payment_intent, plugin.config, channel_USD.slug)

    assert wrapped_checkout_complete.called is False


@patch(
    "saleor.payment.gateways.stripe.webhooks.complete_checkout", wraps=complete_checkout
)
def test_handle_processing_payment_intent_for_checkout(
    wrapped_checkout_complete,
    payment_stripe_for_checkout,
    checkout_with_items,
    stripe_plugin,
    channel_USD,
):
    payment = payment_stripe_for_checkout
    payment.to_confirm = True
    payment.save()
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )
    plugin = stripe_plugin()
    payment_intent = StripeObject(id="ABC", last_response={})
    payment_intent["amount"] = price_to_minor_unit(payment.total, payment.currency)
    payment_intent["currency"] = payment.currency
    payment_intent["status"] = PROCESSING_STATUS
    handle_processing_payment_intent(payment_intent, plugin.config, channel_USD.slug)

    payment.refresh_from_db()

    assert wrapped_checkout_complete.called
    assert payment.checkout_id is None
    assert payment.order
    assert payment.order.checkout_token == str(checkout_with_items.token)
    transaction = payment.transactions.get(kind=TransactionKind.PENDING)
    assert transaction.token == payment_intent.id


@patch(
    "saleor.payment.gateways.stripe.webhooks.complete_checkout", wraps=complete_checkout
)
def test_handle_processing_payment_intent_for_checkout_inactive_payment(
    wrapped_checkout_complete,
    inactive_payment_stripe_for_checkout,
    checkout_with_items,
    stripe_plugin,
    channel_USD,
):
    payment = inactive_payment_stripe_for_checkout
    payment.to_confirm = True
    payment.save()
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )
    plugin = stripe_plugin()
    payment_intent = StripeObject(id="ABC", last_response={})
    payment_intent["amount"] = price_to_minor_unit(payment.total, payment.currency)
    payment_intent["currency"] = payment.currency
    payment_intent["status"] = PROCESSING_STATUS

    handle_processing_payment_intent(payment_intent, plugin.config, channel_USD.slug)

    assert not wrapped_checkout_complete.called


@patch("saleor.checkout.complete_checkout._get_order_data")
@patch("saleor.payment.gateway.void")
@patch("saleor.payment.gateway.refund")
def test_handle_processing_payment_intent_when_order_creation_raises_exception(
    refund_mock,
    void_mock,
    order_data_mock,
    payment_stripe_for_checkout,
    checkout_with_items,
    stripe_plugin,
    channel_USD,
    stripe_payment_intent,
):
    order_data_mock.side_effect = ValidationError("Test error")
    payment = payment_stripe_for_checkout
    payment.to_confirm = True
    payment.save()
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )
    plugin = stripe_plugin()

    stripe_payment_intent["status"] = PROCESSING_STATUS

    handle_processing_payment_intent(
        stripe_payment_intent, plugin.config, channel_USD.slug
    )

    payment.refresh_from_db()

    assert not payment.order
    assert not void_mock.called
    assert not refund_mock.called


@pytest.mark.parametrize("called", [True, False])
@patch(
    "saleor.payment.gateways.stripe.webhooks._process_payment_with_checkout",
    wraps=_process_payment_with_checkout,
)
def test_handle_processing_payment_intent_different_order_channel_slug(
    wrapped_process_payment_with_checkout,
    payment_stripe_for_order,
    checkout_with_items,
    stripe_plugin,
    channel_USD,
    channel_PLN,
    called,
):
    # given
    channel = channel_USD if called else channel_PLN
    payment = payment_stripe_for_order
    plugin = stripe_plugin()
    payment_intent = StripeObject(id="ABC", last_response={})
    payment_intent["amount"] = payment.total
    payment_intent["currency"] = payment.currency
    payment_intent["status"] = PROCESSING_STATUS

    # when
    handle_processing_payment_intent(payment_intent, plugin.config, channel.slug)

    # then
    assert not wrapped_process_payment_with_checkout.called


@pytest.mark.parametrize("called", [True, False])
@patch(
    "saleor.payment.gateways.stripe.webhooks._process_payment_with_checkout",
    wraps=_process_payment_with_checkout,
)
def test_handle_processing_payment_intent_different_checkout_channel_slug(
    wrapped_process_payment_with_checkout,
    payment_stripe_for_checkout,
    checkout_with_items,
    stripe_plugin,
    channel_USD,
    channel_PLN,
    called,
):
    # given
    channel = channel_USD if called else channel_PLN
    payment = payment_stripe_for_checkout
    payment.to_confirm = True
    payment.save()
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )
    plugin = stripe_plugin()
    payment_intent = StripeObject(id="ABC", last_response={})
    payment_intent["amount"] = price_to_minor_unit(payment.total, payment.currency)
    payment_intent["currency"] = payment.currency
    payment_intent["status"] = PROCESSING_STATUS

    # when
    handle_processing_payment_intent(payment_intent, plugin.config, channel.slug)

    # then
    assert wrapped_process_payment_with_checkout.called == called


def test_handle_failed_payment_intent_for_checkout(
    stripe_plugin, payment_stripe_for_checkout, channel_USD
):
    payment = payment_stripe_for_checkout
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )

    plugin = stripe_plugin()

    payment_intent = StripeObject(id="ABC", last_response={})
    payment_intent["amount"] = payment.total
    payment_intent["currency"] = payment.currency
    payment_intent["status"] = FAILED_STATUSES[0]

    handle_failed_payment_intent(payment_intent, plugin.config, channel_USD.slug)

    payment.refresh_from_db()

    assert not payment.order_id
    assert not payment.is_active
    assert payment.charge_status == ChargeStatus.CANCELLED
    assert payment.transactions.filter(kind=TransactionKind.CANCEL).exists()


def test_handle_failed_payment_intent_for_order(
    stripe_plugin, payment_stripe_for_order, channel_USD
):
    payment = payment_stripe_for_order
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )

    plugin = stripe_plugin()

    payment_intent = StripeObject(id="ABC", last_response={})
    payment_intent["amount"] = payment.total
    payment_intent["currency"] = payment.currency
    payment_intent["status"] = FAILED_STATUSES[0]

    handle_failed_payment_intent(payment_intent, plugin.config, channel_USD.slug)

    payment.refresh_from_db()

    assert not payment.is_active
    assert payment.charge_status == ChargeStatus.CANCELLED
    assert payment.transactions.filter(kind=TransactionKind.CANCEL).exists()


@pytest.mark.parametrize("called", [True, False])
@patch(
    "saleor.payment.gateways.stripe.webhooks._update_payment_with_new_transaction",
    wraps=_update_payment_with_new_transaction,
)
@patch("saleor.payment.gateways.stripe.webhooks.order_voided", wraps=order_voided)
def test_handle_failed_payment_intent_different_order_channel_slug(
    wrapped_update_payment_with_new_transaction,
    wrapped_order_voided,
    payment_stripe_for_order,
    stripe_plugin,
    channel_USD,
    channel_PLN,
    called,
):
    # given
    channel = channel_USD if called else channel_PLN
    payment = payment_stripe_for_order
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )

    plugin = stripe_plugin()

    payment_intent = StripeObject(id="ABC", last_response={})
    payment_intent["amount"] = payment.total
    payment_intent["currency"] = payment.currency
    payment_intent["status"] = FAILED_STATUSES[0]

    # when
    handle_failed_payment_intent(payment_intent, plugin.config, channel.slug)

    # then
    assert wrapped_update_payment_with_new_transaction.called == called
    assert wrapped_order_voided.called == called


@pytest.mark.parametrize("called", [True, False])
@patch("saleor.payment.gateways.stripe.webhooks.order_voided", wraps=order_voided)
@patch(
    "saleor.payment.gateways.stripe.webhooks._update_payment_with_new_transaction",
    wraps=_update_payment_with_new_transaction,
)
def test_handle_failed_payment_intent_different_checkout_channel_slug(
    wrapped_update_payment_with_new_transaction,
    wrapped_order_voided,
    payment_stripe_for_checkout,
    stripe_plugin,
    channel_USD,
    channel_PLN,
    called,
):
    # given
    channel = channel_USD if called else channel_PLN
    payment = payment_stripe_for_checkout
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )

    plugin = stripe_plugin()

    payment_intent = StripeObject(id="ABC", last_response={})
    payment_intent["amount"] = payment.total
    payment_intent["currency"] = payment.currency
    payment_intent["status"] = FAILED_STATUSES[0]

    # when
    handle_failed_payment_intent(payment_intent, plugin.config, channel.slug)

    # then
    assert wrapped_update_payment_with_new_transaction.called == called
    assert not wrapped_order_voided.called


def test_handle_fully_refund(stripe_plugin, payment_stripe_for_order, channel_USD):
    payment = payment_stripe_for_order
    payment.captured_amount = payment.total
    payment.save()
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.CAPTURE,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )
    plugin = stripe_plugin()

    refund = StripeObject(id="refund_id")
    refund["amount"] = price_to_minor_unit(payment.total, payment.currency)
    refund["currency"] = payment.currency
    refund["last_response"] = None

    charge = StripeObject()
    charge["payment_intent"] = "ABC"
    charge["refunds"] = StripeObject()
    charge["refunds"]["data"] = [refund]

    handle_refund(charge, plugin.config, channel_USD.slug)

    payment.refresh_from_db()

    assert payment.charge_status == ChargeStatus.FULLY_REFUNDED
    assert payment.is_active is False
    assert payment.captured_amount == Decimal("0")


def test_handle_partial_refund(stripe_plugin, payment_stripe_for_order, channel_USD):
    payment = payment_stripe_for_order
    payment.captured_amount = payment.total
    payment.save()
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.CAPTURE,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )
    plugin = stripe_plugin()

    refund = StripeObject(id="refund_id")
    refund["amount"] = price_to_minor_unit(Decimal("10"), payment.currency)
    refund["currency"] = payment.currency
    refund["last_response"] = None

    charge = StripeObject()
    charge["payment_intent"] = "ABC"
    charge["refunds"] = StripeObject()
    charge["refunds"]["data"] = [refund]

    handle_refund(charge, plugin.config, channel_USD.slug)

    payment.refresh_from_db()

    assert payment.charge_status == ChargeStatus.PARTIALLY_REFUNDED
    assert payment.is_active is True
    assert payment.captured_amount == payment.total - Decimal("10")


def test_handle_refund_already_processed(
    stripe_plugin, payment_stripe_for_order, channel_USD
):
    payment = payment_stripe_for_order
    payment.charge_status = ChargeStatus.PARTIALLY_REFUNDED
    payment.captured_amount = payment.total - Decimal("10")
    payment.save()

    refund_id = "refund_abc"
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.REFUND,
        amount=payment.total,
        currency=payment.currency,
        token=refund_id,
        gateway_response={},
    )
    plugin = stripe_plugin()

    refund = StripeObject(id=refund_id)
    refund["amount"] = price_to_minor_unit(Decimal("10"), payment.currency)
    refund["currency"] = payment.currency
    refund["last_response"] = None

    charge = StripeObject()
    charge["payment_intent"] = "ABC"
    charge["refunds"] = StripeObject()
    charge["refunds"]["data"] = [refund]

    handle_refund(charge, plugin.config, channel_USD.slug)

    payment.refresh_from_db()

    assert payment.charge_status == ChargeStatus.PARTIALLY_REFUNDED
    assert payment.is_active is True
    assert payment.captured_amount == payment.total - Decimal("10")


@patch("saleor.payment.gateways.stripe.webhooks.stripe.Charge.retrieve")
def test_handle_refund_missing_refunds(
    charge_retrieve, stripe_plugin, payment_stripe_for_order, channel_USD
):
    # given
    payment = payment_stripe_for_order
    payment.captured_amount = payment.total
    payment.save()
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.CAPTURE,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )
    plugin = stripe_plugin()

    charge = StripeObject()
    charge["payment_intent"] = "ABC"

    refund = StripeObject(id="refund_id")
    refund["amount"] = price_to_minor_unit(payment.total, payment.currency)
    refund["currency"] = payment.currency
    refund["last_response"] = None

    charge_retrieve_obj = charge
    charge_retrieve_obj["refunds"] = StripeObject()
    charge_retrieve_obj["refunds"]["data"] = [refund]

    charge_retrieve.return_value = charge_retrieve_obj

    # when
    handle_refund(charge, plugin.config, channel_USD.slug)

    # then
    payment.refresh_from_db()

    assert payment.charge_status == ChargeStatus.FULLY_REFUNDED
    assert payment.is_active is False
    assert payment.captured_amount == Decimal("0")


@pytest.mark.parametrize("called", [True, False])
@patch(
    "saleor.payment.gateways.stripe.webhooks._update_payment_with_new_transaction",
    wraps=_update_payment_with_new_transaction,
)
@patch(
    "saleor.payment.gateways.stripe.webhooks.order_refunded",
    wraps=order_refunded,
)
def test_handle_refund_different_order_channel_slug(
    wrapped_update_payment_with_new_transaction,
    wrapped_order_refunded,
    stripe_plugin,
    payment_stripe_for_order,
    channel_USD,
    channel_PLN,
    called,
):
    # given
    channel = channel_USD if called else channel_PLN
    payment = payment_stripe_for_order
    payment.captured_amount = payment.total
    payment.save()
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.CAPTURE,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )
    plugin = stripe_plugin()

    refund = StripeObject(id="refund_id")
    refund["amount"] = price_to_minor_unit(payment.total, payment.currency)
    refund["currency"] = payment.currency
    refund["last_response"] = None

    charge = StripeObject()
    charge["payment_intent"] = "ABC"
    charge["refunds"] = StripeObject()
    charge["refunds"]["data"] = [refund]

    # when
    handle_refund(charge, plugin.config, channel.slug)

    # then
    assert wrapped_update_payment_with_new_transaction.called == called
    assert wrapped_order_refunded.called == called


@pytest.mark.parametrize("called", [True, False])
@patch(
    "saleor.payment.gateways.stripe.webhooks.order_refunded",
    wraps=order_refunded,
)
@patch(
    "saleor.payment.gateways.stripe.webhooks._update_payment_with_new_transaction",
    wraps=_update_payment_with_new_transaction,
)
def test_handle_refund_different_checkout_channel_slug(
    wrapped_update_payment_with_new_transaction,
    wrapped_order_refunded,
    stripe_plugin,
    payment_stripe_for_checkout,
    channel_USD,
    channel_PLN,
    called,
):
    # given
    channel = channel_USD if called else channel_PLN
    payment = payment_stripe_for_checkout
    payment.captured_amount = payment.total
    payment.save()
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.CAPTURE,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )
    plugin = stripe_plugin()

    refund = StripeObject(id="refund_id")
    refund["amount"] = price_to_minor_unit(payment.total, payment.currency)
    refund["currency"] = payment.currency
    refund["last_response"] = None

    charge = StripeObject()
    charge["payment_intent"] = "ABC"
    charge["refunds"] = StripeObject()
    charge["refunds"]["data"] = [refund]

    # when
    handle_refund(charge, plugin.config, channel.slug)

    # then
    assert wrapped_update_payment_with_new_transaction.called == called
    assert not wrapped_order_refunded.called


@pytest.mark.parametrize(
    ("webhook_type", "fun_to_mock"),
    [
        (WEBHOOK_SUCCESS_EVENT, "handle_successful_payment_intent"),
        (WEBHOOK_PROCESSING_EVENT, "handle_processing_payment_intent"),
        (WEBHOOK_FAILED_EVENT, "handle_failed_payment_intent"),
        (WEBHOOK_AUTHORIZED_EVENT, "handle_authorized_payment_intent"),
        (WEBHOOK_CANCELED_EVENT, "handle_failed_payment_intent"),
    ],
)
@patch("saleor.payment.gateways.stripe.stripe_api.stripe.Webhook.construct_event")
def test_handle_webhook_events(
    mocked_webhook_event, webhook_type, fun_to_mock, stripe_plugin, rf, channel_USD
):
    dummy_payload = {
        "id": "evt_1Ip9ANH1Vac4G4dbE9ch7zGS",
    }

    request = rf.post(
        path="/webhooks/", data=dummy_payload, content_type="application/json"
    )

    stripe_signature = "1234"
    request.META["HTTP_STRIPE_SIGNATURE"] = stripe_signature

    event = Mock()
    event.type = webhook_type
    event.data.object = StripeObject()

    mocked_webhook_event.return_value = event

    plugin = stripe_plugin()

    with patch(f"saleor.payment.gateways.stripe.webhooks.{fun_to_mock}") as mocked_fun:
        plugin.webhook(request, "/webhooks/", None)
        mocked_fun.assert_called_once_with(
            event.data.object, plugin.config, channel_USD.slug
        )

    api_key = plugin.config.connection_params["secret_api_key"]
    endpoint_secret = plugin.config.connection_params["webhook_secret"]

    mocked_webhook_event.assert_called_once_with(
        json.dumps(dummy_payload).encode("utf-8"),
        stripe_signature,
        endpoint_secret,
        api_key=api_key,
    )


def test_handle_webhook_events_when_secret_is_missing(stripe_plugin, rf):
    # given
    webhook_type = WEBHOOK_SUCCESS_EVENT

    dummy_payload = {
        "id": "evt_1Ip9ANH1Vac4G4dbE9ch7zGS",
    }

    request = rf.post(
        path="/webhooks/", data=dummy_payload, content_type="application/json"
    )

    stripe_signature = "1234"
    request.META["HTTP_STRIPE_SIGNATURE"] = stripe_signature

    event = Mock()
    event.type = webhook_type
    event.data.object = StripeObject()

    plugin = stripe_plugin(webhook_secret_key=None)

    # when
    response = plugin.webhook(request, "/webhooks/", None)

    # then
    assert response.status_code == 500


@patch("saleor.payment.gateway.refund")
@patch("saleor.checkout.complete_checkout._get_order_data")
def test_finalize_checkout_not_created_order_payment_refund(
    order_data_mock,
    refund_mock,
    stripe_plugin,
    channel_USD,
    payment_stripe_for_checkout,
    stripe_payment_intent,
):
    order_data_mock.side_effect = ValidationError("Test error")
    stripe_plugin()
    checkout = payment_stripe_for_checkout.checkout

    _finalize_checkout(
        checkout,
        payment_stripe_for_checkout,
        stripe_payment_intent,
        TransactionKind.CAPTURE,
        payment_stripe_for_checkout.total,
        payment_stripe_for_checkout.currency,
    )

    payment_stripe_for_checkout.refresh_from_db()

    assert not payment_stripe_for_checkout.order
    assert refund_mock.called


@patch("saleor.payment.gateway.refund")
def test_finalize_checkout_not_created_checkout_variant_unavailable_order_refund(
    refund_mock,
    stripe_plugin,
    channel_USD,
    payment_stripe_for_checkout,
    stripe_payment_intent,
):
    # given
    stripe_plugin()
    checkout = payment_stripe_for_checkout.checkout

    line = checkout.lines.first()
    line.variant.channel_listings.all().delete()

    checkout.price_expiration = timezone.now()
    checkout.save(update_fields=["price_expiration"])

    # when
    with pytest.raises(ValidationError):
        _finalize_checkout(
            checkout,
            payment_stripe_for_checkout,
            stripe_payment_intent,
            TransactionKind.CAPTURE,
            payment_stripe_for_checkout.total,
            payment_stripe_for_checkout.currency,
        )

    # then
    payment_stripe_for_checkout.refresh_from_db()

    assert not payment_stripe_for_checkout.order
    assert refund_mock.called


@patch("saleor.payment.gateway.void")
@patch("saleor.checkout.complete_checkout._get_order_data")
def test_finalize_checkout_not_created_order_payment_void(
    order_data_mock,
    void_mock,
    stripe_plugin,
    channel_USD,
    payment_stripe_for_checkout,
    stripe_payment_intent,
):
    order_data_mock.side_effect = ValidationError("Test error")
    stripe_plugin()
    checkout = payment_stripe_for_checkout.checkout

    _finalize_checkout(
        checkout,
        payment_stripe_for_checkout,
        stripe_payment_intent,
        TransactionKind.AUTH,
        payment_stripe_for_checkout.total,
        payment_stripe_for_checkout.currency,
    )

    payment_stripe_for_checkout.refresh_from_db()

    assert not payment_stripe_for_checkout.order
    assert void_mock.called


@patch("saleor.payment.gateway.void")
def test_finalize_checkout_not_created_checkout_variant_unavailable_order_payment_void(
    void_mock,
    stripe_plugin,
    channel_USD,
    payment_stripe_for_checkout,
    stripe_payment_intent,
):
    # given
    stripe_plugin()
    checkout = payment_stripe_for_checkout.checkout

    line = checkout.lines.first()
    line.variant.channel_listings.all().delete()

    checkout.price_expiration = timezone.now()
    checkout.save(update_fields=["price_expiration"])

    # when
    with pytest.raises(ValidationError):
        _finalize_checkout(
            checkout,
            payment_stripe_for_checkout,
            stripe_payment_intent,
            TransactionKind.AUTH,
            payment_stripe_for_checkout.total,
            payment_stripe_for_checkout.currency,
        )

    # then
    payment_stripe_for_checkout.refresh_from_db()

    assert not payment_stripe_for_checkout.order
    assert void_mock.called


def test_update_payment_method_details_from_intent_payment_info_does_not_exist(
    payment_stripe_for_checkout, stripe_payment_intent
):
    payment = payment_stripe_for_checkout
    update_payment_method_details_from_intent(payment, stripe_payment_intent)

    payment.refresh_from_db()

    assert not payment.cc_brand
    assert not payment.cc_last_digits
    assert not payment.cc_exp_year
    assert not payment.cc_exp_month
    assert not payment.payment_method_type


def test_update_payment_method_details_from_intent_payment_info_exists(
    payment_stripe_for_checkout, stripe_payment_intent_with_details
):
    intent = stripe_payment_intent_with_details
    payment = payment_stripe_for_checkout
    update_payment_method_details_from_intent(payment, intent)

    payment.refresh_from_db()

    assert payment.cc_brand == "visa"
    assert payment.cc_last_digits == "3220"
    assert payment.cc_exp_year == 2030
    assert payment.cc_exp_month == 3
    assert payment.payment_method_type == "card"


@patch("saleor.payment.gateways.stripe.plugin.retrieve_payment_intent")
@patch(
    "saleor.payment.gateways.stripe.webhooks.complete_checkout", wraps=complete_checkout
)
@patch("saleor.payment.gateways.stripe.webhooks.update_payment_method")
def test_handle_successful_payment_intent_for_checkout_when_already_processing_checkout(
    _wrapped_update_payment_method,
    wrapped_checkout_complete,
    mocked_retrieve_payment_intent,
    payment_stripe_for_checkout,
    checkout_with_items,
    stripe_plugin,
    channel_USD,
    django_capture_on_commit_callbacks,
):
    # given
    plugin = stripe_plugin()
    manager = get_plugins_manager(allow_replica=False)
    payment = payment_stripe_for_checkout
    payment.to_confirm = True
    payment.save()
    payment.transactions.create(
        is_success=True,
        action_required=True,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        amount=payment.total,
        currency=payment.currency,
        token="ABC",
        gateway_response={},
    )
    payment_intent = StripeObject(id="ABC", last_response={})
    payment_intent["amount_received"] = price_to_minor_unit(
        payment.total, payment.currency
    )
    payment_intent["setup_future_usage"] = None
    payment_intent["currency"] = payment.currency
    payment_intent["amount"] = payment.total * 100
    payment_intent["status"] = SUCCESS_STATUS
    payment_intent["payment_method"] = StripeObject()
    mocked_retrieve_payment_intent.return_value = (payment_intent, None)

    lines_info, _ = fetch_checkout_lines(checkout_with_items)
    checkout_info = fetch_checkout_info(checkout_with_items, lines_info, manager)

    # when
    def call_webhook_notification(*args, **kwargs):
        handle_successful_payment_intent(
            payment_intent, plugin.config, channel_USD.slug
        )

    with race_condition.RunAfter(
        "saleor.checkout.complete_checkout._process_payment",
        call_webhook_notification,
    ):
        with django_capture_on_commit_callbacks(execute=True):
            complete_checkout(
                manager,
                checkout_info,
                lines_info,
                {},
                False,
                None,
                None,
            )

    # then
    payment.refresh_from_db()
    assert payment.captured_amount == payment.total

    assert wrapped_checkout_complete.called
    assert payment.checkout_id is None
    assert payment.order
    transaction = payment.transactions.get(kind=TransactionKind.CAPTURE)
    assert transaction.token == payment_intent.id


def test_channel_slug_is_different_from_payment_channel_slug_for_checkout_false(
    payment, checkout
):
    # given
    payment.checkout = checkout
    payment.order = None
    payment.save(update_fields=["checkout", "order"])

    channel_slug = checkout.channel.slug

    # when
    result = _channel_slug_is_different_from_payment_channel_slug(channel_slug, payment)

    # then
    assert result is False


def test_channel_slug_is_different_from_payment_channel_slug_for_checkout_true(
    payment, checkout
):
    # given
    payment.checkout = checkout
    payment.order = None
    payment.save(update_fields=["checkout", "order"])

    channel_slug = "test"

    # when
    result = _channel_slug_is_different_from_payment_channel_slug(channel_slug, payment)

    # then
    assert result is True


def test_channel_slug_is_different_from_payment_channel_slug_for_order_false(
    payment, order
):
    # given
    payment.checkout = None
    payment.order = order
    payment.save(update_fields=["checkout", "order"])

    channel_slug = order.channel.slug

    # when
    result = _channel_slug_is_different_from_payment_channel_slug(channel_slug, payment)

    # then
    assert result is False


def test_channel_slug_is_different_from_payment_channel_slug_for_order_true(
    payment, order
):
    # given
    payment.checkout = None
    payment.order = order
    payment.save(update_fields=["checkout", "order"])

    channel_slug = "test"

    # when
    result = _channel_slug_is_different_from_payment_channel_slug(channel_slug, payment)

    # then
    assert result is True


def test_channel_slug_is_different_from_payment_channel_slug_no_order_or_checkout(
    payment, caplog
):
    # given
    payment.checkout = None
    payment.order = None
    payment.save(update_fields=["checkout", "order"])
    caplog.set_level(logging.WARNING)

    channel_slug = "test"

    # when
    result = _channel_slug_is_different_from_payment_channel_slug(channel_slug, payment)

    # then
    assert result is True
    assert (
        caplog.records[0].message
        == "Both payment.checkout and payment.order cannot be None"
    )
    assert caplog.records[0].payment_id == payment.id
