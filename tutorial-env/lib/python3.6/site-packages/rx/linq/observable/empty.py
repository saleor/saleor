from rx.core import Observable, AnonymousObservable
from rx.concurrency import immediate_scheduler
from rx.internal import extensionclassmethod


@extensionclassmethod(Observable)
def empty(cls, scheduler=None):
    """Returns an empty observable sequence, using the specified scheduler
    to send out the single OnCompleted message.

    1 - res = rx.Observable.empty()
    2 - res = rx.Observable.empty(rx.Scheduler.timeout)

    scheduler -- Scheduler to send the termination call on.

    Returns an observable sequence with no elements.
    """

    scheduler = scheduler or immediate_scheduler

    def subscribe(observer):
        def action(scheduler, state):
            observer.on_completed()

        return scheduler.schedule(action)
    return AnonymousObservable(subscribe)

