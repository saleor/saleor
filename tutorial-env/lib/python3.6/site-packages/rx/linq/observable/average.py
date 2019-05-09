from rx.core import Observable
from rx.internal import extensionmethod


class AverageValue(object):

    def __init__(self, sum, count):
        self.sum = sum
        self.count = count


@extensionmethod(Observable)
def average(self, key_selector=None):
    """Computes the average of an observable sequence of values that are in
    the sequence or obtained by invoking a transform function on each
    element of the input sequence if present.

    Example
    res = source.average();
    res = source.average(lambda x: x.value)

    :param Observable self: Observable to average.
    :param types.FunctionType key_selector: A transform function to apply to
        each element.

    :returns: An observable sequence containing a single element with the
        average of the sequence of values.
    :rtype: Observable
    """

    if key_selector:
        return self.map(key_selector).average()

    def accumulator(prev, cur):
        return AverageValue(sum=prev.sum+cur, count=prev.count+1)

    def mapper(s):
        if s.count == 0:
            raise Exception('The input sequence was empty')

        return s.sum / float(s.count)

    seed = AverageValue(sum=0, count=0)
    return self.scan(accumulator, seed).last().map(mapper)
