from rx import Observable, AnonymousObservable
from rx.internal import extensionmethod
from rx.concurrency import timeout_scheduler


@extensionmethod(Observable)
def take_last_with_time(self, duration, scheduler=None):
    """Returns elements within the specified duration from the end of the
    observable source sequence, using the specified schedulers to run timers
    and to drain the collected elements.

    Example:
    res = source.take_last_with_time(5000, scheduler)

    Description:
    This operator accumulates a queue with a length enough to store elements
    received during the initial duration window. As more elements are
    received, elements older than the specified duration are taken from the
    queue and produced on the result sequence. This causes elements to be
    delayed with duration.

    Keyword arguments:
    duration -- {Number} Duration for taking elements from the end of the
        sequence.
    scheduler -- {Scheduler} [Optional] Scheduler to run the timer on. If
        not specified, defaults to rx.Scheduler.timeout.

    Returns {Observable} An observable sequence with the elements taken
    during the specified duration from the end of the source sequence.
    """

    source = self
    scheduler = scheduler or timeout_scheduler
    duration = scheduler.to_timedelta(duration)

    def subscribe(observer):
        q = []

        def on_next(x):
            now = scheduler.now
            q.append({"interval": now, "value": x})
            while len(q) and now - q[0]["interval"] >= duration:
                q.pop(0)

        def on_completed():
            now = scheduler.now
            while len(q):
                next = q.pop(0)
                if now - next["interval"] <= duration:
                    observer.on_next(next["value"])

            observer.on_completed()

        return source.subscribe(on_next, observer.on_error, on_completed)
    return AnonymousObservable(subscribe)
