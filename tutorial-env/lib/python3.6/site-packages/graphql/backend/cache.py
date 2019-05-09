from hashlib import sha1

from six import string_types
from ..type import GraphQLSchema

from .base import GraphQLBackend

# Necessary for static type checking
if False:  # flake8: noqa
    from typing import Any, Dict, Optional, Union, Tuple, Hashable
    from .base import GraphQLDocument

_cached_schemas = {}  # type: Dict[GraphQLSchema, str]

_cached_queries = {}  # type: Dict[str, str]


def get_unique_schema_id(schema):
    # type: (GraphQLSchema) -> str
    """Get a unique id given a GraphQLSchema"""
    assert isinstance(schema, GraphQLSchema), (
        "Must receive a GraphQLSchema as schema. Received {}"
    ).format(repr(schema))

    if schema not in _cached_schemas:
        _cached_schemas[schema] = sha1(str(schema).encode("utf-8")).hexdigest()
    return _cached_schemas[schema]


def get_unique_document_id(query_str):
    # type: (str) -> str
    """Get a unique id given a query_string"""
    assert isinstance(query_str, string_types), (
        "Must receive a string as query_str. Received {}"
    ).format(repr(query_str))

    if query_str not in _cached_queries:
        _cached_queries[query_str] = sha1(str(query_str).encode("utf-8")).hexdigest()
    return _cached_queries[query_str]


class GraphQLCachedBackend(GraphQLBackend):
    """GraphQLCachedBackend will cache the document response from the backend
    given a key for that document"""

    def __init__(
        self,
        backend,  # type: GraphQLBackend
        cache_map=None,  # type: Optional[Dict[Hashable, GraphQLDocument]]
        use_consistent_hash=False,  # type: bool
    ):
        # type: (...) -> None
        assert isinstance(
            backend, GraphQLBackend
        ), "Provided backend must be an instance of GraphQLBackend"
        if cache_map is None:
            cache_map = {}
        self.backend = backend
        self.cache_map = cache_map
        self.use_consistent_hash = use_consistent_hash

    def get_key_for_schema_and_document_string(self, schema, request_string):
        # type: (GraphQLSchema, str) -> int
        """This method returns a unique key given a schema and a request_string"""
        if self.use_consistent_hash:
            schema_id = get_unique_schema_id(schema)
            document_id = get_unique_document_id(request_string)
            return hash((schema_id, document_id))
        return hash((schema, request_string))

    def document_from_string(self, schema, request_string):
        # type: (GraphQLSchema, str) -> Optional[GraphQLDocument]
        """This method returns a GraphQLQuery (from cache if present)"""
        key = self.get_key_for_schema_and_document_string(schema, request_string)
        if key not in self.cache_map:
            self.cache_map[key] = self.backend.document_from_string(
                schema, request_string
            )

        return self.cache_map[key]
