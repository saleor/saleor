from rx.core import Observable
from rx.internal import extensionmethod


@extensionmethod(Observable)
def buffer(self, buffer_openings=None, buffer_closing_selector=None):
    """Projects each element of an observable sequence into zero or more
    buffers.

    Keyword arguments:
    buffer_openings -- Observable sequence whose elements denote the
        creation of windows.
    buffer_closing_selector -- [optional] A function invoked to define the
        closing of each produced window. If a closing selector function is
        specified for the first parameter, this parameter is ignored.

    Returns an observable sequence of windows.
    """

    return self.window(buffer_openings, buffer_closing_selector).select_many(lambda item: item.to_iterable())


@extensionmethod(Observable)
def buffer_with_count(self, count, skip=None):
    """Projects each element of an observable sequence into zero or more
    buffers which are produced based on element count information.

    Example:
    res = xs.buffer_with_count(10)
    res = xs.buffer_with_count(10, 1)

    Keyword parameters:
    count -- {Number} Length of each buffer.
    skip -- {Number} [Optional] Number of elements to skip between creation
        of consecutive buffers. If not provided, defaults to the count.

    Returns an observable {Observable} sequence of buffers.
    """

    if skip is None:
        skip = count

    def selector(x):
        return x.to_iterable()

    def predicate(x):
        return len(x) > 0

    return self.window_with_count(count, skip).select_many(selector).filter(predicate)
