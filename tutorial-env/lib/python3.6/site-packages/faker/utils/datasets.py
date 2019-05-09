# coding=utf-8

from collections import Counter
from functools import reduce
import operator


def add_dicts(*args):
    """
    Adds two or more dicts together. Common keys will have their values added.

    For example::

        >>> t1 = {'a':1, 'b':2}
        >>> t2 = {'b':1, 'c':3}
        >>> t3 = {'d':4}

        >>> add_dicts(t1, t2, t3)
        {'a': 1, 'c': 3, 'b': 3, 'd': 4}

    """

    counters = [Counter(arg) for arg in args]
    return dict(reduce(operator.add, counters))
