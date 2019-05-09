import logging
from threading import Timer
from datetime import timedelta

from rx.core import Scheduler, Disposable
from rx.disposables import SingleAssignmentDisposable, CompositeDisposable

from .schedulerbase import SchedulerBase

log = logging.getLogger("Rx")


class TimeoutScheduler(SchedulerBase):
    """A scheduler that schedules work via a timed callback based upon platform."""

    def schedule(self, action, state=None):
        """Schedules an action to be executed."""

        disposable = SingleAssignmentDisposable()

        def interval():
            disposable.disposable = self.invoke_action(action, state)
        timer = Timer(0, interval)
        timer.setDaemon(True)
        timer.start()

        def dispose():
            timer.cancel()
        return CompositeDisposable(disposable, Disposable.create(dispose))

    def schedule_relative(self, duetime, action, state=None):
        """Schedules an action to be executed after duetime."""

        scheduler = self
        timespan = self.to_timedelta(duetime)
        if timespan == timedelta(0):
            return scheduler.schedule(action, state)

        disposable = SingleAssignmentDisposable()

        def interval():
            disposable.disposable = self.invoke_action(action, state)

        seconds = timespan.total_seconds()
        log.debug("timeout: %s", seconds)
        timer = Timer(seconds, interval)
        timer.setDaemon(True)
        timer.start()

        def dispose():
            timer.cancel()

        return CompositeDisposable(disposable, Disposable.create(dispose))

    def schedule_absolute(self, duetime, action, state=None):
        """Schedules an action to be executed after duetime."""

        duetime = self.to_datetime(duetime)
        return self.schedule_relative(duetime - self.now, action, state)

    def _start_timer(self, period, action):
        timer = Timer(period, action)
        timer.setDaemon(True)
        timer.start()

        return timer


Scheduler.timeout = timeout_scheduler = TimeoutScheduler()
