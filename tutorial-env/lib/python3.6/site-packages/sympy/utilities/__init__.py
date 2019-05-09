"""This module contains some general purpose utilities that are used across
SymPy.
"""
from .iterables import (flatten, group, take, subsets,
    variations, numbered_symbols, cartes, capture, dict_merge,
    postorder_traversal, interactive_traversal,
    prefixes, postfixes, sift, topological_sort, unflatten,
    has_dups, has_variety, reshape, default_sort_key, ordered,
    rotations)

from .misc import filldedent

from .lambdify import lambdify

from .source import source

from .decorator import threaded, xthreaded, public, memoize_property

from .runtests import test, doctest

from .timeutils import timed
