from rx.core import Observable
from rx.subjects import ReplaySubject
from rx.internal import extensionmethod


@extensionmethod(Observable)
def replay(self, selector, buffer_size=None, window=None, scheduler=None):
    """Returns an observable sequence that is the result of invoking the
    selector on a connectable observable sequence that shares a single
    subscription to the underlying sequence replaying notifications subject
    to a maximum time length for the replay buffer.

    This operator is a specialization of Multicast using a ReplaySubject.

    Example:
    res = source.replay(buffer_size=3)
    res = source.replay(buffer_size=3, window=500)
    res = source.replay(None, 3, 500, scheduler)
    res = source.replay(lambda x: x.take(6).repeat(), 3, 500, scheduler)

    Keyword arguments:
    selector -- [Optional] Selector function which can use the multicasted
        source sequence as many times as needed, without causing multiple
        subscriptions to the source sequence. Subscribers to the given
        source will receive all the notifications of the source subject to
        the specified replay buffer trimming policy.
    buffer_size -- [Optional] Maximum element count of the replay buffer.
    window -- [Optional] Maximum time length of the replay buffer.
    scheduler -- [Optional] Scheduler where connected observers within the
        selector function will be invoked on.

    Returns {Observable} An observable sequence that contains the elements
    of a sequence produced by multicasting the source sequence within a
    selector function.
    """

    if callable(selector):
        def subject_selector():
            return ReplaySubject(buffer_size, window, scheduler)
        return self.multicast(subject_selector=subject_selector,
                             selector=selector)
    else:
        return self.multicast(ReplaySubject(buffer_size, window, scheduler))

