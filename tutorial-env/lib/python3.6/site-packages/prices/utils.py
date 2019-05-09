import functools
import operator
from typing import Iterable, TypeVar

T = TypeVar('T')


def sum(values: Iterable[T]) -> T:
    """Return a sum of given values."""
    return functools.reduce(operator.add, values)
