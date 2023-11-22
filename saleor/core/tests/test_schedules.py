from datetime import datetime, timedelta
from decimal import Decimal

import pytz
from django.utils import timezone
from freezegun import freeze_time

from ...checkout.actions import transaction_amounts_for_checkout_updated
from ...discount.models import Sale
from ..schedules import (
    sale_webhook_schedule,
    transaction_release_funds_for_checkout_schedule,
)


@freeze_time("2020-10-10 12:00:00")
def test_sale_webhook_schedule_remaining_estimate_initial_state():
    # given
    schedule = sale_webhook_schedule()

    # when
    remaining = schedule.remaining_estimate(last_run_at=timezone.now())

    # then
    assert remaining == schedule.initial_timedelta


@freeze_time("2020-10-10 12:00:00")
def test_sale_webhook_schedule_remaining_estimate():
    # given
    schedule = sale_webhook_schedule()
    time_delta = timedelta(seconds=30)

    # when
    remaining = schedule.remaining_estimate(last_run_at=timezone.now() - time_delta)

    # then
    assert remaining == schedule.initial_timedelta - time_delta


def test_is_due_not_sale_to_notify_about_not_upcoming_sale(sale, new_sale):
    # given
    now = timezone.now()
    schedule = sale_webhook_schedule()
    sale.start_date = now - timedelta(days=1)
    sale.notification_sent_datetime = now - timedelta(minutes=2)

    new_sale.start_date = now - timedelta(days=2)
    new_sale.notification_sent_datetime = now - timedelta(minutes=2)

    Sale.objects.bulk_update(
        [sale, new_sale], ["start_date", "notification_sent_datetime"]
    )

    # when
    is_due, next_run = schedule.is_due(timezone.now() - timedelta(minutes=1))

    # then
    assert is_due is False
    assert next_run == schedule.initial_timedelta.total_seconds()


def test_is_due_sale_started_to_notify_and_not_upcoming_sale(sale, new_sale):
    # given
    now = timezone.now()
    schedule = sale_webhook_schedule()
    sale.start_date = now - timedelta(minutes=5)
    sale.notification_sent_datetime = now - timedelta(minutes=6)

    new_sale.start_date = now - timedelta(days=2)
    new_sale.notification_sent_datetime = now - timedelta(minutes=2)

    Sale.objects.bulk_update(
        [sale, new_sale],
        ["start_date", "notification_sent_datetime"],
    )

    # when
    is_due, next_run = schedule.is_due(timezone.now() - timedelta(minutes=1))

    # then
    assert is_due is True
    assert next_run == schedule.initial_timedelta.total_seconds()


def test_is_due_sale_ended_to_notify_and_not_upcoming_sale(sale, new_sale):
    # given
    now = timezone.now()
    schedule = sale_webhook_schedule()

    sale.start_date = now - timedelta(days=2)
    sale.notification_sent_datetime = now - timedelta(minutes=2)

    new_sale.start_date = now - timedelta(days=1)
    new_sale.end_date = now - timedelta(minutes=5)
    new_sale.notification_sent_datetime = now - timedelta(minutes=6)

    Sale.objects.bulk_update(
        [sale, new_sale],
        [
            "start_date",
            "end_date",
            "notification_sent_datetime",
        ],
    )

    # when
    is_due, next_run = schedule.is_due(timezone.now() - timedelta(minutes=1))

    # then
    assert is_due is True
    assert next_run == schedule.initial_timedelta.total_seconds()


@freeze_time("2020-10-10 12:00:00")
def test_is_due_sale_started_to_notify_and_upcoming_sale(sale, new_sale):
    # given
    now = timezone.now()
    schedule = sale_webhook_schedule()

    sale.start_date = now - timedelta(minutes=5)
    sale.notification_sent_datetime = now - timedelta(minutes=6)

    time_delta = timedelta(seconds=44)
    new_sale.start_date = now - timedelta(minutes=7)
    new_sale.end_date = timezone.now() + time_delta
    new_sale.notification_sent_datetime = now - timedelta(minutes=6)

    Sale.objects.bulk_update(
        [sale, new_sale],
        [
            "start_date",
            "end_date",
            "notification_sent_datetime",
        ],
    )

    # when
    is_due, next_run = schedule.is_due(timezone.now() - timedelta(minutes=1))

    # then
    assert is_due is True
    assert next_run == time_delta.total_seconds()


@freeze_time("2020-10-10 12:00:00")
def test_is_due_no_sale_to_notify_about_and_upcoming_sale_exists(sale, new_sale):
    # given
    now = timezone.now()
    schedule = sale_webhook_schedule()

    sale.start_date = now - timedelta(minutes=8)
    sale.notification_sent_datetime = now - timedelta(minutes=6)

    time_delta = timedelta(seconds=22)
    new_sale.start_date = now - timedelta(minutes=7)
    new_sale.end_date = timezone.now() + time_delta
    new_sale.notification_sent_datetime = now - timedelta(minutes=6)

    Sale.objects.bulk_update(
        [sale, new_sale],
        ["start_date", "end_date", "notification_sent_datetime"],
    )

    # when
    is_due, next_run = schedule.is_due(timezone.now() - timedelta(minutes=1))

    # then
    assert is_due is False
    assert next_run == time_delta.total_seconds()


@freeze_time("2020-10-10 12:00:00")
def test_is_due_no_sale_to_notify_about_and_upcoming_sale_exists_initial_time_returned(
    sale, new_sale
):
    # given
    now = timezone.now()
    schedule = sale_webhook_schedule()

    sale.start_date = now - timedelta(minutes=8)
    sale.notification_sent_datetime = now - timedelta(minutes=6)

    time_delta = timedelta(minutes=3)
    new_sale.start_date = now - timedelta(minutes=7)
    new_sale.end_date = timezone.now() + time_delta
    new_sale.notification_sent_datetime = now - timedelta(minutes=6)

    Sale.objects.bulk_update(
        [sale, new_sale],
        ["end_date", "notification_sent_datetime"],
    )

    # when
    is_due, next_run = schedule.is_due(timezone.now() - timedelta(minutes=1))

    # then
    assert is_due is False
    assert next_run == schedule.initial_timedelta.total_seconds()


@freeze_time("2020-10-10 12:00:00")
def test_transaction_release_funds_for_checkout_remaining_estimate_initial_state():
    # given
    schedule = transaction_release_funds_for_checkout_schedule()

    # when
    remaining = schedule.remaining_estimate(last_run_at=timezone.now())

    # then
    assert remaining == schedule.initial_timedelta


@freeze_time("2020-10-10 12:00:00")
def test_transaction_release_funds_for_checkout_remaining_estimate():
    # given
    schedule = transaction_release_funds_for_checkout_schedule()
    time_delta = timedelta(seconds=30)

    # when
    remaining = schedule.remaining_estimate(last_run_at=timezone.now() - time_delta)

    # then
    assert remaining == schedule.initial_timedelta - time_delta


@freeze_time("2020-10-10 12:00:00")
def test_transaction_release_funds_for_checkout_not_refundable(
    checkout, transaction_item_generator, plugins_manager
):
    # given
    schedule = transaction_release_funds_for_checkout_schedule()
    with freeze_time("2020-10-10 04:00:00"):
        now = datetime.now(pytz.UTC)
        transaction_item = transaction_item_generator(
            checkout_id=checkout.pk, charged_value=Decimal(100)
        )
        transaction_amounts_for_checkout_updated(transaction_item, plugins_manager)
        checkout.automatically_refundable = False
        checkout.last_change = now
        checkout.save(update_fields=["last_change", "automatically_refundable"])

    # when
    is_due, next_run = schedule.is_due(timezone.now() - timedelta(minutes=1))

    # then
    assert is_due is False
    assert next_run == schedule.initial_timedelta.total_seconds()


@freeze_time("2020-10-10 12:00:00")
def test_transaction_release_funds_for_checkout_with_new_last_change(
    checkout, transaction_item_generator, plugins_manager
):
    # given
    schedule = transaction_release_funds_for_checkout_schedule()
    with freeze_time("2020-10-10 04:00:00"):
        transaction_item = transaction_item_generator(
            checkout_id=checkout.pk, charged_value=Decimal(100)
        )
        transaction_amounts_for_checkout_updated(transaction_item, plugins_manager)
        checkout.automatically_refundable = True
    checkout.last_change = datetime.now(pytz.UTC)
    checkout.save(update_fields=["last_change", "automatically_refundable"])

    # when
    is_due, next_run = schedule.is_due(timezone.now() - timedelta(minutes=1))

    # then
    assert is_due is False
    assert next_run == schedule.initial_timedelta.total_seconds()


@freeze_time("2020-10-10 12:00:00")
def test_transaction_release_funds_for_checkout_with_new_transaction(
    checkout, transaction_item_generator, plugins_manager
):
    # given
    schedule = transaction_release_funds_for_checkout_schedule()
    transaction_item = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(100)
    )
    with freeze_time("2020-10-10 04:00:00"):
        transaction_amounts_for_checkout_updated(transaction_item, plugins_manager)
        checkout.automatically_refundable = True
        checkout.last_change = datetime.now(pytz.UTC)
        checkout.save(update_fields=["last_change", "automatically_refundable"])

    # when
    is_due, next_run = schedule.is_due(timezone.now() - timedelta(minutes=1))

    # then
    assert is_due is False
    assert next_run == schedule.initial_timedelta.total_seconds()


@freeze_time("2020-10-10 12:00:00")
def test_transaction_release_funds_for_checkout_transaction_without_funds(
    checkout, transaction_item_generator, plugins_manager
):
    # given
    schedule = transaction_release_funds_for_checkout_schedule()
    with freeze_time("2020-10-10 04:00:00"):
        now = datetime.now(pytz.UTC)
        transaction_item = transaction_item_generator(
            checkout_id=checkout.pk,
        )
        transaction_amounts_for_checkout_updated(transaction_item, plugins_manager)
        checkout.automatically_refundable = True
        checkout.last_change = now
        checkout.save(update_fields=["last_change", "automatically_refundable"])

    # when
    is_due, next_run = schedule.is_due(timezone.now() - timedelta(minutes=1))

    # then
    assert is_due is False
    assert next_run == schedule.initial_timedelta.total_seconds()


@freeze_time("2020-10-10 12:00:00")
def test_transaction_release_funds_for_checkout_transaction_with_authorized_funds(
    checkout, transaction_item_generator, plugins_manager
):
    # given
    schedule = transaction_release_funds_for_checkout_schedule()
    with freeze_time("2020-10-10 04:00:00"):
        now = datetime.now(pytz.UTC)
        transaction_item = transaction_item_generator(
            checkout_id=checkout.pk,
            authorized_value=Decimal(100),
        )
        transaction_amounts_for_checkout_updated(transaction_item, plugins_manager)
        checkout.automatically_refundable = True
        checkout.last_change = now
        checkout.save(update_fields=["last_change", "automatically_refundable"])

    # when
    is_due, next_run = schedule.is_due(timezone.now() - timedelta(minutes=1))

    # then
    assert is_due is True
    assert next_run == schedule.initial_timedelta.total_seconds()


@freeze_time("2020-10-10 12:00:00")
def test_transaction_release_funds_for_checkout_transaction_with_charged_funds(
    checkout, transaction_item_generator, plugins_manager
):
    # given
    schedule = transaction_release_funds_for_checkout_schedule()
    with freeze_time("2020-10-10 04:00:00"):
        now = datetime.now(pytz.UTC)
        transaction_item = transaction_item_generator(
            checkout_id=checkout.pk,
            charged_value=Decimal(100),
        )
        transaction_amounts_for_checkout_updated(transaction_item, plugins_manager)
        checkout.automatically_refundable = True
        checkout.last_change = now
        checkout.save(update_fields=["last_change", "automatically_refundable"])

    # when
    is_due, next_run = schedule.is_due(timezone.now() - timedelta(minutes=1))

    # then
    assert is_due is True
    assert next_run == schedule.initial_timedelta.total_seconds()
