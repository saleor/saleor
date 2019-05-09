from rx import Observable, AnonymousObservable
from rx.internal import extensionmethod


@extensionmethod(Observable)
def take_last(self, count):
    """Returns a specified number of contiguous elements from the end of an
    observable sequence.

    Example:
    res = source.take_last(5)

    Description:
    This operator accumulates a buffer with a length enough to store
    elements count elements. Upon completion of the source sequence, this
    buffer is drained on the result sequence. This causes the elements to be
    delayed.

    Keyword arguments:
    :param int count: Number of elements to take from the end of the source
        sequence.

    :returns: An observable sequence containing the specified number of elements 
        from the end of the source sequence.
    :rtype: Observable
    """

    source = self

    def subscribe(observer):
        q = []
        def on_next(x):
            q.append(x)
            if len(q) > count:
                q.pop(0)

        def on_completed():
            while len(q):
                observer.on_next(q.pop(0))
            observer.on_completed()

        return source.subscribe(on_next, observer.on_error, on_completed)
    return AnonymousObservable(subscribe)
