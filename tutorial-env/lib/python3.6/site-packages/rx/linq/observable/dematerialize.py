from rx.core import Observable, AnonymousObservable
from rx.internal import extensionmethod


@extensionmethod(Observable)
def dematerialize(self):
    """Dematerializes the explicit notification values of an observable
    sequence as implicit notifications.

    Returns an observable sequence exhibiting the behavior corresponding to
    the source sequence's notification values.
    """

    source = self

    def subscribe(observer):
        def on_next(value):
            return value.accept(observer)

        return source.subscribe(on_next, observer.on_error, observer.on_completed)
    return AnonymousObservable(subscribe)
