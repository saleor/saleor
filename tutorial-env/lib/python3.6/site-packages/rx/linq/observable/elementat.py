from rx import Observable
from rx.internal import extensionmethod

from .elementatordefault import _element_at_or_default


@extensionmethod(Observable)
def element_at(self, index):
    """Returns the element at a specified index in a sequence.

    Example:
    res = source.element_at(5)

    Keyword arguments:
    :param int index: The zero-based index of the element to retrieve.

    :returns: An observable  sequence that produces the element at the
    specified position in the source sequence.
    :rtype: Observable
    """

    return _element_at_or_default(self, index, False)
