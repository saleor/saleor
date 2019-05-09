# Current Thread Scheduler
import time
import logging
import threading
from datetime import timedelta

from rx import config
from rx.core import Scheduler
from rx.internal import PriorityQueue

from .schedulerbase import SchedulerBase
from .scheduleditem import ScheduledItem

log = logging.getLogger('Rx')


class Trampoline(object):
    @classmethod
    def run(cls, queue):
        while len(queue):
            item = queue.dequeue()
            if not item.is_cancelled():
                diff = item.duetime - item.scheduler.now
                while diff > timedelta(0):
                    seconds = diff.seconds + diff.microseconds / 1E6 + diff.days * 86400
                    log.warning("Do not schedule blocking work!")
                    time.sleep(seconds)
                    diff = item.duetime - item.scheduler.now

                if not item.is_cancelled():
                    item.invoke()


class CurrentThreadScheduler(SchedulerBase):
    """Represents an object that schedules units of work on the current
    thread. You never want to schedule timeouts using the CurrentThreadScheduler
    since it will block the current thread while waiting."""

    def __init__(self):
        """Gets a scheduler that schedules work as soon as possible on the
        current thread."""

        self.queues = dict()
        self.lock = config["concurrency"].RLock()

    def schedule(self, action, state=None):
        """Schedules an action to be executed."""

        log.debug("CurrentThreadScheduler.schedule(state=%s)", state)
        return self.schedule_relative(timedelta(0), action, state)

    def schedule_relative(self, duetime, action, state=None):
        """Schedules an action to be executed after duetime."""

        duetime = self.to_timedelta(duetime)

        dt = self.now + SchedulerBase.normalize(duetime)
        si = ScheduledItem(self, state, action, dt)

        queue = self.queue
        if queue is None:
            queue = PriorityQueue(4)
            queue.enqueue(si)

            self.queue = queue
            try:
                Trampoline.run(queue)
            finally:
                self.queue = None
        else:
            queue.enqueue(si)

        return si.disposable

    def schedule_absolute(self, duetime, action, state=None):
        """Schedules an action to be executed at duetime."""

        duetime = self.to_datetime(duetime)
        return self.schedule_relative(duetime - self.now, action, state=None)

    def get_queue(self):
        ident = threading.current_thread().ident

        with self.lock:
            return self.queues.get(ident)

    def set_queue(self, queue):
        ident = threading.current_thread().ident

        with self.lock:
            self.queues[ident] = queue

    queue = property(get_queue, set_queue)

    def schedule_required(self):
        """Test if scheduling is required.

        Gets a value indicating whether the caller must call a
        schedule method. If the trampoline is active, then it returns
        False; otherwise, if  the trampoline is not active, then it
        returns True.
        """
        return self.queue is None

    def ensure_trampoline(self, action):
        """Method for testing the CurrentThreadScheduler."""
        if self.schedule_required():
            return self.schedule(action)
        else:
            return action(self, None)

Scheduler.current_thread = current_thread_scheduler = CurrentThreadScheduler()
