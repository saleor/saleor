from rx.internal import extensionmethod

from .controlledobservable import ControlledObservable
from .stopandwaitobservable import StopAndWaitObservable


@extensionmethod(ControlledObservable)
def stop_and_wait(self):
    """Attaches a stop and wait observable to the current observable.

    :returns: A stop and wait observable.
    :rtype: Observable
    """

    return StopAndWaitObservable(self)
