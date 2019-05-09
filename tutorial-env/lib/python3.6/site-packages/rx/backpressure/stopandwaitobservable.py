from rx.core import Observer, ObservableBase

from rx.internal.utils import check_disposed
from rx.concurrency import timeout_scheduler


class StopAndWaitObserver(Observer):

    def __init__(self, observer, observable, cancel, scheduler=None):
        super(StopAndWaitObserver, self).__init__()

        self.scheduler = scheduler
        self.observer = observer
        self.observable = observable
        self.cancel = cancel
        self.is_disposed = False

    def on_completed(self):
        check_disposed(self)

        self.observer.on_completed()
        self.dispose()

    def on_error(self, error):
        check_disposed(self)

        self.observer.on_error(error)
        self.dispose()

    def on_next(self, value):
        check_disposed(self)

        self.observer.on_next(value)

        def action(scheduler, state):
            self.observable.source.request(1)
        self.scheduler.schedule(action)

    def dispose(self):
        self.observer = None
        if self.cancel:
            self.cancel.dispose()
            self.cancel = None

        self.is_disposed = True


class StopAndWaitObservable(ObservableBase):

    def __init__(self, source, scheduler=None):
        super(StopAndWaitObservable, self).__init__()
        self.scheduler = scheduler or timeout_scheduler
        self.source = source
        self.subscription = None

    def _subscribe_core(self, observer):
        observer = StopAndWaitObserver(observer, self, self.subscription, self.scheduler)
        self.subscription = self.source.subscribe(observer)

        def action(scheduler, state=None):
            self.source.request(1)

        self.scheduler.schedule(action)
        return self.subscription
