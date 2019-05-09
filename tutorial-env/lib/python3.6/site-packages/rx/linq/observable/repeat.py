from rx.core import Observable
from rx.internal.enumerable import Enumerable
from rx.concurrency import current_thread_scheduler
from rx.internal import extensionmethod, extensionclassmethod


@extensionmethod(Observable, instancemethod=True)
def repeat(self, repeat_count=None):
    """Repeats the observable sequence a specified number of times. If the
    repeat count is not specified, the sequence repeats indefinitely.

    1 - repeated = source.repeat()
    2 - repeated = source.repeat(42)

    Keyword arguments:
    repeat_count -- Number of times to repeat the sequence. If not
        provided, repeats the sequence indefinitely.

    Returns the observable sequence producing the elements of the given
    sequence repeatedly."""

    return Observable.defer(lambda: Observable.concat(Enumerable.repeat(self, repeat_count)))


@extensionmethod(Observable)
def __mul__(self, b):
    """Pythonic version of repeat

    Example:
    yx = xs * 5

    Returns self.repeat(b)"""

    assert isinstance(b, int)
    return self.repeat(b)


@extensionclassmethod(Observable)
def repeat(cls, value=None, repeat_count=None, scheduler=None):
    """Generates an observable sequence that repeats the given element the
    specified number of times, using the specified scheduler to send out
    observer messages.

    1 - res = rx.Observable.repeat(42)
    2 - res = rx.Observable.repeat(42, 4)
    3 - res = rx.Observable.repeat(42, 4, Rx.Scheduler.timeout)
    4 - res = rx.Observable.repeat(42, None, Rx.Scheduler.timeout)

    Keyword arguments:
    value -- Element to repeat.
    repeat_count -- [Optional] Number of times to repeat the element. If not
        specified, repeats indefinitely.
    scheduler -- Scheduler to run the producer loop on. If not specified,
        defaults to ImmediateScheduler.

    Returns an observable sequence that repeats the given element the
    specified number of times."""

    scheduler = scheduler or current_thread_scheduler
    if repeat_count == -1:
        repeat_count = None

    xs = Observable.return_value(value, scheduler)
    return xs.repeat(repeat_count)
