from rx import Observable
from rx.internal import extensionmethod


@extensionmethod(Observable, alias=["flat_map_latest", "switch_map"])
def select_switch(self, selector):
    """Projects each element of an observable sequence into a new sequence
    of observable sequences by incorporating the element's index and then
    transforms an observable sequence of observable sequences into an
    observable sequence producing values only from the most recent
    observable sequence.

    Keyword arguments:
    selector -- {Function} A transform function to apply to each source
        element; the second parameter of the function represents the index
        of the source element.

    Returns an observable {Observable} sequence whose elements are the
    result of invoking the transform function on each element of source
    producing an Observable of Observable sequences and that at any point in
    time produces the elements of the most recent inner observable sequence
    that has been received.
    """

    return self.map(selector).switch_latest()
