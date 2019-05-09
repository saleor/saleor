import logging

from rx.core import ObserverBase, ObservableBase
from rx.concurrency import current_thread_scheduler, timeout_scheduler
from rx.disposables import CompositeDisposable
log = logging.getLogger('Rx')


class WindowedObserver(ObserverBase):
    def __init__(self, observer, observable, cancel, scheduler):
        self.observer = observer
        self.observable = observable
        self.cancel = cancel
        self.scheduler = scheduler
        self.received = 0
        self.schedule_disposable = None

        super(WindowedObserver, self).__init__()

    def _on_completed_core(self):
        self.observer.on_completed()
        self.dispose()

    def _on_error_core(self, error):
        self.observer.on_error(error)
        self.dispose()

    def _on_next_core(self, value):
        def inner_schedule_method(s, state):
            return self.observable.source.request(self.observable.window_size)

        self.observer.on_next(value)
        self.received = (self.received + 1) % self.observable.window_size
        if self.received == 0:
            self.schedule_disposable = self.scheduler.schedule(inner_schedule_method)

    def dispose(self):
        self.observer = None
        if self.cancel:
            self.cancel.dispose()
            self.cancel = None

        if self.schedule_disposable:
            self.schedule_disposable.dispose()
            self.schedule_disposable = None

        super(WindowedObserver, self).dispose()


class WindowedObservable(ObservableBase):
    def __init__(self, source, window_size, scheduler=None):
        super(WindowedObservable, self).__init__()

        self.source = source
        self.window_size = window_size
        self.scheduler = scheduler or current_thread_scheduler
        self.subscription = None

    def _subscribe_core(self, observer):
        observer = WindowedObserver(observer, self, self.subscription, self.scheduler)
        self.subscription = self.source.subscribe(observer)

        def action(scheduler, state):
            self.source.request(self.window_size)

        return CompositeDisposable(self.subscription, self.scheduler.schedule(action))
