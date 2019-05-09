from rx.core import Observable
from rx.internal import extensionmethod

from .find import find_value


@extensionmethod(Observable)
def find_index(self, predicate):
    """Searches for an element that matches the conditions defined by the
    specified predicate, and returns an Observable sequence with the
    zero-based index of the first occurrence within the entire Observable
    sequence.

    Keyword Arguments:
    predicate -- {Function} The predicate that defines the conditions of the
        element to search for.

    Returns an observable {Observable} sequence with the zero-based index of
    the first occurrence of an element that matches the conditions defined
    by match, if found; otherwise, -1.
    """
    return find_value(self, predicate, True)
