import json
from typing import Dict, Optional

import pytest
from graphql import get_default_backend
from kombu import Connection

from ....graphql.api import schema
from .. import GraphQLOperationResponse
from ..buffer import ObservabilityBuffer

TESTS_TIMEOUT = 0.1
backend = get_default_backend()


def fill_buffer(
    buffer: ObservabilityBuffer,
    events_count: int,
    data: Optional[str] = None,
):
    data = data or json.dumps({"test": "data"})
    for _ in range(events_count):
        buffer.put_event(data)


@pytest.fixture(scope="session")
def memory_broker_url():
    return "memory://"


@pytest.fixture
def memory_broker(memory_broker_url: str):
    with Connection(memory_broker_url) as conn:
        yield conn
        # Force channel clear
        conn.transport.Channel.queues = {}


@pytest.fixture
def gql_operation_factory():
    def factory(
        query_string: str,
        operation_name: Optional[str] = None,
        variables: Optional[Dict] = None,
        result: Optional[Dict] = None,
    ) -> GraphQLOperationResponse:
        query = backend.document_from_string(schema, query_string)
        return GraphQLOperationResponse(
            name=operation_name, query=query, variables=variables, result=result
        )

    return factory
