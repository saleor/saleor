"""Definitions of sensitive data for observability obfuscation methods.

SENSITIVE_HEADERS is a tuple of sensitive HTTP headers to anonymize before reporting.

SENSITIVE_GQL_FIELDS is a dict of sets representing fields of GraphGL types to anonymize
- Type
- Fields
"""
from ...core.auth import DEFAULT_AUTH_HEADER, SALEOR_AUTH_HEADER
from ...graphql.api import schema
from ...graphql.schema_maps import build_sensitive_fields_map

SENSITIVE_HEADERS = (
    SALEOR_AUTH_HEADER,
    DEFAULT_AUTH_HEADER,
    "COOKIE",
)
SENSITIVE_HEADERS = tuple(
    x[5:] if x.startswith("HTTP_") else x for x in SENSITIVE_HEADERS
)


SENSITIVE_GQL_FIELDS = build_sensitive_fields_map(schema.get_type_map())
