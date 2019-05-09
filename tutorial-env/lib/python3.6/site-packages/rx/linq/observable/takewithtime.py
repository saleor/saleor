from rx import Observable, AnonymousObservable
from rx.disposables import CompositeDisposable
from rx.concurrency import timeout_scheduler
from rx.internal import extensionmethod


@extensionmethod(Observable)
def take_with_time(self, duration, scheduler=None):
    """Takes elements for the specified duration from the start of the
    observable source sequence, using the specified scheduler to run timers.

    Example:
    res = source.take_with_time(5000,  [optional scheduler])

    Description:
    This operator accumulates a queue with a length enough to store elements
    received during the initial duration window. As more elements are
    received, elements older than the specified duration are taken from the
    queue and produced on the result sequence. This causes elements to be
    delayed with duration.

    Keyword arguments:
    duration -- {Number} Duration for taking elements from the start of the
        sequence.
    scheduler -- {Scheduler} Scheduler to run the timer on. If not
        specified, defaults to rx.Scheduler.timeout.

    Returns {Observable} An observable sequence with the elements taken
    during the specified duration from the start of the source sequence.
    """

    source = self
    scheduler = scheduler or timeout_scheduler

    def subscribe(observer):
        def action(scheduler, state):
            observer.on_completed()
        disposable = scheduler.schedule_relative(duration, action)
        return CompositeDisposable(disposable, source.subscribe(observer))
    return AnonymousObservable(subscribe)
