import datetime
from unittest import mock

import pytest
from django.utils import timezone
from freezegun import freeze_time

from ...core.models import EventDelivery
from ...graphql.webhook.subscription_query import SubscriptionQuery
from ...webhook.event_types import WebhookEventAsyncType
from .. import CheckoutAuthorizeStatus
from ..models import Checkout, CheckoutLine
from ..tasks import trigger_abandoned_checkout_events_task

THRESHOLD_MINUTES = 30

TRIGGER_PATH = (
    "saleor.checkout.webhooks.checkout_abandoned."
    "trigger_webhooks_async_for_multiple_objects"
)


@pytest.fixture
def abandoned_checkout_channel(channel_USD):
    channel_USD.abandoned_checkout_enabled = True
    channel_USD.abandoned_checkout_threshold = THRESHOLD_MINUTES
    channel_USD.abandoned_checkout_cut_off_date = timezone.now() - datetime.timedelta(
        days=1
    )
    channel_USD.save(
        update_fields=[
            "abandoned_checkout_enabled",
            "abandoned_checkout_threshold",
            "abandoned_checkout_cut_off_date",
        ]
    )
    return channel_USD


@pytest.fixture
def idle_checkout(checkout_with_item, abandoned_checkout_channel):
    set_last_change(
        checkout_with_item,
        timezone.now() - datetime.timedelta(minutes=THRESHOLD_MINUTES + 1),
    )
    return checkout_with_item


def set_last_change(checkout, last_change):
    # `update()` bypasses `auto_now` on `last_change`.
    Checkout.objects.filter(pk=checkout.pk).update(last_change=last_change)
    checkout.refresh_from_db(fields=["last_change"])


def emitted_checkouts(mocked_trigger):
    return [
        payload.subscribable_object
        for call in mocked_trigger.call_args_list
        for payload in call.kwargs["webhook_payloads_data"]
    ]


@mock.patch(TRIGGER_PATH)
def test_emits_event_for_idle_checkout(
    mocked_trigger, idle_checkout, subscription_checkout_abandoned_webhook
):
    # given
    now = timezone.now()

    # when
    with freeze_time(now):
        trigger_abandoned_checkout_events_task()

    # then
    assert mocked_trigger.call_count == 1
    args, _ = mocked_trigger.call_args
    assert args == (
        WebhookEventAsyncType.CHECKOUT_ABANDONED,
        [subscription_checkout_abandoned_webhook],
    )
    assert emitted_checkouts(mocked_trigger) == [idle_checkout]
    last_change = idle_checkout.last_change
    idle_checkout.refresh_from_db(fields=["abandoned_notified_at", "last_change"])
    assert idle_checkout.abandoned_notified_at == now
    assert idle_checkout.last_change == last_change


@pytest.mark.parametrize(
    ("authorize_status", "expected_emitted"),
    [
        (CheckoutAuthorizeStatus.NONE, True),
        (CheckoutAuthorizeStatus.PARTIAL, True),
        (CheckoutAuthorizeStatus.FULL, False),
    ],
)
@mock.patch(TRIGGER_PATH)
def test_authorize_status(
    mocked_trigger,
    authorize_status,
    expected_emitted,
    idle_checkout,
    subscription_checkout_abandoned_webhook,
):
    # given
    Checkout.objects.filter(pk=idle_checkout.pk).update(
        authorize_status=authorize_status
    )

    # when
    trigger_abandoned_checkout_events_task()

    # then
    expected = [idle_checkout] if expected_emitted else []
    assert emitted_checkouts(mocked_trigger) == expected


@mock.patch(TRIGGER_PATH)
def test_skips_checkout_modified_within_threshold(
    mocked_trigger, idle_checkout, subscription_checkout_abandoned_webhook
):
    # given
    set_last_change(
        idle_checkout,
        timezone.now() - datetime.timedelta(minutes=THRESHOLD_MINUTES - 1),
    )

    # when
    trigger_abandoned_checkout_events_task()

    # then
    mocked_trigger.assert_not_called()
    idle_checkout.refresh_from_db(fields=["abandoned_notified_at"])
    assert idle_checkout.abandoned_notified_at is None


@mock.patch(TRIGGER_PATH)
def test_skips_checkout_modified_before_cut_off_date(
    mocked_trigger,
    idle_checkout,
    abandoned_checkout_channel,
    subscription_checkout_abandoned_webhook,
):
    # given
    set_last_change(
        idle_checkout,
        abandoned_checkout_channel.abandoned_checkout_cut_off_date
        - datetime.timedelta(minutes=1),
    )

    # when
    trigger_abandoned_checkout_events_task()

    # then
    mocked_trigger.assert_not_called()


@mock.patch(TRIGGER_PATH)
def test_skips_channel_with_setting_disabled(
    mocked_trigger,
    idle_checkout,
    abandoned_checkout_channel,
    subscription_checkout_abandoned_webhook,
):
    # given
    abandoned_checkout_channel.abandoned_checkout_enabled = False
    abandoned_checkout_channel.save(update_fields=["abandoned_checkout_enabled"])

    # when
    trigger_abandoned_checkout_events_task()

    # then
    mocked_trigger.assert_not_called()


@mock.patch(TRIGGER_PATH)
def test_skips_when_no_webhook_subscribed(mocked_trigger, idle_checkout):
    # when
    trigger_abandoned_checkout_events_task()

    # then
    mocked_trigger.assert_not_called()
    idle_checkout.refresh_from_db(fields=["abandoned_notified_at"])
    assert idle_checkout.abandoned_notified_at is None


@pytest.mark.parametrize(
    ("email", "has_user", "expected_emitted"),
    [
        (None, False, False),
        ("", False, False),
        (None, True, True),
        ("customer@example.com", False, True),
    ],
)
@mock.patch(TRIGGER_PATH)
def test_requires_customer_contact(
    mocked_trigger,
    email,
    has_user,
    expected_emitted,
    idle_checkout,
    customer_user,
    subscription_checkout_abandoned_webhook,
):
    # given
    Checkout.objects.filter(pk=idle_checkout.pk).update(
        email=email, user=customer_user if has_user else None
    )

    # when
    trigger_abandoned_checkout_events_task()

    # then
    expected = [idle_checkout] if expected_emitted else []
    assert emitted_checkouts(mocked_trigger) == expected


@mock.patch(TRIGGER_PATH)
def test_skips_checkout_without_lines(
    mocked_trigger, idle_checkout, subscription_checkout_abandoned_webhook
):
    # given
    idle_checkout.lines.all().delete()

    # when
    trigger_abandoned_checkout_events_task()

    # then
    mocked_trigger.assert_not_called()


@mock.patch(TRIGGER_PATH)
def test_emits_once_per_idle_period(
    mocked_trigger, idle_checkout, subscription_checkout_abandoned_webhook
):
    # given
    trigger_abandoned_checkout_events_task()
    assert emitted_checkouts(mocked_trigger) == [idle_checkout]
    mocked_trigger.reset_mock()

    # when
    trigger_abandoned_checkout_events_task()

    # then
    mocked_trigger.assert_not_called()


@mock.patch(TRIGGER_PATH)
def test_emits_again_after_checkout_modified(
    mocked_trigger, idle_checkout, subscription_checkout_abandoned_webhook
):
    # given
    notified_at = timezone.now() - datetime.timedelta(hours=2)
    Checkout.objects.filter(pk=idle_checkout.pk).update(
        abandoned_notified_at=notified_at
    )
    set_last_change(idle_checkout, notified_at + datetime.timedelta(minutes=1))

    # when
    trigger_abandoned_checkout_events_task()

    # then
    assert emitted_checkouts(mocked_trigger) == [idle_checkout]


@mock.patch(TRIGGER_PATH)
def test_respects_webhook_channel_filter(
    mocked_trigger,
    idle_checkout,
    channel_PLN,
    subscription_webhook,
):
    # given
    query = """
    subscription {
      checkoutAbandoned(channels: ["%s"]) {
        checkout { id }
      }
    }
    """
    query = query % channel_PLN.slug
    webhook = subscription_webhook(query, WebhookEventAsyncType.CHECKOUT_ABANDONED)
    webhook.filterable_channel_slugs = SubscriptionQuery(
        query
    ).get_filterable_channel_slugs()
    webhook.save(update_fields=["filterable_channel_slugs"])
    assert webhook.filterable_channel_slugs == [channel_PLN.slug]

    # when
    trigger_abandoned_checkout_events_task()

    # then
    mocked_trigger.assert_not_called()
    idle_checkout.refresh_from_db(fields=["abandoned_notified_at"])
    assert idle_checkout.abandoned_notified_at is None


def create_checkout_like(checkout, last_change, email):
    line = checkout.lines.get()
    new_checkout = Checkout.objects.create(
        channel=checkout.channel, currency=checkout.currency, email=email
    )
    CheckoutLine.objects.create(
        checkout=new_checkout,
        variant=line.variant,
        quantity=line.quantity,
        undiscounted_unit_price_amount=line.undiscounted_unit_price_amount,
    )
    set_last_change(new_checkout, last_change)
    return new_checkout


@mock.patch(TRIGGER_PATH)
def test_processes_oldest_checkouts_first_up_to_batch_size(
    mocked_trigger,
    idle_checkout,
    subscription_checkout_abandoned_webhook,
    settings,
):
    # given
    settings.ABANDONED_CHECKOUT_BATCH_SIZE = 1
    older_checkout = create_checkout_like(
        idle_checkout,
        idle_checkout.last_change - datetime.timedelta(minutes=1),
        idle_checkout.email,
    )

    # when
    trigger_abandoned_checkout_events_task()
    first_run = emitted_checkouts(mocked_trigger)
    mocked_trigger.reset_mock()
    trigger_abandoned_checkout_events_task()
    second_run = emitted_checkouts(mocked_trigger)

    # then
    assert first_run == [older_checkout]
    assert second_run == [idle_checkout]


@mock.patch(TRIGGER_PATH)
def test_cursor_moves_past_not_eligible_checkouts(
    mocked_trigger,
    idle_checkout,
    abandoned_checkout_channel,
    subscription_checkout_abandoned_webhook,
    settings,
):
    # given
    settings.ABANDONED_CHECKOUT_SCAN_BATCH_SIZE = 1
    anonymous_checkout = create_checkout_like(
        idle_checkout,
        idle_checkout.last_change - datetime.timedelta(minutes=1),
        email=None,
    )

    # when
    trigger_abandoned_checkout_events_task()
    first_run = emitted_checkouts(mocked_trigger)
    abandoned_checkout_channel.refresh_from_db(
        fields=["abandoned_checkout_processed_until"]
    )
    cursor_after_first_run = (
        abandoned_checkout_channel.abandoned_checkout_processed_until
    )
    mocked_trigger.reset_mock()
    trigger_abandoned_checkout_events_task()
    second_run = emitted_checkouts(mocked_trigger)

    # then
    assert first_run == []
    assert cursor_after_first_run == anonymous_checkout.last_change
    assert second_run == [idle_checkout]


@mock.patch(TRIGGER_PATH)
def test_skips_checkouts_before_cursor(
    mocked_trigger,
    idle_checkout,
    abandoned_checkout_channel,
    subscription_checkout_abandoned_webhook,
):
    # given
    abandoned_checkout_channel.abandoned_checkout_processed_until = (
        idle_checkout.last_change + datetime.timedelta(seconds=1)
    )
    abandoned_checkout_channel.save(
        update_fields=["abandoned_checkout_processed_until"]
    )

    # when
    trigger_abandoned_checkout_events_task()

    # then
    mocked_trigger.assert_not_called()


@mock.patch(TRIGGER_PATH)
def test_batch_limit_does_not_skip_checkouts_with_same_last_change(
    mocked_trigger,
    idle_checkout,
    subscription_checkout_abandoned_webhook,
    settings,
):
    # given
    settings.ABANDONED_CHECKOUT_BATCH_SIZE = 1
    twin_checkout = create_checkout_like(
        idle_checkout, idle_checkout.last_change, idle_checkout.email
    )

    # when
    trigger_abandoned_checkout_events_task()
    first_run = emitted_checkouts(mocked_trigger)
    mocked_trigger.reset_mock()
    trigger_abandoned_checkout_events_task()
    second_run = emitted_checkouts(mocked_trigger)

    # then
    assert {*first_run, *second_run} == {idle_checkout, twin_checkout}
    assert len(first_run) == len(second_run) == 1


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.generate_deferred_payloads"
    ".apply_async"
)
def test_creates_event_delivery(
    mocked_generate_deferred_payloads,
    idle_checkout,
    subscription_checkout_abandoned_webhook,
):
    # when
    trigger_abandoned_checkout_events_task()

    # then
    delivery = EventDelivery.objects.get()
    assert delivery.event_type == WebhookEventAsyncType.CHECKOUT_ABANDONED
    assert delivery.webhook == subscription_checkout_abandoned_webhook
    mocked_generate_deferred_payloads.assert_called_once()
    deferred_payload_data = mocked_generate_deferred_payloads.call_args.kwargs[
        "kwargs"
    ]["deferred_payload_data"]
    assert deferred_payload_data["object_id"] == idle_checkout.pk
