from rx import Observable, AnonymousObservable
from rx.internal import extensionmethod

def _to_set(source, set_type):
    def subscribe(observer):
        s = set_type()

        def on_completed():
            observer.on_next(s)
            observer.on_completed()

        return source.subscribe(s.add, observer.on_error, on_completed)
    return AnonymousObservable(subscribe)


@extensionmethod(Observable)
def to_set(self):
    """Converts the observable sequence to a set.

    Returns {Observable} An observable sequence with a single value of a set
    containing the values from the observable sequence.
    """

    return _to_set(self, set)
