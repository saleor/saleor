from rx import Observable, AnonymousObservable
from rx.internal.utils import adapt_call
from rx.internal import extensionmethod


@extensionmethod(Observable)
def take_while(self, predicate):
    """Returns elements from an observable sequence as long as a specified
    condition is true. The element's index is used in the logic of the
    predicate function.

    1 - source.take_while(lambda value: value < 10)
    2 - source.take_while(lambda value, index: value < 10 or index < 10)

    Keyword arguments:
    predicate -- A function to test each element for a condition; the
        second parameter of the function represents the index of the source
        element.

    Returns an observable sequence that contains the elements from the
    input sequence that occur before the element at which the test no
    longer passes.
    """

    predicate = adapt_call(predicate)
    observable = self
    def subscribe(observer):
        running, i = [True], [0]

        def on_next(value):
            with self.lock:
                if not running[0]:
                    return

                try:
                    running[0] = predicate(value, i[0])
                except Exception as exn:
                    observer.on_error(exn)
                    return
                else:
                    i[0] += 1

            if running[0]:
                observer.on_next(value)
            else:
                observer.on_completed()

        return observable.subscribe(on_next, observer.on_error, observer.on_completed)
    return AnonymousObservable(subscribe)

