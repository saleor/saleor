import logging

from rx.core import Disposable
from rx.disposables import SingleAssignmentDisposable, CompositeDisposable
from rx.concurrency.schedulerbase import SchedulerBase

log = logging.getLogger("Rx")


class QtScheduler(SchedulerBase):
    """A scheduler for a PyQt4/PyQt5/PySide event loop."""

    def __init__(self, qtcore):
        self.qtcore = qtcore
        self._timers = set()

    def _qtimer_schedule(self, time, action, state, periodic=False):
        scheduler = self
        msecs = self.to_relative(time)

        disposable = SingleAssignmentDisposable()

        periodic_state = [state]

        def interval():
            if periodic:
                periodic_state[0] = action(periodic_state[0])
            else:
                disposable.disposable = action(scheduler, state)

        log.debug("timeout: %s", msecs)

        timer = self.qtcore.QTimer()
        timer.setSingleShot(not periodic)
        timer.timeout.connect(interval)
        timer.setInterval(msecs)
        timer.start()
        self._timers.add(timer)

        def dispose():
            timer.stop()
            self._timers.remove(timer)

        return CompositeDisposable(disposable, Disposable.create(dispose))

    def schedule(self, action, state=None):
        """Schedules an action to be executed."""
        return self._qtimer_schedule(0, action, state)

    def schedule_relative(self, duetime, action, state=None):
        """Schedules an action to be executed after duetime.

        Keyword arguments:
        duetime -- {timedelta} Relative time after which to execute the action.
        action -- {Function} Action to be executed.

        Returns {Disposable} The disposable object used to cancel the scheduled
        action (best effort)."""
        return self._qtimer_schedule(duetime, action, state)

    def schedule_absolute(self, duetime, action, state=None):
        """Schedules an action to be executed at duetime.

        Keyword arguments:
        duetime -- {datetime} Absolute time after which to execute the action.
        action -- {Function} Action to be executed.

        Returns {Disposable} The disposable object used to cancel the scheduled
        action (best effort)."""

        duetime = self.to_datetime(duetime)
        return self._qtimer_schedule(duetime, action, state)

    def schedule_periodic(self, period, action, state=None):
        """Schedules a periodic piece of work to be executed in the Qt
        mainloop.

        Keyword arguments:
        period -- Period in milliseconds for running the work periodically.
        action -- Action to be executed.
        state -- [Optional] Initial state passed to the action upon the first
            iteration.

        Returns the disposable object used to cancel the scheduled recurring
        action (best effort)."""

        return self._qtimer_schedule(period, action, state, periodic=True)
