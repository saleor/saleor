#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for `graphql.backend.decider` module."""

import pytest
from threading import Event

from ..base import GraphQLBackend, GraphQLDocument
from ..core import GraphQLCoreBackend
from ..cache import GraphQLCachedBackend
from ..decider import GraphQLDeciderBackend

from .schema import schema

if False:
    from typing import Any


class FakeBackend(GraphQLBackend):
    def __init__(self, name, raises=False):
        # type: (str, bool) -> None
        self.raises = raises
        self.name = name
        self.event = Event()

    @property
    def reached(self):
        return self.event.is_set()

    def document_from_string(self, *args, **kwargs):
        # type: (*Any, **Any) -> str
        self.event.set()
        if self.raises:
            raise Exception("Backend failed")
        return self.name

    def wait(self):
        return self.event.wait()

    def reset(self):
        # type: () -> None
        self.event = Event()


def test_decider_backend_healthy_backend():
    # type: () -> None
    backend1 = FakeBackend(name="main")
    backend2 = FakeBackend(name="fallback")
    decider_backend = GraphQLDeciderBackend(backend1, backend2)

    document = decider_backend.document_from_string(schema, "{ hello }")
    assert not backend1.reached
    assert backend2.reached
    assert document == "fallback"

    backend1.wait()
    backend1.reset()
    backend2.reset()
    document = decider_backend.document_from_string(schema, "{ hello }")
    assert not backend1.reached
    assert not backend2.reached
    assert document == "main"


def test_decider_backend_unhealthy_backend():
    # type: () -> None
    backend1 = FakeBackend(name="main", raises=True)
    backend2 = FakeBackend(name="fallback")
    decider_backend = GraphQLDeciderBackend(backend1, backend2)

    document = decider_backend.document_from_string(schema, "{ hello }")
    assert not backend1.reached
    assert backend2.reached
    assert document == "fallback"

    backend1.wait()
    backend1.reset()
    backend2.reset()
    document = decider_backend.document_from_string(schema, "{ hello }")

    assert document == "fallback"
    assert not backend1.reached
    assert not backend2.reached


def test_decider_old_syntax():
    # type: () -> None
    backend1 = FakeBackend(name="main", raises=True)
    backend2 = FakeBackend(name="fallback")
    decider_backend = GraphQLDeciderBackend([backend1, backend2])
    assert decider_backend.backend is backend1
    assert decider_backend.fallback_backend is backend2


# def test_decider_backend_dont_use_cache():
#     # type: () -> None
#     backend1 = FakeBackend()
#     backend2 = FakeBackend()
#     decider_backend = GraphQLDeciderBackend([backend1, backend2])

#     decider_backend.document_from_string(schema, "{ hello }")
#     assert backend1.reached
#     assert not backend2.reached

#     backend1.reset()
#     decider_backend.document_from_string(schema, "{ hello }")
#     assert backend1.reached


# def test_decider_backend_use_cache_if_provided():
#     # type: () -> None
#     backend1 = FakeBackend()
#     backend2 = FakeBackend()
#     decider_backend = GraphQLDeciderBackend(
#         [GraphQLCachedBackend(backend1), GraphQLCachedBackend(backend2)]
#     )

#     decider_backend.document_from_string(schema, "{ hello }")
#     assert backend1.reached
#     assert not backend2.reached

#     backend1.reset()
#     decider_backend.document_from_string(schema, "{ hello }")
#     assert not backend1.reached
