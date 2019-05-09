import logging

from rx.core import Observable
from rx.concurrency import timeout_scheduler
from rx.internal.utils import Timestamp
from rx.internal import extensionmethod

log = logging.getLogger("Rx")


@extensionmethod(Observable)
def timestamp(self, scheduler=None):
    """Records the timestamp for each value in an observable sequence.

    1 - res = source.timestamp() # produces objects with attributes "value" and
        "timestamp", where value is the original value.
    2 - res = source.timestamp(Scheduler.timeout)

    :param Scheduler scheduler: [Optional] Scheduler used to compute timestamps. If not
        specified, the timeout scheduler is used.

    Returns an observable sequence with timestamp information on values.
    """

    scheduler = scheduler or timeout_scheduler

    def selector(x):
        return Timestamp(value=x, timestamp=scheduler.now)

    return self.map(selector)
