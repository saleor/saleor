from rx import Observable
from rx.internal import extensionclassmethod
from rx.internal import Enumerable


@extensionclassmethod(Observable)
def for_in(cls, sources, result_selector):
    """Concatenates the observable sequences obtained by running the
    specified result selector for each element in source.

    sources -- {Array} An array of values to turn into an observable
        sequence.
    result_selector -- {Function} A function to apply to each item in the
        sources array to turn it into an observable sequence.
    Returns an observable {Observable} sequence from the concatenated
    observable sequences.
    """

    return Observable.concat(Enumerable.for_each(sources, result_selector))
