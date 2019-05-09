from rx.core import Observable, AnonymousObservable
from rx.core.notification import OnNext, OnError, OnCompleted
from rx.internal import extensionmethod


@extensionmethod(Observable)
def materialize(self):
    """Materializes the implicit notifications of an observable sequence as
    explicit notification values.

    Returns an observable sequence containing the materialized notification
    values from the source sequence.
    """

    source = self

    def subscribe(observer):
        def on_next(value):
            observer.on_next(OnNext(value))

        def on_error(exception):
            observer.on_next(OnError(exception))
            observer.on_completed()

        def on_completed():
            observer.on_next(OnCompleted())
            observer.on_completed()

        return source.subscribe(on_next, on_error, on_completed)
    return AnonymousObservable(subscribe)

