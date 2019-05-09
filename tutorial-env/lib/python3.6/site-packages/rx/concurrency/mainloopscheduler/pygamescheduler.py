import logging
from datetime import timedelta

pygame = None

from rx.internal import PriorityQueue
from rx.concurrency.schedulerbase import SchedulerBase
from rx.concurrency.scheduleditem import ScheduledItem

log = logging.getLogger("Rx")


class PyGameScheduler(SchedulerBase):
    """A scheduler that schedules works for PyGame.

    http://www.pygame.org/docs/ref/time.html
    http://www.pygame.org/docs/ref/event.html"""

    def __init__(self, event_id=None):
        global pygame
        import pygame

        self.timer = None
        self.event_id = event_id or pygame.USEREVENT

        self.queue = PriorityQueue()

    def schedule(self, action, state=None):
        """Schedules an action to be executed."""

        log.debug("PyGameScheduler.schedule(state=%s)", state)
        return self.schedule_relative(0, action, state)

    def run(self):
        while len(self.queue):
            item = self.queue.peek()
            diff = item.duetime - self.now
            if diff > timedelta(0):
                break

            item = self.queue.dequeue()
            if not item.is_cancelled():
                item.invoke()

    def schedule_relative(self, duetime, action, state=None):
        """Schedules an action to be executed after duetime.

        Keyword arguments:
        duetime -- {timedelta} Relative time after which to execute the action.
        action -- {Function} Action to be executed.

        Returns {Disposable} The disposable object used to cancel the scheduled
        action (best effort)."""

        dt = self.now + self.to_timedelta(duetime)
        si = ScheduledItem(self, state, action, dt)

        self.queue.enqueue(si)

        return si.disposable

    def schedule_absolute(self, duetime, action, state=None):
        """Schedules an action to be executed at duetime.

        Keyword arguments:
        duetime -- {datetime} Absolute time after which to execute the action.
        action -- {Function} Action to be executed.

        Returns {Disposable} The disposable object used to cancel the scheduled
        action (best effort)."""

        return self.schedule_relative(duetime - self.now, action, state)

    @property
    def now(self):
        """Represents a notion of time for this scheduler. Tasks being scheduled
        on a scheduler will adhere to the time denoted by this property."""

        return self.to_datetime(pygame.time.get_ticks())
