from rx.core import Disposable
from rx.disposables import SingleAssignmentDisposable, CompositeDisposable
from rx.concurrency.schedulerbase import SchedulerBase


class GtkScheduler(SchedulerBase):
    """ A scheduler that schedules work via the GLib main loop
    used in GTK+ applications.

    See https://wiki.gnome.org/Projects/PyGObject
    """

    def _gtk_schedule(self, time, action, state, periodic=False):
        # Do not import GLib into global scope because Qt and GLib
        # don't like each other there
        from gi.repository import GLib

        scheduler = self
        msecs = self.to_relative(time)

        disposable = SingleAssignmentDisposable()

        periodic_state = [state]
        stopped = [False]

        def timer_handler(_):
            if stopped[0]:
                return False

            if periodic:
                periodic_state[0] = action(periodic_state[0])
            else:
                disposable.disposable = action(scheduler, state)

            return periodic

        GLib.timeout_add(msecs, timer_handler, None)

        def dispose():
            stopped[0] = True

        return CompositeDisposable(disposable, Disposable.create(dispose))

    def schedule(self, action, state=None):
        """Schedules an action to be executed."""
        return self._gtk_schedule(0, action, state)

    def schedule_relative(self, duetime, action, state=None):
        """Schedules an action to be executed after duetime.
        Keyword arguments:
        duetime -- {timedelta} Relative time after which to execute the action.
        action -- {Function} Action to be executed.
        Returns {Disposable} The disposable object used to cancel the scheduled
        action (best effort)."""
        return self._gtk_schedule(duetime, action, state)

    def schedule_absolute(self, duetime, action, state=None):
        """Schedules an action to be executed at duetime.
        Keyword arguments:
        duetime -- {datetime} Absolute time after which to execute the action.
        action -- {Function} Action to be executed.
        Returns {Disposable} The disposable object used to cancel the scheduled
        action (best effort)."""

        duetime = self.to_datetime(duetime)
        return self._gtk_schedule(duetime, action, state)

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

        return self._gtk_schedule(period, action, state, periodic=True)
