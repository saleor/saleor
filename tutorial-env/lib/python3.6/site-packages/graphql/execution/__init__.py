# -*- coding: utf-8 -*-
"""
Terminology

"Definitions" are the generic name for top-level statements in the document.
Examples of this include:
1) Operations (such as a query)
2) Fragments

"Operations" are a generic name for requests in the document.
Examples of this include:
1) query,
2) mutation

"Selections" are the statements that can appear legally and at
single level of the query. These include:
1) field references e.g "a"
2) fragment "spreads" e.g. "...c"
3) inline fragment "spreads" e.g. "...on Type { a }"
"""
from .executor import execute, subscribe
from .base import ExecutionResult, ResolveInfo
from .middleware import middlewares, MiddlewareManager


__all__ = [
    "execute",
    "subscribe",
    "ExecutionResult",
    "ResolveInfo",
    "MiddlewareManager",
    "middlewares",
]
