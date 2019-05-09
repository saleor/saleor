from rx.core import Observable
from rx.concurrency import timeout_scheduler
from rx.internal import extensionmethod


@extensionmethod(Observable)
def buffer_with_time(self, timespan, timeshift=None, scheduler=None):
    """Projects each element of an observable sequence into zero or more
    buffers which are produced based on timing information.

    # non-overlapping segments of 1 second
    1 - res = xs.buffer_with_time(1000)
    # segments of 1 second with time shift 0.5 seconds
    2 - res = xs.buffer_with_time(1000, 500)

    Keyword arguments:
    timespan -- Length of each buffer (specified as an integer denoting
        milliseconds).
    timeshift -- [Optional] Interval between creation of consecutive
        buffers (specified as an integer denoting milliseconds), or an
        optional scheduler parameter. If not specified, the time shift
        corresponds to the timespan parameter, resulting in non-overlapping
        adjacent buffers.
    scheduler -- [Optional] Scheduler to run buffer timers on. If not
        specified, the timeout scheduler is used.

    Returns an observable sequence of buffers.
    """

    if not timeshift:
        timeshift = timespan

    scheduler = scheduler or timeout_scheduler

    return self.window_with_time(timespan, timeshift, scheduler) \
        .select_many(lambda x: x.to_iterable())
