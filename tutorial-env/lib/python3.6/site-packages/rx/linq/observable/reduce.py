from rx import Observable
from rx.internal import extensionmethod


@extensionmethod(Observable, alias="aggregate")
def reduce(self, accumulator, seed=None):
    """Applies an accumulator function over an observable sequence,
    returning the result of the aggregation as a single element in the
    result sequence. The specified seed value is used as the initial
    accumulator value.

    For aggregation behavior with incremental intermediate results, see
    Observable.scan.

    Example:
    1 - res = source.reduce(lambda acc, x: acc + x)
    2 - res = source.reduce(lambda acc, x: acc + x, 0)

    Keyword arguments:
    :param types.FunctionType accumulator: An accumulator function to be
        invoked on each element.
    :param T seed: Optional initial accumulator value.

    :returns: An observable sequence containing a single element with the
        final accumulator value.
    :rtype: Observable
    """

    if seed is not None:
        return self.scan(accumulator, seed=seed).start_with(seed).last()
    else:
        return self.scan(accumulator).last()
