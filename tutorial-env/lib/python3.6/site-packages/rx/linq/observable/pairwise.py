from rx import Observable, AnonymousObservable
from rx.internal import extensionmethod


@extensionmethod(Observable)
def pairwise(self):
    """Returns a new observable that triggers on the second and subsequent
    triggerings of the input observable. The Nth triggering of the input
    observable passes the arguments from the N-1th and Nth triggering as a
    pair. The argument passed to the N-1th triggering is held in hidden
    internal state until the Nth triggering occurs.

    Returns an observable {Observable} that triggers on successive pairs of
    observations from the input observable as an array.
    """

    source = self

    def subscribe(observer):
        has_previous = [False]
        previous = [None]

        def on_next(x):
            pair = None

            with self.lock:
                if has_previous[0]:
                    pair = (previous[0], x)
                else:
                    has_previous[0] = True

                previous[0] = x

            if pair:
                observer.on_next(pair)

        return source.subscribe(on_next, observer.on_error, observer.on_completed)
    return AnonymousObservable(subscribe)
