import pytest

from ..field import Field
from ..objecttype import ObjectType
from ..scalars import String
from ..schema import Schema


class MyOtherType(ObjectType):
    field = String()


class Query(ObjectType):
    inner = Field(MyOtherType)


def test_schema():
    schema = Schema(Query)
    assert schema.get_query_type() == schema.get_graphql_type(Query)


def test_schema_get_type():
    schema = Schema(Query)
    assert schema.Query == Query
    assert schema.MyOtherType == MyOtherType


def test_schema_get_type_error():
    schema = Schema(Query)
    with pytest.raises(AttributeError) as exc_info:
        schema.X

    assert str(exc_info.value) == 'Type "X" not found in the Schema'


def test_schema_str():
    schema = Schema(Query)
    assert (
        str(schema)
        == """schema {
  query: Query
}

type MyOtherType {
  field: String
}

type Query {
  inner: MyOtherType
}
"""
    )


def test_schema_introspect():
    schema = Schema(Query)
    assert "__schema" in schema.introspect()
