import pytest

from ...types import Argument, Field, Int, List, NonNull, ObjectType, Schema, String
from ..connection import Connection, ConnectionField, PageInfo
from ..node import Node


class MyObject(ObjectType):
    class Meta:
        interfaces = [Node]

    field = String()


def test_connection():
    class MyObjectConnection(Connection):
        extra = String()

        class Meta:
            node = MyObject

        class Edge:
            other = String()

    assert MyObjectConnection._meta.name == "MyObjectConnection"
    fields = MyObjectConnection._meta.fields
    assert list(fields.keys()) == ["page_info", "edges", "extra"]
    edge_field = fields["edges"]
    pageinfo_field = fields["page_info"]

    assert isinstance(edge_field, Field)
    assert isinstance(edge_field.type, NonNull)
    assert isinstance(edge_field.type.of_type, List)
    assert edge_field.type.of_type.of_type == MyObjectConnection.Edge

    assert isinstance(pageinfo_field, Field)
    assert isinstance(pageinfo_field.type, NonNull)
    assert pageinfo_field.type.of_type == PageInfo


def test_connection_inherit_abstracttype():
    class BaseConnection(object):
        extra = String()

    class MyObjectConnection(BaseConnection, Connection):
        class Meta:
            node = MyObject

    assert MyObjectConnection._meta.name == "MyObjectConnection"
    fields = MyObjectConnection._meta.fields
    assert list(fields.keys()) == ["page_info", "edges", "extra"]


def test_connection_name():
    custom_name = "MyObjectCustomNameConnection"

    class BaseConnection(object):
        extra = String()

    class MyObjectConnection(BaseConnection, Connection):
        class Meta:
            node = MyObject
            name = custom_name

    assert MyObjectConnection._meta.name == custom_name


def test_edge():
    class MyObjectConnection(Connection):
        class Meta:
            node = MyObject

        class Edge:
            other = String()

    Edge = MyObjectConnection.Edge
    assert Edge._meta.name == "MyObjectEdge"
    edge_fields = Edge._meta.fields
    assert list(edge_fields.keys()) == ["node", "cursor", "other"]

    assert isinstance(edge_fields["node"], Field)
    assert edge_fields["node"].type == MyObject

    assert isinstance(edge_fields["other"], Field)
    assert edge_fields["other"].type == String


def test_edge_with_bases():
    class BaseEdge(object):
        extra = String()

    class MyObjectConnection(Connection):
        class Meta:
            node = MyObject

        class Edge(BaseEdge):
            other = String()

    Edge = MyObjectConnection.Edge
    assert Edge._meta.name == "MyObjectEdge"
    edge_fields = Edge._meta.fields
    assert list(edge_fields.keys()) == ["node", "cursor", "extra", "other"]

    assert isinstance(edge_fields["node"], Field)
    assert edge_fields["node"].type == MyObject

    assert isinstance(edge_fields["other"], Field)
    assert edge_fields["other"].type == String


def test_pageinfo():
    assert PageInfo._meta.name == "PageInfo"
    fields = PageInfo._meta.fields
    assert list(fields.keys()) == [
        "has_next_page",
        "has_previous_page",
        "start_cursor",
        "end_cursor",
    ]


def test_connectionfield():
    class MyObjectConnection(Connection):
        class Meta:
            node = MyObject

    field = ConnectionField(MyObjectConnection)
    assert field.args == {
        "before": Argument(String),
        "after": Argument(String),
        "first": Argument(Int),
        "last": Argument(Int),
    }


def test_connectionfield_node_deprecated():
    field = ConnectionField(MyObject)
    with pytest.raises(Exception) as exc_info:
        field.type

    assert "ConnectionField's now need a explicit ConnectionType for Nodes." in str(
        exc_info.value
    )


def test_connectionfield_custom_args():
    class MyObjectConnection(Connection):
        class Meta:
            node = MyObject

    field = ConnectionField(
        MyObjectConnection, before=String(required=True), extra=String()
    )
    assert field.args == {
        "before": Argument(NonNull(String)),
        "after": Argument(String),
        "first": Argument(Int),
        "last": Argument(Int),
        "extra": Argument(String),
    }


def test_connectionfield_required():
    class MyObjectConnection(Connection):
        class Meta:
            node = MyObject

    class Query(ObjectType):
        test_connection = ConnectionField(MyObjectConnection, required=True)

        def resolve_test_connection(root, info, **args):
            return []

    schema = Schema(query=Query)
    executed = schema.execute("{ testConnection { edges { cursor } } }")
    assert not executed.errors
    assert executed.data == {"testConnection": {"edges": []}}
