from rx import Observable, AnonymousObservable
from rx.internal import extensionmethod


@extensionmethod(Observable)
def skip_last(self, count):
    """Bypasses a specified number of elements at the end of an observable
    sequence.

    Description:
    This operator accumulates a queue with a length enough to store the
    first `count` elements. As more elements are received, elements are
    taken from the front of the queue and produced on the result sequence.
    This causes elements to be delayed.

    Keyword arguments
    count -- Number of elements to bypass at the end of the source sequence.

    Returns an observable {Observable} sequence containing the source
    sequence elements except for the bypassed ones at the end.
    """

    source = self

    def subscribe(observer):
        q = []

        def on_next(x):
            front = None
            with self.lock:
                q.append(x)
                if len(q) > count:
                    front = q.pop(0)

            if not front is None:
                observer.on_next(front)

        return source.subscribe(on_next, observer.on_error, 
                                observer.on_completed)
    return AnonymousObservable(subscribe)

