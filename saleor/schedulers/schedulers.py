import copy
import logging
import time
from typing import List, NamedTuple

import celery.beat
import celery.schedules
from celery.signals import setup_logging
from django_celery_beat import models as base_models
from django_celery_beat.clockedschedule import clocked
from django_celery_beat.schedulers import DatabaseScheduler as BaseDatabaseScheduler
from django_celery_beat.schedulers import ModelEntry

from . import customschedule, models

logger = logging.getLogger(__name__)


@setup_logging.connect
def setup_celery_logging(loglevel=None, **_kwargs):
    """Configure the logging level of module loggers with the flag passed to Celery.

    Respects the --loglevel=<level> passed to Celery beats
    """
    logging.getLogger("saleor.schedulers").setLevel(loglevel)


def is_numeric_value(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


class HeapEventType(NamedTuple):
    time: float  # timestamp when it should trigger next
    priority: int
    entry: celery.beat.ScheduleEntry


class CustomModelEntry(ModelEntry):
    """Scheduler entry taken from database row."""

    model_schedules = (
        (celery.schedules.crontab, base_models.CrontabSchedule, "crontab"),
        (celery.schedules.schedule, base_models.IntervalSchedule, "interval"),
        (celery.schedules.solar, base_models.SolarSchedule, "solar"),
        (clocked, base_models.ClockedSchedule, "clocked"),
        (customschedule.CustomSchedule, models.CustomSchedule, "custom"),
    )
    save_fields = ["last_run_at", "total_run_count", "no_changes"]

    @classmethod
    def from_entry(cls, name, app=None, **entry):
        # Super method has 'PeriodicTask' hardcoded
        return cls(
            models.CustomPeriodicTask._default_manager.update_or_create(
                name=name,
                defaults=cls._unpack_fields(**entry),
            ),
            app=app,
        )


class BaseScheduler(celery.beat.Scheduler):
    """Define the base scheduler for Celery beat."""

    def tick(
        self,
        # Parameters are not used but required by invoker
        event_t=HeapEventType,
        min=min,
        heappop=None,
        heappush=None,
    ):
        """Fix version of super class's ``tick`` method.

        Celery's tick() has two issues:
        - Sometimes it sets the wait time between beats higher than what is currently
          in heap, causing to wait much longer than needed (e.g. 5m instead of 20s)
        - If an event that was supposed to happen "right now" return ``False`` in
          ``is_due()``, it will keep on trying to schedule the task forever until
          ``is_due()`` returns True. While waiting to get ``True`` at each beat,
          nothing else executed, thus if it's always ``False`` the worker will be
          stuck forever waiting for ``True``.

        This code is all original except when noted it's not.
        """
        adjust = self.adjust
        max_interval = self.max_interval

        if self._heap is None or not self.schedules_equal(
            self.old_schedulers, self.schedule
        ):
            self.old_schedulers = copy.copy(self.schedule)
            self.populate_heap()

        H: List[HeapEventType] = self._heap

        if not H:
            return max_interval

        now = time.time()

        next_tick: float = max_interval
        # All non-original code
        # Go through each event from the heap from last to first
        # We will remove the items from heap that we executed
        # and will push the new events at the end of the heap
        for heap_pos in range(len(H) - 1, -1, -1):
            event = H[heap_pos]
            entry = event.entry
            next_time_to_run = event.time - now

            # Only check if it's due if it's time to check based on the last is_due()
            # value returned by that event
            if next_time_to_run > 0:
                if next_time_to_run < next_tick:
                    next_tick = next_time_to_run
                continue
            is_due, next_time_to_run = self.is_due(entry)
            if next_time_to_run < next_tick:
                next_tick = next_time_to_run

            if is_due:
                H.pop(heap_pos)
                next_entry = self.reserve(entry)
                self.apply_entry(entry, producer=self.producer)
                H.append(
                    HeapEventType(
                        self._when(next_entry, next_time_to_run),
                        event[1],
                        next_entry,
                    )
                )
                logger.debug(
                    "Triggered %s, will trigger again in %ss",
                    entry.name,
                    next_time_to_run,
                )
        # Non-original code, custom fix for Celery not waiting the correct duration
        # when the first task in heap needs to wait longer than other tasks in heap
        adjusted_next_time_to_run = adjust(next_tick)
        return min(
            adjusted_next_time_to_run
            if is_numeric_value(adjusted_next_time_to_run)
            else max_interval,
            max_interval,
        )


class PersistentScheduler(celery.beat.PersistentScheduler, BaseScheduler):
    """Celery beat scheduler backed by ``shelve`` python module for persistence.

    Usage:
    $ celery --app saleor.celeryconf:app beat \
        --scheduler saleor.schedulers.schedulers.PersistentScheduler
    """


class DatabaseScheduler(BaseDatabaseScheduler, BaseScheduler):
    """Celery beat scheduler backed by the database for persistence.

    This uses the django-celery-beat package.

    Usage:
    $ celery --app saleor.celeryconf:app beat \
        --scheduler saleor.schedulers.schedulers.DatabaseScheduler
    """

    Entry = CustomModelEntry
    Model = models.CustomPeriodicTask
    Changes = base_models.PeriodicTasks
