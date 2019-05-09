from rx.core import Observer, ObservableBase, Disposable
from rx.subjects import Subject
from rx.disposables import AnonymousDisposable
from rx.concurrency import current_thread_scheduler
from rx.core.notification import OnCompleted, OnError, OnNext


class ControlledSubject(ObservableBase, Observer):
    def __init__(self, enable_queue=True, scheduler=None):
        super(ControlledSubject, self).__init__()

        self.subject = Subject()
        self.enable_queue = enable_queue
        self.queue = [] if enable_queue else None
        self.requested_count = 0
        self.requested_disposable = Disposable.empty()
        self.error = None
        self.has_failed = False
        self.has_completed = False
        self.scheduler = scheduler or current_thread_scheduler

    def _subscribe_core(self, observer):
        return self.subject.subscribe(observer)

    def on_completed(self):
        self.has_completed = True

        if not self.enable_queue or len(self.queue) == 0:
            self.subject.on_completed()
            self.dispose_current_request()
        else:
            self.queue.append(OnCompleted())

    def on_error(self, error):
        self.has_failed = True
        self.error = error

        if not self.enable_queue or len(self.queue) == 0:
            self.subject.on_error(error)
            self.dispose_current_request()
        else:
            self.queue.append(OnError(error))

    def on_next(self, value):
        if self.requested_count <= 0:
            self.enable_queue and self.queue.append(OnNext(value))
        else:
            self.requested_count -= 1
            if self.requested_count == 0:
                self.dispose_current_request()
            self.subject.on_next(value)

    def _process_request(self, number_of_items):
        if self.enable_queue:
            while len(self.queue) > 0 and (number_of_items > 0 or self.queue[0].kind != 'N'):
                first = self.queue.pop(0)
                first.accept(self.subject)
                if first.kind == 'N':
                    number_of_items -= 1
                else:
                    self.dispose_current_request()
                    self.queue = []

        return number_of_items

    def request(self, number):
        self.dispose_current_request()

        def action(scheduler, i):
            remaining = self._process_request(i)
            stopped = self.has_completed and self.has_failed
            if not stopped and remaining > 0:
                self.requested_count = remaining

            def dispose():
                self.requested_count = 0

            return AnonymousDisposable(dispose)
            # Scheduled item is still in progress. Return a new
            # disposable to allow the request to be interrupted
            # via dispose.

        self.requested_disposable = self.scheduler.schedule(action, state=number)
        return self.requested_disposable

    def dispose_current_request(self):
        if self.requested_disposable:
            self.requested_disposable.dispose()
            self.requested_disposable = None
