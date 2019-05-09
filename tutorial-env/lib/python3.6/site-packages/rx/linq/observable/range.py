from rx.core import Observable, AnonymousObservable
from rx.concurrency import current_thread_scheduler
from rx.internal import extensionclassmethod
from rx.disposables import MultipleAssignmentDisposable


@extensionclassmethod(Observable)
def range(cls, start, count, scheduler=None):
    """Generates an observable sequence of integral numbers within a
    specified range, using the specified scheduler to send out observer
    messages.

    1 - res = Rx.Observable.range(0, 10)
    2 - res = Rx.Observable.range(0, 10, rx.Scheduler.timeout)

    Keyword arguments:
    start -- The value of the first integer in the sequence.
    count -- The number of sequential integers to generate.
    scheduler -- [Optional] Scheduler to run the generator loop on. If not
        specified, defaults to Scheduler.current_thread.

    Returns an observable sequence that contains a range of sequential
    integral numbers.
    """
    scheduler = scheduler or current_thread_scheduler
    end = start + count

    def subscribe(observer):
        sd = MultipleAssignmentDisposable()

        def action(scheduler, n):
            if n < end:
                observer.on_next(n)
                sd.disposable = scheduler.schedule(action, n + 1)
            else:
                observer.on_completed()

        sd.disposable = scheduler.schedule(action, start)
        return sd
    return AnonymousObservable(subscribe)
