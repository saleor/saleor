from rx import Observable
from rx.internal import extensionmethod

from rx.joins import Pattern

@extensionmethod(Observable, alias="then")
def then_do(self, selector):
    """Matches when the observable sequence has an available value and projects
    the value.

    :param types.FunctionType selector: Selector that will be invoked for values
        in the source sequence.
    :returns: Plan that produces the projected values, to be fed (with other
        plans) to the when operator.
    :rtype: Plan
    """

    return Pattern([self]).then_do(selector)

