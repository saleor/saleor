from rx.core import Observable, AnonymousObservable

from rx.concurrency import immediate_scheduler
from rx.internal import extensionclassmethod


@extensionclassmethod(Observable, alias="throw_exception")
def throw(cls, exception, scheduler=None):
    """Returns an observable sequence that terminates with an exception,
    using the specified scheduler to send out the single OnError message.

    1 - res = rx.Observable.throw_exception(Exception('Error'))
    2 - res = rx.Observable.throw_exception(Exception('Error'),
                                            rx.Scheduler.timeout)

    Keyword arguments:
    exception -- An object used for the sequence's termination.
    scheduler -- Scheduler to send the exceptional termination call on. If
        not specified, defaults to ImmediateScheduler.

    Returns the observable sequence that terminates exceptionally with the
    specified exception object.
    """

    scheduler = scheduler or immediate_scheduler

    exception = exception if isinstance(exception, Exception) else Exception(exception)

    def subscribe(observer):
        def action(scheduler, state):
            observer.on_error(exception)

        return scheduler.schedule(action)
    return AnonymousObservable(subscribe)
