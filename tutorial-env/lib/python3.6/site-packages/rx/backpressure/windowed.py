from rx.internal import extensionmethod

from .controlledobservable import ControlledObservable
from .windowedobservable import WindowedObservable


@extensionmethod(ControlledObservable)
def windowed(self, window_size):
    """Creates a sliding windowed observable based upon the window size.

    Keyword arguments:
    :param int window_size: The number of items in the window

    :returns: A windowed observable based upon the window size.
    :rtype: Observable
    """

    return WindowedObservable(self, window_size)