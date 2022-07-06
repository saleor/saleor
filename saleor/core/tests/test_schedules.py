from datetime import timedelta

from django.utils import timezone
from freezegun import freeze_time

from ...discount.models import Sale
from ..schedules import sale_webhook_schedule


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
    schedule = sale_webhook_schedule()
    sale.started_notification_sent = True
    sale.ended_notification_sent = True

    new_sale.started_notification_sent = True
    new_sale.ended_notification_sent = True

    Sale.objects.bulk_update(
        [sale, new_sale], ["started_notification_sent", "ended_notification_sent"]
    )

    # when
    is_due, next_run = schedule.is_due(timezone.now() - timedelta(minutes=1))

    # then
    assert is_due is False
    assert next_run == schedule.initial_timedelta.total_seconds()


def test_is_due_sale_started_to_notify_and_not_upcoming_sale(sale, new_sale):
    # given
    schedule = sale_webhook_schedule()
    sale.start_date = timezone.now() - timedelta(minutes=5)
    sale.started_notification_sent = False
    sale.ended_notification_sent = True

    new_sale.started_notification_sent = True
    new_sale.ended_notification_sent = True

    Sale.objects.bulk_update(
        [sale, new_sale],
        ["start_date", "started_notification_sent", "ended_notification_sent"],
    )

    # when
    is_due, next_run = schedule.is_due(timezone.now() - timedelta(minutes=1))

    # then
    assert is_due is True
    assert next_run == schedule.initial_timedelta.total_seconds()


def test_is_due_sale_ended_to_notify_and_not_upcoming_sale(sale, new_sale):
    # given
    schedule = sale_webhook_schedule()
    sale.started_notification_sent = True
    sale.ended_notification_sent = True

    new_sale.end_date = timezone.now() - timedelta(minutes=5)
    new_sale.started_notification_sent = True
    new_sale.ended_notification_sent = False

    Sale.objects.bulk_update(
        [sale, new_sale],
        ["end_date", "started_notification_sent", "ended_notification_sent"],
    )

    # when
    is_due, next_run = schedule.is_due(timezone.now() - timedelta(minutes=1))

    # then
    assert is_due is True
    assert next_run == schedule.initial_timedelta.total_seconds()


@freeze_time("2020-10-10 12:00:00")
def test_is_due_sale_started_to_notify_and_upcoming_sale(sale, new_sale):
    # given
    schedule = sale_webhook_schedule()
    sale.start_date = timezone.now() - timedelta(minutes=5)
    sale.started_notification_sent = False
    sale.ended_notification_sent = True

    time_delta = timedelta(seconds=44)
    new_sale.end_date = timezone.now() + time_delta
    new_sale.started_notification_sent = True
    new_sale.ended_notification_sent = False

    Sale.objects.bulk_update(
        [sale, new_sale],
        [
            "start_date",
            "end_date",
            "started_notification_sent",
            "ended_notification_sent",
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
    schedule = sale_webhook_schedule()
    sale.started_notification_sent = True
    sale.ended_notification_sent = True

    time_delta = timedelta(seconds=44)
    new_sale.end_date = timezone.now() + time_delta
    new_sale.started_notification_sent = True
    new_sale.ended_notification_sent = False

    Sale.objects.bulk_update(
        [sale, new_sale],
        ["end_date", "started_notification_sent", "ended_notification_sent"],
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
    schedule = sale_webhook_schedule()
    sale.started_notification_sent = True
    sale.ended_notification_sent = True

    time_delta = timedelta(minutes=3)
    new_sale.end_date = timezone.now() + time_delta
    new_sale.started_notification_sent = True
    new_sale.ended_notification_sent = False

    Sale.objects.bulk_update(
        [sale, new_sale],
        ["end_date", "started_notification_sent", "ended_notification_sent"],
    )

    # when
    is_due, next_run = schedule.is_due(timezone.now() - timedelta(minutes=1))

    # then
    assert is_due is False
    assert next_run == schedule.initial_timedelta.total_seconds()
