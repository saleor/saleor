from rx import Observable
from rx.internal import extensionmethod


@extensionmethod(Observable)
def pluck(self, key):
    """Retrieves the value of a specified key using dict-like access (as in
    element[key]) from all elements in the Observable sequence.

    Keyword arguments:
    key {String} The key to pluck.

    Returns a new Observable {Observable} sequence of key values.

    To pluck an attribute of each element, use pluck_attr.

    """

    return self.map(lambda x: x[key])


@extensionmethod(Observable)
def pluck_attr(self, property):
    """Retrieves the value of a specified property (using getattr) from all
    elements in the Observable sequence.

    Keyword arguments:
    property {String} The property to pluck.

    Returns a new Observable {Observable} sequence of property values.

    To pluck values using dict-like access (as in element[key]) on each
    element, use pluck.

    """

    return self.map(lambda x: getattr(x, property))
