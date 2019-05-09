from rx import Observable
from rx.internal import extensionmethod

from .singleordefault import single_or_default_async


@extensionmethod(Observable)
def single(self, predicate=None):
    """Returns the only element of an observable sequence that satisfies the
    condition in the optional predicate, and reports an exception if there
    is not exactly one element in the observable sequence.

    Example:
    res = source.single()
    res = source.single(lambda x: x == 42)

    Keyword arguments:
    predicate -- {Function} [Optional] A predicate function to evaluate for
        elements in the source sequence.

    Returns {Observable} Sequence containing the single element in the
    observable sequence that satisfies the condition in the predicate.
    """

    return self.filter(predicate).single() if predicate else \
        single_or_default_async(self, False)
