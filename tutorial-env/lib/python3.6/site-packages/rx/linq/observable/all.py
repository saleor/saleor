from rx.core import Observable
from rx.internal import extensionmethod


@extensionmethod(Observable, alias="every")
def all(self, predicate):
    """Determines whether all elements of an observable sequence satisfy a
    condition.

    1 - res = source.all(lambda value: value.length > 3)

    Keyword arguments:
    :param bool predicate: A function to test each element for a condition.

    :returns: An observable sequence containing a single element determining
    whether all elements in the source sequence pass the test in the
    specified predicate.
    """

    return self.filter(lambda v: not predicate(v)).some().map(lambda b: not b)
