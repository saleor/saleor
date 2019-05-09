from abc import abstractmethod

from rx.internal import noop
from . import Observer, Disposable


class ObserverBase(Observer, Disposable):
    """Base class for implementations of the Observer class. This base
    class enforces the grammar of observers where OnError and
    OnCompleted are terminal messages.
    """

    def __init__(self):
        self.is_stopped = False

    def on_next(self, value):
        """Notify the observer of a new element in the sequence."""
        if not self.is_stopped:
            self._on_next_core(value)

    @abstractmethod
    def _on_next_core(self, value):
        return NotImplemented

    def on_error(self, error):
        """Notifies the observer that an exception has occurred.

        Keyword arguments:
        error -- The error that has occurred."""

        if not self.is_stopped:
            ObserverBase.dispose(self)
            self._on_error_core(error)

    @abstractmethod
    def _on_error_core(self, error):
        return NotImplemented

    def on_completed(self):
        """Notifies the observer of the end of the sequence."""

        if not self.is_stopped:
            ObserverBase.dispose(self)
            self._on_completed_core()

    @abstractmethod
    def _on_completed_core(self):
        return NotImplemented

    def dispose(self):
        """Disposes the observer, causing it to transition to the stopped
        state."""

        self.on_next = noop
        self.is_stopped = True

    def fail(self, exn):
        if not self.is_stopped:
            ObserverBase.dispose(self)
            self._on_error_core(exn)
            return True

        return False
