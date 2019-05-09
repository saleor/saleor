from rx.core import Observable, AnonymousObservable
from rx.disposables import CompositeDisposable, \
    SingleAssignmentDisposable, SerialDisposable
from rx.internal import extensionmethod


@extensionmethod(Observable)
def timeout_with_selector(self, first_timeout=None,
                          timeout_duration_selector=None, other=None):
    """Returns the source observable sequence, switching to the other
    observable sequence if a timeout is signaled.

    1 - res = source.timeout_with_selector(rx.Observable.timer(500))
    2 - res = source.timeout_with_selector(rx.Observable.timer(500),
                lambda x: rx.Observable.timer(200))
    3 - res = source.timeout_with_selector(rx.Observable.timer(500),
                lambda x: rx.Observable.timer(200)),
                rx.Observable.return_value(42))

    first_timeout -- [Optional] Observable sequence that represents the
        timeout for the first element. If not provided, this defaults to
        Observable.never().
    timeout_Duration_selector -- [Optional] Selector to retrieve an
        observable sequence that represents the timeout between the current
        element and the next element.
    other -- [Optional] Sequence to return in case of a timeout. If not
        provided, this is set to Observable.throw_exception().

    Returns the source sequence switching to the other sequence in case of
    a timeout.
    """

    first_timeout = first_timeout or Observable.never()
    other = other or Observable.throw_exception(Exception('Timeout'))
    source = self

    def subscribe(observer):
        subscription = SerialDisposable()
        timer = SerialDisposable()
        original = SingleAssignmentDisposable()

        subscription.disposable = original

        switched = False
        _id = [0]

        def set_timer(timeout):
            my_id = _id[0]

            def timer_wins():
                return _id[0] == my_id

            d = SingleAssignmentDisposable()
            timer.disposable = d

            def on_next(x):
                if timer_wins():
                    subscription.disposable = other.subscribe(observer)

                d.dispose()

            def on_error(e):
                if timer_wins():
                    observer.on_error(e)

            def on_completed():
                if timer_wins():
                    subscription.disposable = other.subscribe(observer)

            d.disposable = timeout.subscribe(on_next, on_error, on_completed)

        set_timer(first_timeout)

        def observer_wins():
            res = not switched
            if res:
                _id[0] += 1

            return res

        def on_next(x):
            if observer_wins():
                observer.on_next(x)
                timeout = None
                try:
                    timeout = timeout_duration_selector(x)
                except Exception as e:
                    observer.on_error(e)
                    return

                set_timer(timeout)

        def on_error(e):
            if observer_wins():
                observer.on_error(e)

        def on_completed():
            if observer_wins():
                observer.on_completed()

        original.disposable = source.subscribe(on_next, on_error, on_completed)
        return CompositeDisposable(subscription, timer)
    return AnonymousObservable(subscribe)
