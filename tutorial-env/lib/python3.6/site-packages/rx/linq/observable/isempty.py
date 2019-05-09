from rx import Observable
from rx.internal import extensionmethod

@extensionmethod(Observable)
def is_empty(self):
    """Determines whether an observable sequence is empty.

    Returns an observable {Observable} sequence containing a single element
    determining whether the source sequence is empty.
    """

    return self.some().map(lambda b: not b)

