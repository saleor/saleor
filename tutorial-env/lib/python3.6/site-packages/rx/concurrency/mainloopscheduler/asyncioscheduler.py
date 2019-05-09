import logging
asyncio = None

from rx.core import Disposable
from rx.disposables import SingleAssignmentDisposable, CompositeDisposable
from rx.concurrency.schedulerbase import SchedulerBase

log = logging.getLogger("Rx")


class AsyncIOScheduler(SchedulerBase):
    """A scheduler that schedules work via the asyncio mainloop."""

    def __init__(self, loop=None):
        global asyncio
        import rx
        asyncio = rx.config['asyncio']

        self.loop = loop or asyncio.get_event_loop()

    def schedule(self, action, state=None):
        """Schedules an action to be executed."""

        disposable = SingleAssignmentDisposable()

        def interval():
            disposable.disposable = self.invoke_action(action, state)
        handle = self.loop.call_soon(interval)

        def dispose():
            handle.cancel()

        return CompositeDisposable(disposable, Disposable.create(dispose))

    def schedule_relative(self, duetime, action, state=None):
        """Schedules an action to be executed at duetime.

        Keyword arguments:
        duetime -- {timedelta} Relative time after which to execute the
            action.
        action -- {Function} Action to be executed.

        Returns {Disposable} The disposable object used to cancel the
        scheduled action (best effort)."""

        scheduler = self
        seconds = self.to_relative(duetime)/1000.0
        if seconds == 0:
            return scheduler.schedule(action, state)

        disposable = SingleAssignmentDisposable()

        def interval():
            disposable.disposable = self.invoke_action(action, state)

        handle = self.loop.call_later(seconds, interval)

        def dispose():
            handle.cancel()

        return CompositeDisposable(disposable, Disposable.create(dispose))

    def schedule_absolute(self, duetime, action, state=None):
        """Schedules an action to be executed at duetime.

        Keyword arguments:
        :param datetime duetime: Absolute time after which to execute the
            action.
        :param types.FunctionType action: Action to be executed.
        :param T state: Optional state to be given to the action function.

        :returns: The disposable object used to cancel the scheduled action
            (best effort).
        :rtype: Disposable
        """

        duetime = self.to_datetime(duetime)
        return self.schedule_relative(duetime - self.now, action, state)

    @property
    def now(self):
        """Represents a notion of time for this scheduler. Tasks being
        scheduled on a scheduler will adhere to the time denoted by this
        property.
        """

        return self.to_datetime(self.loop.time()*1000)
