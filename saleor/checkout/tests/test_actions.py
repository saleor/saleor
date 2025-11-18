import datetime
from decimal import Decimal
from unittest.mock import ANY, call, patch

import pytest
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time

from ...core.models import EventDelivery
from ...core.utils.events import call_event_including_protected_events
from ...graphql.webhook.dataloaders.pregenerated_payload_for_checkout_tax import (
    PregeneratedCheckoutTaxPayloadsByCheckoutTokenLoader,
)
from ...graphql.webhook.dataloaders.pregenerated_payloads_for_checkout_filter_shipping_methods import (
    PregeneratedCheckoutFilterShippingMethodPayloadsByCheckoutTokenLoader,
)
from ...plugins.manager import get_plugins_manager
from ...webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from .. import CheckoutAuthorizeStatus, CheckoutChargeStatus
from ..actions import (
    call_checkout_event,
    call_checkout_events,
    call_checkout_info_event,
    transaction_amounts_for_checkout_updated,
    transaction_amounts_for_checkout_updated_without_price_recalculation,
)
from ..calculations import calculate_checkout_total, fetch_checkout_data
from ..fetch import fetch_checkout_info, fetch_checkout_lines


@patch("saleor.checkout.tasks.automatic_checkout_completion_task.delay")
@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
@patch("saleor.plugins.manager.PluginsManager.checkout_fully_authorized")
def test_transaction_amounts_for_checkout_updated_fully_paid(
    mocked_fully_authorized,
    mocked_fully_paid,
    mocked_automatic_checkout_completion_task,
    checkout_with_items,
    transaction_item_generator,
    plugins_manager,
    django_capture_on_commit_callbacks,
):
    # given
    checkout = checkout_with_items
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)
    transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=checkout_info.checkout.total.gross.amount
    )
    assert checkout_info.channel.automatically_complete_fully_paid_checkouts is False

    # when
    with django_capture_on_commit_callbacks(execute=True):
        transaction_amounts_for_checkout_updated(
            transaction, manager=plugins_manager, user=None, app=None
        )

    # then
    checkout.refresh_from_db()
    assert checkout.charge_status == CheckoutChargeStatus.FULL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL
    mocked_fully_paid.assert_called_with(checkout, webhooks=set())
    mocked_fully_authorized.assert_called_with(checkout, webhooks=set())
    assert not mocked_automatic_checkout_completion_task.called


@patch("saleor.checkout.tasks.automatic_checkout_completion_task.delay")
@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
@patch("saleor.plugins.manager.PluginsManager.checkout_fully_authorized")
def test_transaction_amounts_for_checkout_updated_not_fully_paid_no_automatic_complete(
    mocked_fully_authorized,
    mocked_fully_paid,
    mocked_automatic_checkout_completion_task,
    checkout_with_items,
    transaction_item_generator,
    plugins_manager,
    django_capture_on_commit_callbacks,
):
    # given
    checkout = checkout_with_items
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)
    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        charged_value=checkout_info.checkout.total.gross.amount / 2,
    )
    channel = checkout_info.channel
    channel.automatically_complete_fully_paid_checkouts = True
    channel.save(update_fields=["automatically_complete_fully_paid_checkouts"])

    # when
    with django_capture_on_commit_callbacks(execute=True):
        transaction_amounts_for_checkout_updated(
            transaction, manager=plugins_manager, user=None, app=None
        )

    # then
    checkout.refresh_from_db()
    assert checkout.charge_status == CheckoutChargeStatus.PARTIAL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.PARTIAL
    assert not mocked_fully_authorized.called
    assert not mocked_fully_paid.called
    assert not mocked_automatic_checkout_completion_task.called


@patch("saleor.checkout.tasks.automatic_checkout_completion_task.delay")
@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
@patch("saleor.plugins.manager.PluginsManager.checkout_fully_authorized")
def test_transaction_amounts_for_checkout_updated_with_already_fully_paid(
    mocked_fully_paid,
    mocked_fully_authorized,
    mocked_automatic_checkout_completion_task,
    checkout_with_items,
    transaction_item_generator,
    plugins_manager,
    django_capture_on_commit_callbacks,
):
    # given
    checkout = checkout_with_items
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)
    transaction_item_generator(
        checkout_id=checkout.pk, charged_value=checkout_info.checkout.total.gross.amount
    )
    assert checkout_info.channel.automatically_complete_fully_paid_checkouts is False

    fetch_checkout_data(checkout_info, plugins_manager, lines, force_status_update=True)

    second_transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=checkout_info.checkout.total.gross.amount
    )
    # when
    with django_capture_on_commit_callbacks(execute=True):
        transaction_amounts_for_checkout_updated(
            second_transaction, manager=plugins_manager, user=None, app=None
        )

    # then
    checkout.refresh_from_db()
    assert checkout.charge_status == CheckoutChargeStatus.OVERCHARGED
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL
    assert not mocked_fully_paid.called
    assert not mocked_fully_authorized.called
    assert not mocked_automatic_checkout_completion_task.called


@patch("saleor.checkout.tasks.automatic_checkout_completion_task.delay")
@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
@patch("saleor.plugins.manager.PluginsManager.checkout_fully_authorized")
def test_transaction_amounts_for_checkout_updated_with_already_fully_authorized(
    mocked_fully_paid,
    mocked_fully_authorized,
    mocked_automatic_checkout_completion_task,
    checkout_with_items,
    transaction_item_generator,
    plugins_manager,
    django_capture_on_commit_callbacks,
):
    # given
    checkout = checkout_with_items
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)
    total = calculate_checkout_total(
        manager=plugins_manager, checkout_info=checkout_info, lines=lines, address=None
    )

    first_authorized_amount = total.gross.amount - 1
    second_authorized_amount = 1
    transaction_item_generator(
        checkout_id=checkout.pk,
        authorized_value=first_authorized_amount,
    )

    second_transaction = transaction_item_generator(
        checkout_id=checkout.pk, authorized_value=second_authorized_amount
    )

    fetch_checkout_data(checkout_info, plugins_manager, lines, force_status_update=True)

    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL
    assert checkout.charge_status == CheckoutChargeStatus.NONE

    # when
    with django_capture_on_commit_callbacks(execute=True):
        transaction_amounts_for_checkout_updated(
            second_transaction, manager=plugins_manager, user=None, app=None
        )

    # then
    checkout.refresh_from_db()
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL
    assert checkout.charge_status == CheckoutChargeStatus.NONE
    assert not mocked_fully_paid.called
    assert not mocked_fully_authorized.called
    assert not mocked_automatic_checkout_completion_task.called


@patch("saleor.checkout.tasks.automatic_checkout_completion_task.delay")
@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
@patch("saleor.plugins.manager.PluginsManager.checkout_fully_authorized")
def test_transaction_amounts_for_checkout_updated_fully_authorized(
    mocked_fully_authorized,
    mocked_fully_paid,
    mocked_automatic_checkout_completion_task,
    checkout_with_items,
    transaction_item_generator,
    plugins_manager,
    django_capture_on_commit_callbacks,
):
    # given
    checkout = checkout_with_items
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)
    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        authorized_value=checkout_info.checkout.total.gross.amount,
    )
    assert checkout_info.channel.automatically_complete_fully_paid_checkouts is False

    # when
    with django_capture_on_commit_callbacks(execute=True):
        transaction_amounts_for_checkout_updated(
            transaction, manager=plugins_manager, user=None, app=None
        )

    # then
    checkout.refresh_from_db()
    assert checkout.charge_status == CheckoutChargeStatus.NONE
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL
    assert not mocked_fully_paid.called
    assert not mocked_automatic_checkout_completion_task.called
    mocked_fully_authorized.assert_called_once_with(checkout, webhooks=set())


@pytest.mark.parametrize(
    "previous_modified_at",
    [None, datetime.datetime(2018, 5, 31, 12, 0, 0, tzinfo=datetime.UTC)],
)
@freeze_time("2023-05-31 12:00:01")
def test_transaction_amounts_for_checkout_updated_updates_last_transaction_modified_at(
    previous_modified_at,
    checkout_with_items,
    transaction_item_generator,
    plugins_manager,
    django_capture_on_commit_callbacks,
):
    # given
    checkout = checkout_with_items
    checkout.last_transaction_modified_at = previous_modified_at
    checkout.save(update_fields=["last_transaction_modified_at"])

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        plugins_manager,
        lines,
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=checkout_info.checkout.total.gross.amount
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        transaction_amounts_for_checkout_updated(
            transaction, manager=plugins_manager, user=None, app=None
        )

    # then
    checkout.refresh_from_db()
    assert checkout.last_transaction_modified_at == transaction.modified_at


def test_get_checkout_refundable_with_transaction_and_last_refund_success(
    checkout_with_items,
    transaction_item_generator,
    plugins_manager,
):
    # given
    checkout = checkout_with_items

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        plugins_manager,
        lines,
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(10.0)
    )

    # when
    transaction_amounts_for_checkout_updated(
        transaction, manager=plugins_manager, user=None, app=None
    )

    # then
    checkout.refresh_from_db()
    assert checkout.automatically_refundable is True


def test_get_checkout_refundable_with_transaction_and_last_refund_failure(
    checkout_with_items,
    transaction_item_generator,
    plugins_manager,
):
    # given
    checkout = checkout_with_items
    checkout.automatically_refundable = True
    checkout.save(update_fields=["automatically_refundable"])

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        plugins_manager,
        lines,
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(10.0), last_refund_success=False
    )

    # when
    transaction_amounts_for_checkout_updated(
        transaction, manager=plugins_manager, user=None, app=None
    )

    # then
    checkout.refresh_from_db()
    assert checkout.automatically_refundable is False


def test_get_checkout_refundable_with_transaction_without_funds(
    checkout_with_items,
    transaction_item_generator,
    plugins_manager,
):
    # given
    checkout = checkout_with_items
    checkout.automatically_refundable = True
    checkout.save(update_fields=["automatically_refundable"])

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        plugins_manager,
        lines,
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(0)
    )

    # when
    transaction_amounts_for_checkout_updated(
        transaction, manager=plugins_manager, user=None, app=None
    )

    # then
    checkout.refresh_from_db()
    assert checkout.automatically_refundable is False


def test_get_checkout_refundable_with_multiple_transactions_without_funds(
    checkout_with_items,
    transaction_item_generator,
    plugins_manager,
):
    # given
    checkout = checkout_with_items
    checkout.automatically_refundable = True
    checkout.save(update_fields=["automatically_refundable"])

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        plugins_manager,
        lines,
    )
    first_transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(0)
    )
    transaction_item_generator(checkout_id=checkout.pk, charged_value=Decimal(0))

    # when
    transaction_amounts_for_checkout_updated(
        first_transaction, manager=plugins_manager, user=None, app=None
    )

    # then
    checkout.refresh_from_db()
    assert checkout.automatically_refundable is False


def test_get_checkout_refundable_with_multiple_transactions_with_failure_refund(
    checkout_with_items,
    transaction_item_generator,
    plugins_manager,
):
    # given
    checkout = checkout_with_items
    checkout.automatically_refundable = True
    checkout.save(update_fields=["automatically_refundable"])

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        plugins_manager,
        lines,
    )
    first_transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(10), last_refund_success=False
    )
    transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(10), last_refund_success=False
    )

    # when
    transaction_amounts_for_checkout_updated(
        first_transaction, manager=plugins_manager, app=None, user=None
    )

    # then
    checkout.refresh_from_db()
    assert checkout.automatically_refundable is False


def test_get_checkout_refundable_with_multiple_active_transactions(
    checkout_with_items,
    transaction_item_generator,
    plugins_manager,
):
    # given
    checkout = checkout_with_items
    checkout.automatically_refundable = True
    checkout.save(update_fields=["automatically_refundable"])

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        plugins_manager,
        lines,
    )
    first_transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(10), last_refund_success=False
    )
    transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(10), last_refund_success=True
    )
    transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(10), last_refund_success=True
    )

    # when
    transaction_amounts_for_checkout_updated(
        first_transaction, manager=plugins_manager, user=None, app=None
    )

    # then
    checkout.refresh_from_db()
    assert checkout.automatically_refundable is True


@freeze_time("2023-05-31 12:00:01")
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_checkout_event_incorrect_webhook_event(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    checkout_with_items,
    setup_checkout_webhooks,
    django_capture_on_commit_callbacks,
):
    # given
    plugins_manager = get_plugins_manager(allow_replica=False)
    checkout_with_items.price_expiration = timezone.now()
    checkout_with_items.save(update_fields=["price_expiration"])

    mocked_send_webhook_request_sync.return_value = []
    setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_CREATED)

    incorrect_event = WebhookEventAsyncType.ORDER_UPDATED
    # when

    with django_capture_on_commit_callbacks(execute=True):
        with pytest.raises(
            ValueError,
            match=f"Event {incorrect_event} not found in CHECKOUT_WEBHOOK_EVENT_MAP.",
        ):
            call_checkout_event(
                plugins_manager,
                incorrect_event,
                checkout_with_items,
            )

    # then
    assert not mocked_send_webhook_request_async.called
    assert not mocked_send_webhook_request_sync.called


@freeze_time("2023-05-31 12:00:01")
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.checkout.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_checkout_event_triggers_sync_webhook_when_needed(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    checkout_with_items,
    setup_checkout_webhooks,
    settings,
    django_capture_on_commit_callbacks,
    address,
):
    # given
    plugins_manager = get_plugins_manager(allow_replica=False)
    checkout_with_items.price_expiration = timezone.now()

    # Set address - so SHIPPING_LIST_METHODS_FOR_CHECKOUT is executed too
    checkout_with_items.shipping_address = address
    checkout_with_items.billing_address = address

    checkout_with_items.save(
        update_fields=["price_expiration", "billing_address", "shipping_address"]
    )

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_created_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_CREATED)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        with freeze_time("2023-06-01 12:00:01"):
            call_checkout_event(
                plugins_manager,
                WebhookEventAsyncType.CHECKOUT_CREATED,
                checkout_with_items,
            )

    # then
    # confirm that event delivery was generated for each async webhook.
    checkout_create_delivery = EventDelivery.objects.get(
        webhook_id=checkout_created_webhook.id
    )
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={
            "event_delivery_id": checkout_create_delivery.id,
            "telemetry_context": ANY,
        },
        queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        MessageGroupId="example.com:saleorappadditional",
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 3
    assert not EventDelivery.objects.exclude(
        webhook_id=checkout_created_webhook.id
    ).exists()

    shipping_methods_call, filter_shipping_call, tax_delivery_call = (
        mocked_send_webhook_request_sync.mock_calls
    )
    shipping_methods_delivery = shipping_methods_call.args[0]
    assert shipping_methods_delivery.webhook_id == shipping_webhook.id
    assert (
        shipping_methods_delivery.event_type
        == WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
    )

    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    )

    tax_delivery = tax_delivery_call.args[0]
    assert tax_delivery.webhook_id == tax_webhook.id

    mocked_call_event_including_protected_events.assert_called_once_with(
        plugins_manager.checkout_created,
        checkout_with_items,
        webhooks={checkout_created_webhook},
    )


@freeze_time("2023-05-31 12:00:01")
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.checkout.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_checkout_event_skips_tax_webhook_when_not_expired(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    checkout_with_items,
    setup_checkout_webhooks,
    settings,
    django_capture_on_commit_callbacks,
    address,
):
    # given
    plugins_manager = get_plugins_manager(allow_replica=False)

    # Ensure shipping & billing is set, so shipping webhooks are actually emitted
    checkout_with_items.shipping_address = address
    checkout_with_items.billing_address = address

    checkout_with_items.price_expiration = timezone.now() + datetime.timedelta(hours=1)
    checkout_with_items.save(
        update_fields=["price_expiration", "shipping_address", "billing_address"]
    )

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_created_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_CREATED)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        call_checkout_event(
            plugins_manager,
            WebhookEventAsyncType.CHECKOUT_CREATED,
            checkout_with_items,
        )

    # then
    # confirm that event delivery was generated for each async webhook.
    checkout_create_delivery = EventDelivery.objects.get(
        webhook_id=checkout_created_webhook.id
    )
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={
            "event_delivery_id": checkout_create_delivery.id,
            "telemetry_context": ANY,
        },
        queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        MessageGroupId="example.com:saleorappadditional",
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 2
    assert not EventDelivery.objects.exclude(
        webhook_id=checkout_created_webhook.id
    ).exists()

    shipping_methods_call, filter_shipping_call = (
        mocked_send_webhook_request_sync.mock_calls
    )
    shipping_methods_delivery = shipping_methods_call.args[0]
    assert shipping_methods_delivery.webhook_id == shipping_webhook.id
    assert (
        shipping_methods_delivery.event_type
        == WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
    )

    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    )

    mocked_call_event_including_protected_events.assert_called_once_with(
        plugins_manager.checkout_created,
        checkout_with_items,
        webhooks={checkout_created_webhook},
    )


@freeze_time("2023-05-31 12:00:01")
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_checkout_event_skip_sync_webhooks_when_async_missing(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    checkout_with_items,
    setup_checkout_webhooks,
    django_capture_on_commit_callbacks,
):
    # given
    plugins_manager = get_plugins_manager(allow_replica=False)
    checkout_with_items.price_expiration = timezone.now()
    checkout_with_items.save(update_fields=["price_expiration"])

    mocked_send_webhook_request_sync.return_value = []

    # setup sync webhooks with async that is not going to be called
    setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_CREATED)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        with freeze_time("2023-06-01 12:00:01"):
            call_checkout_event(
                plugins_manager,
                WebhookEventAsyncType.CHECKOUT_UPDATED,
                checkout_with_items,
            )

    # then

    assert not mocked_send_webhook_request_async.called
    assert not mocked_send_webhook_request_sync.called


@freeze_time("2023-05-31 12:00:01")
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.checkout.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_checkout_event_only_async_when_sync_missing(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    checkout_with_items,
    permission_manage_checkouts,
    settings,
    webhook,
    django_capture_on_commit_callbacks,
):
    # given
    plugins_manager = get_plugins_manager(allow_replica=False)
    checkout_with_items.price_expiration = timezone.now()
    checkout_with_items.save(update_fields=["price_expiration"])

    webhook.events.create(event_type=WebhookEventAsyncType.CHECKOUT_CREATED)
    webhook.app.permissions.add(permission_manage_checkouts)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        with freeze_time("2023-06-01 12:00:01"):
            call_checkout_event(
                plugins_manager,
                WebhookEventAsyncType.CHECKOUT_CREATED,
                checkout_with_items,
            )

    # then

    # confirm that event delivery was generated for each async webhook.
    checkout_create_delivery = EventDelivery.objects.get(webhook_id=webhook.id)

    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={
            "event_delivery_id": checkout_create_delivery.id,
            "telemetry_context": ANY,
        },
        queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        MessageGroupId="example.com:saleorapptest",
    )
    assert not mocked_send_webhook_request_sync.called
    mocked_call_event_including_protected_events.assert_called_once_with(
        plugins_manager.checkout_created, checkout_with_items, webhooks={webhook}
    )


@freeze_time("2023-05-31 12:00:01")
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_checkout_info_event_incorrect_webhook_event(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    checkout_with_items,
    setup_checkout_webhooks,
    django_capture_on_commit_callbacks,
):
    # given
    plugins_manager = get_plugins_manager(allow_replica=False)
    checkout_with_items.price_expiration = timezone.now()
    checkout_with_items.save(update_fields=["price_expiration"])

    mocked_send_webhook_request_sync.return_value = []
    setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_CREATED)

    lines_info, _ = fetch_checkout_lines(
        checkout_with_items,
    )
    checkout_info = fetch_checkout_info(
        checkout_with_items,
        lines_info,
        plugins_manager,
    )
    incorrect_webhook_event = WebhookEventAsyncType.ORDER_UPDATED

    # when
    with django_capture_on_commit_callbacks(execute=True):
        with pytest.raises(
            ValueError,
            match=f"Event {incorrect_webhook_event} not found in CHECKOUT_WEBHOOK_EVENT_MAP.",
        ):
            call_checkout_info_event(
                plugins_manager,
                incorrect_webhook_event,
                checkout_info,
                lines_info,
            )

    # then
    assert not mocked_send_webhook_request_async.called
    assert not mocked_send_webhook_request_sync.called


@freeze_time("2023-05-31 12:00:01")
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.checkout.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_checkout_info_event_triggers_sync_webhook_when_needed(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    checkout_with_items,
    setup_checkout_webhooks,
    settings,
    django_capture_on_commit_callbacks,
    address,
):
    # given
    plugins_manager = get_plugins_manager(allow_replica=False)

    # Ensure shipping is set so shipping webhooks are emitted
    checkout_with_items.shipping_address = address
    checkout_with_items.billing_address = address

    checkout_with_items.price_expiration = timezone.now()
    checkout_with_items.save(
        update_fields=["price_expiration", "billing_address", "shipping_address"]
    )

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_created_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_CREATED)

    lines_info, _ = fetch_checkout_lines(
        checkout_with_items,
    )
    checkout_info = fetch_checkout_info(
        checkout_with_items,
        lines_info,
        plugins_manager,
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        with freeze_time("2023-06-01 12:00:01"):
            call_checkout_info_event(
                plugins_manager,
                WebhookEventAsyncType.CHECKOUT_CREATED,
                checkout_info,
                lines_info,
            )

    # then

    # confirm that event delivery was generated for each async webhook.
    checkout_create_delivery = EventDelivery.objects.get(
        webhook_id=checkout_created_webhook.id
    )
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={
            "event_delivery_id": checkout_create_delivery.id,
            "telemetry_context": ANY,
        },
        queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        MessageGroupId="example.com:saleorappadditional",
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 3
    assert not EventDelivery.objects.exclude(
        webhook_id=checkout_created_webhook.id
    ).exists()

    shipping_methods_call, filter_shipping_call, tax_delivery_call = (
        mocked_send_webhook_request_sync.mock_calls
    )
    shipping_methods_delivery = shipping_methods_call.args[0]
    assert shipping_methods_delivery.webhook_id == shipping_webhook.id
    assert (
        shipping_methods_delivery.event_type
        == WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
    )

    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    )

    tax_delivery = tax_delivery_call.args[0]
    assert tax_delivery.webhook_id == tax_webhook.id

    mocked_call_event_including_protected_events.assert_called_once_with(
        plugins_manager.checkout_created,
        checkout_with_items,
        webhooks={checkout_created_webhook},
    )


@freeze_time("2023-05-31 12:00:01")
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.checkout.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_checkout_info_event_skips_tax_webhook_when_not_expired(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    checkout_with_items,
    setup_checkout_webhooks,
    settings,
    django_capture_on_commit_callbacks,
    address,
):
    # given
    plugins_manager = get_plugins_manager(allow_replica=False)

    # Ensure shipping is set so shipping webhooks are emitted
    checkout_with_items.shipping_address = address
    checkout_with_items.billing_address = address

    checkout_with_items.price_expiration = timezone.now() + datetime.timedelta(hours=1)
    checkout_with_items.save(
        update_fields=["price_expiration", "billing_address", "shipping_address"]
    )

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_created_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_CREATED)

    lines_info, _ = fetch_checkout_lines(
        checkout_with_items,
    )
    checkout_info = fetch_checkout_info(
        checkout_with_items,
        lines_info,
        plugins_manager,
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        call_checkout_info_event(
            plugins_manager,
            WebhookEventAsyncType.CHECKOUT_CREATED,
            checkout_info,
            lines_info,
        )

    # then

    # confirm that event delivery was generated for each async webhook.
    checkout_create_delivery = EventDelivery.objects.get(
        webhook_id=checkout_created_webhook.id
    )
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={
            "event_delivery_id": checkout_create_delivery.id,
            "telemetry_context": ANY,
        },
        queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        MessageGroupId="example.com:saleorappadditional",
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 2
    assert not EventDelivery.objects.exclude(
        webhook_id=checkout_created_webhook.id
    ).exists()

    shipping_methods_call, filter_shipping_call = (
        mocked_send_webhook_request_sync.mock_calls
    )
    shipping_methods_delivery = shipping_methods_call.args[0]
    assert shipping_methods_delivery.webhook_id == shipping_webhook.id
    assert (
        shipping_methods_delivery.event_type
        == WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
    )

    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    )

    mocked_call_event_including_protected_events.assert_called_once_with(
        plugins_manager.checkout_created,
        checkout_with_items,
        webhooks={checkout_created_webhook},
    )


@freeze_time("2023-05-31 12:00:01")
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.checkout.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_checkout_info_event_only_async_when_sync_missing(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    checkout_with_items,
    permission_manage_checkouts,
    settings,
    webhook,
    django_capture_on_commit_callbacks,
):
    # given
    plugins_manager = get_plugins_manager(allow_replica=False)
    checkout_with_items.price_expiration = timezone.now()
    checkout_with_items.save(update_fields=["price_expiration"])

    webhook.events.create(event_type=WebhookEventAsyncType.CHECKOUT_CREATED)
    webhook.app.permissions.add(permission_manage_checkouts)

    lines_info, _ = fetch_checkout_lines(
        checkout_with_items,
    )
    checkout_info = fetch_checkout_info(
        checkout_with_items,
        lines_info,
        plugins_manager,
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        with freeze_time("2023-06-01 12:00:01"):
            call_checkout_info_event(
                plugins_manager,
                WebhookEventAsyncType.CHECKOUT_CREATED,
                checkout_info,
                lines_info,
            )

    # then

    # confirm that event delivery was generated for each async webhook.
    checkout_create_delivery = EventDelivery.objects.get(webhook_id=webhook.id)

    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={
            "event_delivery_id": checkout_create_delivery.id,
            "telemetry_context": ANY,
        },
        queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        MessageGroupId="example.com:saleorapptest",
    )
    assert not mocked_send_webhook_request_sync.called
    mocked_call_event_including_protected_events.assert_called_once_with(
        plugins_manager.checkout_created, checkout_with_items, webhooks={webhook}
    )


@freeze_time("2023-05-31 12:00:01")
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_checkout_info_event_skip_sync_webhooks_when_async_missing(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    checkout_with_items,
    setup_checkout_webhooks,
    django_capture_on_commit_callbacks,
):
    # given
    plugins_manager = get_plugins_manager(allow_replica=False)
    checkout_with_items.price_expiration = timezone.now()
    checkout_with_items.save(update_fields=["price_expiration"])

    mocked_send_webhook_request_sync.return_value = []

    # setup sync webhooks with async that is not going to be called
    setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_CREATED)

    lines_info, _ = fetch_checkout_lines(
        checkout_with_items,
    )
    checkout_info = fetch_checkout_info(
        checkout_with_items,
        lines_info,
        plugins_manager,
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        with freeze_time("2023-06-01 12:00:01"):
            call_checkout_info_event(
                plugins_manager,
                WebhookEventAsyncType.CHECKOUT_UPDATED,
                checkout_info,
                lines_info,
            )

    # then

    assert not mocked_send_webhook_request_async.called
    assert not mocked_send_webhook_request_sync.called


@freeze_time("2023-05-31 12:00:01")
@patch(
    "saleor.checkout.actions.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.checkout.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_transaction_amounts_for_checkout_fully_paid_triggers_sync_webhook(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_checkout_info_event,
    setup_checkout_webhooks,
    settings,
    checkout_with_items,
    transaction_item_generator,
    django_capture_on_commit_callbacks,
    address,
):
    # given
    plugins_manager = get_plugins_manager(allow_replica=False)
    checkout_with_items.price_expiration = timezone.now() - datetime.timedelta(hours=10)

    # Ensure shipping is set so shipping webhooks are emitted
    checkout_with_items.shipping_address = address
    checkout_with_items.billing_address = address

    checkout_with_items.save(
        update_fields=["price_expiration", "billing_address", "shipping_address"]
    )

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_fully_paid_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_FULLY_PAID)
    checkout = checkout_with_items
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)
    transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=checkout_info.checkout.total.gross.amount
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        transaction_amounts_for_checkout_updated(
            transaction, manager=plugins_manager, user=None, app=None
        )

    # then

    # confirm that event delivery was generated for each async webhook.
    checkout_fully_paid_delivery = EventDelivery.objects.get(
        webhook_id=checkout_fully_paid_webhook.id
    )
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={
            "event_delivery_id": checkout_fully_paid_delivery.id,
            "telemetry_context": ANY,
        },
        queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        MessageGroupId="example.com:saleorappadditional",
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 3
    assert not EventDelivery.objects.exclude(
        webhook_id=checkout_fully_paid_webhook.id
    ).exists()

    tax_delivery_call, shipping_methods_call, filter_shipping_call = (
        mocked_send_webhook_request_sync.mock_calls
    )
    shipping_methods_delivery = shipping_methods_call.args[0]
    assert shipping_methods_delivery.webhook_id == shipping_webhook.id
    assert (
        shipping_methods_delivery.event_type
        == WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
    )

    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    )

    tax_delivery = tax_delivery_call.args[0]
    assert tax_delivery.webhook_id == tax_webhook.id

    assert wrapped_call_checkout_info_event.called

    assert mocked_call_event_including_protected_events.call_count == 2
    mocked_call_event_including_protected_events.assert_any_call(
        plugins_manager.checkout_fully_paid,
        checkout_with_items,
        webhooks={checkout_fully_paid_webhook},
    )
    mocked_call_event_including_protected_events.assert_any_call(
        plugins_manager.checkout_fully_authorized,
        checkout_with_items,
        webhooks=set(),
    )


@freeze_time("2023-05-31 12:00:01")
@patch(
    "saleor.checkout.actions.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.checkout.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_transaction_amounts_for_checkout_fully_authorized_triggers_sync_webhook(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_checkout_info_event,
    setup_checkout_webhooks,
    settings,
    checkout_with_items,
    transaction_item_generator,
    django_capture_on_commit_callbacks,
    address,
):
    # given
    plugins_manager = get_plugins_manager(allow_replica=False)
    checkout_with_items.price_expiration = timezone.now() - datetime.timedelta(hours=10)

    # Ensure shipping is set so shipping webhooks are emitted
    checkout_with_items.shipping_address = address
    checkout_with_items.billing_address = address

    checkout_with_items.save(
        update_fields=["price_expiration", "billing_address", "shipping_address"]
    )

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_fully_authorized_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_FULLY_AUTHORIZED)
    checkout = checkout_with_items
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)

    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        authorized_value=checkout_info.checkout.total.gross.amount,
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        transaction_amounts_for_checkout_updated(
            transaction, manager=plugins_manager, user=None, app=None
        )

    # then

    # confirm that event delivery was generated for each async webhook.
    checkout_fully_authorized_delivery = EventDelivery.objects.get(
        webhook_id=checkout_fully_authorized_webhook.id
    )
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={
            "event_delivery_id": checkout_fully_authorized_delivery.id,
            "telemetry_context": ANY,
        },
        queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        MessageGroupId="example.com:saleorappadditional",
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 3
    assert not EventDelivery.objects.exclude(
        webhook_id=checkout_fully_authorized_webhook.id
    ).exists()

    tax_delivery_call, shipping_methods_call, filter_shipping_call = (
        mocked_send_webhook_request_sync.mock_calls
    )
    shipping_methods_delivery = shipping_methods_call.args[0]
    assert shipping_methods_delivery.webhook_id == shipping_webhook.id
    assert (
        shipping_methods_delivery.event_type
        == WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
    )

    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    )

    tax_delivery = tax_delivery_call.args[0]
    assert tax_delivery.webhook_id == tax_webhook.id

    assert wrapped_call_checkout_info_event.called

    mocked_call_event_including_protected_events.assert_called_once_with(
        plugins_manager.checkout_fully_authorized,
        checkout_with_items,
        webhooks={checkout_fully_authorized_webhook},
    )


@freeze_time("2023-05-31 12:00:01")
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_checkout_events_incorrect_webhook_event(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    checkout_with_items,
    setup_checkout_webhooks,
    django_capture_on_commit_callbacks,
):
    # given
    plugins_manager = get_plugins_manager(allow_replica=False)
    checkout_with_items.price_expiration = timezone.now()
    checkout_with_items.save(update_fields=["price_expiration"])

    mocked_send_webhook_request_sync.return_value = []
    setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_CREATED)

    incorrect_event = WebhookEventAsyncType.ORDER_UPDATED
    # when

    with django_capture_on_commit_callbacks(execute=True):
        with pytest.raises(
            ValueError,
            match=f"Events { {incorrect_event} } not found in CHECKOUT_WEBHOOK_EVENT_MAP.",
        ):
            call_checkout_events(
                plugins_manager,
                [incorrect_event, WebhookEventAsyncType.CHECKOUT_CREATED],
                checkout_with_items,
            )

    # then
    assert not mocked_send_webhook_request_async.called
    assert not mocked_send_webhook_request_sync.called


@freeze_time("2023-05-31 12:00:01")
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.checkout.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_checkout_events_triggers_sync_webhook_when_needed(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    checkout_with_items,
    setup_checkout_webhooks,
    settings,
    django_capture_on_commit_callbacks,
    address,
):
    # given
    plugins_manager = get_plugins_manager(allow_replica=False)
    checkout_with_items.price_expiration = timezone.now()

    # Ensure shipping is set so shipping webhooks are emitted
    checkout_with_items.shipping_address = address
    checkout_with_items.billing_address = address

    checkout_with_items.save(
        update_fields=["price_expiration", "shipping_address", "billing_address"]
    )

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_created_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_CREATED)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        with freeze_time("2023-06-01 12:00:01"):
            call_checkout_events(
                plugins_manager,
                [
                    WebhookEventAsyncType.CHECKOUT_CREATED,
                    WebhookEventAsyncType.CHECKOUT_UPDATED,
                ],
                checkout_with_items,
            )

    # then
    # confirm that event delivery was generated for each async webhook.
    checkout_create_delivery = EventDelivery.objects.get(
        webhook_id=checkout_created_webhook.id
    )
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={
            "event_delivery_id": checkout_create_delivery.id,
            "telemetry_context": ANY,
        },
        queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        MessageGroupId="example.com:saleorappadditional",
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 3
    assert not EventDelivery.objects.exclude(
        webhook_id=checkout_created_webhook.id
    ).exists()

    shipping_methods_call, filter_shipping_call, tax_delivery_call = (
        mocked_send_webhook_request_sync.mock_calls
    )
    shipping_methods_delivery = shipping_methods_call.args[0]
    assert shipping_methods_delivery.webhook_id == shipping_webhook.id
    assert (
        shipping_methods_delivery.event_type
        == WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
    )

    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    )

    tax_delivery = tax_delivery_call.args[0]
    assert tax_delivery.webhook_id == tax_webhook.id

    mocked_call_event_including_protected_events.assert_has_calls(
        [
            call(
                plugins_manager.checkout_created,
                checkout_with_items,
                webhooks={checkout_created_webhook},
            ),
            call(plugins_manager.checkout_updated, checkout_with_items, webhooks=set()),
        ]
    )


@freeze_time("2023-05-31 12:00:01")
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.checkout.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_checkout_events_skips_tax_webhook_when_not_expired(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    checkout_with_items,
    setup_checkout_webhooks,
    settings,
    django_capture_on_commit_callbacks,
    address,
):
    # given
    plugins_manager = get_plugins_manager(allow_replica=False)
    checkout_with_items.price_expiration = timezone.now() + datetime.timedelta(hours=1)

    # Ensure shipping is set so shipping webhooks are emitted
    checkout_with_items.shipping_address = address
    checkout_with_items.billing_address = address

    checkout_with_items.save(
        update_fields=["price_expiration", "billing_address", "shipping_address"]
    )

    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_created_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_CREATED)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        call_checkout_events(
            plugins_manager,
            [
                WebhookEventAsyncType.CHECKOUT_CREATED,
                WebhookEventAsyncType.CHECKOUT_UPDATED,
            ],
            checkout_with_items,
        )

    # then
    # confirm that event delivery was generated for each async webhook.
    checkout_create_delivery = EventDelivery.objects.get(
        webhook_id=checkout_created_webhook.id
    )
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={
            "event_delivery_id": checkout_create_delivery.id,
            "telemetry_context": ANY,
        },
        queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        MessageGroupId="example.com:saleorappadditional",
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 2
    assert not EventDelivery.objects.exclude(
        webhook_id=checkout_created_webhook.id
    ).exists()

    shipping_methods_call, filter_shipping_call = (
        mocked_send_webhook_request_sync.mock_calls
    )
    shipping_methods_delivery = shipping_methods_call.args[0]
    assert shipping_methods_delivery.webhook_id == shipping_webhook.id
    assert (
        shipping_methods_delivery.event_type
        == WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
    )

    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    )

    mocked_call_event_including_protected_events.assert_has_calls(
        [
            call(
                plugins_manager.checkout_created,
                checkout_with_items,
                webhooks={checkout_created_webhook},
            ),
            call(plugins_manager.checkout_updated, checkout_with_items, webhooks=set()),
        ]
    )


@freeze_time("2023-05-31 12:00:01")
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_checkout_events_skip_sync_webhooks_when_async_missing(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    checkout_with_items,
    setup_checkout_webhooks,
    django_capture_on_commit_callbacks,
):
    # given
    plugins_manager = get_plugins_manager(allow_replica=False)
    checkout_with_items.price_expiration = timezone.now()
    checkout_with_items.save(update_fields=["price_expiration"])

    mocked_send_webhook_request_sync.return_value = []

    # setup sync webhooks with async that is not going to be called
    setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_CREATED)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        with freeze_time("2023-06-01 12:00:01"):
            call_checkout_events(
                plugins_manager,
                [
                    WebhookEventAsyncType.CHECKOUT_FULLY_PAID,
                    WebhookEventAsyncType.CHECKOUT_UPDATED,
                ],
                checkout_with_items,
            )

    # then

    assert not mocked_send_webhook_request_async.called
    assert not mocked_send_webhook_request_sync.called


@freeze_time("2023-05-31 12:00:01")
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.checkout.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_checkout_events_only_async_when_sync_missing(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    checkout_with_items,
    permission_manage_checkouts,
    settings,
    webhook,
    django_capture_on_commit_callbacks,
):
    # given
    plugins_manager = get_plugins_manager(allow_replica=False)
    checkout_with_items.price_expiration = timezone.now()
    checkout_with_items.save(update_fields=["price_expiration"])

    webhook.events.create(event_type=WebhookEventAsyncType.CHECKOUT_CREATED)
    webhook.app.permissions.add(permission_manage_checkouts)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        with freeze_time("2023-06-01 12:00:01"):
            call_checkout_events(
                plugins_manager,
                [
                    WebhookEventAsyncType.CHECKOUT_CREATED,
                    WebhookEventAsyncType.CHECKOUT_UPDATED,
                ],
                checkout_with_items,
            )

    # then

    # confirm that event delivery was generated for each async webhook.
    checkout_create_delivery = EventDelivery.objects.get(webhook_id=webhook.id)

    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={
            "event_delivery_id": checkout_create_delivery.id,
            "telemetry_context": ANY,
        },
        queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        MessageGroupId="example.com:saleorapptest",
    )
    assert not mocked_send_webhook_request_sync.called
    mocked_call_event_including_protected_events.assert_has_calls(
        [
            call(
                plugins_manager.checkout_created,
                checkout_with_items,
                webhooks={webhook},
            ),
            call(plugins_manager.checkout_updated, checkout_with_items, webhooks=set()),
        ]
    )


@pytest.mark.parametrize(
    ("gift_card_balance", "expected_authorize_status", "expected_charge_status"),
    [
        (0, CheckoutAuthorizeStatus.PARTIAL, CheckoutChargeStatus.PARTIAL),
        (10, CheckoutAuthorizeStatus.PARTIAL, CheckoutChargeStatus.PARTIAL),
        (20, CheckoutAuthorizeStatus.FULL, CheckoutChargeStatus.FULL),
        (40, CheckoutAuthorizeStatus.FULL, CheckoutChargeStatus.OVERCHARGED),
    ],
)
def test_transaction_amounts_for_checkout_updated_without_price_recalculation_considers_gift_cards_balance_when_updating_checkout_payment_status(
    checkout_with_gift_card,
    gift_card_balance,
    expected_authorize_status,
    expected_charge_status,
    transaction_item_generator,
):
    # given
    checkout = checkout_with_gift_card
    gift_card = checkout.gift_cards.first()
    gift_card.initial_balance_amount = Decimal(gift_card_balance)
    gift_card.current_balance_amount = Decimal(gift_card_balance)
    gift_card.save()

    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    address = checkout.shipping_address or checkout.billing_address

    assert checkout.authorize_status == CheckoutAuthorizeStatus.NONE
    assert checkout.charge_status == CheckoutChargeStatus.NONE

    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        charged_value=Decimal(10),
    )

    total = calculate_checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    assert total.gross.amount == Decimal(30)

    # when
    transaction_amounts_for_checkout_updated_without_price_recalculation(
        transaction, checkout, manager, None, None
    )

    # then
    checkout.refresh_from_db()
    assert checkout.authorize_status == expected_authorize_status
    assert checkout.charge_status == expected_charge_status


@freeze_time("2023-05-31 12:00:01")
@patch(
    "saleor.graphql.checkout.types.PregeneratedCheckoutTaxPayloadsByCheckoutTokenLoader",
    wraps=PregeneratedCheckoutTaxPayloadsByCheckoutTokenLoader,
)
@patch(
    "saleor.graphql.checkout.types."
    "PregeneratedCheckoutFilterShippingMethodPayloadsByCheckoutTokenLoader",
    wraps=PregeneratedCheckoutFilterShippingMethodPayloadsByCheckoutTokenLoader,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.checkout.actions.call_event_including_protected_events",
    wraps=call_event_including_protected_events,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_call_checkout_events_skips_pregenerated_payloads_in_non_deferred_async_webhooks(
    mocked_call_event_including_protected_events,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    mocked_pregenerated_tax_payload_loader,
    mocked_pregenerated_filter_shipping_payload_loader,
    checkout_with_items,
    setup_checkout_webhooks,
    settings,
    django_capture_on_commit_callbacks,
    address,
    caplog,
):
    # given
    plugins_manager = get_plugins_manager(allow_replica=False)
    checkout_with_items.price_expiration = timezone.now()

    # Ensure shipping is set so shipping webhooks are emitted
    checkout_with_items.shipping_address = address
    checkout_with_items.billing_address = address

    checkout_with_items.save(
        update_fields=["price_expiration", "shipping_address", "billing_address"]
    )

    mocked_send_webhook_request_sync.return_value = []
    setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_METADATA_UPDATED)

    # when
    with django_capture_on_commit_callbacks(execute=True):
        with freeze_time("2023-06-01 12:00:01"):
            call_checkout_events(
                plugins_manager,
                [
                    WebhookEventAsyncType.CHECKOUT_METADATA_UPDATED,
                ],
                checkout_with_items,
            )

    # then
    # Make sure that we didnt recieve notification about missing payloads for sync webhooks
    # and make sure, that pregenerated payload loaders were called. Pregenerated dataloaders
    # should skip the payload when called inside non-deferred webhook processing. This is skipped
    # as all sync webhooks are called inside the mutation.
    assert mocked_pregenerated_tax_payload_loader.called
    assert mocked_pregenerated_filter_shipping_payload_loader.called
    assert "Subscription did not return a payload." not in caplog.text
