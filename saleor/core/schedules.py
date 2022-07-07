from collections import namedtuple
from datetime import datetime

import pytz
from celery.schedules import BaseSchedule
from celery.utils.time import maybe_timedelta, remaining
from django.db.models import Q

schedstate = namedtuple("schedstate", ("is_due", "next"))


class sale_webhook_schedule(BaseSchedule):
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
        super().__init__(nowfun=nowfun, app=app)

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

        now = datetime.now(pytz.UTC)

        # is_due is True when there is any sale for which the started or
        # ended notification should be send
        is_due = Sale.objects.filter(
            (Q(started_notification_sent=False) & Q(start_date__lte=now))
            | (Q(ended_notification_sent=False) & Q(end_date__lte=now))
        ).exists()

        upcoming_sales = Sale.objects.filter(
            (Q(started_notification_sent=False) & Q(start_date__gt=now))
            | (Q(ended_notification_sent=False) & Q(end_date__gt=now))
        )
        if not upcoming_sales:
            self.next_run = self.initial_timedelta.total_seconds()
            return schedstate(is_due, self.next_run)

        # calculate the earliest incoming date of starting or ending sale
        next_start_date = upcoming_sales.order_by("start_date").first().start_date
        next_end_date = upcoming_sales.order_by("end_date").first().end_date

        # get the earlier date
        next_upcoming_date = (
            min(next_start_date, next_end_date) if next_end_date else next_start_date
        )

        self.next_run = min((next_upcoming_date - now), self.initial_timedelta)

        return schedstate(is_due, self.next_run.total_seconds())
