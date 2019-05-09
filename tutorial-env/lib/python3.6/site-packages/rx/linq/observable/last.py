from rx import Observable
from rx.internal import extensionmethod

from .lastordefault import last_or_default_async


@extensionmethod(Observable)
def last(self, predicate=None):
    """Returns the last element of an observable sequence that satisfies the
    condition in the predicate if specified, else the last element.

    Example:
    res = source.last()
    res = source.last(lambda x: x > 3)

    Keyword arguments:
    predicate -- {Function} [Optional] A predicate function to evaluate for
        elements in the source sequence.

    Returns {Observable} Sequence containing the last element in the
    observable sequence that satisfies the condition in the predicate.
    """

    return self.filter(predicate).last() if predicate else last_or_default_async(self, False)
