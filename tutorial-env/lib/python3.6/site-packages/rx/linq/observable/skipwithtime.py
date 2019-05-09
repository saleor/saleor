from rx import Observable, AnonymousObservable
from rx.disposables import CompositeDisposable
from rx.internal import extensionmethod
from rx.concurrency import timeout_scheduler

@extensionmethod(Observable)
def skip_with_time(self, duration, scheduler=None):
    """Skips elements for the specified duration from the start of the
    observable source sequence, using the specified scheduler to run timers.

    Example:
    1 - res = source.skip_with_time(5000, [optional scheduler])

    Description:
    Specifying a zero value for duration doesn't guarantee no elements will
    be dropped from the start of the source sequence. This is a side-effect
    of the asynchrony introduced by the scheduler, where the action that
    causes callbacks from the source sequence to be forwarded may not
    execute immediately, despite the zero due time.

    Errors produced by the source sequence are always forwarded to the
    result sequence, even if the error occurs before the duration.

    Keyword arguments:
    duration -- {Number} Duration for skipping elements from the start of
        the sequence.
    scheduler -- {Scheduler} Scheduler to run the timer on. If not
        specified, defaults to Rx.Scheduler.timeout.

    Returns n observable {Observable} sequence with the elements skipped
    during the specified duration from the start of the source sequence.
    """

    source = self
    scheduler = scheduler or timeout_scheduler

    def subscribe(observer):
        open = [False]

        def action(scheduler, state):
            open[0] = True

        t = scheduler.schedule_relative(duration, action)

        def on_next(x):
            if open[0]:
                observer.on_next(x)

        d = source.subscribe(on_next, observer.on_error, observer.on_completed)
        return CompositeDisposable(t, d)
    return AnonymousObservable(subscribe)

