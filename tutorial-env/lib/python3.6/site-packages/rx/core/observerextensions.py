from rx.internal import extensionmethod

from . import Observer
from .anonymousobserver import AnonymousObserver


@extensionmethod(Observer)
def to_notifier(self):
    """Creates a notification callback from an observer.

    Returns the action that forwards its input notification to the
    underlying observer."""

    observer = self

    def func(notifier):
        return notifier.accept(observer)
    return func


@extensionmethod(Observer)
def as_observer(self):
    """Hides the identity of an observer.

    Returns an observer that hides the identity of the specified observer.
    """

    return AnonymousObserver(self.on_next, self.on_error, self.on_completed)
