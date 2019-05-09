from rx import Observable
from rx.concurrency import timeout_scheduler
from rx.internal import extensionmethod


@extensionmethod(Observable)
def buffer_with_time_or_count(self, timespan, count, scheduler=None):
    """Projects each element of an observable sequence into a buffer that
    is completed when either it's full or a given amount of time has
    elapsed.

    # 5s or 50 items in an array
    1 - res = source.buffer_with_time_or_count(5000, 50)
    # 5s or 50 items in an array
    2 - res = source.buffer_with_time_or_count(5000, 50, Scheduler.timeout)

    Keyword arguments:
    timespan -- Maximum time length of a buffer.
    count -- Maximum element count of a buffer.
    scheduler -- [Optional] Scheduler to run bufferin timers on. If not
        specified, the timeout scheduler is used.

    Returns an observable sequence of buffers.
    """

    scheduler = scheduler or timeout_scheduler
    return self.window_with_time_or_count(timespan, count, scheduler) \
        .flat_map(lambda x: x.to_iterable())
