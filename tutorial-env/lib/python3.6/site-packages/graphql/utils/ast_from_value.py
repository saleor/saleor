import json
import re
import sys

from six import string_types

from ..language import ast
from ..type.definition import (
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLList,
    GraphQLNonNull,
)
from ..type.scalars import GraphQLFloat


def ast_from_value(value, type=None):
    if isinstance(type, GraphQLNonNull):
        return ast_from_value(value, type.of_type)

    if value is None:
        return None

    if isinstance(value, list):
        item_type = type.of_type if isinstance(type, GraphQLList) else None
        return ast.ListValue([ast_from_value(item, item_type) for item in value])

    elif isinstance(type, GraphQLList):
        return ast_from_value(value, type.of_type)

    if isinstance(value, bool):
        return ast.BooleanValue(value)

    if isinstance(value, (int, float)):
        string_num = str(value)
        int_value = int(value)
        is_int_value = string_num.isdigit()

        if is_int_value or (int_value == value and value < sys.maxsize):
            if type == GraphQLFloat:
                return ast.FloatValue(str(float(value)))

            return ast.IntValue(str(int(value)))

        return ast.FloatValue(string_num)

    if isinstance(value, string_types):
        if isinstance(type, GraphQLEnumType) and re.match(
            r"^[_a-zA-Z][_a-zA-Z0-9]*$", value
        ):
            return ast.EnumValue(value)

        return ast.StringValue(json.dumps(value)[1:-1])

    assert isinstance(value, dict)

    fields = []
    is_graph_ql_input_object_type = isinstance(type, GraphQLInputObjectType)

    for field_name, field_value in value.items():
        field_type = None
        if is_graph_ql_input_object_type:
            field_def = type.fields.get(field_name)
            field_type = field_def and field_def.type

        field_value = ast_from_value(field_value, field_type)
        if field_value:
            fields.append(ast.ObjectField(ast.Name(field_name), field_value))

    return ast.ObjectValue(fields)
