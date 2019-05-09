import copy

from graphql.language.visitor_meta import QUERY_DOCUMENT_KEYS


def test_ast_is_hashable():
    # type: () -> None
    for node_class in QUERY_DOCUMENT_KEYS:
        node = node_class(loc=None, **{k: k for k in node_class._fields})
        assert hash(node)


def test_ast_is_copyable():
    # type: () -> None
    for node_class in QUERY_DOCUMENT_KEYS:
        node = node_class(loc=None, **{k: k for k in node_class._fields})
        assert copy.copy(node) == node


def test_ast_is_reprable():
    # type: () -> None
    for node_class in QUERY_DOCUMENT_KEYS:
        node = node_class(loc=None, **{k: k for k in node_class._fields})
        assert repr(node)
