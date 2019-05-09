from rx import Observable
from rx.internal import extensionmethod


@extensionmethod(Observable)
def group_by(self, key_selector, element_selector=None,
             key_serializer=None):
    """Groups the elements of an observable sequence according to a
    specified key selector function and comparer and selects the resulting
    elements by using a specified function.

    1 - observable.group_by(lambda x: x.id)
    2 - observable.group_by(lambda x: x.id, lambda x: x.name)
    3 - observable.group_by(
        lambda x: x.id,
        lambda x: x.name,
        lambda x: str(x))

    Keyword arguments:
    key_selector -- A function to extract the key for each element.
    element_selector -- [Optional] A function to map each source element to
        an element in an observable group.
    comparer -- {Function} [Optional] Used to determine whether the objects
        are equal.

    Returns a sequence of observable groups, each of which corresponds to a
    unique key value, containing all elements that share that same key
    value.
    """

    def duration_selector(x):
        return Observable.never()

    return self.group_by_until(key_selector, element_selector, duration_selector, key_serializer)
