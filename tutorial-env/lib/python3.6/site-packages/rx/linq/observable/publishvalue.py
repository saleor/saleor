from rx import Observable
from rx.subjects import BehaviorSubject
from rx.internal import extensionmethod


@extensionmethod(Observable)
def publish_value(self, initial_value, selector=None):
    """Returns an observable sequence that is the result of invoking the
    selector on a connectable observable sequence that shares a single
    subscription to the underlying sequence and starts with initial_value.

    This operator is a specialization of Multicast using a BehaviorSubject.

    Example:
    res = source.publish_value(42)
    res = source.publish_value(42, lambda x: x.map(lambda y: y * y))

    Keyword arguments:
    initial_value -- {Mixed} Initial value received by observers upon
        subscription.
    selector -- {Function} [Optional] Optional selector function which can
        use the multicasted source sequence as many times as needed, without
        causing multiple subscriptions to the source sequence. Subscribers
        to the given source will receive immediately receive the initial
        value, followed by all notifications of the source from the time of
        the subscription on.

    Returns {Observable} An observable sequence that contains the elements
    of a sequence produced by multicasting the source sequence within a
    selector function.
    """

    if selector:
        def subject_selector():
            return BehaviorSubject(initial_value)

        return self.multicast(subject_selector=subject_selector,
                              selector=selector)
    else:
        return self.multicast(BehaviorSubject(initial_value))
