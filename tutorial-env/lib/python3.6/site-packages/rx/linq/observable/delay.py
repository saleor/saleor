import logging
from datetime import datetime, timedelta

from rx.core import Observable, AnonymousObservable
from rx.disposables import CompositeDisposable, SerialDisposable, MultipleAssignmentDisposable
from rx.concurrency import timeout_scheduler
from rx.internal import extensionmethod

log = logging.getLogger("Rx")


class Timestamp(object):
    def __init__(self, value, timestamp):
        self.value = value
        self.timestamp = timestamp


def observable_delay_timespan(source, duetime, scheduler):
    duetime = scheduler.to_timedelta(duetime)

    def subscribe(observer):
        cancelable = SerialDisposable()
        exception = [None]
        active = [False]
        running = [False]
        queue = []

        def on_next(notification):
            log.debug("observable_delay_timespan:subscribe:on_next()")
            should_run = False

            with source.lock:
                if notification.value.kind == 'E':
                    del queue[:]
                    queue.append(notification)
                    exception[0] = notification.value.exception
                    should_run = not running[0]
                else:
                    queue.append(Timestamp(value=notification.value, timestamp=notification.timestamp + duetime))
                    should_run = not active[0]
                    active[0] = True

            if should_run:
                if exception[0]:
                    log.error("*** Exception: %s", exception[0])
                    observer.on_error(exception[0])
                else:
                    mad = MultipleAssignmentDisposable()
                    cancelable.disposable = mad

                    def action(scheduler, state):
                        if exception[0]:
                            log.error("observable_delay_timespan:subscribe:on_next:action(), exception: %s", exception[0])
                            return

                        with source.lock:
                            running[0] = True
                            while True:
                                result = None
                                if len(queue) and queue[0].timestamp <= scheduler.now:
                                    result = queue.pop(0).value

                                if result:
                                    result.accept(observer)

                                if not result:
                                    break

                            should_continue = False
                            recurse_duetime = 0
                            if len(queue):
                                should_continue = True
                                diff = queue[0].timestamp - scheduler.now
                                zero = timedelta(0) if isinstance(diff, timedelta) else 0
                                recurse_duetime = max(zero, diff)
                            else:
                                active[0] = False

                            ex = exception[0]
                            running[0] = False

                        if ex:
                            observer.on_error(ex)
                        elif should_continue:
                            mad.disposable = scheduler.schedule_relative(recurse_duetime, action)

                    mad.disposable = scheduler.schedule_relative(duetime, action)
        subscription = source.materialize().timestamp(scheduler).subscribe(on_next)
        return CompositeDisposable(subscription, cancelable)
    return AnonymousObservable(subscribe)


def observable_delay_date(source, duetime, scheduler):
    def defer():
        timespan = scheduler.to_datetime(duetime) - scheduler.now
        return observable_delay_timespan(source, timespan, scheduler)

    return Observable.defer(defer)


@extensionmethod(Observable)
def delay(self, duetime, scheduler=None):
    """Time shifts the observable sequence by duetime. The relative time
    intervals between the values are preserved.

    1 - res = rx.Observable.delay(datetime())
    2 - res = rx.Observable.delay(datetime(), Scheduler.timeout)

    3 - res = rx.Observable.delay(5000)
    4 - res = rx.Observable.delay(5000, Scheduler.timeout)

    Keyword arguments:
    :param datetime|int duetime: Absolute (specified as a datetime object) or
        relative time (specified as an integer denoting milliseconds) by which
        to shift the observable sequence.
    :param Scheduler scheduler: [Optional] Scheduler to run the delay timers on.
        If not specified, the timeout scheduler is used.

    :returns: Time-shifted sequence.
    :rtype: Observable
    """

    scheduler = scheduler or timeout_scheduler
    if isinstance(duetime, datetime):
        observable = observable_delay_date(self, duetime, scheduler)
    else:
        observable = observable_delay_timespan(self, duetime, scheduler)

    return observable
