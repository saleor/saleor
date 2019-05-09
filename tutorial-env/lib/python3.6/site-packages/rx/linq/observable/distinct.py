from rx.core import Observable, AnonymousObservable
from rx.internal.basic import identity, default_comparer
from rx.internal import extensionmethod

# Swap out for Array.findIndex
def array_index_of_comparer(array, item, comparer):
    for i, a in enumerate(array):
        if comparer(a, item):
            return i
    return -1

class HashSet(object):
    def __init__(self, comparer):
        self.comparer = comparer
        self.set = []

    def push(self, value):
        ret_value = array_index_of_comparer(self.set, value, self.comparer) == -1
        ret_value and self.set.append(value)
        return ret_value


@extensionmethod(Observable)
def distinct(self, key_selector=None, comparer=None):
    """Returns an observable sequence that contains only distinct elements
    according to the key_selector and the comparer. Usage of this operator
    should be considered carefully due to the maintenance of an internal
    lookup structure which can grow large.

    Example:
    res = obs = xs.distinct()
    obs = xs.distinct(lambda x: x.id)
    obs = xs.distinct(lambda x: x.id, lambda a,b: a == b)

    Keyword arguments:
    key_selector -- {Function} [Optional]  A function to compute the
        comparison key for each element.
    comparer -- {Function} [Optional]  Used to compare items in the
        collection.

    Returns an observable {Observable} sequence only containing the distinct
    elements, based on a computed key value, from the source sequence.
    """

    source = self
    comparer = comparer or default_comparer

    def subscribe(observer):
        hashset = HashSet(comparer)

        def on_next(x):
            key = x

            if key_selector:
                try:
                    key = key_selector(x)
                except Exception as ex:
                    observer.on_error(ex)
                    return

            hashset.push(key) and observer.on_next(x)
        return source.subscribe(on_next, observer.on_error,
                                observer.on_completed)
    return AnonymousObservable(subscribe)
