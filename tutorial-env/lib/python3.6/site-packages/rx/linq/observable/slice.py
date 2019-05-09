from rx import Observable
from rx.internal import extensionmethod


@extensionmethod(Observable, name="slice")
def slice_(self, start=None, stop=None, step=1):
    """Slices the given observable. It is basically a wrapper around the
    operators skip(), skip_last(), take(), take_last() and filter().

    This marble diagram helps you remember how slices works with streams.
    Positive numbers is relative to the start of the events, while negative
    numbers are relative to the end (on_completed) of the stream.

    r---e---a---c---t---i---v---e---|
    0   1   2   3   4   5   6   7   8
   -8  -7  -6  -5  -4  -3  -2  -1   0

    Example:
    result = source.slice(1, 10)
    result = source.slice(1, -2)
    result = source.slice(1, -1, 2)

    Keyword arguments:
    :param Observable self: Observable to slice
    :param int start: Number of elements to skip of take last
    :param int stop: Last element to take of skip last
    :param int step: Takes every step element. Must be larger than zero

    :returns: Returns a sliced observable sequence.
    :rtype: Observable
    """

    source = self

    has_start = start is not None
    has_stop = stop is not None
    has_step = step is not None

    if has_stop and stop >= 0:
        source = source.take(stop)

    if has_start and start > 0:
        source = source.skip(start)

    if has_start and start < 0:
        source = source.take_last(abs(start))

    if has_stop and stop < 0:
        source = source.skip_last(abs(stop))

    if has_step:
        if step > 1:
            source = source.filter(lambda x, i: i % step == 0)
        elif step < 0:
            # Reversing events is not supported
            raise TypeError("Negative step not supported.")

    return source


@extensionmethod(Observable)
def __getitem__(self, key):
    """Slices the given observable using Python slice notation. The
    arguments to slice is start, stop and step given within brackets [] and
    separated with the ':' character. It is basically a wrapper around the
    operators skip(), skip_last(), take(), take_last() and filter().

    This marble diagram helps you remember how slices works with streams.
    Positive numbers is relative to the start of the events, while negative
    numbers are relative to the end (on_completed) of the stream.

    r---e---a---c---t---i---v---e---|
    0   1   2   3   4   5   6   7   8
   -8  -7  -6  -5  -4  -3  -2  -1   0

    Example:
    result = source[1:10]
    result = source[1:-2]
    result = source[1:-1:2]

    Keyword arguments:
    :param Observable self: Observable to slice
    :param slice key: Slice object

    :returns: A sliced observable sequence.
    :rtype: Observable
    :raises TypeError: If key is not of type int or slice
    """

    if isinstance(key, slice):
        start, stop, step = key.start, key.stop, key.step
    elif isinstance(key, int):
        start, stop, step = key, key + 1, 1
    else:
        raise TypeError("Invalid argument type.")

    return slice_(self, start, stop, step)
