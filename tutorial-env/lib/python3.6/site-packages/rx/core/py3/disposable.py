from abc import ABCMeta, abstractmethod


class Disposable(metaclass=ABCMeta):
    """Abstract disposable class"""

    @abstractmethod
    def dispose(self):
        return NotImplemented

    def __enter__(self):
        """Context management protocol."""
        pass

    def __exit__(self, type, value, traceback):
        """Context management protocol."""
        self.dispose()
