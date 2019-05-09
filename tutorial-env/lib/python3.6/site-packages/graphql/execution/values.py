import collections
import json

from six import string_types

from ..error import GraphQLError
from ..language import ast
from ..language.printer import print_ast
from ..type import (
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLScalarType,
    is_input_type,
)
from ..utils.is_valid_value import is_valid_value
from ..utils.type_from_ast import type_from_ast
from ..utils.value_from_ast import value_from_ast

# Necessary for static type checking
if False:  # flake8: noqa
    from ..language.ast import VariableDefinition, Argument
    from ..type.schema import GraphQLSchema
    from ..type.definition import GraphQLArgument
    from typing import Any, Dict, List, Union, Dict, Optional

__all__ = ["get_variable_values", "get_argument_values"]


def get_variable_values(
    schema,  # type: GraphQLSchema
    definition_asts,  # type: List[VariableDefinition]
    inputs,  # type: Any
):
    # type: (...) -> Dict[str, Any]
    """Prepares an object map of variables of the correct type based on the provided variable definitions and arbitrary input.
    If the input cannot be parsed to match the variable definitions, a GraphQLError will be thrown."""
    if inputs is None:
        inputs = {}

    values = {}
    for def_ast in definition_asts:
        var_name = def_ast.variable.name.value
        var_type = type_from_ast(schema, def_ast.type)
        value = inputs.get(var_name)

        if not is_input_type(var_type):
            raise GraphQLError(
                'Variable "${var_name}" expected value of type "{var_type}" which cannot be used as an input type.'.format(
                    var_name=var_name, var_type=print_ast(def_ast.type)
                ),
                [def_ast],
            )
        elif value is None:
            if def_ast.default_value is not None:
                values[var_name] = value_from_ast(
                    def_ast.default_value, var_type
                )  # type: ignore
            if isinstance(var_type, GraphQLNonNull):
                raise GraphQLError(
                    'Variable "${var_name}" of required type "{var_type}" was not provided.'.format(
                        var_name=var_name, var_type=var_type
                    ),
                    [def_ast],
                )
        else:
            errors = is_valid_value(value, var_type)
            if errors:
                message = u"\n" + u"\n".join(errors)
                raise GraphQLError(
                    'Variable "${}" got invalid value {}.{}'.format(
                        var_name, json.dumps(value, sort_keys=True), message
                    ),
                    [def_ast],
                )
            coerced_value = coerce_value(var_type, value)
            if coerced_value is None:
                raise Exception("Should have reported error.")

            values[var_name] = coerced_value

    return values


def get_argument_values(
    arg_defs,  # type: Union[Dict[str, GraphQLArgument], Dict]
    arg_asts,  # type: Optional[List[Argument]]
    variables=None,  # type: Optional[Dict[str, Union[List, Dict, int, float, bool, str, None]]]
):
    # type: (...) -> Dict[str, Any]
    """Prepares an object map of argument values given a list of argument
    definitions and list of argument AST nodes."""
    if not arg_defs:
        return {}

    if arg_asts:
        arg_ast_map = {
            arg.name.value: arg for arg in arg_asts
        }  # type: Dict[str, Argument]
    else:
        arg_ast_map = {}

    result = {}
    for name, arg_def in arg_defs.items():
        arg_type = arg_def.type
        arg_ast = arg_ast_map.get(name)
        if name not in arg_ast_map:
            if arg_def.default_value is not None:
                result[arg_def.out_name or name] = arg_def.default_value
                continue
            elif isinstance(arg_type, GraphQLNonNull):
                raise GraphQLError(
                    'Argument "{name}" of required type {arg_type}" was not provided.'.format(
                        name=name, arg_type=arg_type
                    ),
                    arg_asts,
                )
        elif isinstance(arg_ast.value, ast.Variable):  # type: ignore
            variable_name = arg_ast.value.name.value  # type: ignore
            if variables and variable_name in variables:
                result[arg_def.out_name or name] = variables[variable_name]
            elif arg_def.default_value is not None:
                result[arg_def.out_name or name] = arg_def.default_value
            elif isinstance(arg_type, GraphQLNonNull):
                raise GraphQLError(
                    'Argument "{name}" of required type {arg_type}" provided the variable "${variable_name}" which was not provided'.format(
                        name=name, arg_type=arg_type, variable_name=variable_name
                    ),
                    arg_asts,
                )
            continue

        else:
            value = value_from_ast(arg_ast.value, arg_type, variables)  # type: ignore
            if value is None:
                if arg_def.default_value is not None:
                    value = arg_def.default_value
                    result[arg_def.out_name or name] = value
            else:
                # We use out_name as the output name for the
                # dict if exists
                result[arg_def.out_name or name] = value

    return result


def coerce_value(type, value):
    # type: (Any, Any) -> Union[List, Dict, int, float, bool, str, None]
    """Given a type and any value, return a runtime value coerced to match the type."""
    if isinstance(type, GraphQLNonNull):
        # Note: we're not checking that the result of coerceValue is
        # non-null.
        # We only call this function after calling isValidValue.
        return coerce_value(type.of_type, value)

    if value is None:
        return None

    if isinstance(type, GraphQLList):
        item_type = type.of_type
        if not isinstance(value, string_types) and isinstance(
            value, collections.Iterable
        ):
            return [coerce_value(item_type, item) for item in value]
        else:
            return [coerce_value(item_type, value)]

    if isinstance(type, GraphQLInputObjectType):
        fields = type.fields
        obj = {}
        for field_name, field in fields.items():
            if field_name not in value:
                if field.default_value is not None:
                    field_value = field.default_value
                    obj[field.out_name or field_name] = field_value
            else:
                field_value = coerce_value(field.type, value.get(field_name))
                obj[field.out_name or field_name] = field_value

        return type.create_container(obj)

    assert isinstance(type, (GraphQLScalarType, GraphQLEnumType)), "Must be input type"

    return type.parse_value(value)
