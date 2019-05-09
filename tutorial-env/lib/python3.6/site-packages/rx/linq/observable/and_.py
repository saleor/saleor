from rx.core import Observable
from rx.internal import extensionmethod

from rx.joins import Pattern


@extensionmethod(Observable)
def and_(self, right):
    """Creates a pattern that matches when both observable sequences
    have an available value.

    :param Observable right: Observable sequence to match with the
        current sequence.
    :returns: Pattern object that matches when both observable sequences
        have an available value.
    """

    return Pattern([self, right])
