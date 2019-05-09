from collections import OrderedDict

from graphql.language import ast
from graphql.type.definition import (
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLInputObjectField,
    GraphQLInputObjectType,
    GraphQLList,
)
from graphql.type.scalars import GraphQLFloat
from graphql.utils.ast_from_value import ast_from_value


def test_converts_boolean_values_to_asts():
    assert ast_from_value(True) == ast.BooleanValue(True)
    assert ast_from_value(False) == ast.BooleanValue(False)


def test_converts_numeric_values_to_asts():
    assert ast_from_value(123) == ast.IntValue("123")
    assert ast_from_value(123.0) == ast.IntValue("123")
    assert ast_from_value(123.5) == ast.FloatValue("123.5")
    assert ast_from_value(1e4) == ast.IntValue("10000")
    assert ast_from_value(1e40) == ast.FloatValue("1e+40")


def test_it_converts_numeric_values_to_float_asts():
    assert ast_from_value(123, GraphQLFloat) == ast.FloatValue("123.0")
    assert ast_from_value(123.0, GraphQLFloat) == ast.FloatValue("123.0")
    assert ast_from_value(123.5, GraphQLFloat) == ast.FloatValue("123.5")
    assert ast_from_value(1e4, GraphQLFloat) == ast.FloatValue("10000.0")
    assert ast_from_value(1e40, GraphQLFloat) == ast.FloatValue("1e+40")


def test_it_converts_string_values_to_asts():
    assert ast_from_value("hello") == ast.StringValue("hello")
    assert ast_from_value("VALUE") == ast.StringValue("VALUE")
    assert ast_from_value(u"VAL\nUE") == ast.StringValue("VAL\\nUE")
    assert ast_from_value("VAL\nUE") == ast.StringValue("VAL\\nUE")
    assert ast_from_value("123") == ast.StringValue("123")


my_enum = GraphQLEnumType(
    "MyEnum", {"HELLO": GraphQLEnumValue(1), "GOODBYE": GraphQLEnumValue(2)}
)


def test_converts_string_values_to_enum_asts_if_possible():
    assert ast_from_value("hello", my_enum) == ast.EnumValue("hello")
    assert ast_from_value("HELLO", my_enum) == ast.EnumValue("HELLO")
    assert ast_from_value("VAL\nUE", my_enum) == ast.StringValue("VAL\\nUE")
    assert ast_from_value("123", my_enum) == ast.StringValue("123")


def test_converts_array_values_to_list_asts():
    assert ast_from_value(["FOO", "BAR"]) == ast.ListValue(
        values=[ast.StringValue("FOO"), ast.StringValue("BAR")]
    )


def test_converts_list_singletons():
    assert ast_from_value("FOO", GraphQLList(my_enum)) == ast.EnumValue("FOO")


def test_converts_input_objects():
    value = OrderedDict([("foo", 3), ("bar", "HELLO")])

    assert ast_from_value(value) == ast.ObjectValue(
        fields=[
            ast.ObjectField(name=ast.Name("foo"), value=ast.IntValue("3")),
            ast.ObjectField(name=ast.Name("bar"), value=ast.StringValue("HELLO")),
        ]
    )

    input_obj = GraphQLInputObjectType(
        "MyInputObj",
        {
            "foo": GraphQLInputObjectField(GraphQLFloat),
            "bar": GraphQLInputObjectField(my_enum),
        },
    )

    assert ast_from_value(value, input_obj) == ast.ObjectValue(
        fields=[
            ast.ObjectField(name=ast.Name("foo"), value=ast.FloatValue("3.0")),
            ast.ObjectField(name=ast.Name("bar"), value=ast.EnumValue("HELLO")),
        ]
    )
