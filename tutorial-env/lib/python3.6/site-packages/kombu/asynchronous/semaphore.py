# -*- coding: utf-8 -*-
"""Semaphores and concurrency primitives."""
from __future__ import absolute_import, unicode_literals

from collections import deque

from kombu.five import python_2_unicode_compatible

__all__ = ('DummyLock', 'LaxBoundedSemaphore')


@python_2_unicode_compatible
class LaxBoundedSemaphore(object):
    """Asynchronous Bounded Semaphore.

    Lax means that the value will stay within the specified
    range even if released more times than it was acquired.

    Example:
        >>> from future import print_statement as printf
        # ^ ignore: just fooling stupid pyflakes

        >>> x = LaxBoundedSemaphore(2)

        >>> x.acquire(printf, 'HELLO 1')
        HELLO 1

        >>> x.acquire(printf, 'HELLO 2')
        HELLO 2

        >>> x.acquire(printf, 'HELLO 3')
        >>> x._waiters   # private, do not access directly
        [print, ('HELLO 3',)]

        >>> x.release()
        HELLO 3
    """

    def __init__(self, value):
        self.initial_value = self.value = value
        self._waiting = deque()
        self._add_waiter = self._waiting.append
        self._pop_waiter = self._waiting.popleft

    def acquire(self, callback, *partial_args, **partial_kwargs):
        """Acquire semaphore.

        This will immediately apply ``callback`` if
        the resource is available, otherwise the callback is suspended
        until the semaphore is released.

        Arguments:
            callback (Callable): The callback to apply.
            *partial_args (Any): partial arguments to callback.
        """
        value = self.value
        if value <= 0:
            self._add_waiter((callback, partial_args, partial_kwargs))
            return False
        else:
            self.value = max(value - 1, 0)
            callback(*partial_args, **partial_kwargs)
            return True

    def release(self):
        """Release semaphore.

        Note:
            If there are any waiters this will apply the first waiter
            that is waiting for the resource (FIFO order).
        """
        try:
            waiter, args, kwargs = self._pop_waiter()
        except IndexError:
            self.value = min(self.value + 1, self.initial_value)
        else:
            waiter(*args, **kwargs)

    def grow(self, n=1):
        """Change the size of the semaphore to accept more users."""
        self.initial_value += n
        self.value += n
        [self.release() for _ in range(n)]

    def shrink(self, n=1):
        """Change the size of the semaphore to accept less users."""
        self.initial_value = max(self.initial_value - n, 0)
        self.value = max(self.value - n, 0)

    def clear(self):
        """Reset the semaphore, which also wipes out any waiting callbacks."""
        self._waiting.clear()
        self.value = self.initial_value

    def __repr__(self):
        return '<{0} at {1:#x} value:{2} waiting:{3}>'.format(
            self.__class__.__name__, id(self), self.value, len(self._waiting),
        )


class DummyLock(object):
    """Pretending to be a lock."""

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        pass
