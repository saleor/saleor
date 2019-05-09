from rx.core import Disposable
from rx.disposables import SingleAssignmentDisposable, CompositeDisposable
from rx.concurrency.schedulerbase import SchedulerBase


class TkinterScheduler(SchedulerBase):
    """A scheduler that schedules work via the Tkinter main event loop.

    http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/universal.html
    http://effbot.org/tkinterbook/widget.htm"""

    def __init__(self, master):
        self.master = master

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

        msecs = self.to_relative(duetime)

        disposable = SingleAssignmentDisposable()

        def invoke_action():
            disposable.disposable = self.invoke_action(action, state)

        alarm = self.master.after(msecs, invoke_action)

        def dispose():
            self.master.after_cancel(alarm)

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
