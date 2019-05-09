import math
import types

from rx.core.notification import OnNext, OnError, OnCompleted
from .recorded import Recorded
from .subscription import Subscription


def is_prime(i):
    """Tests if number is prime or not"""

    if i <= 1:
        return False

    _max = int(math.floor(math.sqrt(i)))
    for j in range(2, _max+1):
        if not i % j:
            return False

    return True


# New predicate tests
class OnNextPredicate(object):
    def __init__(self, predicate):
        self.predicate = predicate

    def __eq__(self, other):
        if other == self:
            return True
        if other is None:
            return False
        if other.kind != 'N':
            return False
        return self.predicate(other.value)


class OnErrorPredicate(object):
    def __init__(self, predicate):
        self.predicate = predicate

    def __eq__(self, other):
        if other == self:
            return True
        if other is None:
            return False
        if other.kind != 'E':
            return False
        return self.predicate(other.exception)


class ReactiveTest(object):
    created = 100
    subscribed = 200
    disposed = 1000

    @classmethod
    def on_next(cls, ticks, value):
        if isinstance(value, types.FunctionType):
            return Recorded(ticks, OnNextPredicate(value))

        return Recorded(ticks, OnNext(value))

    @classmethod
    def on_error(cls, ticks, exception):
        if isinstance(exception, types.FunctionType):
            return Recorded(ticks, OnErrorPredicate(exception))

        return Recorded(ticks, OnError(exception))

    @classmethod
    def on_completed(cls, ticks):
        return Recorded(ticks, OnCompleted())

    @classmethod
    def subscribe(cls, start, end):
        return Subscription(start, end)
