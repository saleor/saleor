from collections import OrderedDict

from graphql.type import (
    GraphQLField,
    GraphQLFloat,
    GraphQLInt,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
    GraphQLUnionType,
)

from ..type_comparators import is_equal_type, is_type_sub_type_of


def _test_schema(field_type):
    return GraphQLSchema(
        query=GraphQLObjectType(
            name="Query", fields=OrderedDict([("field", GraphQLField(field_type))])
        )
    )


def test_is_equal_type_same_reference_are_equal():
    assert is_equal_type(GraphQLString, GraphQLString)


def test_is_equal_type_int_and_float_are_not_equal():
    assert not is_equal_type(GraphQLInt, GraphQLFloat)


def test_is_equal_type_lists_of_same_type_are_equal():
    assert is_equal_type(GraphQLList(GraphQLInt), GraphQLList(GraphQLInt))


def test_is_equal_type_lists_is_not_equal_to_item():
    assert not is_equal_type(GraphQLList(GraphQLInt), GraphQLInt)


def test_is_equal_type_nonnull_of_same_type_are_equal():
    assert is_equal_type(GraphQLNonNull(GraphQLInt), GraphQLNonNull(GraphQLInt))


def test_is_equal_type_nonnull_is_not_equal_to_nullable():
    assert not is_equal_type(GraphQLNonNull(GraphQLInt), GraphQLInt)


def test_is_equal_type_nonnull_is_not_equal_to_nullable():
    assert not is_equal_type(GraphQLNonNull(GraphQLInt), GraphQLInt)


def test_is_type_sub_type_of_same_reference_is_subtype():
    schema = _test_schema(GraphQLString)
    assert is_type_sub_type_of(schema, GraphQLString, GraphQLString)


def test_is_type_sub_type_of_int_is_not_subtype_of_float():
    schema = _test_schema(GraphQLString)
    assert not is_type_sub_type_of(schema, GraphQLInt, GraphQLFloat)


def test_is_type_sub_type_of_non_null_is_subtype_of_nullable():
    schema = _test_schema(GraphQLString)
    assert is_type_sub_type_of(schema, GraphQLNonNull(GraphQLInt), GraphQLInt)


def test_is_type_sub_type_of_nullable_is_not_subtype_of_non_null():
    schema = _test_schema(GraphQLString)
    assert not is_type_sub_type_of(schema, GraphQLInt, GraphQLNonNull(GraphQLInt))


def test_is_type_sub_type_of_item_is_not_subtype_of_list():
    schema = _test_schema(GraphQLString)
    assert not is_type_sub_type_of(schema, GraphQLInt, GraphQLList(GraphQLInt))


def test_is_type_sub_type_of_list_is_not_subtype_of_item():
    schema = _test_schema(GraphQLString)
    assert not is_type_sub_type_of(schema, GraphQLList(GraphQLInt), GraphQLInt)


def test_is_type_sub_type_of_member_is_subtype_of_union():
    member = GraphQLObjectType(
        name="Object",
        is_type_of=lambda *_: True,
        fields={"field": GraphQLField(GraphQLString)},
    )
    union = GraphQLUnionType(name="Union", types=[member])
    schema = _test_schema(union)
    assert is_type_sub_type_of(schema, member, union)


def test_is_type_sub_type_of_implementation_is_subtype_of_interface():
    iface = GraphQLInterfaceType(
        name="Interface", fields={"field": GraphQLField(GraphQLString)}
    )
    impl = GraphQLObjectType(
        name="Object",
        is_type_of=lambda *_: True,
        interfaces=[iface],
        fields={"field": GraphQLField(GraphQLString)},
    )
    schema = _test_schema(impl)
    assert is_type_sub_type_of(schema, impl, iface)
