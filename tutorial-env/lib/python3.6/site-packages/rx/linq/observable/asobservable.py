from rx.core import Observable, AnonymousObservable
from rx.internal import extensionmethod


@extensionmethod(Observable)
def as_observable(self):
    """Hides the identity of an observable sequence.

    :returns: An observable sequence that hides the identity of the source
        sequence.
    :rtype: Observable
    """

    source = self

    def subscribe(observer):
        return source.subscribe(observer)

    return AnonymousObservable(subscribe)
