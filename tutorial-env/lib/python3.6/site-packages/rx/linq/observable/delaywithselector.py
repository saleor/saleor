from rx.core import Observable, AnonymousObservable
from rx.disposables import CompositeDisposable, \
    SingleAssignmentDisposable, SerialDisposable
from rx.internal import extensionmethod


@extensionmethod(Observable)
def delay_with_selector(self, subscription_delay=None,
                        delay_duration_selector=None):
    """Time shifts the observable sequence based on a subscription delay
    and a delay selector function for each element.

    # with selector only
    1 - res = source.delay_with_selector(lambda x: Scheduler.timer(5000))
    # with delay and selector
    2 - res = source.delay_with_selector(Observable.timer(2000),
                                         lambda x: Observable.timer(x))

    subscription_delay -- [Optional] Sequence indicating the delay for the
        subscription to the source.
    delay_duration_selector [Optional] Selector function to retrieve a
        sequence indicating the delay for each given element.

    Returns time-shifted sequence.
    """

    source = self
    sub_delay, selector = None, None

    if isinstance(subscription_delay, Observable):
        selector = delay_duration_selector
        sub_delay = subscription_delay
    else:
        selector = subscription_delay

    def subscribe(observer):
        delays = CompositeDisposable()
        at_end = [False]

        def done():
            if (at_end[0] and delays.length == 0):
                observer.on_completed()

        subscription = SerialDisposable()

        def start():
            def on_next(x):
                try:
                    delay = selector(x)
                except Exception as error:
                    observer.on_error(error)
                    return

                d = SingleAssignmentDisposable()
                delays.add(d)

                def on_next(_):
                    observer.on_next(x)
                    delays.remove(d)
                    done()

                def on_completed():
                    observer.on_next(x)
                    delays.remove(d)
                    done()

                d.disposable = delay.subscribe(on_next, observer.on_error,
                                               on_completed)

            def on_completed():
                at_end[0] = True
                subscription.dispose()
                done()

            subscription.disposable = source.subscribe(on_next,
                                                       observer.on_error,
                                                       on_completed)

        if not sub_delay:
            start()
        else:
            subscription.disposable(sub_delay.subscribe(
                lambda _: start(),
                observer.on_error,
                start))

        return CompositeDisposable(subscription, delays)
    return AnonymousObservable(subscribe)
