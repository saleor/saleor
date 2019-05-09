from rx import Observable, AnonymousObservable
from rx.internal import ArgumentOutOfRangeException
from rx.internal import extensionmethod


@extensionmethod(Observable)
def take(self, count, scheduler=None):
    """Returns a specified number of contiguous elements from the start of
    an observable sequence, using the specified scheduler for the edge case
    of take(0).

    1 - source.take(5)
    2 - source.take(0, rx.Scheduler.timeout)

    Keyword arguments:
    count -- The number of elements to return.
    scheduler -- [Optional] Scheduler used to produce an OnCompleted
        message in case count is set to 0.

    Returns an observable sequence that contains the specified number of
    elements from the start of the input sequence.
    """

    if count < 0:
        raise ArgumentOutOfRangeException()

    if not count:
        return Observable.empty(scheduler)

    observable = self
    def subscribe(observer):
        remaining = [count]

        def on_next(value):
            if remaining[0] > 0:
                remaining[0] -= 1
                observer.on_next(value)
                if not remaining[0]:
                    observer.on_completed()

        return observable.subscribe(on_next, observer.on_error, observer.on_completed)
    return AnonymousObservable(subscribe)
