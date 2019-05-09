from rx import Observable, AnonymousObservable
from rx.internal import extensionmethod

def _to_dict(source, map_type, key_selector, element_selector):
    def subscribe(observer):
        m = map_type()

        def on_next(x):
            try:
                key = key_selector(x)
            except Exception as ex:
                observer.on_error(ex)
                return

            element = x
            if element_selector:
                try:
                    element = element_selector(x)
                except Exception as ex:
                    observer.on_error(ex)
                    return

            m[key] = element

        def on_completed():
            observer.on_next(m)
            observer.on_completed()

        return source.subscribe(on_next, observer.on_error, on_completed)
    return AnonymousObservable(subscribe)


@extensionmethod(Observable)
def to_dict(self, key_selector, element_selector=None):
    """Converts the observable sequence to a Map if it exists.

    Keyword arguments:
    key_selector -- {Function} A function which produces the key for the
        Map.
    element_selector -- {Function} [Optional] An optional function which
        produces the element for the Map. If not present, defaults to the
        value from the observable sequence.
    Returns {Observable} An observable sequence with a single value of a Map
    containing the values from the observable sequence.
    """

    return _to_dict(self, dict, key_selector, element_selector)

