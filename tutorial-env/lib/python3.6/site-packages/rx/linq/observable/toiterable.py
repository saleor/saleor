from rx.core import Observable, AnonymousObservable
from rx.internal import extensionmethod


@extensionmethod(Observable)
def to_iterable(self):
    """Creates an iterable from an observable sequence.

    :returns: An observable sequence containing a single element with a list
    containing all the elements of the source sequence.
    :rtype: Observable
    """

    source = self

    def subscribe(observer):
        queue = []

        def on_next(item):
            queue.append(item)

        def on_completed():
            observer.on_next(queue)
            observer.on_completed()

        return source.subscribe(on_next, observer.on_error, on_completed)
    return AnonymousObservable(subscribe)
