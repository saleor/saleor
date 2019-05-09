import logging

from rx.core import Disposable
from rx.concurrency.schedulerbase import SchedulerBase
from rx.disposables import SingleAssignmentDisposable, CompositeDisposable

log = logging.getLogger("Rx")


class TwistedScheduler(SchedulerBase):
    """A scheduler that schedules work via the Twisted reactor mainloop."""

    def __init__(self, reactor):
        self.reactor = reactor

    def schedule(self, action, state=None):
        """Schedules an action to be executed."""

        return self.schedule_relative(0, action, state)

    def schedule_relative(self, duetime, action, state=None):
        """Schedules an action to be executed after duetime.

        Keyword arguments:
        duetime -- {timedelta} Relative time after which to execute the action.
        action -- {Function} Action to be executed.

        Returns {Disposable} The disposable object used to cancel the scheduled
        action (best effort)."""

        from twisted.internet.task import deferLater

        scheduler = self
        seconds = self.to_relative(duetime)/1000.0

        disposable = SingleAssignmentDisposable()

        def interval():
            disposable.disposable = action(scheduler, state)

        log.debug("timeout: %s", seconds)
        handle = deferLater(self.reactor, seconds, interval).addErrback(lambda _: None)

        def dispose():
            if not handle.called:
                handle.cancel()

        return CompositeDisposable(disposable, Disposable.create(dispose))

    def schedule_absolute(self, duetime, action, state=None):
        """Schedules an action to be executed at duetime.

        Keyword arguments:
        duetime -- {datetime} Absolute time after which to execute the action.
        action -- {Function} Action to be executed.

        Returns {Disposable} The disposable object used to cancel the scheduled
        action (best effort)."""

        duetime = self.to_datetime(duetime)
        return self.schedule_relative(duetime - self.now, action, state)

    @property
    def now(self):
        """Represents a notion of time for this scheduler. Tasks being scheduled
        on a scheduler will adhere to the time denoted by this property."""

        return self.to_datetime(int(self.reactor.seconds()*1000))
