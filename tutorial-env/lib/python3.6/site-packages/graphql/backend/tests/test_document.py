from ...language.base import parse
from ..base import GraphQLDocument
from .schema import schema
from graphql.backend.base import GraphQLDocument


def create_document(document_string):
    # type: (str) -> GraphQLDocument
    document_ast = parse(document_string)
    return GraphQLDocument(
        schema=schema,
        document_string=document_string,
        document_ast=document_ast,
        execute=lambda *_: None,
    )


def test_document_operations_map_unnamed_operation():
    # type: () -> None
    document = create_document("{ hello }")
    assert document.operations_map == {None: "query"}


def test_document_operations_map_multiple_queries():
    document = create_document(
        """
    query MyQuery1 { hello }
    query MyQuery2 { hello }
    """
    )
    assert document.operations_map == {"MyQuery1": "query", "MyQuery2": "query"}


def test_document_operations_map_multiple_queries():
    # type: () -> None
    document = create_document(
        """
    query MyQuery { hello }
    mutation MyMutation { hello }
    subscription MySubscription { hello }
    """
    )
    assert document.operations_map == {
        "MyQuery": "query",
        "MyMutation": "mutation",
        "MySubscription": "subscription",
    }


def test_document_get_operation_type_unnamed_operation():
    # type: () -> None
    document = create_document(
        """
    query { hello }
    """
    )
    assert document.get_operation_type(None) == "query"
    assert document.get_operation_type("Unknown") is None


def test_document_get_operation_type_multiple_operations():
    # type: () -> None
    document = create_document(
        """
    query MyQuery { hello }
    mutation MyMutation {hello}
    """
    )
    assert document.get_operation_type(None) is None
    assert document.get_operation_type("MyQuery") == "query"
    assert document.get_operation_type("MyMutation") == "mutation"
    assert document.get_operation_type("Unexistent") is None


def test_document_get_operation_type_multiple_operations_empty_operation_name():
    # type: () -> None
    document = create_document(
        """
    query MyQuery { hello }
    mutation {hello}
    """
    )
    assert document.get_operation_type(None) is "mutation"
