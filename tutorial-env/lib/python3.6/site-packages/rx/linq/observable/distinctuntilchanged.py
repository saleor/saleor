from rx.core import Observable, AnonymousObservable
from rx.internal.basic import identity, default_comparer
from rx.internal import extensionmethod


@extensionmethod(Observable)
def distinct_until_changed(self, key_selector=None, comparer=None):
    """Returns an observable sequence that contains only distinct
    contiguous elements according to the key_selector and the comparer.

    1 - obs = observable.distinct_until_changed();
    2 - obs = observable.distinct_until_changed(lambda x: x.id)
    3 - obs = observable.distinct_until_changed(lambda x: x.id,
                                                lambda x, y: x == y)

    key_selector -- [Optional] A function to compute the comparison key for
        each element. If not provided, it projects the value.
    comparer -- [Optional] Equality comparer for computed key values. If
        not provided, defaults to an equality comparer function.

    Return An observable sequence only containing the distinct contiguous
    elements, based on a computed key value, from the source sequence.
    """

    source = self
    key_selector = key_selector or identity
    comparer = comparer or default_comparer

    def subscribe(observer):
        has_current_key = [False]
        current_key = [None]

        def on_next(value):
            comparer_equals = False
            try:
                key = key_selector(value)
            except Exception as exception:
                observer.on_error(exception)
                return

            if has_current_key[0]:
                try:
                    comparer_equals = comparer(current_key[0], key)
                except Exception as exception:
                    observer.on_error(exception)
                    return

            if not has_current_key[0] or not comparer_equals:
                has_current_key[0] = True
                current_key[0] = key
                observer.on_next(value)

        return source.subscribe(on_next, observer.on_error, observer.on_completed)
    return AnonymousObservable(subscribe)
