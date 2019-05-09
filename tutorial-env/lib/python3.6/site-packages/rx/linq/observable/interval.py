from rx.core import Observable
from rx.concurrency import TimeoutScheduler
from rx.internal import extensionclassmethod


@extensionclassmethod(Observable)
def interval(cls, period, scheduler=None):
    """Returns an observable sequence that produces a value after each
    period.

    Example:
    1 - res = rx.Observable.interval(1000)
    2 - res = rx.Observable.interval(1000, rx.Scheduler.timeout)

    Keyword arguments:
    period -- Period for producing the values in the resulting sequence
        (specified as an integer denoting milliseconds).
    scheduler -- [Optional] Scheduler to run the timer on. If not specified,
        rx.Scheduler.timeout is used.

    Returns an observable sequence that produces a value after each period.
    """

    scheduler = scheduler or TimeoutScheduler()
    return Observable.timer(period, period, scheduler)
