from rx import config
from rx.core import Disposable


class SingleAssignmentDisposable(Disposable):
    """Represents a disposable resource which only allows a single assignment
    of its underlying disposable resource. If an underlying disposable resource
    has already been set, future attempts to set the underlying disposable
    resource will throw an Error."""

    def __init__(self):
        """Initializes a new instance of the SingleAssignmentDisposable
        class.
        """
        self.is_disposed = False
        self.current = None
        self.lock = config["concurrency"].RLock()

        super(Disposable, self).__init__()

    def get_disposable(self):
        return self.current

    def set_disposable(self, value):
        if self.current:
            raise Exception('Disposable has already been assigned')

        should_dispose = self.is_disposed
        old = None

        with self.lock:
            if not should_dispose:
                old = self.current
                self.current = value

        if old:
            old.dispose()

        if should_dispose and value:
            value.dispose()

    disposable = property(get_disposable, set_disposable)

    def dispose(self):
        """Sets the status to disposed"""
        old = None

        with self.lock:
            if not self.is_disposed:
                self.is_disposed = True
                old = self.current
                self.current = None

        if old:
            old.dispose()
