from decimal import Decimal
from unittest.mock import ANY, call, patch

import pytest
from django.test import override_settings

from ...channel import MarkAsPaidStrategy
from ...core.models import EventDelivery
from ...core.utils.events import call_event_including_protected_events
from ...giftcard import GiftCardEvents
from ...giftcard.models import GiftCard, GiftCardEvent
from ...order.fetch import OrderLineInfo, fetch_order_info
from ...payment import ChargeStatus, PaymentError, TransactionEventType, TransactionKind
from ...payment.models import Payment
from ...plugins.manager import get_plugins_manager
from ...product.models import DigitalContent
from ...product.tests.utils import create_image
from ...warehouse.models import Allocation, Stock
from ...webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ...webhook.utils import get_webhooks_for_multiple_events
from .. import (
    FulfillmentStatus,
    OrderAuthorizeStatus,
    OrderChargeStatus,
    OrderEvents,
    OrderStatus,
)
from ..actions import (
    WEBHOOK_EVENTS_FOR_FULLY_PAID,
    WEBHOOK_EVENTS_FOR_ORDER_CANCELED,
    WEBHOOK_EVENTS_FOR_ORDER_CHARGED,
    WEBHOOK_EVENTS_FOR_ORDER_CREATED,
    WEBHOOK_EVENTS_FOR_ORDER_FULFILLED,
    WEBHOOK_EVENTS_FOR_ORDER_REFUNDED,
    automatically_fulfill_digital_lines,
    call_order_event,
    call_order_events,
    cancel_fulfillment,
    cancel_order,
    clean_mark_order_as_paid,
    fulfill_order_lines,
    handle_fully_paid_order,
    mark_order_as_paid_with_payment,
    mark_order_as_paid_with_transaction,
    order_authorized,
    order_awaits_fulfillment_approval,
    order_charged,
    order_confirmed,
    order_created,
    order_fulfilled,
    order_refunded,
    order_transaction_updated,
    order_voided,
)
from ..fetch import OrderInfo
from ..models import Fulfillment, OrderLine
from ..notifications import (
    send_fulfillment_confirmation_to_customer,
    send_payment_confirmation,
)
from ..utils import updates_amounts_for_order


@patch(
    "saleor.order.actions.send_fulfillment_confirmation_to_customer",
    wraps=send_fulfillment_confirmation_to_customer,
)
@patch(
    "saleor.order.actions.send_payment_confirmation", wraps=send_payment_confirmation
)
@patch("saleor.plugins.manager.PluginsManager.fulfillment_created")
def test_handle_fully_paid_order_digital_lines(
    mock_fulfillment_created,
    mock_send_payment_confirmation,
    send_fulfillment_confirmation_to_customer,
    order_with_digital_line,
):
    # given
    order = order_with_digital_line
    order.payments.add(Payment.objects.create())
    redirect_url = "http://localhost.pl"
    order = order_with_digital_line
    order.redirect_url = redirect_url
    order.save()
    order_info = fetch_order_info(order)
    manager = get_plugins_manager(allow_replica=False)

    webhook_event_map = get_webhooks_for_multiple_events(WEBHOOK_EVENTS_FOR_FULLY_PAID)

    # when
    handle_fully_paid_order(manager, order_info, webhook_event_map=webhook_event_map)

    # then
    fulfillment = order.fulfillments.first()
    event_order_paid = order.events.get()

    assert event_order_paid.type == OrderEvents.ORDER_FULLY_PAID

    mock_send_payment_confirmation.assert_called_once_with(order_info, manager)
    send_fulfillment_confirmation_to_customer.assert_called_once_with(
        order, fulfillment, user=order.user, app=None, manager=manager
    )

    order.refresh_from_db()
    assert order.status == OrderStatus.FULFILLED
    mock_fulfillment_created.assert_called_once_with(fulfillment)


@patch("saleor.order.actions.send_payment_confirmation")
def test_handle_fully_paid_order(mock_send_payment_confirmation, order):
    # given
    manager = get_plugins_manager(allow_replica=False)

    order.payments.add(Payment.objects.create())
    order_info = fetch_order_info(order)

    webhook_event_map = get_webhooks_for_multiple_events(WEBHOOK_EVENTS_FOR_FULLY_PAID)

    # when
    handle_fully_paid_order(manager, order_info, webhook_event_map=webhook_event_map)

    # then
    event_order_paid = order.events.get()
    assert event_order_paid.type == OrderEvents.ORDER_FULLY_PAID

    mock_send_payment_confirmation.assert_called_once_with(order_info, manager)


@patch("saleor.order.notifications.send_payment_confirmation")
def test_handle_fully_paid_order_no_email(mock_send_payment_confirmation, order):
    # given
    order.user = None
    order.user_email = ""
    manager = get_plugins_manager(allow_replica=False)
    order_info = fetch_order_info(order)

    # when
    webhook_event_map = get_webhooks_for_multiple_events(WEBHOOK_EVENTS_FOR_FULLY_PAID)

    # then
    handle_fully_paid_order(manager, order_info, webhook_event_map=webhook_event_map)
    event = order.events.get()
    assert event.type == OrderEvents.ORDER_FULLY_PAID
    assert not mock_send_payment_confirmation.called


@patch("saleor.order.actions.send_payment_confirmation")
def test_handle_fully_paid_order_with_gateway(mock_send_payment_confirmation, order):
    # given
    manager = get_plugins_manager(allow_replica=False)

    order.payments.add(Payment.objects.create())
    order_info = fetch_order_info(order)

    webhook_event_map = get_webhooks_for_multiple_events(WEBHOOK_EVENTS_FOR_FULLY_PAID)

    # when
    handle_fully_paid_order(
        manager,
        order_info,
        gateway="mirumee.payments.dummy",
        webhook_event_map=webhook_event_map,
    )

    # then
    event_order_paid = order.events.get()
    assert event_order_paid.type == OrderEvents.ORDER_FULLY_PAID
    assert event_order_paid.parameters == {"payment_gateway": "mirumee.payments.dummy"}

    mock_send_payment_confirmation.assert_called_once_with(order_info, manager)


@patch("saleor.giftcard.utils.send_gift_card_notification")
@patch("saleor.order.actions.send_payment_confirmation")
def test_handle_fully_paid_order_gift_cards_created(
    mock_send_payment_confirmation,
    send_notification_mock,
    site_settings,
    order_with_lines,
    non_shippable_gift_card_product,
    shippable_gift_card_product,
    django_capture_on_commit_callbacks,
):
    """Test that digital gift cards are issued when automatic fulfillment is enabled."""
    # given
    channel = order_with_lines.channel
    channel.automatically_fulfill_non_shippable_gift_card = True
    channel.save()

    order = order_with_lines

    non_shippable_gift_card_line = order_with_lines.lines.first()
    non_shippable_variant = non_shippable_gift_card_product.variants.get()
    non_shippable_gift_card_line.variant = non_shippable_variant
    non_shippable_gift_card_line.is_gift_card = True
    non_shippable_gift_card_line.is_shipping_required = False
    non_shippable_gift_card_line.quantity = 1
    allocation = non_shippable_gift_card_line.allocations.first()
    allocation.quantity_allocated = 1
    allocation.save(update_fields=["quantity_allocated"])

    shippable_gift_card_line = order_with_lines.lines.last()
    shippable_variant = shippable_gift_card_product.variants.get()
    shippable_gift_card_line.variant = shippable_variant
    shippable_gift_card_line.is_gift_card = True
    shippable_gift_card_line.is_shipping_required = True
    shippable_gift_card_line.quantity = 1

    OrderLine.objects.bulk_update(
        [non_shippable_gift_card_line, shippable_gift_card_line],
        ["variant", "is_gift_card", "is_shipping_required", "quantity"],
    )

    manager = get_plugins_manager(allow_replica=False)

    order.payments.add(Payment.objects.create())
    order_info = fetch_order_info(order)

    webhook_event_map = get_webhooks_for_multiple_events(WEBHOOK_EVENTS_FOR_FULLY_PAID)

    # when
    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        handle_fully_paid_order(
            manager, order_info, webhook_event_map=webhook_event_map
        )

    # second on_commit_callbacks as callbacks from first iteration triggers other
    # on_commit callbacks
    with django_capture_on_commit_callbacks(execute=True):
        for callback in callbacks:
            callback()

    # then
    assert order.events.filter(type=OrderEvents.ORDER_FULLY_PAID)

    mock_send_payment_confirmation.assert_called_once_with(order_info, manager)

    gift_card = GiftCard.objects.get()
    assert gift_card.initial_balance == non_shippable_gift_card_line.unit_price_gross
    assert GiftCardEvent.objects.filter(gift_card=gift_card, type=GiftCardEvents.BOUGHT)

    send_notification_mock.assert_called_once_with(
        None,
        None,
        order.user,
        order.user_email,
        gift_card,
        manager,
        order.channel.slug,
        resending=False,
    )


@patch("saleor.giftcard.utils.send_gift_card_notification")
@patch("saleor.order.actions.send_payment_confirmation")
def test_handle_fully_paid_order_gift_cards_not_created(
    mock_send_payment_confirmation,
    send_notification_mock,
    site_settings,
    order_with_lines,
    non_shippable_gift_card_product,
    shippable_gift_card_product,
    django_capture_on_commit_callbacks,
):
    """Ensure digital gift cards are not issued when automatic fulfillment is disabled."""
    # given
    channel = order_with_lines.channel
    channel.automatically_fulfill_non_shippable_gift_card = False
    channel.save()

    order = order_with_lines

    non_shippable_gift_card_line = order_with_lines.lines.first()
    non_shippable_variant = non_shippable_gift_card_product.variants.get()
    non_shippable_gift_card_line.variant = non_shippable_variant
    non_shippable_gift_card_line.is_gift_card = True
    non_shippable_gift_card_line.is_shipping_required = False
    non_shippable_gift_card_line.quantity = 1
    allocation = non_shippable_gift_card_line.allocations.first()
    allocation.quantity_allocated = 1
    allocation.save(update_fields=["quantity_allocated"])

    shippable_gift_card_line = order_with_lines.lines.last()
    shippable_variant = shippable_gift_card_product.variants.get()
    shippable_gift_card_line.variant = shippable_variant
    shippable_gift_card_line.is_gift_card = True
    shippable_gift_card_line.is_shipping_required = True
    shippable_gift_card_line.quantity = 1

    OrderLine.objects.bulk_update(
        [non_shippable_gift_card_line, shippable_gift_card_line],
        ["variant", "is_gift_card", "is_shipping_required", "quantity"],
    )

    manager = get_plugins_manager(allow_replica=False)

    order.payments.add(Payment.objects.create())
    order_info = fetch_order_info(order)

    webhook_event_map = get_webhooks_for_multiple_events(WEBHOOK_EVENTS_FOR_FULLY_PAID)

    # when
    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        handle_fully_paid_order(
            manager, order_info, webhook_event_map=webhook_event_map
        )

    # second on_commit_callbacks as callbacks from first iteration triggers other
    # on_commit callbacks
    with django_capture_on_commit_callbacks(execute=True):
        for callback in callbacks:
            callback()

    # then
    assert order.events.filter(type=OrderEvents.ORDER_FULLY_PAID)

    mock_send_payment_confirmation.assert_called_once_with(order_info, manager)

    assert not GiftCard.objects.exists()
    send_notification_mock.assert_not_called()


@pytest.mark.parametrize("automatically_confirm_all_new_orders", [True, False])
@patch("saleor.order.actions.send_payment_confirmation")
def test_handle_fully_paid_order_for_draft_order(
    mock_send_payment_confirmation, automatically_confirm_all_new_orders, draft_order
):
    # given
    manager = get_plugins_manager(allow_replica=False)

    channel = draft_order.channel
    channel.automatically_confirm_all_new_orders = automatically_confirm_all_new_orders
    channel.save(update_fields=["automatically_confirm_all_new_orders"])

    draft_order.payments.add(Payment.objects.create())
    order_info = fetch_order_info(draft_order)

    # when
    webhook_event_map = get_webhooks_for_multiple_events(WEBHOOK_EVENTS_FOR_FULLY_PAID)

    handle_fully_paid_order(manager, order_info, webhook_event_map=webhook_event_map)

    # then
    event_order_paid = draft_order.events.get()
    assert event_order_paid.type == OrderEvents.ORDER_FULLY_PAID
    assert draft_order.status == OrderStatus.DRAFT

    mock_send_payment_confirmation.assert_called_once_with(order_info, manager)


@patch(
    "saleor.order.actions.call_order_events",
    wraps=call_order_events,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_handle_fully_paid_order_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_order_events,
    setup_order_webhooks,
    order_with_lines,
    customer_user,
    settings,
    django_capture_on_commit_callbacks,
):
    # given
    plugins_manager = get_plugins_manager(False)
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        additional_order_webhook,
    ) = setup_order_webhooks(
        [
            WebhookEventAsyncType.ORDER_UPDATED,
            WebhookEventAsyncType.ORDER_FULLY_PAID,
        ]
    )
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.charge_status = OrderChargeStatus.FULL
    order.save(update_fields=["status", "should_refresh_prices", "charge_status"])

    order.channel.automatically_confirm_all_new_orders = False
    order.channel.save(update_fields=["automatically_confirm_all_new_orders"])

    order_info = OrderInfo(
        order=order,
        customer_email=order.get_customer_email(),
        channel=order.channel,
        payment=order.get_last_payment(),
        lines_data=[],
    )

    webhook_event_map = get_webhooks_for_multiple_events(WEBHOOK_EVENTS_FOR_FULLY_PAID)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        handle_fully_paid_order(plugins_manager, order_info, webhook_event_map)

    # then
    # confirm that event delivery was generated for each async webhook.
    order_fully_paid_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_FULLY_PAID,
    )
    order_updated_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_UPDATED,
    )

    order_deliveries = [order_updated_delivery, order_fully_paid_delivery]

    mocked_send_webhook_request_async.assert_has_calls(
        [
            call(
                kwargs={"event_delivery_id": delivery.id},
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
                bind=True,
                retry_backoff=10,
                retry_kwargs={"max_retries": 5},
            )
            for delivery in order_deliveries
        ],
        any_order=True,
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 2
    assert not EventDelivery.objects.exclude(
        webhook_id=additional_order_webhook.id
    ).exists()

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
    assert filter_shipping_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    wrapped_call_order_events.assert_called_once_with(
        plugins_manager,
        [WebhookEventAsyncType.ORDER_FULLY_PAID, WebhookEventAsyncType.ORDER_UPDATED],
        order,
        webhook_event_map=webhook_event_map,
    )


def test_mark_as_paid_with_payment(admin_user, draft_order):
    manager = get_plugins_manager(allow_replica=False)
    mark_order_as_paid_with_payment(draft_order, admin_user, None, manager)
    payment = draft_order.payments.last()
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.captured_amount == draft_order.total.gross.amount
    assert draft_order.events.last().type == (OrderEvents.ORDER_MARKED_AS_PAID)
    transactions = payment.transactions.all()
    assert transactions.count() == 1
    assert transactions[0].kind == TransactionKind.EXTERNAL


def test_mark_as_paid_with_external_reference_with_payment(admin_user, draft_order):
    external_reference = "transaction_id"
    manager = get_plugins_manager(allow_replica=False)
    mark_order_as_paid_with_payment(
        draft_order, admin_user, None, manager, external_reference=external_reference
    )
    payment = draft_order.payments.last()
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.captured_amount == draft_order.total.gross.amount
    assert payment.psp_reference == external_reference
    assert draft_order.events.last().type == (OrderEvents.ORDER_MARKED_AS_PAID)
    transactions = payment.transactions.all()
    assert transactions.count() == 1
    assert transactions[0].kind == TransactionKind.EXTERNAL
    assert transactions[0].token == external_reference


def test_mark_as_paid_no_billing_address(admin_user, draft_order):
    draft_order.billing_address = None
    draft_order.save()

    manager = get_plugins_manager(allow_replica=False)
    with pytest.raises(PaymentError, match="Order does not have a billing address."):
        mark_order_as_paid_with_payment(draft_order, admin_user, None, manager)


def test_clean_mark_order_as_paid(payment_txn_preauth):
    order = payment_txn_preauth.order
    with pytest.raises(
        PaymentError, match="Orders with payments can not be manually marked as paid."
    ):
        clean_mark_order_as_paid(order)


def test_mark_as_paid_with_transaction(admin_user, draft_order):
    # given
    manager = get_plugins_manager(allow_replica=False)
    channel = draft_order.channel
    channel.order_mark_as_paid_strategy = MarkAsPaidStrategy.TRANSACTION_FLOW
    channel.save(update_fields=["order_mark_as_paid_strategy"])

    # when
    mark_order_as_paid_with_transaction(draft_order, admin_user, None, manager)

    # then
    draft_order.refresh_from_db()
    assert not draft_order.payments.exists()
    transaction = draft_order.payment_transactions.get()

    assert transaction.charged_value == draft_order.total.gross.amount
    assert draft_order.authorize_status == OrderAuthorizeStatus.FULL
    assert draft_order.charge_status == OrderChargeStatus.FULL
    assert draft_order.total_charged.amount == transaction.charged_value

    transaction_event = transaction.events.filter(
        type=TransactionEventType.CHARGE_SUCCESS
    ).get()
    assert transaction_event.amount_value == draft_order.total.gross.amount
    assert transaction_event.type == TransactionEventType.CHARGE_SUCCESS


def test_mark_as_paid_with_external_reference_with_transaction(admin_user, draft_order):
    # given
    external_reference = "transaction_id"
    manager = get_plugins_manager(allow_replica=False)
    channel = draft_order.channel
    channel.order_mark_as_paid_strategy = MarkAsPaidStrategy.TRANSACTION_FLOW
    channel.save(update_fields=["order_mark_as_paid_strategy"])

    # when
    mark_order_as_paid_with_transaction(
        draft_order, admin_user, None, manager, external_reference=external_reference
    )

    # then
    assert not draft_order.payments.exists()
    transaction = draft_order.payment_transactions.get()
    assert transaction.psp_reference == external_reference


def test_cancel_fulfillment(fulfilled_order, warehouse):
    fulfillment = fulfilled_order.fulfillments.first()
    line_1, line_2 = fulfillment.lines.all()

    cancel_fulfillment(
        fulfillment, None, None, warehouse, get_plugins_manager(allow_replica=False)
    )

    fulfillment.refresh_from_db()
    fulfilled_order.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.CANCELED
    assert fulfilled_order.status == OrderStatus.UNFULFILLED
    assert line_1.order_line.quantity_fulfilled == 0
    assert line_2.order_line.quantity_fulfilled == 0


def test_cancel_fulfillment_variant_witout_inventory_tracking(
    fulfilled_order_without_inventory_tracking, warehouse
):
    fulfillment = fulfilled_order_without_inventory_tracking.fulfillments.first()
    line = fulfillment.lines.first()
    stock = line.order_line.variant.stocks.get()
    stock_quantity_before = stock.quantity

    cancel_fulfillment(
        fulfillment, None, None, warehouse, get_plugins_manager(allow_replica=False)
    )

    fulfillment.refresh_from_db()
    line.refresh_from_db()
    fulfilled_order_without_inventory_tracking.refresh_from_db()
    assert fulfillment.status == FulfillmentStatus.CANCELED
    assert line.order_line.quantity_fulfilled == 0
    assert fulfilled_order_without_inventory_tracking.status == OrderStatus.UNFULFILLED
    assert stock_quantity_before == line.order_line.variant.stocks.get().quantity


@patch("saleor.order.actions.send_order_canceled_confirmation")
def test_cancel_order(
    send_order_canceled_confirmation_mock,
    fulfilled_order_with_all_cancelled_fulfillments,
    django_capture_on_commit_callbacks,
):
    # given
    order = fulfilled_order_with_all_cancelled_fulfillments
    manager = get_plugins_manager(allow_replica=False)

    assert Allocation.objects.filter(
        order_line__order=order, quantity_allocated__gt=0
    ).exists()

    # when
    with django_capture_on_commit_callbacks(execute=True):
        cancel_order(order, None, None, manager)

    # then
    order_event = order.events.last()
    assert order_event.type == OrderEvents.CANCELED

    assert order.status == OrderStatus.CANCELED
    assert not Allocation.objects.filter(
        order_line__order=order, quantity_allocated__gt=0
    ).exists()

    send_order_canceled_confirmation_mock.assert_called_once_with(
        order, None, None, manager
    )


@patch(
    "saleor.order.actions.call_order_events",
    wraps=call_order_events,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_cancel_order_dont_trigger_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_order_events,
    setup_order_webhooks,
    order_with_lines,
    settings,
    django_capture_on_commit_callbacks,
):
    # given
    plugins_manager = get_plugins_manager(False)
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        additional_order_webhook,
    ) = setup_order_webhooks(
        [
            WebhookEventAsyncType.ORDER_UPDATED,
            WebhookEventAsyncType.ORDER_CANCELLED,
        ]
    )

    webhook_event_map = get_webhooks_for_multiple_events(
        WEBHOOK_EVENTS_FOR_ORDER_CANCELED
    )

    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.charge_status = OrderChargeStatus.FULL
    order.save(update_fields=["status", "should_refresh_prices", "charge_status"])

    # when
    with django_capture_on_commit_callbacks(execute=True):
        cancel_order(order, None, None, plugins_manager)

    # then
    # confirm that event delivery was generated for each async webhook.
    order_updated_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_UPDATED,
    )
    order_cancelled_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_CANCELLED,
    )
    tax_delivery = EventDelivery.objects.filter(webhook_id=tax_webhook.id).first()
    filter_shipping_delivery = EventDelivery.objects.filter(
        webhook_id=shipping_filter_webhook.id,
        event_type=WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
    ).first()
    assert not tax_delivery
    assert not filter_shipping_delivery

    order_deliveries = [
        order_cancelled_delivery,
        order_updated_delivery,
    ]

    mocked_send_webhook_request_async.assert_has_calls(
        [
            call(
                kwargs={"event_delivery_id": delivery.id},
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
                bind=True,
                retry_backoff=10,
                retry_kwargs={"max_retries": 5},
            )
            for delivery in order_deliveries
        ],
        any_order=True,
    )
    assert not mocked_send_webhook_request_sync.called

    wrapped_call_order_events.assert_called_once_with(
        plugins_manager,
        [
            WebhookEventAsyncType.ORDER_CANCELLED,
            WebhookEventAsyncType.ORDER_UPDATED,
        ],
        order,
        webhook_event_map=webhook_event_map,
    )


@patch("saleor.plugins.manager.PluginsManager.order_refunded")
@patch("saleor.plugins.manager.PluginsManager.order_fully_refunded")
@patch("saleor.order.actions.send_order_refunded_confirmation")
def test_order_refunded_by_user(
    send_order_refunded_confirmation_mock,
    order_fully_refunded_mock,
    order_refunded_mock,
    order,
    checkout_with_item,
    django_capture_on_commit_callbacks,
):
    # given
    payment = Payment.objects.create(
        gateway="mirumee.payments.dummy", is_active=True, checkout=checkout_with_item
    )
    amount = order.total.gross.amount
    app = None

    # when
    manager = get_plugins_manager(allow_replica=False)
    with django_capture_on_commit_callbacks(execute=True):
        order_refunded(order, order.user, app, amount, payment, manager)

    # then
    order_event = order.events.last()
    assert order_event.type == OrderEvents.PAYMENT_REFUNDED

    send_order_refunded_confirmation_mock.assert_called_once_with(
        order, order.user, None, amount, order.currency, manager
    )
    order_fully_refunded_mock.assert_called_once_with(order, webhooks=set())
    order_refunded_mock.assert_called_once_with(order, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_refunded")
@patch("saleor.plugins.manager.PluginsManager.order_fully_refunded")
@patch("saleor.order.actions.send_order_refunded_confirmation")
def test_order_refunded_by_app(
    send_order_refunded_confirmation_mock,
    order_fully_refunded_mock,
    order_refunded_mock,
    order,
    checkout_with_item,
    app,
    django_capture_on_commit_callbacks,
):
    # given
    payment = Payment.objects.create(
        gateway="mirumee.payments.dummy", is_active=True, checkout=checkout_with_item
    )
    amount = order.total.gross.amount

    # when
    manager = get_plugins_manager(allow_replica=False)
    with django_capture_on_commit_callbacks(execute=True):
        order_refunded(order, None, app, amount, payment, manager)

    # then
    order_event = order.events.last()
    assert order_event.type == OrderEvents.PAYMENT_REFUNDED

    send_order_refunded_confirmation_mock.assert_called_once_with(
        order, None, app, amount, order.currency, manager
    )
    order_fully_refunded_mock.assert_called_once_with(order, webhooks=set())
    order_refunded_mock.assert_called_once_with(order, webhooks=set())


@patch(
    "saleor.order.actions.call_order_events",
    wraps=call_order_events,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_order_refunded_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_order_events,
    setup_order_webhooks,
    order_with_lines,
    settings,
    django_capture_on_commit_callbacks,
    app,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        additional_order_webhook,
    ) = setup_order_webhooks(
        [
            WebhookEventAsyncType.ORDER_REFUNDED,
            WebhookEventAsyncType.ORDER_UPDATED,
            WebhookEventAsyncType.ORDER_FULLY_REFUNDED,
        ]
    )

    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save(update_fields=["status", "should_refresh_prices"])

    payment = Payment.objects.create(
        gateway="mirumee.payments.dummy",
        is_active=True,
        order=order,
        charge_status=ChargeStatus.FULLY_REFUNDED,
    )
    payment.transactions.create(
        kind=TransactionKind.REFUND,
        is_success=True,
        amount=order.total.gross.amount,
        gateway_response={},
    )
    amount = order.total.gross.amount
    plugins_manager = get_plugins_manager(allow_replica=False)

    webhook_event_map = get_webhooks_for_multiple_events(
        WEBHOOK_EVENTS_FOR_ORDER_REFUNDED
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        order_refunded(order, None, app, amount, payment, plugins_manager)

    # then
    # confirm that event delivery was generated for each async webhook.
    order_updated_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_UPDATED,
    )
    order_refunded_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_REFUNDED,
    )
    order_fully_refunded_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_FULLY_REFUNDED,
    )

    order_deliveries = [
        order_updated_delivery,
        order_fully_refunded_delivery,
        order_refunded_delivery,
    ]

    mocked_send_webhook_request_async.assert_has_calls(
        [
            call(
                kwargs={"event_delivery_id": delivery.id},
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
                bind=True,
                retry_backoff=10,
                retry_kwargs={"max_retries": 5},
            )
            for delivery in order_deliveries
        ],
        any_order=True,
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 2
    assert not EventDelivery.objects.exclude(
        webhook_id=additional_order_webhook.id
    ).exists()

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
    assert filter_shipping_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    wrapped_call_order_events.assert_called_once_with(
        plugins_manager,
        [
            WebhookEventAsyncType.ORDER_REFUNDED,
            WebhookEventAsyncType.ORDER_UPDATED,
            WebhookEventAsyncType.ORDER_FULLY_REFUNDED,
        ],
        order,
        webhook_event_map=webhook_event_map,
    )


@patch(
    "saleor.order.actions.call_order_event",
    wraps=call_order_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_order_voided_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_order_event,
    setup_order_webhooks,
    order_with_lines,
    settings,
    django_capture_on_commit_callbacks,
    app,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        additional_order_webhook,
    ) = setup_order_webhooks(
        WebhookEventAsyncType.ORDER_UPDATED,
    )

    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save(update_fields=["status", "should_refresh_prices"])

    payment = Payment.objects.create(
        gateway="mirumee.payments.dummy",
        is_active=True,
        order=order,
        charge_status=ChargeStatus.FULLY_REFUNDED,
    )

    plugins_manager = get_plugins_manager(allow_replica=False)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        order_voided(order, None, app, payment, plugins_manager)

    # then
    # confirm that event delivery was generated for each async webhook.
    order_updated_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_UPDATED,
    )
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": order_updated_delivery.id},
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 2
    assert not EventDelivery.objects.exclude(
        webhook_id=additional_order_webhook.id
    ).exists()

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
    assert filter_shipping_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    wrapped_call_order_event.assert_called_once_with(
        plugins_manager,
        WebhookEventAsyncType.ORDER_UPDATED,
        order,
    )


@patch(
    "saleor.order.actions.call_order_events",
    wraps=call_order_events,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_order_fulfilled_dont_trigger_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_order_events,
    setup_order_webhooks,
    fulfilled_order,
    settings,
    site_settings,
    django_capture_on_commit_callbacks,
    app,
):
    # given
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment_lines = list(fulfillment.lines.all())
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        additional_order_webhook,
    ) = setup_order_webhooks(
        [WebhookEventAsyncType.ORDER_UPDATED, WebhookEventAsyncType.ORDER_FULFILLED]
    )
    plugins_manager = get_plugins_manager(allow_replica=False)

    webhook_event_map = get_webhooks_for_multiple_events(
        WEBHOOK_EVENTS_FOR_ORDER_FULFILLED
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        order_fulfilled(
            [fulfillment],
            None,
            app,
            fulfillment_lines,
            plugins_manager,
            [],
            site_settings,
        )

    # then
    # confirm that event delivery was generated for each async webhook.
    order_updated_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_UPDATED,
    )
    order_fulfilled_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_FULFILLED,
    )
    tax_delivery = EventDelivery.objects.filter(webhook_id=tax_webhook.id).first()
    filter_shipping_delivery = EventDelivery.objects.filter(
        webhook_id=shipping_filter_webhook.id,
        event_type=WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
    ).first()
    assert not tax_delivery
    assert not filter_shipping_delivery

    order_deliveries = [
        order_updated_delivery,
        order_fulfilled_delivery,
    ]

    mocked_send_webhook_request_async.assert_has_calls(
        [
            call(
                kwargs={"event_delivery_id": delivery.id},
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
                bind=True,
                retry_backoff=10,
                retry_kwargs={"max_retries": 5},
            )
            for delivery in order_deliveries
        ],
        any_order=True,
    )
    assert not mocked_send_webhook_request_sync.called

    wrapped_call_order_events.assert_called_once_with(
        plugins_manager,
        [
            WebhookEventAsyncType.ORDER_UPDATED,
            WebhookEventAsyncType.ORDER_FULFILLED,
        ],
        fulfilled_order,
        webhook_event_map=webhook_event_map,
    )


@patch(
    "saleor.order.actions.call_order_event",
    wraps=call_order_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_order_awaits_fulfillment_approval_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_order_event,
    setup_order_webhooks,
    fulfilled_order,
    settings,
    site_settings,
    django_capture_on_commit_callbacks,
    app,
):
    # given
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.status = FulfillmentStatus.WAITING_FOR_APPROVAL
    fulfillment.save()
    fulfillment_lines = list(fulfillment.lines.all())

    order = fulfilled_order
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save(update_fields=["status", "should_refresh_prices"])

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        additional_order_webhook,
    ) = setup_order_webhooks(
        [
            WebhookEventAsyncType.ORDER_UPDATED,
        ]
    )
    plugins_manager = get_plugins_manager(allow_replica=False)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        order_awaits_fulfillment_approval(
            [fulfillment],
            None,
            app,
            fulfillment_lines,
            plugins_manager,
        )

    # then
    # confirm that event delivery was generated for each async webhook.
    order_updated_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_UPDATED,
    )

    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": order_updated_delivery.id},
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 2
    assert not EventDelivery.objects.exclude(
        webhook_id=additional_order_webhook.id
    ).exists()

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
    assert filter_shipping_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    wrapped_call_order_event.assert_called_once_with(
        plugins_manager,
        WebhookEventAsyncType.ORDER_UPDATED,
        fulfilled_order,
    )


@patch(
    "saleor.order.actions.call_order_event",
    wraps=call_order_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_order_authorized_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_order_event,
    setup_order_webhooks,
    order_with_lines,
    settings,
    django_capture_on_commit_callbacks,
    app,
):
    # given

    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save(update_fields=["status", "should_refresh_prices"])

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        additional_order_webhook,
    ) = setup_order_webhooks(
        [
            WebhookEventAsyncType.ORDER_UPDATED,
        ]
    )
    payment = Payment.objects.create(
        gateway="mirumee.payments.dummy",
        is_active=True,
        order=order,
        charge_status=ChargeStatus.FULLY_REFUNDED,
    )

    plugins_manager = get_plugins_manager(allow_replica=False)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        order_authorized(
            order, None, app, order.total.gross.amount, payment, plugins_manager
        )

    # then
    # confirm that event delivery was generated for each async webhook.
    order_updated_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_UPDATED,
    )
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": order_updated_delivery.id},
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 2
    assert not EventDelivery.objects.exclude(
        webhook_id=additional_order_webhook.id
    ).exists()

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
    assert filter_shipping_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    wrapped_call_order_event.assert_called_once_with(
        plugins_manager,
        WebhookEventAsyncType.ORDER_UPDATED,
        order,
        webhook_event_map=None,
    )


@patch(
    "saleor.order.actions.call_order_event",
    wraps=call_order_event,
)
@patch(
    "saleor.order.actions.call_order_events",
    wraps=call_order_events,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_order_charged_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_order_events,
    wrapped_call_order_event,
    setup_order_webhooks,
    order_with_lines,
    settings,
    django_capture_on_commit_callbacks,
    app,
):
    # given

    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.charge_status = OrderChargeStatus.FULL
    order.save(update_fields=["status", "should_refresh_prices", "charge_status"])

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        additional_order_webhook,
    ) = setup_order_webhooks(
        [
            WebhookEventAsyncType.ORDER_PAID,
            WebhookEventAsyncType.ORDER_FULLY_PAID,
            WebhookEventAsyncType.ORDER_UPDATED,
        ]
    )

    webhook_event_map = get_webhooks_for_multiple_events(
        WEBHOOK_EVENTS_FOR_ORDER_CHARGED
    )

    plugins_manager = get_plugins_manager(allow_replica=False)
    order_info = fetch_order_info(order)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        order_charged(
            order_info, None, app, order.total.gross.amount, None, plugins_manager
        )

    # then
    # confirm that event delivery was generated for each async webhook.
    order_updated_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_UPDATED,
    )
    order_fully_paid_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_FULLY_PAID,
    )
    order_paid_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_PAID,
    )

    order_deliveries = [
        order_updated_delivery,
        order_fully_paid_delivery,
        order_paid_delivery,
    ]

    mocked_send_webhook_request_async.assert_has_calls(
        [
            call(
                kwargs={"event_delivery_id": delivery.id},
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
                bind=True,
                retry_backoff=10,
                retry_kwargs={"max_retries": 5},
            )
            for delivery in order_deliveries
        ],
        any_order=True,
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 2
    assert not EventDelivery.objects.exclude(
        webhook_id=additional_order_webhook.id
    ).exists()

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
    assert filter_shipping_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    wrapped_call_order_events.assert_called_once_with(
        plugins_manager,
        [WebhookEventAsyncType.ORDER_FULLY_PAID, WebhookEventAsyncType.ORDER_UPDATED],
        order,
        webhook_event_map=webhook_event_map,
    )
    wrapped_call_order_event.assert_called_once_with(
        plugins_manager,
        WebhookEventAsyncType.ORDER_PAID,
        order,
        webhook_event_map=webhook_event_map,
    )


def test_fulfill_order_lines(order_with_lines):
    order = order_with_lines
    line = order.lines.first()
    quantity_fulfilled_before = line.quantity_fulfilled
    variant = line.variant
    stock = Stock.objects.get(product_variant=variant)
    stock_quantity_after = stock.quantity - line.quantity

    fulfill_order_lines(
        [
            OrderLineInfo(
                line=line,
                quantity=line.quantity,
                variant=variant,
                warehouse_pk=stock.warehouse.pk,
            )
        ],
        get_plugins_manager(allow_replica=False),
    )

    stock.refresh_from_db()
    assert stock.quantity == stock_quantity_after
    assert line.quantity_fulfilled == quantity_fulfilled_before + line.quantity


def test_fulfill_order_lines_multiple_lines(order_with_lines):
    order = order_with_lines
    lines = order.lines.all()

    assert lines.count() > 1

    quantity_fulfilled_before_1 = lines[0].quantity_fulfilled
    variant_1 = lines[0].variant
    stock_1 = Stock.objects.get(product_variant=variant_1)
    stock_quantity_after_1 = stock_1.quantity - lines[0].quantity

    quantity_fulfilled_before_2 = lines[1].quantity_fulfilled
    variant_2 = lines[1].variant
    stock_2 = Stock.objects.get(product_variant=variant_2)
    stock_quantity_after_2 = stock_2.quantity - lines[1].quantity

    fulfill_order_lines(
        [
            OrderLineInfo(
                line=lines[0],
                quantity=lines[0].quantity,
                variant=variant_1,
                warehouse_pk=stock_1.warehouse.pk,
            ),
            OrderLineInfo(
                line=lines[1],
                quantity=lines[1].quantity,
                variant=variant_2,
                warehouse_pk=stock_2.warehouse.pk,
            ),
        ],
        get_plugins_manager(allow_replica=False),
    )

    stock_1.refresh_from_db()
    assert stock_1.quantity == stock_quantity_after_1
    assert (
        lines[0].quantity_fulfilled == quantity_fulfilled_before_1 + lines[0].quantity
    )

    stock_2.refresh_from_db()
    assert stock_2.quantity == stock_quantity_after_2
    assert (
        lines[1].quantity_fulfilled == quantity_fulfilled_before_2 + lines[1].quantity
    )


def test_fulfill_order_lines_with_variant_deleted(order_with_lines):
    line = order_with_lines.lines.first()
    line.variant.delete()

    line.refresh_from_db()

    fulfill_order_lines(
        [OrderLineInfo(line=line, quantity=line.quantity)],
        get_plugins_manager(allow_replica=False),
    )


def test_fulfill_order_lines_without_inventory_tracking(order_with_lines):
    order = order_with_lines
    line = order.lines.first()
    quantity_fulfilled_before = line.quantity_fulfilled
    variant = line.variant
    variant.track_inventory = False
    variant.save()
    stock = Stock.objects.get(product_variant=variant)

    # stock should not change
    stock_quantity_after = stock.quantity

    fulfill_order_lines(
        [
            OrderLineInfo(
                line=line,
                quantity=line.quantity,
                variant=variant,
                warehouse_pk=stock.warehouse.pk,
            )
        ],
        get_plugins_manager(allow_replica=False),
    )

    stock.refresh_from_db()
    assert stock.quantity == stock_quantity_after
    assert line.quantity_fulfilled == quantity_fulfilled_before + line.quantity


@patch("saleor.order.actions.send_fulfillment_confirmation_to_customer")
@patch("saleor.order.utils.get_default_digital_content_settings")
@patch("saleor.plugins.manager.PluginsManager.fulfillment_created")
def test_fulfill_digital_lines(
    mock_fulfillment_created,
    mock_digital_settings,
    mock_email_fulfillment,
    order_with_lines,
    media_root,
):
    mock_digital_settings.return_value = {"automatic_fulfillment": True}
    line = order_with_lines.lines.all()[0]

    image_file, image_name = create_image()
    variant = line.variant

    product_type = variant.product.product_type
    product_type.is_digital = True
    product_type.is_shipping_required = False
    product_type.save(update_fields=["is_digital", "is_shipping_required"])

    digital_content = DigitalContent.objects.create(
        content_file=image_file, product_variant=variant, use_default_settings=True
    )

    line.variant.digital_content = digital_content
    line.is_shipping_required = False
    line.save()

    order_with_lines.refresh_from_db()
    order_info = fetch_order_info(order_with_lines)
    manager = get_plugins_manager(allow_replica=False)

    automatically_fulfill_digital_lines(order_info, manager)

    line.refresh_from_db()
    fulfillment = Fulfillment.objects.get(order=order_with_lines)
    fulfillment_lines = fulfillment.lines.all()

    assert fulfillment_lines.count() == 1
    assert line.digital_content_url
    assert mock_email_fulfillment.called
    mock_fulfillment_created.assert_called_once_with(fulfillment)


@patch("saleor.order.actions.send_fulfillment_confirmation_to_customer")
@patch("saleor.order.utils.get_default_digital_content_settings")
@patch("saleor.plugins.manager.PluginsManager.fulfillment_created")
def test_fulfill_digital_lines_no_allocation(
    mock_fulfillment_created,
    mock_digital_settings,
    mock_email_fulfillment,
    order_with_lines,
    media_root,
):
    # given
    mock_digital_settings.return_value = {"automatic_fulfillment": True}
    line = order_with_lines.lines.all()[0]

    image_file, image_name = create_image()
    variant = line.variant

    product_type = variant.product.product_type
    product_type.is_digital = True
    product_type.is_shipping_required = False
    product_type.save(update_fields=["is_digital", "is_shipping_required"])

    digital_content = DigitalContent.objects.create(
        content_file=image_file, product_variant=variant, use_default_settings=True
    )

    variant.digital_content = digital_content
    variant.track_inventory = False
    variant.save()

    line.is_shipping_required = False
    line.allocations.all().delete()
    line.save()

    order_with_lines.refresh_from_db()
    order_info = fetch_order_info(order_with_lines)
    manager = get_plugins_manager(allow_replica=False)

    # when
    automatically_fulfill_digital_lines(order_info, manager)

    # then
    line.refresh_from_db()
    fulfillment = Fulfillment.objects.get(order=order_with_lines)
    fulfillment_lines = fulfillment.lines.all()

    assert fulfillment_lines.count() == 1
    assert line.digital_content_url
    assert mock_email_fulfillment.called
    mock_fulfillment_created.assert_called_once_with(fulfillment)


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_paid")
def test_order_transaction_updated_order_fully_paid(
    order_fully_paid,
    order_updated,
    order_with_lines,
    transaction_item_generator,
    django_capture_on_commit_callbacks,
):
    # given
    order_info = fetch_order_info(order_with_lines)
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.pk, charged_value=order_with_lines.total.gross.amount
    )
    manager = get_plugins_manager(allow_replica=False)
    updates_amounts_for_order(
        order_with_lines,
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        order_transaction_updated(
            order_info=order_info,
            transaction_item=transaction_item,
            manager=manager,
            user=None,
            app=None,
            previous_authorized_value=Decimal(0),
            previous_charged_value=Decimal(0),
            previous_refunded_value=Decimal(0),
        )

    # then
    order_fully_paid.assert_called_once_with(order_with_lines, webhooks=set())
    order_updated.assert_called_once_with(order_with_lines, webhooks=set())


@patch(
    "saleor.order.actions.call_order_event",
    wraps=call_order_event,
)
@patch(
    "saleor.order.actions.call_order_events",
    wraps=call_order_events,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_order_transaction_updated_for_charged_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_order_events,
    wrapped_call_order_event,
    setup_order_webhooks,
    order_with_lines,
    transaction_item_generator,
    django_capture_on_commit_callbacks,
    app,
    settings,
):
    # given
    plugins_manager = get_plugins_manager(allow_replica=False)
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        additional_order_webhook,
    ) = setup_order_webhooks(
        [
            WebhookEventAsyncType.ORDER_PAID,
            WebhookEventAsyncType.ORDER_FULLY_PAID,
            WebhookEventAsyncType.ORDER_UPDATED,
        ]
    )
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save(update_fields=["status", "should_refresh_prices"])

    webhook_event_map = get_webhooks_for_multiple_events(
        WEBHOOK_EVENTS_FOR_ORDER_CHARGED
    )

    order_info = fetch_order_info(order_with_lines)
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.pk,
        charged_value=order_with_lines.total.gross.amount,
    )

    updates_amounts_for_order(
        order_with_lines,
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        order_transaction_updated(
            order_info=order_info,
            transaction_item=transaction_item,
            manager=plugins_manager,
            user=None,
            app=None,
            previous_authorized_value=Decimal(0),
            previous_charged_value=Decimal(0),
            previous_refunded_value=Decimal(0),
        )

    # then
    # confirm that event delivery was generated for each async webhook.
    order_updated_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_UPDATED,
    )
    order_fully_paid_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_FULLY_PAID,
    )
    order_paid_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_PAID,
    )

    order_deliveries = [
        order_updated_delivery,
        order_fully_paid_delivery,
        order_paid_delivery,
    ]

    mocked_send_webhook_request_async.assert_has_calls(
        [
            call(
                kwargs={"event_delivery_id": delivery.id},
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
                bind=True,
                retry_backoff=10,
                retry_kwargs={"max_retries": 5},
            )
            for delivery in order_deliveries
        ],
        any_order=True,
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 2
    assert not EventDelivery.objects.exclude(
        webhook_id=additional_order_webhook.id
    ).exists()

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
    assert filter_shipping_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    wrapped_call_order_events.assert_called_once_with(
        plugins_manager,
        [WebhookEventAsyncType.ORDER_FULLY_PAID, WebhookEventAsyncType.ORDER_UPDATED],
        order,
        webhook_event_map=webhook_event_map,
    )
    wrapped_call_order_event.assert_called_once_with(
        plugins_manager,
        WebhookEventAsyncType.ORDER_PAID,
        order,
        webhook_event_map=webhook_event_map,
    )


@patch(
    "saleor.order.actions.call_order_event",
    wraps=call_order_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_order_transaction_updated_for_authorized_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_order_event,
    setup_order_webhooks,
    order_with_lines,
    transaction_item_generator,
    django_capture_on_commit_callbacks,
    app,
    settings,
):
    # given
    plugins_manager = get_plugins_manager(allow_replica=False)
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        additional_order_webhook,
    ) = setup_order_webhooks(
        WebhookEventAsyncType.ORDER_UPDATED,
    )
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save(update_fields=["status", "should_refresh_prices"])

    webhook_event_map = get_webhooks_for_multiple_events(
        [WebhookEventAsyncType.ORDER_UPDATED, *WebhookEventSyncType.ORDER_EVENTS]
    )

    order_info = fetch_order_info(order_with_lines)
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.pk,
        authorized_value=order_with_lines.total.gross.amount,
    )

    updates_amounts_for_order(
        order_with_lines,
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        order_transaction_updated(
            order_info=order_info,
            transaction_item=transaction_item,
            manager=plugins_manager,
            user=None,
            app=None,
            previous_authorized_value=Decimal(0),
            previous_charged_value=Decimal(0),
            previous_refunded_value=Decimal(0),
        )

    # then
    # confirm that event delivery was generated for each async webhook.
    order_updated_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_UPDATED,
    )
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": order_updated_delivery.id},
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 2
    assert not EventDelivery.objects.exclude(
        webhook_id=additional_order_webhook.id
    ).exists()

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
    assert filter_shipping_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    wrapped_call_order_event.assert_called_once_with(
        plugins_manager,
        WebhookEventAsyncType.ORDER_UPDATED,
        order,
        webhook_event_map=webhook_event_map,
    )


@patch(
    "saleor.order.actions.call_order_events",
    wraps=call_order_events,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_order_transaction_updated_for_refunded_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_order_events,
    setup_order_webhooks,
    order_with_lines,
    transaction_item_generator,
    django_capture_on_commit_callbacks,
    app,
    settings,
):
    # given
    plugins_manager = get_plugins_manager(allow_replica=False)
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        additional_order_webhook,
    ) = setup_order_webhooks(
        [
            WebhookEventAsyncType.ORDER_REFUNDED,
            WebhookEventAsyncType.ORDER_FULLY_REFUNDED,
            WebhookEventAsyncType.ORDER_UPDATED,
        ]
    )
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save(update_fields=["status", "should_refresh_prices"])

    webhook_event_map = get_webhooks_for_multiple_events(
        WEBHOOK_EVENTS_FOR_ORDER_REFUNDED
    )

    order_info = fetch_order_info(order_with_lines)
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.pk,
        refunded_value=order_with_lines.total.gross.amount,
    )

    updates_amounts_for_order(
        order_with_lines,
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        order_transaction_updated(
            order_info=order_info,
            transaction_item=transaction_item,
            manager=plugins_manager,
            user=None,
            app=None,
            previous_authorized_value=Decimal(0),
            previous_charged_value=Decimal(0),
            previous_refunded_value=Decimal(0),
        )

    # then
    # confirm that event delivery was generated for each async webhook.
    order_updated_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_UPDATED,
    )
    order_refunded_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_REFUNDED,
    )
    order_fully_refunded_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_FULLY_REFUNDED,
    )

    order_deliveries = [
        order_updated_delivery,
        order_fully_refunded_delivery,
        order_refunded_delivery,
    ]

    mocked_send_webhook_request_async.assert_has_calls(
        [
            call(
                kwargs={"event_delivery_id": delivery.id},
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
                bind=True,
                retry_backoff=10,
                retry_kwargs={"max_retries": 5},
            )
            for delivery in order_deliveries
        ],
        any_order=True,
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 2

    assert not EventDelivery.objects.exclude(
        webhook_id=additional_order_webhook.id
    ).exists()

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
    assert filter_shipping_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    wrapped_call_order_events.assert_called_once_with(
        plugins_manager,
        [
            WebhookEventAsyncType.ORDER_REFUNDED,
            WebhookEventAsyncType.ORDER_UPDATED,
            WebhookEventAsyncType.ORDER_FULLY_REFUNDED,
        ],
        order,
        webhook_event_map=webhook_event_map,
    )


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_paid")
def test_order_transaction_updated_order_partially_paid(
    order_fully_paid,
    order_updated,
    order_with_lines,
    transaction_item_generator,
    django_capture_on_commit_callbacks,
):
    # given
    order_info = fetch_order_info(order_with_lines)
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.pk, charged_value=Decimal("10")
    )
    manager = get_plugins_manager(allow_replica=False)
    updates_amounts_for_order(
        order_with_lines,
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        order_transaction_updated(
            order_info=order_info,
            transaction_item=transaction_item,
            manager=manager,
            user=None,
            app=None,
            previous_authorized_value=Decimal(0),
            previous_charged_value=Decimal(0),
            previous_refunded_value=Decimal(0),
        )

    # then
    assert not order_fully_paid.called
    order_updated.assert_called_once_with(order_with_lines, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_paid")
def test_order_transaction_updated_order_partially_paid_and_multiple_transactions(
    order_fully_paid,
    order_updated,
    order_with_lines,
    transaction_item_generator,
    django_capture_on_commit_callbacks,
):
    # given
    order_info = fetch_order_info(order_with_lines)
    transaction_item_generator(
        order_id=order_with_lines.pk, charged_value=Decimal("10")
    )
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.pk, charged_value=Decimal("5")
    )
    manager = get_plugins_manager(allow_replica=False)
    updates_amounts_for_order(
        order_with_lines,
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        order_transaction_updated(
            order_info=order_info,
            transaction_item=transaction_item,
            manager=manager,
            user=None,
            app=None,
            previous_authorized_value=Decimal(0),
            previous_charged_value=Decimal(0),
            previous_refunded_value=Decimal(0),
        )

    # then
    assert not order_fully_paid.called
    order_updated.assert_called_once_with(order_with_lines, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_paid")
def test_order_transaction_updated_with_the_same_transaction_charged_amount(
    order_fully_paid,
    order_updated,
    order_with_lines,
    transaction_item_generator,
    django_capture_on_commit_callbacks,
):
    # given
    order_info = fetch_order_info(order_with_lines)
    charged_value = Decimal("5")

    transaction_item = transaction_item_generator(
        order_id=order_with_lines.pk, charged_value=charged_value
    )
    manager = get_plugins_manager(allow_replica=False)
    updates_amounts_for_order(
        order_with_lines,
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        order_transaction_updated(
            order_info=order_info,
            transaction_item=transaction_item,
            manager=manager,
            user=None,
            app=None,
            previous_authorized_value=Decimal(0),
            previous_charged_value=charged_value,
            previous_refunded_value=Decimal(0),
        )

    # then
    assert not order_fully_paid.called
    assert not order_updated.called


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_paid")
def test_order_transaction_updated_order_authorized(
    order_fully_paid,
    order_updated,
    order_with_lines,
    transaction_item_generator,
    django_capture_on_commit_callbacks,
):
    # given
    order_info = fetch_order_info(order_with_lines)
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.pk,
        authorized_value=order_with_lines.total.gross.amount,
    )
    manager = get_plugins_manager(allow_replica=False)
    updates_amounts_for_order(
        order_with_lines,
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        order_transaction_updated(
            order_info=order_info,
            transaction_item=transaction_item,
            manager=manager,
            user=None,
            app=None,
            previous_authorized_value=Decimal(0),
            previous_charged_value=Decimal(0),
            previous_refunded_value=Decimal(0),
        )

    # then
    assert not order_fully_paid.called
    order_updated.assert_called_once_with(order_with_lines, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_paid")
def test_order_transaction_updated_order_partially_authorized_and_multiple_transactions(
    order_fully_paid,
    order_updated,
    order_with_lines,
    transaction_item_generator,
    django_capture_on_commit_callbacks,
):
    # given
    order_info = fetch_order_info(order_with_lines)
    transaction_item_generator(
        order_id=order_with_lines.pk, authorized_value=Decimal("10")
    )
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.pk, authorized_value=Decimal("5")
    )
    manager = get_plugins_manager(allow_replica=False)
    updates_amounts_for_order(
        order_with_lines,
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        order_transaction_updated(
            order_info=order_info,
            transaction_item=transaction_item,
            manager=manager,
            user=None,
            app=None,
            previous_authorized_value=Decimal(0),
            previous_charged_value=Decimal(0),
            previous_refunded_value=Decimal(0),
        )

    # then
    assert not order_fully_paid.called
    order_updated.assert_called_once_with(order_with_lines, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_paid")
def test_order_transaction_updated_with_the_same_transaction_authorized_amount(
    order_fully_paid,
    order_updated,
    order_with_lines,
    transaction_item_generator,
    django_capture_on_commit_callbacks,
):
    # given
    order_info = fetch_order_info(order_with_lines)
    authorized_value = Decimal("5")

    transaction_item = transaction_item_generator(
        order_id=order_with_lines.pk, authorized_value=authorized_value
    )
    manager = get_plugins_manager(allow_replica=False)
    updates_amounts_for_order(
        order_with_lines,
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        order_transaction_updated(
            order_info=order_info,
            transaction_item=transaction_item,
            manager=manager,
            user=None,
            app=None,
            previous_authorized_value=authorized_value,
            previous_charged_value=Decimal(0),
            previous_refunded_value=Decimal(0),
        )

    # then
    assert not order_fully_paid.called
    assert not order_updated.called


@patch("saleor.plugins.manager.PluginsManager.order_refunded")
@patch("saleor.plugins.manager.PluginsManager.order_fully_refunded")
def test_order_transaction_updated_order_fully_refunded(
    order_fully_refunded,
    order_refunded,
    order_with_lines,
    transaction_item_generator,
    django_capture_on_commit_callbacks,
):
    # given
    order_info = fetch_order_info(order_with_lines)
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.pk, refunded_value=order_with_lines.total.gross.amount
    )
    manager = get_plugins_manager(allow_replica=False)
    updates_amounts_for_order(
        order_with_lines,
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        order_transaction_updated(
            order_info=order_info,
            transaction_item=transaction_item,
            manager=manager,
            user=None,
            app=None,
            previous_authorized_value=Decimal(0),
            previous_charged_value=Decimal(0),
            previous_refunded_value=Decimal(0),
        )

    # then
    order_fully_refunded.assert_called_once_with(order_with_lines, webhooks=set())
    order_refunded.assert_called_once_with(order_with_lines, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_refunded")
@patch("saleor.plugins.manager.PluginsManager.order_fully_refunded")
def test_order_transaction_updated_order_partially_refunded(
    order_fully_refunded,
    order_refunded,
    order_with_lines,
    transaction_item_generator,
    django_capture_on_commit_callbacks,
):
    # given
    order_info = fetch_order_info(order_with_lines)
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.pk, refunded_value=Decimal(10)
    )
    manager = get_plugins_manager(allow_replica=False)
    updates_amounts_for_order(
        order_with_lines,
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        order_transaction_updated(
            order_info=order_info,
            transaction_item=transaction_item,
            manager=manager,
            user=None,
            app=None,
            previous_authorized_value=Decimal(0),
            previous_charged_value=Decimal(0),
            previous_refunded_value=Decimal(0),
        )

    # then
    assert not order_fully_refunded.called
    order_refunded.assert_called_once_with(order_with_lines, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_refunded")
@patch("saleor.plugins.manager.PluginsManager.order_fully_refunded")
def test_order_transaction_updated_order_fully_refunded_and_multiple_transactions(
    order_fully_refunded,
    order_refunded,
    order_with_lines,
    transaction_item_generator,
    django_capture_on_commit_callbacks,
):
    # given
    order_info = fetch_order_info(order_with_lines)
    transaction_item_generator(
        order_id=order_with_lines.pk, refunded_value=Decimal("10")
    )
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.pk,
        refunded_value=order_with_lines.total.gross.amount - Decimal("10"),
    )
    manager = get_plugins_manager(allow_replica=False)
    updates_amounts_for_order(
        order_with_lines,
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        order_transaction_updated(
            order_info=order_info,
            transaction_item=transaction_item,
            manager=manager,
            user=None,
            app=None,
            previous_authorized_value=Decimal(0),
            previous_charged_value=Decimal(0),
            previous_refunded_value=Decimal(0),
        )

    # then
    order_fully_refunded.assert_called_once_with(order_with_lines, webhooks=set())
    order_refunded.assert_called_once_with(order_with_lines, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_refunded")
@patch("saleor.plugins.manager.PluginsManager.order_fully_refunded")
def test_order_transaction_updated_order_fully_refunded_with_transaction_and_payment(
    order_fully_refunded,
    order_refunded,
    order_with_lines,
    transaction_item_generator,
    payment_dummy,
    django_capture_on_commit_callbacks,
):
    # given
    payment = payment_dummy
    payment.order = order_with_lines
    payment.charge_status = ChargeStatus.PARTIALLY_REFUNDED
    payment.is_active = True
    payment.save()

    payment.transactions.create(
        amount=Decimal("10"),
        currency=payment.currency,
        kind=TransactionKind.REFUND,
        gateway_response={},
        is_success=True,
    )

    order_info = fetch_order_info(order_with_lines)
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.pk,
        refunded_value=order_with_lines.total.gross.amount - Decimal("10"),
    )

    manager = get_plugins_manager(allow_replica=False)
    updates_amounts_for_order(
        order_with_lines,
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        order_transaction_updated(
            order_info=order_info,
            transaction_item=transaction_item,
            manager=manager,
            user=None,
            app=None,
            previous_authorized_value=Decimal(0),
            previous_charged_value=Decimal(0),
            previous_refunded_value=Decimal(0),
        )

    # then
    order_refunded.assert_called_once_with(order_with_lines, webhooks=set())
    order_fully_refunded.assert_called_once_with(order_with_lines, webhooks=set())


@pytest.mark.parametrize(
    "webhook_event",
    [
        WebhookEventAsyncType.ORDER_CREATED,
        WebhookEventAsyncType.ORDER_CONFIRMED,
        WebhookEventAsyncType.ORDER_PAID,
        WebhookEventAsyncType.ORDER_FULLY_PAID,
        WebhookEventAsyncType.ORDER_REFUNDED,
        WebhookEventAsyncType.ORDER_FULLY_REFUNDED,
        WebhookEventAsyncType.ORDER_UPDATED,
        WebhookEventAsyncType.ORDER_CANCELLED,
        WebhookEventAsyncType.ORDER_EXPIRED,
        WebhookEventAsyncType.ORDER_FULFILLED,
        WebhookEventAsyncType.ORDER_METADATA_UPDATED,
    ],
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.order.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_order_event_triggers_sync_webhook(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    setup_order_webhooks,
    order_with_lines,
    settings,
    django_capture_on_commit_callbacks,
    webhook_event,
):
    # given
    plugins_manager = get_plugins_manager(False)
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save(update_fields=["status", "should_refresh_prices"])

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        order_webhook,
    ) = setup_order_webhooks(webhook_event)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        call_order_event(
            plugins_manager,
            webhook_event,
            order,
        )

    # then
    order_delivery = EventDelivery.objects.get(webhook_id=order_webhook.id)
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": order_delivery.id},
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

    mocked_call_event_including_protected_events.assert_called_once_with(
        ANY, order_with_lines, webhooks={order_webhook}
    )


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_order_event_incorrect_webhook_event(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    setup_order_webhooks,
    order_with_lines,
    django_capture_on_commit_callbacks,
):
    # given
    plugins_manager = get_plugins_manager(False)
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save(update_fields=["status", "should_refresh_prices"])

    mocked_send_webhook_request_sync.return_value = []
    setup_order_webhooks(WebhookEventAsyncType.ORDER_CREATED)

    incorrect_event = WebhookEventAsyncType.CHECKOUT_UPDATED

    # when
    with django_capture_on_commit_callbacks(execute=True):
        with pytest.raises(
            ValueError,
            match=f"Event {incorrect_event} not found in ORDER_WEBHOOK_EVENT_MAP.",
        ):
            call_order_event(
                plugins_manager,
                incorrect_event,
                order,
            )

    # then
    assert not mocked_send_webhook_request_async.called
    assert not mocked_send_webhook_request_sync.called


@pytest.mark.parametrize(
    "webhook_event",
    [
        WebhookEventAsyncType.ORDER_CREATED,
        WebhookEventAsyncType.ORDER_CONFIRMED,
        WebhookEventAsyncType.ORDER_PAID,
        WebhookEventAsyncType.ORDER_FULLY_PAID,
        WebhookEventAsyncType.ORDER_REFUNDED,
        WebhookEventAsyncType.ORDER_FULLY_REFUNDED,
        WebhookEventAsyncType.ORDER_UPDATED,
        WebhookEventAsyncType.ORDER_CANCELLED,
        WebhookEventAsyncType.ORDER_EXPIRED,
        WebhookEventAsyncType.ORDER_FULFILLED,
        WebhookEventAsyncType.ORDER_METADATA_UPDATED,
    ],
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.order.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_order_event_missing_filter_shipping_method_webhook(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    setup_order_webhooks,
    order_with_lines,
    settings,
    django_capture_on_commit_callbacks,
    webhook_event,
):
    # given
    plugins_manager = get_plugins_manager(False)
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save(update_fields=["status", "should_refresh_prices"])

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        order_webhook,
    ) = setup_order_webhooks(webhook_event)

    shipping_filter_webhook.is_active = False
    shipping_filter_webhook.save(update_fields=["is_active"])

    # when
    with django_capture_on_commit_callbacks(execute=True):
        call_order_event(
            plugins_manager,
            webhook_event,
            order,
        )

    # then
    order_delivery = EventDelivery.objects.get(webhook_id=order_webhook.id)
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": order_delivery.id},
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )

    mocked_send_webhook_request_sync.assert_called_once()
    assert not EventDelivery.objects.exclude(webhook_id=order_webhook.id).exists()

    tax_delivery = mocked_send_webhook_request_sync.mock_calls[0].args[0]
    assert tax_delivery.webhook_id == tax_webhook.id

    mocked_call_event_including_protected_events.assert_called_once_with(
        ANY, order_with_lines, webhooks={order_webhook}
    )


@pytest.mark.parametrize(
    "webhook_event",
    [
        WebhookEventAsyncType.ORDER_CREATED,
        WebhookEventAsyncType.ORDER_CONFIRMED,
        WebhookEventAsyncType.ORDER_PAID,
        WebhookEventAsyncType.ORDER_FULLY_PAID,
        WebhookEventAsyncType.ORDER_REFUNDED,
        WebhookEventAsyncType.ORDER_FULLY_REFUNDED,
        WebhookEventAsyncType.ORDER_UPDATED,
        WebhookEventAsyncType.ORDER_CANCELLED,
        WebhookEventAsyncType.ORDER_EXPIRED,
        WebhookEventAsyncType.ORDER_FULFILLED,
        WebhookEventAsyncType.ORDER_METADATA_UPDATED,
        WebhookEventAsyncType.DRAFT_ORDER_CREATED,
        WebhookEventAsyncType.DRAFT_ORDER_UPDATED,
    ],
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.order.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_order_event_skips_tax_webhook_when_prices_are_valid(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    setup_order_webhooks,
    order_with_lines,
    settings,
    django_capture_on_commit_callbacks,
    webhook_event,
):
    # given
    plugins_manager = get_plugins_manager(False)
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(
        update_fields=[
            "status",
        ]
    )

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        order_webhook,
    ) = setup_order_webhooks(webhook_event)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        call_order_event(
            plugins_manager,
            webhook_event,
            order,
        )

    # then
    order_delivery = EventDelivery.objects.get(webhook_id=order_webhook.id)
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": order_delivery.id},
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )

    # confirm each sync webhook was called without saving event delivery
    mocked_send_webhook_request_sync.assert_called_once()
    assert not EventDelivery.objects.exclude(webhook_id=order_webhook.id).exists()

    filter_shipping_call = mocked_send_webhook_request_sync.mock_calls[0]
    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    )
    assert filter_shipping_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    mocked_call_event_including_protected_events.assert_called_once_with(
        ANY, order_with_lines, webhooks={order_webhook}
    )


@pytest.mark.parametrize(
    "webhook_event",
    [
        WebhookEventAsyncType.ORDER_CREATED,
        WebhookEventAsyncType.ORDER_CONFIRMED,
        WebhookEventAsyncType.ORDER_PAID,
        WebhookEventAsyncType.ORDER_FULLY_PAID,
        WebhookEventAsyncType.ORDER_REFUNDED,
        WebhookEventAsyncType.ORDER_FULLY_REFUNDED,
        WebhookEventAsyncType.ORDER_UPDATED,
        WebhookEventAsyncType.ORDER_CANCELLED,
        WebhookEventAsyncType.ORDER_EXPIRED,
        WebhookEventAsyncType.ORDER_FULFILLED,
        WebhookEventAsyncType.ORDER_METADATA_UPDATED,
        WebhookEventAsyncType.DRAFT_ORDER_CREATED,
        WebhookEventAsyncType.DRAFT_ORDER_UPDATED,
    ],
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.order.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_order_event_skips_sync_webhooks_when_order_not_editable(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    setup_order_webhooks,
    order_with_lines,
    settings,
    django_capture_on_commit_callbacks,
    webhook_event,
):
    # given
    plugins_manager = get_plugins_manager(False)
    order = order_with_lines
    order.status = OrderStatus.UNFULFILLED
    order.save(
        update_fields=[
            "status",
        ]
    )

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        order_webhook,
    ) = setup_order_webhooks(webhook_event)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        call_order_event(
            plugins_manager,
            webhook_event,
            order,
        )

    # then
    order_delivery = EventDelivery.objects.get(webhook_id=order_webhook.id)
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": order_delivery.id},
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )
    assert not mocked_send_webhook_request_sync.called
    assert not EventDelivery.objects.exclude(webhook_id=order_webhook.id).exists()
    mocked_call_event_including_protected_events.assert_called_once_with(
        ANY, order_with_lines, webhooks={order_webhook}
    )


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.order.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_order_event_skips_sync_webhooks_when_draft_order_deleted(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    setup_order_webhooks,
    order_with_lines,
    settings,
    django_capture_on_commit_callbacks,
):
    # given
    plugins_manager = get_plugins_manager(False)
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        order_webhook,
    ) = setup_order_webhooks(WebhookEventAsyncType.DRAFT_ORDER_DELETED)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        call_order_event(
            plugins_manager,
            WebhookEventAsyncType.DRAFT_ORDER_DELETED,
            order,
        )

    # then
    order_delivery = EventDelivery.objects.get(webhook_id=order_webhook.id)
    tax_delivery = EventDelivery.objects.filter(webhook_id=tax_webhook.id).first()
    filter_shipping_delivery = EventDelivery.objects.filter(
        webhook_id=shipping_filter_webhook.id,
        event_type=WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
    ).first()
    assert not filter_shipping_delivery
    assert not tax_delivery
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": order_delivery.id},
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )
    assert not mocked_send_webhook_request_sync.called
    mocked_call_event_including_protected_events.assert_called_once_with(
        ANY, order_with_lines, webhooks={order_webhook}
    )


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_order_event_skips_when_async_webhooks_missing(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    setup_order_webhooks,
    order_with_lines,
    settings,
    django_capture_on_commit_callbacks,
):
    # given
    plugins_manager = get_plugins_manager(False)
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save(update_fields=["status", "should_refresh_prices"])

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        checkout_webhook,
    ) = setup_order_webhooks(WebhookEventAsyncType.CHECKOUT_CREATED)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        call_order_event(
            plugins_manager,
            WebhookEventAsyncType.ORDER_CREATED,
            order,
        )

    # then
    tax_delivery = EventDelivery.objects.filter(webhook_id=tax_webhook.id).first()
    filter_shipping_delivery = EventDelivery.objects.filter(
        webhook_id=shipping_filter_webhook.id,
        event_type=WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
    ).first()
    assert not filter_shipping_delivery
    assert not tax_delivery
    assert not mocked_send_webhook_request_async.called
    assert not mocked_send_webhook_request_sync.called


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.order.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_order_event_skips_when_sync_webhooks_missing(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    order_with_lines,
    settings,
    webhook,
    permission_manage_orders,
    django_capture_on_commit_callbacks,
):
    # given
    plugins_manager = get_plugins_manager(False)
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save(update_fields=["status", "should_refresh_prices"])

    webhook.app.permissions.add(permission_manage_orders)

    mocked_send_webhook_request_sync.return_value = []

    # when
    with django_capture_on_commit_callbacks(execute=True):
        call_order_event(
            plugins_manager,
            WebhookEventAsyncType.ORDER_CREATED,
            order,
        )

    # then
    order_delivery = EventDelivery.objects.get(webhook_id=webhook.id)
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": order_delivery.id},
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )
    assert not mocked_send_webhook_request_sync.called
    mocked_call_event_including_protected_events.assert_called_once_with(
        plugins_manager.order_created, order_with_lines, webhooks={webhook}
    )


@pytest.mark.parametrize(
    "webhook_event",
    [
        WebhookEventAsyncType.ORDER_CREATED,
        WebhookEventAsyncType.ORDER_CONFIRMED,
        WebhookEventAsyncType.ORDER_PAID,
        WebhookEventAsyncType.ORDER_FULLY_PAID,
        WebhookEventAsyncType.ORDER_REFUNDED,
        WebhookEventAsyncType.ORDER_FULLY_REFUNDED,
        WebhookEventAsyncType.ORDER_UPDATED,
        WebhookEventAsyncType.ORDER_CANCELLED,
        WebhookEventAsyncType.ORDER_EXPIRED,
        WebhookEventAsyncType.ORDER_FULFILLED,
    ],
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.order.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_order_events_triggers_sync_webhook(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    setup_order_webhooks,
    order_with_lines,
    settings,
    django_capture_on_commit_callbacks,
    webhook_event,
):
    # given
    plugins_manager = get_plugins_manager(False)
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save(update_fields=["status", "should_refresh_prices"])

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        order_webhook,
    ) = setup_order_webhooks(webhook_event)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        call_order_events(
            plugins_manager,
            [
                webhook_event,
                WebhookEventAsyncType.ORDER_METADATA_UPDATED,
            ],
            order,
        )

    # then
    order_delivery = EventDelivery.objects.get(webhook_id=order_webhook.id)
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": order_delivery.id},
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
    assert filter_shipping_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    mocked_call_event_including_protected_events.assert_has_calls(
        [
            call(
                ANY,
                order_with_lines,
                webhooks={order_webhook},
            ),
            call(
                plugins_manager.order_metadata_updated, order_with_lines, webhooks=set()
            ),
        ]
    )


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.order.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_order_events_incorrect_webhook_event(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    setup_order_webhooks,
    order_with_lines,
    django_capture_on_commit_callbacks,
):
    # given
    plugins_manager = get_plugins_manager(False)
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save(update_fields=["status", "should_refresh_prices"])

    mocked_send_webhook_request_sync.return_value = []
    setup_order_webhooks(WebhookEventAsyncType.ORDER_CREATED)

    incorrect_event = WebhookEventAsyncType.CHECKOUT_UPDATED

    # when
    with django_capture_on_commit_callbacks(execute=True):
        with pytest.raises(
            ValueError,
            match=f"Events { {incorrect_event} } not found in ORDER_WEBHOOK_EVENT_MAP.",
        ):
            call_order_events(
                plugins_manager,
                [
                    incorrect_event,
                    WebhookEventAsyncType.ORDER_METADATA_UPDATED,
                ],
                order,
            )

    # then
    assert not mocked_send_webhook_request_async.called
    assert not mocked_send_webhook_request_sync.called
    assert not mocked_call_event_including_protected_events.called


@pytest.mark.parametrize(
    "webhook_event",
    [
        WebhookEventAsyncType.ORDER_CREATED,
        WebhookEventAsyncType.ORDER_CONFIRMED,
        WebhookEventAsyncType.ORDER_PAID,
        WebhookEventAsyncType.ORDER_FULLY_PAID,
        WebhookEventAsyncType.ORDER_REFUNDED,
        WebhookEventAsyncType.ORDER_FULLY_REFUNDED,
        WebhookEventAsyncType.ORDER_UPDATED,
        WebhookEventAsyncType.ORDER_CANCELLED,
        WebhookEventAsyncType.ORDER_EXPIRED,
        WebhookEventAsyncType.ORDER_FULFILLED,
    ],
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.order.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_order_events_missing_filter_shipping_method_webhook(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    setup_order_webhooks,
    order_with_lines,
    settings,
    django_capture_on_commit_callbacks,
    webhook_event,
):
    # given
    plugins_manager = get_plugins_manager(False)
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save(update_fields=["status", "should_refresh_prices"])

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        order_webhook,
    ) = setup_order_webhooks(webhook_event)

    shipping_filter_webhook.is_active = False
    shipping_filter_webhook.save(update_fields=["is_active"])

    # when
    with django_capture_on_commit_callbacks(execute=True):
        call_order_events(
            plugins_manager,
            [
                webhook_event,
                WebhookEventAsyncType.ORDER_METADATA_UPDATED,
            ],
            order,
        )

    # then
    order_delivery = EventDelivery.objects.get(webhook_id=order_webhook.id)
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": order_delivery.id},
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )

    # confirm each sync webhook was called without saving event delivery
    mocked_send_webhook_request_sync.assert_called_once()
    assert not EventDelivery.objects.exclude(webhook_id=order_webhook.id).exists()

    tax_delivery = mocked_send_webhook_request_sync.mock_calls[0].args[0]
    assert tax_delivery.webhook_id == tax_webhook.id

    mocked_call_event_including_protected_events.assert_has_calls(
        [
            call(
                ANY,
                order_with_lines,
                webhooks={order_webhook},
            ),
            call(
                plugins_manager.order_metadata_updated, order_with_lines, webhooks=set()
            ),
        ]
    )


@pytest.mark.parametrize(
    "webhook_event",
    [
        WebhookEventAsyncType.ORDER_CREATED,
        WebhookEventAsyncType.ORDER_CONFIRMED,
        WebhookEventAsyncType.ORDER_PAID,
        WebhookEventAsyncType.ORDER_FULLY_PAID,
        WebhookEventAsyncType.ORDER_REFUNDED,
        WebhookEventAsyncType.ORDER_FULLY_REFUNDED,
        WebhookEventAsyncType.ORDER_UPDATED,
        WebhookEventAsyncType.ORDER_CANCELLED,
        WebhookEventAsyncType.ORDER_EXPIRED,
        WebhookEventAsyncType.ORDER_FULFILLED,
        WebhookEventAsyncType.DRAFT_ORDER_CREATED,
        WebhookEventAsyncType.DRAFT_ORDER_UPDATED,
    ],
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.order.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_order_events_skips_tax_webhook_when_prices_are_valid(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    setup_order_webhooks,
    order_with_lines,
    settings,
    django_capture_on_commit_callbacks,
    webhook_event,
):
    # given
    plugins_manager = get_plugins_manager(False)
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(
        update_fields=[
            "status",
        ]
    )

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        order_webhook,
    ) = setup_order_webhooks(webhook_event)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        call_order_events(
            plugins_manager,
            [
                webhook_event,
                WebhookEventAsyncType.ORDER_METADATA_UPDATED,
            ],
            order,
        )

    # then
    order_delivery = EventDelivery.objects.get(webhook_id=order_webhook.id)
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": order_delivery.id},
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )

    # confirm each sync webhook was called without saving event delivery
    mocked_send_webhook_request_sync.assert_called_once()
    assert not EventDelivery.objects.exclude(webhook_id=order_webhook.id).exists()

    filter_shipping_call = mocked_send_webhook_request_sync.mock_calls[0]
    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    )
    assert filter_shipping_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    mocked_call_event_including_protected_events.assert_has_calls(
        [
            call(
                ANY,
                order_with_lines,
                webhooks={order_webhook},
            ),
            call(
                plugins_manager.order_metadata_updated, order_with_lines, webhooks=set()
            ),
        ]
    )


@pytest.mark.parametrize(
    "webhook_event",
    [
        WebhookEventAsyncType.ORDER_CREATED,
        WebhookEventAsyncType.ORDER_CONFIRMED,
        WebhookEventAsyncType.ORDER_PAID,
        WebhookEventAsyncType.ORDER_FULLY_PAID,
        WebhookEventAsyncType.ORDER_REFUNDED,
        WebhookEventAsyncType.ORDER_FULLY_REFUNDED,
        WebhookEventAsyncType.ORDER_UPDATED,
        WebhookEventAsyncType.ORDER_CANCELLED,
        WebhookEventAsyncType.ORDER_EXPIRED,
        WebhookEventAsyncType.ORDER_FULFILLED,
        WebhookEventAsyncType.DRAFT_ORDER_CREATED,
        WebhookEventAsyncType.DRAFT_ORDER_UPDATED,
    ],
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.order.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_order_events_skips_sync_webhooks_when_order_not_editable(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    setup_order_webhooks,
    order_with_lines,
    settings,
    django_capture_on_commit_callbacks,
    webhook_event,
):
    # given
    plugins_manager = get_plugins_manager(False)
    order = order_with_lines
    order.status = OrderStatus.UNFULFILLED
    order.save(
        update_fields=[
            "status",
        ]
    )

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        order_webhook,
    ) = setup_order_webhooks(webhook_event)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        call_order_events(
            plugins_manager,
            [
                webhook_event,
                WebhookEventAsyncType.ORDER_METADATA_UPDATED,
            ],
            order,
        )

    # then
    order_delivery = EventDelivery.objects.get(webhook_id=order_webhook.id)
    tax_delivery = EventDelivery.objects.filter(webhook_id=tax_webhook.id).first()
    filter_shipping_delivery = EventDelivery.objects.filter(
        webhook_id=shipping_filter_webhook.id,
        event_type=WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
    ).first()
    assert not filter_shipping_delivery
    assert not tax_delivery
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": order_delivery.id},
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )
    assert not mocked_send_webhook_request_sync.called
    mocked_call_event_including_protected_events.assert_has_calls(
        [
            call(
                ANY,
                order_with_lines,
                webhooks={order_webhook},
            ),
            call(
                plugins_manager.order_metadata_updated, order_with_lines, webhooks=set()
            ),
        ]
    )


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.order.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_order_events_skips_sync_webhooks_when_draft_order_deleted(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    setup_order_webhooks,
    order_with_lines,
    settings,
    django_capture_on_commit_callbacks,
):
    # given
    plugins_manager = get_plugins_manager(False)
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        order_webhook,
    ) = setup_order_webhooks(WebhookEventAsyncType.DRAFT_ORDER_DELETED)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        call_order_events(
            plugins_manager,
            [
                WebhookEventAsyncType.DRAFT_ORDER_DELETED,
                WebhookEventAsyncType.ORDER_METADATA_UPDATED,
            ],
            order,
        )

    # then
    order_delivery = EventDelivery.objects.get(webhook_id=order_webhook.id)
    tax_delivery = EventDelivery.objects.filter(webhook_id=tax_webhook.id).first()
    filter_shipping_delivery = EventDelivery.objects.filter(
        webhook_id=shipping_filter_webhook.id,
        event_type=WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
    ).first()
    assert not filter_shipping_delivery
    assert not tax_delivery
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": order_delivery.id},
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )
    assert not mocked_send_webhook_request_sync.called
    mocked_call_event_including_protected_events.assert_has_calls(
        [
            call(
                plugins_manager.draft_order_deleted,
                order_with_lines,
                webhooks={order_webhook},
            ),
            call(
                plugins_manager.order_metadata_updated, order_with_lines, webhooks=set()
            ),
        ]
    )


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_order_events_skips_when_async_webhooks_missing(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    setup_order_webhooks,
    order_with_lines,
    settings,
    django_capture_on_commit_callbacks,
):
    # given
    plugins_manager = get_plugins_manager(False)
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save(update_fields=["status", "should_refresh_prices"])

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        checkout_webhook,
    ) = setup_order_webhooks(WebhookEventAsyncType.CHECKOUT_CREATED)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        call_order_events(
            plugins_manager,
            [
                WebhookEventAsyncType.ORDER_CREATED,
                WebhookEventAsyncType.ORDER_METADATA_UPDATED,
            ],
            order,
        )

    # then
    tax_delivery = EventDelivery.objects.filter(webhook_id=tax_webhook.id).first()
    filter_shipping_delivery = EventDelivery.objects.filter(
        webhook_id=shipping_filter_webhook.id,
        event_type=WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
    ).first()
    assert not filter_shipping_delivery
    assert not tax_delivery
    assert not mocked_send_webhook_request_async.called
    assert not mocked_send_webhook_request_sync.called


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.order.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_order_events_skips_when_sync_webhooks_missing(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    order_with_lines,
    settings,
    webhook,
    permission_manage_orders,
    django_capture_on_commit_callbacks,
):
    # given
    plugins_manager = get_plugins_manager(False)
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save(update_fields=["status", "should_refresh_prices"])

    webhook.app.permissions.add(permission_manage_orders)

    mocked_send_webhook_request_sync.return_value = []

    # when
    with django_capture_on_commit_callbacks(execute=True):
        call_order_events(
            plugins_manager,
            [
                WebhookEventAsyncType.ORDER_CREATED,
                WebhookEventAsyncType.ORDER_METADATA_UPDATED,
            ],
            order,
        )

    # then
    order_delivery = EventDelivery.objects.get(webhook_id=webhook.id)
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": order_delivery.id},
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )
    assert not mocked_send_webhook_request_sync.called
    mocked_call_event_including_protected_events.assert_has_calls(
        [
            call(
                plugins_manager.order_created,
                order_with_lines,
                webhooks={webhook},
            ),
            call(
                plugins_manager.order_metadata_updated, order_with_lines, webhooks=set()
            ),
        ]
    )


@patch(
    "saleor.order.actions.call_order_event",
    wraps=call_order_event,
)
@patch(
    "saleor.order.actions.call_order_events",
    wraps=call_order_events,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_order_created_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_order_events,
    wrapped_call_order_event,
    setup_order_webhooks,
    order_with_lines,
    customer_user,
    settings,
    django_capture_on_commit_callbacks,
):
    # given
    plugins_manager = get_plugins_manager(False)
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        additional_order_webhook,
    ) = setup_order_webhooks(
        [
            WebhookEventAsyncType.ORDER_CREATED,
            WebhookEventAsyncType.ORDER_PAID,
            WebhookEventAsyncType.ORDER_UPDATED,
            WebhookEventAsyncType.ORDER_FULLY_PAID,
            WebhookEventAsyncType.ORDER_CONFIRMED,
        ]
    )
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.charge_status = OrderChargeStatus.FULL
    order.save(update_fields=["status", "should_refresh_prices", "charge_status"])

    order.channel.automatically_confirm_all_new_orders = True
    order.channel.save(update_fields=["automatically_confirm_all_new_orders"])
    order_info = OrderInfo(
        order=order,
        customer_email=order.get_customer_email(),
        channel=order.channel,
        payment=order.get_last_payment(),
        lines_data=[],
    )

    webhook_event_map = get_webhooks_for_multiple_events(
        WEBHOOK_EVENTS_FOR_ORDER_CREATED
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        order_created(order_info, user=customer_user, app=None, manager=plugins_manager)

    # then
    # confirm that event delivery was generated for each async webhook.
    order_confirmed_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_CONFIRMED,
    )
    order_updated_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_CREATED,
    )
    order_paid_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_PAID,
    )
    order_fully_paid_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_FULLY_PAID,
    )

    order_deliveries = [
        order_confirmed_delivery,
        order_updated_delivery,
        order_paid_delivery,
        order_fully_paid_delivery,
    ]

    mocked_send_webhook_request_async.assert_has_calls(
        [
            call(
                kwargs={"event_delivery_id": delivery.id},
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
                bind=True,
                retry_backoff=10,
                retry_kwargs={"max_retries": 5},
            )
            for delivery in order_deliveries
        ],
        any_order=True,
    )
    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 2
    assert not EventDelivery.objects.exclude(
        webhook_id=additional_order_webhook.id
    ).exists()

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
    assert filter_shipping_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    wrapped_call_order_events.assert_called_once_with(
        plugins_manager,
        [WebhookEventAsyncType.ORDER_FULLY_PAID, WebhookEventAsyncType.ORDER_UPDATED],
        order,
        webhook_event_map=webhook_event_map,
    )
    wrapped_call_order_event.assert_has_calls(
        [
            call(
                plugins_manager,
                WebhookEventAsyncType.ORDER_CREATED,
                order,
                webhook_event_map=webhook_event_map,
            ),
            call(
                plugins_manager,
                WebhookEventAsyncType.ORDER_CONFIRMED,
                order,
                webhook_event_map=webhook_event_map,
            ),
            call(
                plugins_manager,
                WebhookEventAsyncType.ORDER_PAID,
                order,
                webhook_event_map=webhook_event_map,
            ),
        ],
        any_order=True,
    )


@patch(
    "saleor.order.actions.call_order_event",
    wraps=call_order_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_order_confirmed_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_order_event,
    setup_order_webhooks,
    order_with_lines,
    customer_user,
    settings,
    django_capture_on_commit_callbacks,
):
    # given
    plugins_manager = get_plugins_manager(False)
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        additional_order_webhook,
    ) = setup_order_webhooks(
        [
            WebhookEventAsyncType.ORDER_CONFIRMED,
        ]
    )

    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save(update_fields=["status", "should_refresh_prices"])

    # when
    with django_capture_on_commit_callbacks(execute=True):
        order_confirmed(order, user=customer_user, app=None, manager=plugins_manager)

    # then
    # confirm that event delivery was generated for each async webhook.
    order_confirmed_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_CONFIRMED,
    )
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": order_confirmed_delivery.id},
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 2
    assert not EventDelivery.objects.exclude(
        webhook_id=additional_order_webhook.id
    ).exists()

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
    assert filter_shipping_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    assert wrapped_call_order_event.called
