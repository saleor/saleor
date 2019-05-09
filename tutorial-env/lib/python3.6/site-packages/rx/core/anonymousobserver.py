from rx.internal import noop, default_error
from .observerbase import ObserverBase


class AnonymousObserver(ObserverBase):
    def __init__(self, on_next=None, on_error=None, on_completed=None):
        super(AnonymousObserver, self).__init__()

        self._next = on_next or noop
        self._error = on_error or default_error
        self._completed = on_completed or noop

    def _on_next_core(self, value):
        self._next(value)

    def _on_error_core(self, error):
        self._error(error)

    def _on_completed_core(self):
        self._completed()
