import datetime
from typing import NamedTuple, cast

from celery.utils.time import maybe_timedelta, remaining
from django.db.models import F, Q
from django.utils import timezone

from ..schedulers.customschedule import CustomSchedule


class schedstate(NamedTuple):
    is_due: bool
    next: float


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
        self.initial_timedelta: datetime.timedelta = cast(
            datetime.timedelta, maybe_timedelta(initial_timedelta)
        )
        self.next_run: datetime.timedelta = self.initial_timedelta
        super().__init__(
            schedule=self,
            nowfun=nowfun,
            app=app,
            import_path="saleor.core.schedules.initiated_promotion_webhook_schedule",
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

        now = datetime.datetime.now(tz=datetime.UTC)

        # remaining time must be calculated as the next call is overridden with 0
        # when is_due was True (/celery/beat.py Scheduler.populate_heap)
        rem_delta = self.remaining_estimate(last_run_at)
        remaining = max(rem_delta.total_seconds(), 0)

        staring_promotions = get_starting_promotions()
        ending_promotions = get_ending_promotions()

        # if task needs to be handled in batches, schedule next run with const value
        if len(staring_promotions | ending_promotions) > PROMOTION_TOGGLE_BATCH_SIZE:
            self.next_run = datetime.timedelta(seconds=self.NEXT_BATCH_RUN_TIME)
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
        next_upcoming_date: datetime.datetime
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


class TimeBaseSchedule(CustomSchedule):
    """Base schedule for time-based periodic tasks.

    Arguments:
        import_path (str): Import path of the schedule.
        initial_timedelta (float, ~datetime.timedelta):
            Initial time interval in seconds.
        nowfun (Callable): Function returning the current date and time
            (:class:`~datetime.datetime`).
        app (Celery): Celery app instance.

    """

    class Meta:
        abstract = True

    def __init__(self, import_path: str, initial_timedelta, nowfun=None, app=None):
        self.initial_timedelta: datetime.timedelta = cast(
            datetime.timedelta, maybe_timedelta(initial_timedelta)
        )
        self.next_run: datetime.timedelta = self.initial_timedelta
        super().__init__(
            schedule=self,
            nowfun=nowfun,
            app=app,
            import_path=import_path,
        )

    def are_dirty(self) -> bool:
        raise NotImplementedError

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
        last_run_at = self.maybe_make_aware(last_run_at)
        rem_delta = self.remaining_estimate(last_run_at)
        remaining_s = max(rem_delta.total_seconds(), 0)
        if remaining_s == 0:
            remaining_s = self.initial_timedelta.total_seconds()

        are_marked_as_dirty = self.are_dirty()
        return schedstate(is_due=are_marked_as_dirty, next=remaining_s)


class checkout_automatic_completion_schedule(TimeBaseSchedule):
    def __init__(self, initial_timedelta=60, nowfun=None, app=None):
        # initial_timedelta defaults to 60 seconds, as referencing settings.py variables
        # would require rebuilding the schedule. settings depends on this class instance,
        # leading to a circular import if accessed directly.
        import_path = (
            "saleor.core.schedules.initiated_checkout_automatic_completion_schedule"
        )
        super().__init__(import_path, initial_timedelta, nowfun, app)

    def are_dirty(self) -> bool:
        from django.conf import settings

        from ..channel.models import Channel
        from ..checkout import CheckoutAuthorizeStatus
        from ..checkout.models import Checkout

        channels = Channel.objects.filter(
            automatically_complete_fully_paid_checkouts=True
        )
        now = timezone.now()
        oldest_allowed_checkout = (
            now - settings.AUTOMATIC_CHECKOUT_COMPLETION_OLDEST_MODIFIED
        )
        for channel in channels:
            # calculate threshold time for automatic completion for given channel
            delay_minutes = channel.automatic_completion_delay or 0
            threshold_time = now - datetime.timedelta(minutes=float(delay_minutes))
            filter_kwargs = {
                "authorize_status": CheckoutAuthorizeStatus.FULL,
                "last_change__gte": oldest_allowed_checkout,
                "channel_id": channel.pk,
                "last_change__lt": threshold_time,
                "total_gross_amount__gt": 0,
                "billing_address__isnull": False,
            }
            if cut_off_date := channel.automatic_completion_cut_off_date:
                filter_kwargs["created_at__gte"] = cut_off_date
            if (
                Checkout.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
                .filter(Q(email__isnull=False) | Q(user__isnull=False))
                .filter(
                    **filter_kwargs,
                )
                .exists()
            ):
                return True
        return False


initiated_promotion_webhook_schedule = promotion_webhook_schedule()
initiated_checkout_automatic_completion_schedule = (
    checkout_automatic_completion_schedule()
)
