from rx import config
from rx.core import Disposable


class ScheduledDisposable(Disposable):
    """Represents a disposable resource whose disposal invocation will be
    scheduled on the specified Scheduler"""

    def __init__(self, scheduler, disposable):
        """Initializes a new instance of the ScheduledDisposable class that
        uses a Scheduler on which to dispose the disposable."""

        self.scheduler = scheduler
        self.disposable = disposable
        self.is_disposed = False
        self.lock = config["concurrency"].RLock()

        super(ScheduledDisposable, self).__init__()

    def dispose(self):
        """Disposes the wrapped disposable on the provided scheduler."""

        parent = self

        def action(scheduler, state):
            """Scheduled dispose action"""

            should_dispose = False

            with self.lock:
                if not parent.is_disposed:
                    parent.is_disposed = True
                    should_dispose = True
            if should_dispose:
                parent.disposable.dispose()

        self.scheduler.schedule(action)
