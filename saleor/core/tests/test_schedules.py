from datetime import timedelta

from django.utils import timezone
from freezegun import freeze_time

from ...discount.models import Promotion
from ..schedules import promotion_webhook_schedule


@freeze_time("2020-10-10 12:00:00")
def test_promotion_webhook_schedule_remaining_estimate_initial_state():
    # given
    schedule = promotion_webhook_schedule()

    # when
    remaining = schedule.remaining_estimate(last_run_at=timezone.now())

    # then
    assert remaining == schedule.initial_timedelta


@freeze_time("2020-10-10 12:00:00")
def test_promotion_webhook_schedule_remaining_estimate():
    # given
    schedule = promotion_webhook_schedule()
    time_delta = timedelta(seconds=30)

    # when
    remaining = schedule.remaining_estimate(last_run_at=timezone.now() - time_delta)

    # then
    assert remaining == schedule.initial_timedelta - time_delta


def test_is_due_not_promotion_to_notify_about_not_upcoming_promotion(promotion_list):
    # given
    now = timezone.now()
    schedule = promotion_webhook_schedule()

    promotion_1 = promotion_list[0]
    promotion_2 = promotion_list[1]

    promotion_1.start_date = now - timedelta(days=1)
    promotion_1.last_notification_scheduled_at = now - timedelta(minutes=2)

    promotion_2.start_date = now - timedelta(days=2)
    promotion_2.last_notification_scheduled_at = now - timedelta(minutes=2)

    Promotion.objects.bulk_update(
        [promotion_1, promotion_2], ["start_date", "last_notification_scheduled_at"]
    )

    # when
    is_due, next_run = schedule.is_due(timezone.now() - timedelta(minutes=1))

    # then
    assert is_due is False
    assert next_run == schedule.initial_timedelta.total_seconds()


def test_is_due_promotion_started_to_notify_and_not_upcoming_promotion(promotion_list):
    # given
    now = timezone.now()
    schedule = promotion_webhook_schedule()

    promotion_1 = promotion_list[0]
    promotion_2 = promotion_list[1]

    promotion_1.start_date = now - timedelta(minutes=5)
    promotion_1.last_notification_scheduled_at = now - timedelta(minutes=6)

    promotion_2.start_date = now - timedelta(days=2)
    promotion_2.last_notification_scheduled_at = now - timedelta(minutes=2)

    Promotion.objects.bulk_update(
        [promotion_1, promotion_2],
        ["start_date", "last_notification_scheduled_at"],
    )

    # when
    is_due, next_run = schedule.is_due(timezone.now() - timedelta(minutes=1))

    # then
    assert is_due is True
    assert next_run == schedule.initial_timedelta.total_seconds()


def test_is_due_promotion_ended_to_notify_and_not_upcoming_promotion(promotion_list):
    # given
    now = timezone.now()
    schedule = promotion_webhook_schedule()

    promotion_1 = promotion_list[0]
    promotion_2 = promotion_list[1]

    promotion_1.start_date = now - timedelta(days=2)
    promotion_1.last_notification_scheduled_at = now - timedelta(minutes=2)

    promotion_2.start_date = now - timedelta(days=1)
    promotion_2.end_date = now - timedelta(minutes=5)
    promotion_2.last_notification_scheduled_at = now - timedelta(minutes=6)

    Promotion.objects.bulk_update(
        [promotion_1, promotion_2],
        [
            "start_date",
            "end_date",
            "last_notification_scheduled_at",
        ],
    )

    # when
    is_due, next_run = schedule.is_due(timezone.now() - timedelta(minutes=1))

    # then
    assert is_due is True
    assert next_run == schedule.initial_timedelta.total_seconds()


@freeze_time("2020-10-10 12:00:00")
def test_is_due_promotion_started_to_notify_and_upcoming_promotion(promotion_list):
    # given
    now = timezone.now()
    schedule = promotion_webhook_schedule()

    promotion_1 = promotion_list[0]
    promotion_2 = promotion_list[1]

    promotion_1.start_date = now - timedelta(minutes=5)
    promotion_1.last_notification_scheduled_at = now - timedelta(minutes=6)

    time_delta = timedelta(seconds=44)
    promotion_2.start_date = now - timedelta(minutes=7)
    promotion_2.end_date = timezone.now() + time_delta
    promotion_2.last_notification_scheduled_at = now - timedelta(minutes=6)

    Promotion.objects.bulk_update(
        [promotion_1, promotion_2],
        [
            "start_date",
            "end_date",
            "last_notification_scheduled_at",
        ],
    )

    # when
    is_due, next_run = schedule.is_due(timezone.now() - timedelta(minutes=1))

    # then
    assert is_due is True
    assert next_run == time_delta.total_seconds()


@freeze_time("2020-10-10 12:00:00")
def test_is_due_no_promotion_to_notify_about_and_upcoming_promotion_exists(
    promotion_list,
):
    # given
    now = timezone.now()
    schedule = promotion_webhook_schedule()

    promotion_1 = promotion_list[0]
    promotion_2 = promotion_list[1]

    promotion_1.start_date = now - timedelta(minutes=8)
    promotion_1.last_notification_scheduled_at = now - timedelta(minutes=6)

    time_delta = timedelta(seconds=22)
    promotion_2.start_date = now - timedelta(minutes=7)
    promotion_2.end_date = timezone.now() + time_delta
    promotion_2.last_notification_scheduled_at = now - timedelta(minutes=6)

    Promotion.objects.bulk_update(
        [promotion_1, promotion_2],
        ["start_date", "end_date", "last_notification_scheduled_at"],
    )

    # when
    is_due, next_run = schedule.is_due(timezone.now() - timedelta(minutes=1))

    # then
    assert is_due is False
    assert next_run == time_delta.total_seconds()


@freeze_time("2020-10-10 12:00:00")
def test_is_due_no_promo_to_notify_about_upcoming_promo_exists_initial_time_returned(
    promotion_list,
):
    # given
    now = timezone.now()
    schedule = promotion_webhook_schedule()

    promotion_1 = promotion_list[0]
    promotion_2 = promotion_list[1]

    promotion_1.start_date = now - timedelta(minutes=8)
    promotion_1.last_notification_scheduled_at = now - timedelta(minutes=6)

    time_delta = timedelta(minutes=3)
    promotion_2.start_date = now - timedelta(minutes=7)
    promotion_2.end_date = timezone.now() + time_delta
    promotion_2.last_notification_scheduled_at = now - timedelta(minutes=6)

    Promotion.objects.bulk_update(
        [promotion_1, promotion_2],
        ["end_date", "last_notification_scheduled_at"],
    )

    # when
    is_due, next_run = schedule.is_due(timezone.now() - timedelta(minutes=1))

    # then
    assert is_due is False
    assert next_run == schedule.initial_timedelta.total_seconds()
