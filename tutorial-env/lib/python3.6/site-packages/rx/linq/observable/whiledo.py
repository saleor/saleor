from rx.core import Observable

from rx.internal.enumerable import Enumerable
from rx.internal import extensionclassmethod


@extensionclassmethod(Observable)
def while_do(cls, condition, source):
    """Repeats source as long as condition holds emulating a while loop.

    Keyword arguments:
    :param types.FunctionType condition: The condition which determines if the
        source will be repeated.
    :param Observable source: The observable sequence that will be run if the
        condition function returns true.

    :returns: An observable sequence which is repeated as long as the condition
        holds.
    :rtype: Observable
    """

    source = Observable.from_future(source)
    return Observable.concat(Enumerable.while_do(condition, source))
