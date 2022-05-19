from typing import Dict, Optional

import pytest
from graphql import get_default_backend

from ....graphql.api import schema
from ..utils import GraphQLOperationResponse

backend = get_default_backend()


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
