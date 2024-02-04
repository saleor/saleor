from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from ...order import OrderEvents
from ...plugins.manager import get_plugins_manager
from ...webhook.event_types import WebhookEventSyncType
from ...webhook.models import Webhook
from .. import (
    ChargeStatus,
    CustomPaymentChoices,
    PaymentError,
    TransactionAction,
    TransactionEventType,
    TransactionKind,
    gateway,
)
from ..gateway import (
    request_cancelation_action,
    request_charge_action,
    request_refund_action,
)
from ..interface import GatewayResponse, TransactionActionData
from ..models import TransactionItem
from ..utils import create_payment_information

RAW_RESPONSE = {"test": "abcdefgheijklmn"}
PROCESS_PAYMENT_RESPONSE = GatewayResponse(
    is_success=True,
    customer_id="test_customer",
    action_required=False,
    kind=TransactionKind.CAPTURE,
    amount=Decimal(10.0),
    currency="usd",
    transaction_id="1234",
    error=None,
    raw_response=RAW_RESPONSE,
)
AUTHORIZE_RESPONSE = GatewayResponse(
    is_success=True,
    customer_id="test_customer",
    action_required=False,
    kind=TransactionKind.AUTH,
    amount=Decimal(10.0),
    currency="usd",
    transaction_id="1234",
    error=None,
    raw_response=RAW_RESPONSE,
)
VOID_AMOUNT = Decimal("98.40")
VOID_RESPONSE = GatewayResponse(
    is_success=True,
    customer_id="test_customer",
    action_required=False,
    kind=TransactionKind.VOID,
    amount=VOID_AMOUNT,
    currency="usd",
    transaction_id="1234",
    error=None,
    raw_response=RAW_RESPONSE,
)
PARTIAL_REFUND_AMOUNT = Decimal(2.0)
PARTIAL_REFUND_RESPONSE = GatewayResponse(
    is_success=True,
    customer_id="test_customer",
    action_required=False,
    kind=TransactionKind.REFUND,
    amount=PARTIAL_REFUND_AMOUNT,
    currency="usd",
    transaction_id="1234",
    error=None,
    raw_response=RAW_RESPONSE,
)
FULL_REFUND_AMOUNT = Decimal("98.40")
FULL_REFUND_RESPONSE = GatewayResponse(
    is_success=True,
    customer_id="test_customer",
    action_required=False,
    kind=TransactionKind.REFUND,
    amount=FULL_REFUND_AMOUNT,
    currency="usd",
    transaction_id="1234",
    error=None,
    raw_response=RAW_RESPONSE,
)
CONFIRM_AMOUNT = Decimal("98.40")
CONFIRM_RESPONSE = GatewayResponse(
    is_success=True,
    customer_id="test_customer",
    action_required=False,
    kind=TransactionKind.CONFIRM,
    amount=CONFIRM_AMOUNT,
    currency="usd",
    transaction_id="1234",
    error=None,
    raw_response=RAW_RESPONSE,
)
TOKEN = "token"
USED_GATEWAY = "mirumee.payments.dummy"


@patch("saleor.payment.gateway.update_payment")
def test_process_payment(
    update_payment_mock, fake_payment_interface, payment_txn_preauth
):
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_preauth, payment_token=TOKEN
    )
    fake_payment_interface.process_payment.return_value = PROCESS_PAYMENT_RESPONSE

    transaction = gateway.process_payment(
        payment=payment_txn_preauth,
        token=TOKEN,
        manager=fake_payment_interface,
        channel_slug=payment_txn_preauth.order.channel.slug,
    )

    fake_payment_interface.process_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA, channel_slug=payment_txn_preauth.order.channel.slug
    )
    assert transaction.amount == PROCESS_PAYMENT_RESPONSE.amount
    assert transaction.kind == TransactionKind.CAPTURE
    assert transaction.currency == "usd"
    assert transaction.gateway_response == RAW_RESPONSE
    update_payment_mock.assert_called_once_with(
        payment_txn_preauth, PROCESS_PAYMENT_RESPONSE
    )


def test_store_source_when_processing_payment(
    fake_payment_interface, payment_txn_preauth
):
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_preauth, payment_token=TOKEN, store_source=True
    )
    fake_payment_interface.process_payment.return_value = PROCESS_PAYMENT_RESPONSE

    transaction = gateway.process_payment(
        payment=payment_txn_preauth,
        token=TOKEN,
        manager=fake_payment_interface,
        store_source=True,
        channel_slug=payment_txn_preauth.order.channel.slug,
    )

    fake_payment_interface.process_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA, channel_slug=payment_txn_preauth.order.channel.slug
    )
    assert transaction.customer_id == PROCESS_PAYMENT_RESPONSE.customer_id


@patch("saleor.payment.gateway.update_payment")
def test_authorize_payment(update_payment_mock, fake_payment_interface, payment_dummy):
    PAYMENT_DATA = create_payment_information(
        payment=payment_dummy, payment_token=TOKEN
    )
    fake_payment_interface.authorize_payment.return_value = AUTHORIZE_RESPONSE

    transaction = gateway.authorize(
        payment=payment_dummy,
        token=TOKEN,
        manager=fake_payment_interface,
        channel_slug=payment_dummy.order.channel.slug,
    )

    fake_payment_interface.authorize_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA, channel_slug=payment_dummy.order.channel.slug
    )
    assert transaction.amount == AUTHORIZE_RESPONSE.amount
    assert transaction.kind == TransactionKind.AUTH
    assert transaction.currency == "usd"
    assert transaction.gateway_response == RAW_RESPONSE
    update_payment_mock.assert_called_once_with(payment_dummy, AUTHORIZE_RESPONSE)


@patch("saleor.payment.gateway.update_payment")
def test_capture_payment(
    update_payment_mock, fake_payment_interface, payment_txn_preauth
):
    auth_transaction = payment_txn_preauth.transactions.get()
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_preauth, payment_token=auth_transaction.token
    )
    fake_payment_interface.capture_payment.return_value = PROCESS_PAYMENT_RESPONSE

    transaction = gateway.capture(
        payment=payment_txn_preauth,
        manager=fake_payment_interface,
        channel_slug=payment_txn_preauth.order.channel.slug,
    )

    fake_payment_interface.capture_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA, channel_slug=payment_txn_preauth.order.channel.slug
    )
    assert transaction.amount == PROCESS_PAYMENT_RESPONSE.amount
    assert transaction.kind == TransactionKind.CAPTURE
    assert transaction.currency == "usd"
    assert transaction.gateway_response == RAW_RESPONSE
    update_payment_mock.assert_called_once_with(
        payment_txn_preauth, PROCESS_PAYMENT_RESPONSE
    )


def test_refund_for_manual_payment(payment_txn_captured):
    payment_txn_captured.gateway = CustomPaymentChoices.MANUAL
    transaction = gateway.refund(
        payment=payment_txn_captured,
        manager=get_plugins_manager(allow_replica=False),
        amount=PARTIAL_REFUND_AMOUNT,
        channel_slug=payment_txn_captured.order.channel.slug,
    )
    payment_txn_captured.refresh_from_db()
    assert payment_txn_captured.charge_status == ChargeStatus.PARTIALLY_REFUNDED
    assert transaction.amount == PARTIAL_REFUND_AMOUNT
    assert transaction.kind == TransactionKind.REFUND
    assert transaction.currency == "USD"


def test_partial_refund_payment(fake_payment_interface, payment_txn_captured):
    capture_transaction = payment_txn_captured.transactions.get()
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_captured,
        amount=PARTIAL_REFUND_AMOUNT,
        payment_token=capture_transaction.token,
    )
    fake_payment_interface.refund_payment.return_value = PARTIAL_REFUND_RESPONSE
    transaction = gateway.refund(
        payment=payment_txn_captured,
        manager=fake_payment_interface,
        amount=PARTIAL_REFUND_AMOUNT,
        channel_slug=payment_txn_captured.order.channel.slug,
    )
    fake_payment_interface.refund_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA, channel_slug=payment_txn_captured.order.channel.slug
    )

    payment_txn_captured.refresh_from_db()
    assert payment_txn_captured.charge_status == ChargeStatus.PARTIALLY_REFUNDED
    assert transaction.amount == PARTIAL_REFUND_AMOUNT
    assert transaction.kind == TransactionKind.REFUND
    assert transaction.currency == "usd"
    assert transaction.gateway_response == RAW_RESPONSE


def test_full_refund_payment(fake_payment_interface, payment_txn_captured):
    capture_transaction = payment_txn_captured.transactions.get()
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_captured,
        amount=FULL_REFUND_AMOUNT,
        payment_token=capture_transaction.token,
    )
    fake_payment_interface.refund_payment.return_value = FULL_REFUND_RESPONSE
    transaction = gateway.refund(
        payment=payment_txn_captured,
        manager=fake_payment_interface,
        channel_slug=payment_txn_captured.order.channel.slug,
    )
    fake_payment_interface.refund_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA, channel_slug=payment_txn_captured.order.channel.slug
    )

    payment_txn_captured.refresh_from_db()
    assert payment_txn_captured.charge_status == ChargeStatus.FULLY_REFUNDED
    assert transaction.amount == FULL_REFUND_AMOUNT
    assert transaction.kind == TransactionKind.REFUND
    assert transaction.currency == "usd"
    assert transaction.gateway_response == RAW_RESPONSE


def test_void_payment(fake_payment_interface, payment_txn_preauth):
    auth_transaction = payment_txn_preauth.transactions.get()
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_preauth,
        payment_token=auth_transaction.token,
        amount=VOID_AMOUNT,
    )
    fake_payment_interface.void_payment.return_value = VOID_RESPONSE

    transaction = gateway.void(
        payment=payment_txn_preauth,
        manager=fake_payment_interface,
        channel_slug=payment_txn_preauth.order.channel.slug,
    )

    fake_payment_interface.void_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA, channel_slug=payment_txn_preauth.order.channel.slug
    )
    payment_txn_preauth.refresh_from_db()
    assert not payment_txn_preauth.is_active
    assert transaction.amount == VOID_RESPONSE.amount
    assert transaction.kind == TransactionKind.VOID
    assert transaction.currency == "usd"
    assert transaction.gateway_response == RAW_RESPONSE


@patch("saleor.payment.gateway.update_payment")
def test_confirm_payment(
    update_payment_mock, fake_payment_interface, payment_txn_to_confirm
):
    auth_transaction = payment_txn_to_confirm.transactions.get()
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_to_confirm,
        payment_token=auth_transaction.token,
        amount=CONFIRM_AMOUNT,
    )
    fake_payment_interface.confirm_payment.return_value = CONFIRM_RESPONSE

    transaction = gateway.confirm(
        payment=payment_txn_to_confirm,
        manager=fake_payment_interface,
        channel_slug=payment_txn_to_confirm.order.channel.slug,
    )

    fake_payment_interface.confirm_payment.assert_called_once_with(
        USED_GATEWAY,
        PAYMENT_DATA,
        channel_slug=payment_txn_to_confirm.order.channel.slug,
    )
    assert transaction.amount == CONFIRM_RESPONSE.amount
    assert transaction.kind == TransactionKind.CONFIRM
    assert transaction.currency == "usd"
    assert transaction.gateway_response == RAW_RESPONSE
    update_payment_mock.assert_called_once_with(
        payment_txn_to_confirm, CONFIRM_RESPONSE
    )


def test_list_gateways(fake_payment_interface):
    gateways = [{"name": "Stripe"}, {"name": "Braintree"}]
    fake_payment_interface.list_payment_gateways.return_value = gateways
    lst = gateway.list_gateways(fake_payment_interface)
    fake_payment_interface.list_payment_gateways.assert_called_once()
    assert lst == gateways


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
def test_request_charge_action_missing_active_event(
    mocked_is_active, order, staff_user
):
    # given
    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["capture", "cancel"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10"),
    )
    action_value = Decimal("5.00")
    requested_event = transaction.events.create(
        amount_value=action_value,
        currency=transaction.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )
    mocked_is_active.return_value = False

    # when & then
    with pytest.raises(PaymentError):
        request_charge_action(
            transaction=transaction,
            manager=get_plugins_manager(allow_replica=False),
            charge_value=action_value,
            channel_slug=order.channel.slug,
            user=staff_user,
            app=None,
            request_event=requested_event,
        )


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_charge_requested")
def test_request_charge_action_on_order(
    mocked_transaction_request,
    mocked_is_active,
    order,
    staff_user,
    permission_manage_payments,
    app,
):
    # given
    app.permissions.add(permission_manage_payments)
    webhook = app.webhooks.create(
        name="Simple webhook", app=app, target_url="http://127.0.0.1"
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED)

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["capture", "cancel"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10"),
        app=app,
    )
    action_value = Decimal("5.00")
    requested_event = transaction.events.create(
        amount_value=action_value,
        currency=transaction.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )
    mocked_is_active.side_effect = [False, True]

    # when
    request_charge_action(
        transaction=transaction,
        manager=get_plugins_manager(allow_replica=False),
        charge_value=action_value,
        channel_slug=order.channel.slug,
        user=staff_user,
        app=None,
        request_event=requested_event,
    )

    # then
    assert mocked_is_active.called
    mocked_transaction_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.CHARGE,
            action_value=action_value,
            event=requested_event,
            transaction_app_owner=app,
        ),
        order.channel.slug,
    )

    event = order.events.first()
    assert event.type == OrderEvents.TRANSACTION_CHARGE_REQUESTED
    assert Decimal(event.parameters["amount"]) == action_value
    assert event.parameters["reference"] == transaction.psp_reference
    assert event.user == staff_user


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_charge_requested")
def test_request_charge_action_by_app(
    mocked_transaction_request,
    mocked_is_active,
    order,
    app,
    webhook_app,
    permission_manage_payments,
):
    # given
    webhook_app.permissions.add(permission_manage_payments)
    webhook = webhook_app.webhooks.create(
        name="Simple webhook", target_url="http://127.0.0.1"
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED)
    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["capture", "cancel"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10"),
        app=webhook_app,
    )
    action_value = Decimal("5.00")
    requested_event = transaction.events.create(
        amount_value=action_value,
        currency=transaction.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )
    mocked_is_active.side_effect = [False, True]

    # when
    request_charge_action(
        transaction=transaction,
        manager=get_plugins_manager(allow_replica=False),
        charge_value=action_value,
        channel_slug=order.channel.slug,
        user=None,
        app=app,
        request_event=requested_event,
    )

    # then
    assert mocked_is_active.called
    mocked_transaction_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.CHARGE,
            action_value=action_value,
            event=requested_event,
            transaction_app_owner=webhook_app,
        ),
        order.channel.slug,
    )

    event = order.events.first()
    assert event.type == OrderEvents.TRANSACTION_CHARGE_REQUESTED
    assert Decimal(event.parameters["amount"]) == action_value
    assert event.parameters["reference"] == transaction.psp_reference
    assert event.app == app


@patch("saleor.plugins.manager.PluginsManager.transaction_charge_requested")
def test_request_action_by_removed_app(mocked_transaction_request, order, removed_app):
    # given
    app_identifier = "webhook.app.identifier"
    removed_app.identifier = app_identifier
    removed_app.save()
    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["capture", "void"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10"),
        app_identifier=app_identifier,
    )
    action_value = Decimal("5.00")
    requested_event = transaction.events.create(
        amount_value=action_value,
        currency=transaction.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    # when & then
    with pytest.raises(PaymentError):
        request_charge_action(
            transaction=transaction,
            manager=get_plugins_manager(allow_replica=False),
            charge_value=action_value,
            channel_slug=order.channel.slug,
            user=None,
            app=removed_app,
            request_event=requested_event,
        )
    assert not mocked_transaction_request.called


@patch("saleor.plugins.manager.PluginsManager.transaction_charge_requested")
def test_request_action_by_disabled_app(mocked_transaction_request, order, app):
    # given
    app_identifier = "webhook.app.identifier"
    app.identifier = app_identifier
    app.is_active = False
    app.save()
    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["capture", "void"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10"),
        app_identifier=app_identifier,
    )
    action_value = Decimal("5.00")
    requested_event = transaction.events.create(
        amount_value=action_value,
        currency=transaction.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    # when & then
    with pytest.raises(PaymentError):
        request_charge_action(
            transaction=transaction,
            manager=get_plugins_manager(allow_replica=False),
            charge_value=action_value,
            channel_slug=order.channel.slug,
            user=None,
            app=app,
            request_event=requested_event,
        )
    assert not mocked_transaction_request.called


@patch("saleor.plugins.manager.PluginsManager.transaction_charge_requested")
def test_request_action_by_removed_app_and_second_active(
    mocked_transaction_request,
    order,
    removed_app,
    webhook_app,
    permission_manage_payments,
):
    # given
    app_identifier = "webhook.app.identifier"
    active_app = webhook_app
    active_app.identifier = app_identifier
    active_app.save()
    active_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=active_app,
    )
    event_type = WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED
    webhook.events.create(event_type=event_type)

    removed_app.identifier = app_identifier
    removed_app.save()

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["capture", "void"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10"),
        app_identifier=app_identifier,
        app=removed_app,
    )
    action_value = Decimal("5.00")
    requested_event = transaction.events.create(
        amount_value=action_value,
        currency=transaction.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    # when
    request_charge_action(
        transaction=transaction,
        manager=get_plugins_manager(allow_replica=False),
        charge_value=action_value,
        channel_slug=order.channel.slug,
        user=None,
        app=None,
        request_event=requested_event,
    )

    # then
    mocked_transaction_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.CHARGE,
            action_value=action_value,
            event=requested_event,
            transaction_app_owner=active_app,
        ),
        order.channel.slug,
    )


@patch("saleor.plugins.manager.PluginsManager.transaction_charge_requested")
def test_request_action_by_disabled_app_and_second_active(
    mocked_transaction_request, order, app, webhook_app, permission_manage_payments
):
    # given
    app_identifier = "webhook.app.identifier"
    active_app = webhook_app
    active_app.identifier = app_identifier
    active_app.save()
    active_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=active_app,
    )
    event_type = WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED
    webhook.events.create(event_type=event_type)

    app.identifier = app_identifier
    app.is_active = False
    app.save()

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["capture", "void"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10"),
        app_identifier=app_identifier,
        app=app,
    )
    action_value = Decimal("5.00")
    requested_event = transaction.events.create(
        amount_value=action_value,
        currency=transaction.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    # when
    request_charge_action(
        transaction=transaction,
        manager=get_plugins_manager(allow_replica=False),
        charge_value=action_value,
        channel_slug=order.channel.slug,
        user=None,
        app=None,
        request_event=requested_event,
    )

    # then
    mocked_transaction_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.CHARGE,
            action_value=action_value,
            event=requested_event,
            transaction_app_owner=active_app,
        ),
        order.channel.slug,
    )


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_charge_requested")
def test_request_charge_action_on_checkout(
    mocked_transaction_request,
    mocked_is_active,
    checkout,
    staff_user,
    app,
    permission_manage_payments,
):
    # given
    app.permissions.add(permission_manage_payments)
    webhook = app.webhooks.create(
        name="Simple webhook", app=app, target_url="http://127.0.0.1"
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED)

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["capture", "cancel"],
        currency="USD",
        checkout_id=checkout.pk,
        authorized_value=Decimal("10"),
        app=app,
    )
    action_value = Decimal("5.00")
    requested_event = transaction.events.create(
        amount_value=action_value,
        currency=transaction.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )
    mocked_is_active.side_effect = [False, True]

    # when
    request_charge_action(
        transaction=transaction,
        manager=get_plugins_manager(allow_replica=False),
        charge_value=action_value,
        channel_slug=checkout.channel.slug,
        user=staff_user,
        app=None,
        request_event=requested_event,
    )

    # then
    assert mocked_is_active.called
    mocked_transaction_request.assert_called_once_with(
        TransactionActionData(
            action_type=TransactionAction.CHARGE,
            transaction=transaction,
            event=requested_event,
            action_value=action_value,
            transaction_app_owner=app,
        ),
        checkout.channel.slug,
    )


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
def test_request_refund_action_missing_active_event(
    mocked_is_active, order, staff_user
):
    # given
    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        order_id=order.pk,
        charged_value=Decimal("10"),
    )
    action_value = Decimal("5.00")
    requested_event = transaction.events.create(
        amount_value=action_value,
        currency=transaction.currency,
        type=TransactionEventType.REFUND_REQUEST,
    )
    mocked_is_active.return_value = False

    # when & then
    with pytest.raises(PaymentError):
        request_refund_action(
            transaction=transaction,
            manager=get_plugins_manager(allow_replica=False),
            refund_value=action_value,
            channel_slug=order.channel.slug,
            user=staff_user,
            app=None,
            request_event=requested_event,
        )


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
def test_request_refund_action_updates_refundable_for_checkout(
    mocked_is_active, staff_user, checkout, transaction_item_generator
):
    # given
    checkout.automatically_refundable = True
    checkout.save()
    transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(100)
    )
    action_value = Decimal("5.00")
    requested_event = transaction.events.create(
        amount_value=action_value,
        currency=transaction.currency,
        type=TransactionEventType.REFUND_REQUEST,
    )
    mocked_is_active.side_effect = [False, False]

    # when
    with pytest.raises(PaymentError):
        request_refund_action(
            transaction=transaction,
            manager=get_plugins_manager(allow_replica=False),
            refund_value=action_value,
            channel_slug=checkout.channel.slug,
            user=staff_user,
            app=None,
            request_event=requested_event,
        )

    # then
    transaction.refresh_from_db()
    checkout.refresh_from_db()
    assert checkout.automatically_refundable is False
    assert transaction.last_refund_success is False


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_refund_requested")
def test_request_refund_action_on_order(
    mocked_transaction_request,
    mocked_is_active,
    order,
    staff_user,
    app,
    permission_manage_payments,
):
    # given
    app.permissions.add(permission_manage_payments)
    webhook = app.webhooks.create(
        name="Simple webhook", app=app, target_url="http://127.0.0.1"
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED)

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        order_id=order.pk,
        charged_value=Decimal("10"),
        app=app,
    )
    action_value = Decimal("5.00")
    requested_event = transaction.events.create(
        amount_value=action_value,
        currency=transaction.currency,
        type=TransactionEventType.REFUND_REQUEST,
    )
    mocked_is_active.side_effect = [False, True]

    # when
    request_refund_action(
        transaction=transaction,
        manager=get_plugins_manager(allow_replica=False),
        refund_value=action_value,
        channel_slug=order.channel.slug,
        user=staff_user,
        app=None,
        request_event=requested_event,
    )

    # then
    assert mocked_is_active.called
    mocked_transaction_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.REFUND,
            action_value=action_value,
            event=requested_event,
            transaction_app_owner=app,
        ),
        order.channel.slug,
    )

    event = order.events.first()
    assert event.type == OrderEvents.TRANSACTION_REFUND_REQUESTED
    assert Decimal(event.parameters["amount"]) == action_value
    assert event.parameters["reference"] == transaction.psp_reference
    assert event.user == staff_user


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_refund_requested")
def test_request_refund_action_with_granted_refund(
    mocked_transaction_request,
    mocked_is_active,
    order_with_lines,
    staff_user,
    permission_manage_payments,
    app,
):
    # given
    app.permissions.add(permission_manage_payments)
    webhook = app.webhooks.create(
        name="Simple webhook", app=app, target_url="http://127.0.0.1"
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED)

    order_line = order_with_lines.lines.first()
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=order_line.unit_price_gross_amount
    )
    granted_refund.lines.create(
        quantity=1,
        order_line=order_line,
    )

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        order_id=order_with_lines.pk,
        charged_value=Decimal("10"),
        app=app,
    )
    action_value = order_line.unit_price_gross_amount
    requested_event = transaction.events.create(
        amount_value=action_value,
        currency=transaction.currency,
        type=TransactionEventType.REFUND_REQUEST,
    )
    mocked_is_active.side_effect = [False, True]

    # when
    request_refund_action(
        transaction=transaction,
        manager=get_plugins_manager(allow_replica=False),
        refund_value=action_value,
        channel_slug=order_with_lines.channel.slug,
        user=staff_user,
        app=None,
        request_event=requested_event,
        granted_refund=granted_refund,
    )

    # then
    assert mocked_is_active.called
    mocked_transaction_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.REFUND,
            action_value=action_value,
            event=requested_event,
            transaction_app_owner=app,
            granted_refund=granted_refund,
        ),
        order_with_lines.channel.slug,
    )

    event = order_with_lines.events.first()
    assert event.type == OrderEvents.TRANSACTION_REFUND_REQUESTED
    assert Decimal(event.parameters["amount"]) == action_value
    assert event.parameters["reference"] == transaction.psp_reference
    assert event.user == staff_user


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_refund_requested")
def test_request_refund_action_by_app(
    mocked_transaction_request,
    mocked_is_active,
    order,
    app,
    webhook_app,
    permission_manage_payments,
):
    # given
    webhook_app.permissions.add(permission_manage_payments)
    webhook = webhook_app.webhooks.create(
        name="Simple webhook", app=app, target_url="http://127.0.0.1"
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED)

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        order_id=order.pk,
        charged_value=Decimal("10"),
        app=webhook_app,
    )
    action_value = Decimal("5.00")
    requested_event = transaction.events.create(
        amount_value=action_value,
        currency=transaction.currency,
        type=TransactionEventType.REFUND_REQUEST,
    )
    mocked_is_active.side_effect = [False, True]

    # when
    request_refund_action(
        transaction=transaction,
        manager=get_plugins_manager(allow_replica=False),
        refund_value=action_value,
        channel_slug=order.channel.slug,
        user=None,
        app=app,
        request_event=requested_event,
    )

    # then
    assert mocked_is_active.called
    mocked_transaction_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.REFUND,
            action_value=action_value,
            event=requested_event,
            transaction_app_owner=webhook_app,
        ),
        order.channel.slug,
    )

    event = order.events.first()
    assert event.type == OrderEvents.TRANSACTION_REFUND_REQUESTED
    assert Decimal(event.parameters["amount"]) == action_value
    assert event.parameters["reference"] == transaction.psp_reference
    assert event.app == app
    assert not event.user


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_refund_requested")
def test_request_refund_action_on_checkout(
    mocked_transaction_request,
    mocked_is_active,
    checkout,
    staff_user,
    app,
    permission_manage_payments,
):
    # given
    app.permissions.add(permission_manage_payments)
    webhook = app.webhooks.create(
        name="Simple webhook", app=app, target_url="http://127.0.0.1"
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED)

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        checkout_id=checkout.pk,
        charged_value=Decimal("10"),
        app=app,
    )
    action_value = Decimal("5.00")
    requested_event = transaction.events.create(
        amount_value=action_value,
        currency=transaction.currency,
        type=TransactionEventType.REFUND_REQUEST,
    )
    mocked_is_active.side_effect = [False, True]

    # when
    request_refund_action(
        transaction=transaction,
        manager=get_plugins_manager(allow_replica=False),
        refund_value=action_value,
        channel_slug=checkout.channel.slug,
        user=staff_user,
        app=None,
        request_event=requested_event,
    )

    # then
    assert mocked_is_active.called
    mocked_transaction_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.REFUND,
            action_value=action_value,
            event=requested_event,
            transaction_app_owner=app,
        ),
        checkout.channel.slug,
    )


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
def test_request_cancelation_action_missing_active_event(
    mocked_is_active, order, staff_user
):
    # given
    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["capture", "cancel"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10"),
    )
    requested_event = transaction.events.create(
        currency=transaction.currency,
        type=TransactionEventType.CANCEL_REQUEST,
    )

    mocked_is_active.return_value = False

    # when & then
    with pytest.raises(PaymentError):
        request_cancelation_action(
            transaction=transaction,
            manager=get_plugins_manager(allow_replica=False),
            cancel_value=None,
            channel_slug=order.channel.slug,
            user=staff_user,
            app=None,
            request_event=requested_event,
            action=TransactionAction.CANCEL,
        )


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
def test_request_cancel_action_updates_refundable_for_checkout(
    mocked_is_active, checkout, staff_user, transaction_item_generator
):
    # given
    checkout.automatically_refundable = True
    checkout.save()

    transaction = transaction_item_generator(
        checkout_id=checkout.pk, authorized_value=Decimal(100)
    )
    requested_event = transaction.events.create(
        currency=transaction.currency,
        type=TransactionEventType.CANCEL_REQUEST,
    )

    mocked_is_active.return_value = False

    # when
    with pytest.raises(PaymentError):
        request_cancelation_action(
            transaction=transaction,
            manager=get_plugins_manager(allow_replica=False),
            cancel_value=None,
            channel_slug=checkout.channel.slug,
            user=staff_user,
            app=None,
            request_event=requested_event,
            action=TransactionAction.CANCEL,
        )

    # then
    transaction.refresh_from_db()
    checkout.refresh_from_db()
    assert checkout.automatically_refundable is False
    assert transaction.last_refund_success is False


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_cancelation_requested")
def test_request_cancelation_action_on_order(
    mocked_transaction_request,
    mocked_is_active,
    order,
    staff_user,
    app,
    permission_manage_payments,
):
    # given
    app.permissions.add(permission_manage_payments)
    webhook = app.webhooks.create(
        name="Simple webhook", app=app, target_url="http://127.0.0.1"
    )
    webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_CANCELATION_REQUESTED
    )

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["capture", "cancel"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10"),
        app=app,
    )
    requested_event = transaction.events.create(
        currency=transaction.currency,
        type=TransactionEventType.CANCEL_REQUEST,
    )
    mocked_is_active.side_effect = [False, True]

    # when
    request_cancelation_action(
        transaction=transaction,
        manager=get_plugins_manager(allow_replica=False),
        cancel_value=None,
        channel_slug=order.channel.slug,
        user=staff_user,
        app=None,
        request_event=requested_event,
        action=TransactionAction.CANCEL,
    )

    # then
    assert mocked_is_active.called
    mocked_transaction_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.CANCEL,
            action_value=None,
            event=requested_event,
            transaction_app_owner=app,
        ),
        order.channel.slug,
    )

    event = order.events.first()
    assert event.type == OrderEvents.TRANSACTION_CANCEL_REQUESTED
    assert event.parameters["reference"] == transaction.psp_reference
    assert event.user == staff_user


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_cancelation_requested")
def test_request_cancelation_action_by_app(
    mocked_transaction_request,
    mocked_is_active,
    order,
    app,
    webhook_app,
    permission_manage_payments,
):
    # given
    webhook_app.permissions.add(permission_manage_payments)
    webhook = webhook_app.webhooks.create(
        name="Simple webhook", target_url="http://127.0.0.1"
    )
    webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_CANCELATION_REQUESTED
    )

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["capture", "cancel"],
        currency="USD",
        order_id=order.pk,
        authorized_value=Decimal("10"),
        app=webhook_app,
    )
    requested_event = transaction.events.create(
        currency=transaction.currency, type=TransactionEventType.CANCEL_REQUEST
    )
    mocked_is_active.side_effect = [False, True]

    # when
    request_cancelation_action(
        transaction=transaction,
        manager=get_plugins_manager(allow_replica=False),
        cancel_value=None,
        channel_slug=order.channel.slug,
        user=None,
        app=app,
        request_event=requested_event,
        action=TransactionAction.CANCEL,
    )

    # then
    assert mocked_is_active.called
    mocked_transaction_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.CANCEL,
            action_value=None,
            event=requested_event,
            transaction_app_owner=webhook_app,
        ),
        order.channel.slug,
    )

    event = order.events.first()
    assert event.type == OrderEvents.TRANSACTION_CANCEL_REQUESTED
    assert event.parameters["reference"] == transaction.psp_reference
    assert event.app == app
    assert not event.user


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_cancelation_requested")
def test_request_cancelation_action_on_checkout(
    mocked_transaction_request,
    mocked_is_active,
    checkout,
    staff_user,
    app,
    permission_manage_payments,
):
    # given
    app.permissions.add(permission_manage_payments)
    webhook = app.webhooks.create(
        name="Simple webhook", app=app, target_url="http://127.0.0.1"
    )
    webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_CANCELATION_REQUESTED
    )

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["capture", "cancel"],
        currency="USD",
        checkout_id=checkout.pk,
        authorized_value=Decimal("10"),
        app=app,
    )
    requested_event = transaction.events.create(
        currency=transaction.currency,
        type=TransactionEventType.CANCEL_REQUEST,
    )
    mocked_is_active.side_effect = [False, True]

    # when
    request_cancelation_action(
        transaction=transaction,
        manager=get_plugins_manager(allow_replica=False),
        cancel_value=None,
        channel_slug=checkout.channel.slug,
        user=staff_user,
        app=None,
        request_event=requested_event,
        action=TransactionAction.CANCEL,
    )

    # then
    assert mocked_is_active.called
    mocked_transaction_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.CANCEL,
            action_value=None,
            event=requested_event,
            transaction_app_owner=app,
        ),
        checkout.channel.slug,
    )


@patch("saleor.payment.gateway.void")
@patch("saleor.payment.gateway.refund")
def test_payment_refund_or_void_no_payment(refund_mock, void_mock):
    """Test that neither refund nor void is called when there is no payment object."""
    # when
    gateway.payment_refund_or_void(None, get_plugins_manager(allow_replica=False), None)

    # then
    refund_mock.assert_not_called()
    void_mock.assert_not_called()


@patch("saleor.payment.gateway.refund")
def test_payment_refund_or_void_refund_called(refund_mock, payment):
    """Test that refund is called when there is no matching transaction."""
    # given
    payment.transactions.count() == 0
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.save(update_fields=["charge_status"])

    # when
    gateway.payment_refund_or_void(
        payment, get_plugins_manager(allow_replica=False), None
    )

    # then
    assert refund_mock.called_once()


@patch("saleor.payment.gateway.refund")
def test_payment_refund_or_void_refund_not_called_refund_already_started(
    refund_mock, payment
):
    """Test that refund is not called if a matching transaction already exists."""
    # given
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.save(update_fields=["charge_status"])

    assert payment.can_refund() is True

    payment.transactions.create(
        is_success=True,
        action_required=False,
        kind=TransactionKind.REFUND_ONGOING,
        amount=payment.total,
        currency=payment.currency,
        token="test",
        gateway_response={},
    )

    # when
    gateway.payment_refund_or_void(
        payment, get_plugins_manager(allow_replica=False), None
    )

    # then
    refund_mock.assert_not_called()


@patch("saleor.payment.gateway.refund")
def test_payment_refund_or_void_refund_called_txn_exist(refund_mock, payment):
    """Test that refund is called when existing transactions don't cover the captured amount."""
    # given
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.save(update_fields=["charge_status"])
    assert payment.can_refund() is True
    payment.captured_amount = payment.total
    payment.save(update_fields=["captured_amount"])
    txn = payment.transactions.create(
        is_success=True,
        action_required=False,
        kind=TransactionKind.REFUND_ONGOING,
        amount=payment.captured_amount / 2,
        currency=payment.currency,
        token="test",
        gateway_response={},
    )

    # when
    gateway.payment_refund_or_void(
        payment,
        get_plugins_manager(allow_replica=False),
        None,
        transaction_id=txn.token,
    )

    # then
    assert refund_mock.called_once()


@patch("saleor.payment.gateway.refund")
def test_payment_refund_or_void_refund_called_no_txn_with_given_transaction_id(
    refund_mock, payment
):
    """Test that refund is called when unrelated refund transactions exist."""
    # given
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.save(update_fields=["charge_status"])
    assert payment.can_refund() is True
    payment.captured_amount = payment.total
    payment.save(update_fields=["captured_amount"])
    payment.transactions.create(
        is_success=True,
        action_required=False,
        kind=TransactionKind.REFUND_ONGOING,
        amount=payment.captured_amount,
        currency=payment.currency,
        token="test",
        gateway_response={},
    )

    # when
    gateway.payment_refund_or_void(
        payment,
        get_plugins_manager(allow_replica=False),
        None,
        transaction_id="another value",
    )

    # then
    assert refund_mock.called_once()


@patch("saleor.payment.gateway.void")
def test_payment_refund_or_void_void_called(void_mock, payment):
    """Test that void is called when there is no matching transaction."""
    # given
    payment.can_void = Mock(return_value=True)
    assert payment.can_void() is True
    payment.transactions.count() == 0

    # when
    gateway.payment_refund_or_void(
        payment, get_plugins_manager(allow_replica=False), None
    )

    # then
    assert void_mock.called_once()


@patch("saleor.payment.gateway.void")
def test_payment_refund_or_void_void_not_called_txn_exist(void_mock, payment):
    """Test that void is not called if a matching void transaction already exists."""
    # given
    payment.can_void = Mock(return_value=True)
    assert payment.can_refund() is False
    assert payment.can_void() is True

    txn = payment.transactions.create(
        is_success=True,
        action_required=False,
        kind=TransactionKind.VOID,
        amount=payment.total,
        currency=payment.currency,
        token="test",
        gateway_response={},
    )

    # when
    gateway.payment_refund_or_void(
        payment,
        get_plugins_manager(allow_replica=False),
        None,
        transaction_id=txn.token,
    )

    # then
    void_mock.assert_not_called()
