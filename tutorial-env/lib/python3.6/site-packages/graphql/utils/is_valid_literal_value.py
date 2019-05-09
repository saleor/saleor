from ..language import ast
from ..language.printer import print_ast
from ..type.definition import (
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLScalarType,
)

# Necessary for static type checking
if False:  # flake8: noqa
    from ..language.ast import ObjectValue, StringValue
    from ..type.definition import GraphQLInputObjectType, GraphQLScalarType
    from typing import Union, Any, List

_empty_list = []  # type: List


def is_valid_literal_value(type, value_ast):
    # type: (Union[GraphQLInputObjectType, GraphQLScalarType, GraphQLNonNull, GraphQLList], Any) -> List
    if isinstance(type, GraphQLNonNull):
        of_type = type.of_type
        if not value_ast:
            return [u'Expected "{}", found null.'.format(type)]

        return is_valid_literal_value(of_type, value_ast)  # type: ignore

    if not value_ast:
        return _empty_list

    if isinstance(value_ast, ast.Variable):
        return _empty_list

    if isinstance(type, GraphQLList):
        item_type = type.of_type
        if isinstance(value_ast, ast.ListValue):
            errors = []

            for i, item_ast in enumerate(value_ast.values):
                item_errors = is_valid_literal_value(item_type, item_ast)
                for error in item_errors:
                    errors.append(u"In element #{}: {}".format(i, error))

            return errors

        return is_valid_literal_value(item_type, value_ast)

    if isinstance(type, GraphQLInputObjectType):
        if not isinstance(value_ast, ast.ObjectValue):
            return [u'Expected "{}", found not an object.'.format(type)]

        fields = type.fields
        field_asts = value_ast.fields

        errors = []
        for provided_field_ast in field_asts:
            if provided_field_ast.name.value not in fields:
                errors.append(
                    u'In field "{}": Unknown field.'.format(
                        provided_field_ast.name.value
                    )
                )

        field_ast_map = {field_ast.name.value: field_ast for field_ast in field_asts}

        def get_field_ast_value(field_name):
            # type: (str) -> Union[None, ObjectValue, StringValue]
            if field_name in field_ast_map:
                return field_ast_map[field_name].value
            return None

        for field_name, field in fields.items():
            subfield_errors = is_valid_literal_value(
                field.type, get_field_ast_value(field_name)
            )
            errors.extend(
                u'In field "{}": {}'.format(field_name, e) for e in subfield_errors
            )

        return errors

    assert isinstance(type, (GraphQLScalarType, GraphQLEnumType)), "Must be input type"

    parse_result = type.parse_literal(value_ast)
    if parse_result is None:
        return [
            u'Expected type "{}", found {}.'.format(type.name, print_ast(value_ast))
        ]

    return _empty_list
