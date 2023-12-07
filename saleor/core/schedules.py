from collections import namedtuple
from datetime import datetime, timedelta
from typing import cast

import pytz
from celery.utils.log import get_task_logger
from celery.utils.time import maybe_timedelta, remaining
from django.db.models import F, Q


from ..schedulers.customschedule import CustomSchedule

task_logger = get_task_logger(__name__)
schedstate = namedtuple("schedstate", ("is_due", "next"))


# from django.apps import apps
# PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")


def pp(msg, msg2="", id=""):
    dash_long = 100
    task_logger.info(
        f"\n{'-' * dash_long}\n"
        f"MSG: {str(msg)}\n"
        f"MSG2: {str(msg2)}\n"
        f"{str('-' * int(dash_long/2))}ID: {str(id)}\n"
        f"{'-' * dash_long}"
    )


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

    def __init__(self, initial_timedelta=30, nowfun=None, app=None):
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
        self.due_count = 0
        self.time = datetime.now(pytz.UTC)
        pp("init")

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
            get_ending_promotions,
            get_starting_promotions,
            PROMOTION_TOGGLE_BATCH_SIZE,
        )

        NEXT_BATCH_RUN_TIME = float(45)
        now = datetime.now(pytz.UTC)

        # remaining time must be calculated as the next call is overridden with 0
        # when is_due was True (/celery/beat.py Scheduler.populate_heap)
        rem_delta = self.remaining_estimate(last_run_at)
        remaining = max(rem_delta.total_seconds(), 0)

        # is_due is True when there is at least one sale to notify about
        # and the remaining time from previous call is 0
        staring_promotions = get_starting_promotions().order_by("start_date")
        ending_promotions = get_ending_promotions().order_by("end_date")

        promotion_process = staring_promotions | ending_promotions
        promotion_process_ids = [p.id for p in promotion_process]

        self.due_count += 1
        pp("is_due", self.due_count, self.time)
        # if task needs to be handled in batches, schedule next run with const value
        # if (
        #     len(staring_promotions) + len(ending_promotions)
        #     > PROMOTION_TOGGLE_BATCH_SIZE
        # ):
        #     pp("batch", self.due_count, self.time)
        #     next_run = (now + timedelta(seconds=NEXT_BATCH_RUN_TIME)) - now
        #     self.next_run = next_run
        #     is_due = False
        #     x = schedstate(is_due, NEXT_BATCH_RUN_TIME)
        #     pp(f"batch:"
        #        f"\nnext_run: {next_run}"
        #        f"\nnext_run_type: {type(next_run)}"
        #        f"\nself_next_run_type: {type(self.next_run)}"
        #        f"\nis-due: {is_due}"
        #        f"\nnext run date: {now + timedelta(seconds=NEXT_BATCH_RUN_TIME)}"
        #        f"\nschedstate: {x}"
        #        f"\nNEXT_BATCH_RUN_TIME: {NEXT_BATCH_RUN_TIME}"
        #        f"\nNEXT_BATCH_RUN_TIME type: {type(NEXT_BATCH_RUN_TIME)}"
        #        f"\nlen(staring_promotions) + len(ending_promotions) = {len(staring_promotions) + len(ending_promotions)}"
        #        )
        #     return x


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

        next_run = min((next_upcoming_date - now), self.initial_timedelta)
        self.next_run = next_run
        x = schedstate(is_due, self.next_run.total_seconds())
        pp(f"exit:"
           f"\nnext_run: {next_run}"
           f"\nnext_run_type: {type(next_run)}"
           f"\nself_next_run_type: {type(self.next_run)}"
           f"\nis-due: {is_due}"
           f"\nnext run date: {now + timedelta(seconds=NEXT_BATCH_RUN_TIME)}"
           f"\nschedstate: {x}"
           f"\nself.next_run.total_seconds(): {self.next_run.total_seconds()}"
           f"\nself.next_run.total_seconds() type: {type(self.next_run.total_seconds())}"
           f"\nlen(staring_promotions) + len(ending_promotions) = {len(staring_promotions) + len(ending_promotions)}"
           )
        return x


initiated_promotion_webhook_schedule = promotion_webhook_schedule()
