from collections import namedtuple
from datetime import datetime

import pytz
from celery.utils.time import maybe_timedelta, remaining
from django.db.models import F, Q

from ..schedulers.customschedule import CustomSchedule

schedstate = namedtuple("schedstate", ("is_due", "next"))


class sale_webhook_schedule(CustomSchedule):
    """Schedule for sale webhook periodic task.

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
        self.initial_timedelta = maybe_timedelta(initial_timedelta)
        self.next_run = self.initial_timedelta
        super().__init__(
            schedule=self,
            nowfun=nowfun,
            app=app,
            import_path="saleor.core.schedules.initiated_sale_webhook_schedule",
        )

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
        from ..discount.models import Sale
        from ..discount.tasks import get_sales_to_notify_about

        now = datetime.now(pytz.UTC)

        # remaining time must be calculated as the next call is overridden with 0
        # when is_due was True (/celery/beat.py Scheduler.populate_heap)
        rem_delta = self.remaining_estimate(last_run_at)
        remaining = max(rem_delta.total_seconds(), 0)

        # is_due is True when there is at least one sale to notify about
        # and the remaining time from previous call is 0
        is_due = remaining == 0 and get_sales_to_notify_about().exists()

        upcoming_start_dates = Sale.objects.filter(
            (
                (
                    Q(notification_sent_datetime__isnull=True)
                    | Q(notification_sent_datetime__lt=F("start_date"))
                )
                & Q(start_date__gt=now)
            )
        ).order_by("start_date")
        upcoming_end_dates = Sale.objects.filter(
            (
                (
                    Q(notification_sent_datetime__isnull=True)
                    | Q(notification_sent_datetime__lt=F("end_date"))
                )
                & Q(end_date__gt=now)
            )
        ).order_by("end_date")

        if not upcoming_start_dates and not upcoming_end_dates:
            self.next_run = self.initial_timedelta
            return schedstate(is_due, self.next_run.total_seconds())

        # calculate the earliest incoming date of starting or ending sale
        next_start_date = (
            upcoming_start_dates.first().start_date if upcoming_start_dates else None
        )
        next_end_date = (
            upcoming_end_dates.first().end_date if upcoming_end_dates else None
        )

        # get the earlier date
        if next_start_date and next_end_date:
            next_upcoming_date = min(next_start_date, next_end_date)
        else:
            next_upcoming_date = next_start_date if next_start_date else next_end_date

        self.next_run = min((next_upcoming_date - now), self.initial_timedelta)
        return schedstate(is_due, self.next_run.total_seconds())


initiated_sale_webhook_schedule = sale_webhook_schedule()
