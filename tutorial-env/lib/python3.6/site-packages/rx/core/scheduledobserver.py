from rx import config
from rx.disposables import SerialDisposable

from .observerbase import ObserverBase


class ScheduledObserver(ObserverBase):
    def __init__(self, scheduler, observer):
        super(ScheduledObserver, self).__init__()

        self.scheduler = scheduler
        self.observer = observer

        self.lock = config["concurrency"].RLock()
        self.is_acquired = False
        self.has_faulted = False
        self.queue = []
        self.disposable = SerialDisposable()

        # Note to self: list append is thread safe
        # http://effbot.org/pyfaq/what-kinds-of-global-value-mutation-are-thread-safe.htm

    def _on_next_core(self, value):
        def action():
            self.observer.on_next(value)
        self.queue.append(action)

    def _on_error_core(self, exception):
        def action():
            self.observer.on_error(exception)
        self.queue.append(action)

    def _on_completed_core(self):
        def action():
            self.observer.on_completed()
        self.queue.append(action)

    def ensure_active(self):
        is_owner = False

        with self.lock:
            if not self.has_faulted and len(self.queue):
                is_owner = not self.is_acquired
                self.is_acquired = True

        if is_owner:
            self.disposable.disposable = self.scheduler.schedule(self.run)

    def run(self, recurse, state):
        parent = self

        with self.lock:
            if len(parent.queue):
                work = parent.queue.pop(0)
            else:
                parent.is_acquired = False
                return

        try:
            work()
        except Exception:
            with self.lock:
                parent.queue = []
                parent.has_faulted = True
            raise

        self.scheduler.schedule(self.run)

    def dispose(self):
        super(ScheduledObserver, self).dispose()
        self.disposable.dispose()
