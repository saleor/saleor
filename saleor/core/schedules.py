from collections import namedtuple
from datetime import datetime, timedelta
from typing import cast

import pytz
from celery.utils.time import maybe_timedelta, remaining
from django.db.models import F, Q

from ..schedulers.customschedule import CustomSchedule

schedstate = namedtuple("schedstate", ("is_due", "next"))


class promotion_webhook_schedule(CustomSchedule):
    """Schedule for promotion webhook periodic task.

    The lowercase with an underscore is used for the name as all celery schedules
    are written this way. According to PEP it's allowed behavior:
    https://peps.python.org/pep-0008/#class-names.

    Arguments:
        initial_timedelta (float, ~datetime.timedelta):
            Initial time interval in seconds.
        nowfun (Callable): Function returning the current date and time
            (:class:`~datetime.datetime`).
        app (Celery): Celery app instance.

    """

    def __init__(self, initial_timedelta=60, nowfun=None, app=None):
        self.initial_timedelta: timedelta = cast(
            timedelta, maybe_timedelta(initial_timedelta)
        )
        self.next_run: timedelta = self.initial_timedelta
        super().__init__(
            schedule=self,
            nowfun=nowfun,
            app=app,
            import_path="saleor.core.schedules.promotion_webhook_schedule",
        )
        # Seconds left to next batch processing
        self.NEXT_BATCH_RUN_TIME = 5

    def remaining_estimate(self, last_run_at):
        """Estimate of next run time.

        Returns when the periodic task should run next as a timedelta.
        """
        return remaining(
            self.maybe_make_aware(last_run_at),
            self.next_run,
            self.maybe_make_aware(self.now()),
        )

    def is_due(self, last_run_at):
        """Return tuple of ``(is_due, next_time_to_run)``.

        Note:
            Next time to run is in seconds.

        """
        from ..discount.models import Promotion
        from ..discount.tasks import (
            PROMOTION_TOGGLE_BATCH_SIZE,
            get_ending_promotions,
            get_starting_promotions,
        )

        now = datetime.now(pytz.UTC)

        # remaining time must be calculated as the next call is overridden with 0
        # when is_due was True (/celery/beat.py Scheduler.populate_heap)
        rem_delta = self.remaining_estimate(last_run_at)
        remaining = max(rem_delta.total_seconds(), 0)

        staring_promotions = get_starting_promotions()
        ending_promotions = get_ending_promotions()

        # if task needs to be handled in batches, schedule next run with const value
        if len(staring_promotions | ending_promotions) > PROMOTION_TOGGLE_BATCH_SIZE:
            self.next_run = timedelta(seconds=self.NEXT_BATCH_RUN_TIME)
            is_due = remaining == 0
            return schedstate(is_due, self.NEXT_BATCH_RUN_TIME)

        # is_due is True when there is at least one sale to notify about
        # and the remaining time from previous call is 0
        is_due = remaining == 0 and (
            staring_promotions.exists() or ending_promotions.exists()
        )

        upcoming_start_dates = Promotion.objects.filter(
            (
                Q(last_notification_scheduled_at__isnull=True)
                | Q(last_notification_scheduled_at__lt=F("start_date"))
            )
            & Q(start_date__gt=now)
        ).order_by("start_date")
        upcoming_end_dates = Promotion.objects.filter(
            (
                Q(last_notification_scheduled_at__isnull=True)
                | Q(last_notification_scheduled_at__lt=F("end_date"))
            )
            & Q(end_date__gt=now)
        ).order_by("end_date")

        nearest_start_date = upcoming_start_dates.first()
        nearest_end_date = upcoming_end_dates.first()

        # calculate the earliest incoming date of starting or ending sale
        next_upcoming_date: datetime
        if nearest_start_date and nearest_end_date and nearest_end_date.end_date:
            next_upcoming_date = min(
                nearest_start_date.start_date, nearest_end_date.end_date
            )
        else:
            if nearest_start_date:
                next_upcoming_date = nearest_start_date.start_date
            elif nearest_end_date and nearest_end_date.end_date:
                next_upcoming_date = nearest_end_date.end_date
            else:
                next_upcoming_date = now + self.initial_timedelta

        self.next_run = min((next_upcoming_date - now), self.initial_timedelta)
        return schedstate(is_due, self.next_run.total_seconds())


initiated_promotion_webhook_schedule = promotion_webhook_schedule()
