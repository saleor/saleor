from rx import config
from rx.internal import noop
from rx.core import Disposable


class AnonymousDisposable(Disposable):
    """Main disposable class"""

    def __init__(self, action=None):
        """Creates a disposable object that invokes the specified action when
        disposed.

        Keyword arguments:
        dispose -- Action to run during the first call to Disposable.dispose.
            The action is guaranteed to be run at most once.

        Returns the disposable object that runs the given action upon disposal.
        """

        self.is_disposed = False
        self.action = action or noop

        self.lock = config["concurrency"].RLock()

    def dispose(self):
        """Performs the task of cleaning up resources."""

        dispose = False
        with self.lock:
            if not self.is_disposed:
                dispose = True
                self.is_disposed = True

        if dispose:
            self.action()

    @classmethod
    def empty(cls):
        return cls(noop)

    @classmethod
    def create(cls, action):
        return cls(action)
