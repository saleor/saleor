from rx.internal import noop
from rx.core import Observable, AnonymousObservable
from rx.disposables import CompositeDisposable
from rx.internal import extensionmethod


@extensionmethod(Observable)
def take_until(self, other):
    """Returns the values from the source observable sequence until the
    other observable sequence produces a value.

    Keyword arguments:
    other -- Observable sequence that terminates propagation of elements of
        the source sequence.

    Returns an observable sequence containing the elements of the source
    sequence up to the point the other sequence interrupted further
    propagation.
    """

    source = self
    other = Observable.from_future(other)

    def subscribe(observer):

        def on_completed(x):
            observer.on_completed()

        return CompositeDisposable(
            source.subscribe(observer),
            other.subscribe(on_completed, observer.on_error, noop)
        )
    return AnonymousObservable(subscribe)


