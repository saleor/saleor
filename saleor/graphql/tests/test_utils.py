import re

import pytest
from django.test import override_settings
from graphql import GraphQLError
from graphql.utils import schema_printer

from ..api import backend, schema
from ..utils import ALLOWED_ERRORS, INTERNAL_ERROR_MESSAGE, format_error
from ..utils.validators import check_if_query_contains_only_schema
from .utils import get_graphql_content


def test_multiple_interface_separator_in_schema(api_client):
    query = """
    query __ApolloGetServiceDefinition__ {
        _service {
            sdl
        }
    }
    """
    response = api_client.post_graphql(query)

    content = get_graphql_content(response)
    sdl = content["data"]["_service"]["sdl"]
    comma_separated_interfaces = re.findall("implements (\\w+,) (\\w+)", sdl)
    ampersand_separated_interfaces = re.findall("implements (\\w+) & (\\w+)", sdl)
    assert not comma_separated_interfaces
    assert ampersand_separated_interfaces


def test_graphql_core_contains_patched_function():
    assert hasattr(schema_printer, "_print_object")


@override_settings(DEBUG=False)
def test_format_error_hides_internal_error_msg_in_production_mode():
    error = ValueError("Example error")
    result = format_error(error, ())
    assert result["message"] == INTERNAL_ERROR_MESSAGE


@override_settings(DEBUG=False)
def test_format_error_prints_allowed_errors():
    error_cls = ALLOWED_ERRORS[0]
    error = error_cls("Example error")
    result = format_error(error, ())
    assert result["message"] == str(error)


@override_settings(DEBUG=True)
def test_format_error_prints_internal_error_msg_in_debug_mode():
    error = ValueError("Example error")
    result = format_error(error, ())
    assert result["message"] == str(error)


def test_check_if_query_contains_only_schema_with_schema_query():
    # given
    query = """
    query {
        __schema {
            __typename
        }
    }
    """
    document = backend.document_from_string(schema, query)

    # when
    result = check_if_query_contains_only_schema(document)

    # then
    assert result is True


def test_check_if_query_contains_only_schema_with_mixed_query():
    # given
    query = """
    query {
        __schema {
            __typename
        }
        shop {
            name
        }
    }
    """
    document = backend.document_from_string(schema, query)

    # then
    with pytest.raises(GraphQLError):
        check_if_query_contains_only_schema(document)


def test_check_if_query_contains_only_schema_with_mixed_query_and_fragments():
    # given
    query = """
    query {
        ... {
            __schema {
                __typename
            }
        }
        ... {
            shop {
                name
            }
        }
    }
    """
    document = backend.document_from_string(schema, query)

    # then
    with pytest.raises(GraphQLError):
        check_if_query_contains_only_schema(document)


def test_check_if_query_contains_only_schema_with_fragments():
    # given
    query = """
    fragment ShopFragment on Shop {
        ... on Node {
            __typename
        }
    }

    query {
        shop {
            ...ShopFragment
        }
    }
    """
    document = backend.document_from_string(schema, query)

    # when
    result = check_if_query_contains_only_schema(document)

    # then
    assert result is False


def test_check_if_query_contains_only_schema_with_schema_query_and_inline_fragment():
    # given
    query = """
    query {
        ... on Query {
            __schema {
                __typename
            }
        }
    }
    """
    document = backend.document_from_string(schema, query)

    # when
    result = check_if_query_contains_only_schema(document)

    # then
    assert result is True


def test_check_if_query_contains_only_schema_with_schema_query_and_unconditional_inline_fragment():
    # given
    query = """
    query {
        ... {
            __schema {
                __typename
            }
        }
    }
    """
    document = backend.document_from_string(schema, query)

    # when
    result = check_if_query_contains_only_schema(document)

    # then
    assert result is True


def test_check_if_query_contains_only_schema_with_schema_query_and_named_fragment():
    # given
    query = """
    fragment SchemaFragment on Query {
        __schema {
            __typename
        }
    }

    query {
        ...SchemaFragment
    }
    """
    document = backend.document_from_string(schema, query)

    # when
    result = check_if_query_contains_only_schema(document)

    # then
    assert result is True


def test_check_if_query_contains_only_schema_with_schema_query_and_fragments():
    # given
    query = """
    fragment SchemaFragment on Query {
        ... {
            __schema {
                __typename
            }
        }
    }

    query {
        ...SchemaFragment
    }
    """
    document = backend.document_from_string(schema, query)

    # when
    result = check_if_query_contains_only_schema(document)

    # then
    assert result is True


def test_check_if_query_contains_only_schema_with_introspection():
    # given
    query = """
        query IntrospectionQuery {
            __schema {
                queryType { name }
                mutationType { name }
                subscriptionType { name }
                types {
                    ...FullType
                }
                directives {
                    name
                    description
                    locations
                    args {
                        ...InputValue
                    }
                }
            }
        }
        fragment FullType on __Type {
            kind
            name
            description
            fields(includeDeprecated: true) {
                name
                description
                args {
                    ...InputValue
                }
                type {
                    ...TypeRef
                }
                isDeprecated
                deprecationReason
            }
            inputFields {
                ...InputValue
            }
            interfaces {
                ...TypeRef
            }
            enumValues(includeDeprecated: true) {
                name
                description
                isDeprecated
                deprecationReason
            }
            possibleTypes {
                ...TypeRef
            }
        }
        fragment InputValue on __InputValue {
            name
            description
            type { ...TypeRef }
            defaultValue
        }
        fragment TypeRef on __Type {
            kind
            name
            ofType {
                kind
                name
                ofType {
                    kind
                    name
                    ofType {
                        kind
                        name
                        ofType {
                            kind
                            name
                            ofType {
                                kind
                                name
                                ofType {
                                    kind
                                    name
                                    ofType {
                                        kind
                                        name
                                        ofType {
                                            kind
                                            name
                                            ofType {
                                                kind
                                                name
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    """
    document = backend.document_from_string(schema, query)

    # when
    result = check_if_query_contains_only_schema(document)

    # then
    assert result is True
