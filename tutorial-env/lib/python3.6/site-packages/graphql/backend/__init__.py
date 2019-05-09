# -*- coding: utf-8 -*-
"""
This module provides a dynamic way of using different
engines for a GraphQL schema query resolution.
"""

from .base import GraphQLBackend, GraphQLDocument
from .core import GraphQLCoreBackend
from .decider import GraphQLDeciderBackend
from .cache import GraphQLCachedBackend

# Necessary for static type checking
if False:  # flake8: noqa
    from typing import Union

_default_backend = None


def get_default_backend():
    # type: () -> GraphQLCoreBackend
    global _default_backend
    if _default_backend is None:
        _default_backend = GraphQLCoreBackend()
    return _default_backend


def set_default_backend(backend):
    # type: (GraphQLCoreBackend) -> None
    global _default_backend
    assert isinstance(
        backend, GraphQLBackend
    ), "backend must be an instance of GraphQLBackend."
    _default_backend = backend


__all__ = [
    "GraphQLBackend",
    "GraphQLDocument",
    "GraphQLCoreBackend",
    "GraphQLDeciderBackend",
    "GraphQLCachedBackend",
    "get_default_backend",
    "set_default_backend",
]
