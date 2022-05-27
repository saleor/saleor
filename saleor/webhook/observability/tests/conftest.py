from typing import Dict, Optional
from unittest.mock import patch

import fakeredis
import pytest
from graphql import get_default_backend
from redis import ConnectionPool

from ....graphql.api import schema
from ..buffers import RedisBuffer
from ..utils import GraphQLOperationResponse, get_buffer_name

backend = get_default_backend()

BROKER_URL = "redis://fake-redis"
KEY, MAX_SIZE, BATCH_SIZE = get_buffer_name(), 10, 5


@pytest.fixture
def gql_operation_factory():
    def factory(
        query_string: str,
        operation_name: Optional[str] = None,
        variables: Optional[Dict] = None,
        result: Optional[Dict] = None,
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
def redis_server(settings):
    settings.OBSERVABILITY_BROKER_URL = BROKER_URL
    settings.OBSERVABILITY_BUFFER_SIZE_LIMIT = MAX_SIZE
    settings.OBSERVABILITY_BUFFER_BATCH_SIZE = BATCH_SIZE
    server = fakeredis.FakeServer()
    server.connected = True
    yield server


@pytest.fixture
def patch_redis(redis_server):
    with patch(
        "saleor.webhook.observability.buffers.RedisBuffer.get_connection_pool",
        lambda x: ConnectionPool(
            connection_class=fakeredis.FakeConnection, server=redis_server
        ),
    ):
        yield redis_server


@pytest.fixture
def buffer(redis_server, patch_redis):
    buffer = RedisBuffer(BROKER_URL, KEY, max_size=MAX_SIZE, batch_size=BATCH_SIZE)
    yield buffer
    redis_server.connected = True
    buffer.clear()
