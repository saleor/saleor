#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for `graphql.backend.core` module."""

import pytest
from graphql.execution.executors.sync import SyncExecutor

from ..base import GraphQLBackend, GraphQLDocument
from ..core import GraphQLCoreBackend
from .schema import schema

if False:
    from typing import Any


def test_core_backend():
    # type: () -> None
    """Sample pytest test function with the pytest fixture as an argument."""
    backend = GraphQLCoreBackend()
    assert isinstance(backend, GraphQLBackend)
    document = backend.document_from_string(schema, "{ hello }")
    assert isinstance(document, GraphQLDocument)
    result = document.execute()
    assert not result.errors
    assert result.data == {"hello": "World"}


def test_backend_is_not_cached_by_default():
    # type: () -> None
    """Sample pytest test function with the pytest fixture as an argument."""
    backend = GraphQLCoreBackend()
    document1 = backend.document_from_string(schema, "{ hello }")
    document2 = backend.document_from_string(schema, "{ hello }")
    assert document1 != document2


class BaseExecutor(SyncExecutor):
    executed = False

    def execute(self, *args, **kwargs):
        # type: (*Any, **Any) -> str
        self.executed = True
        return super(BaseExecutor, self).execute(*args, **kwargs)


def test_backend_can_execute_custom_executor():
    # type: () -> None
    executor = BaseExecutor()
    backend = GraphQLCoreBackend(executor=executor)
    document1 = backend.document_from_string(schema, "{ hello }")
    result = document1.execute()
    assert not result.errors
    assert result.data == {"hello": "World"}
    assert executor.executed
