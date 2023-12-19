import json
from typing import Optional
from unittest.mock import patch

import fakeredis
import pytest
from django.core.cache import cache
from graphql import get_default_backend
from redis import ConnectionPool

from ....graphql.api import schema
from ..buffers import RedisBuffer
from ..utils import GraphQLOperationResponse, get_buffer_name

backend = get_default_backend()

BROKER_URL_HOST = "fake-redis"
BROKER_URL = f"redis://{BROKER_URL_HOST}"
KEY, MAX_SIZE, BATCH_SIZE = get_buffer_name(), 10, 5


@pytest.fixture
def gql_operation_factory():
    def factory(
        query_string: str,
        operation_name: Optional[str] = None,
        variables: Optional[dict] = None,
        result: Optional[dict] = None,
        result_invalid=False,
    ) -> GraphQLOperationResponse:
        query = backend.document_from_string(schema, query_string)
        return GraphQLOperationResponse(
            name=operation_name,
            query=query,
            variables=variables,
            result=result,
            result_invalid=result_invalid,
        )

    return factory


@pytest.fixture
def _clear_cache():
    yield
    cache.clear()


@pytest.fixture
def redis_server(settings):
    settings.OBSERVABILITY_BROKER_URL = BROKER_URL
    settings.OBSERVABILITY_BUFFER_SIZE_LIMIT = MAX_SIZE
    settings.OBSERVABILITY_BUFFER_BATCH_SIZE = BATCH_SIZE
    server = fakeredis.FakeServer()
    server.connected = True
    return server


@pytest.fixture
def patch_connection_pool(redis_server):
    t = "saleor.webhook.observability.buffers.RedisBuffer.get_or_create_connection_pool"
    with patch(
        t,
        return_value=ConnectionPool(
            connection_class=fakeredis.FakeConnection,
            server=redis_server,
        ),
    ):
        yield redis_server


@pytest.fixture
def buffer(patch_connection_pool):
    buffer = RedisBuffer(BROKER_URL, KEY, max_size=MAX_SIZE, batch_size=BATCH_SIZE)
    return buffer


@pytest.fixture
def event_data():
    return json.dumps({"event": "data"}).encode("utf-8")
