from ..language.printer import print_ast
from ..type.definition import (
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLUnionType,
)
from ..type.directives import DEFAULT_DEPRECATION_REASON
from .ast_from_value import ast_from_value


# Necessary for static type checking
if False:  # flake8: noqa
    from ..type.definition import (
        GraphQLArgument,
        GraphQLType,
        GraphQLField,
        GraphQLInputObjectField,
        GraphQLEnumValue,
    )
    from ..type.schema import GraphQLSchema
    from ..type.directives import GraphQLDirective
    from typing import Any, Union, Callable


def print_schema(schema):
    # type: (GraphQLSchema) -> str
    return _print_filtered_schema(
        schema, lambda n: not (is_spec_directive(n)), _is_defined_type
    )


def print_introspection_schema(schema):
    # type: (GraphQLSchema) -> str
    return _print_filtered_schema(schema, is_spec_directive, _is_introspection_type)


def is_spec_directive(directive_name):
    # type: (str) -> bool
    return directive_name in ("skip", "include", "deprecated")


def _is_defined_type(typename):
    # type: (Any) -> bool
    return not _is_introspection_type(typename) and not _is_builtin_scalar(typename)


def _is_introspection_type(typename):
    # type: (str) -> bool
    return typename.startswith("__")


_builtin_scalars = frozenset(["String", "Boolean", "Int", "Float", "ID"])


def _is_builtin_scalar(typename):
    # type: (str) -> bool
    return typename in _builtin_scalars


def _print_filtered_schema(schema, directive_filter, type_filter):
    # type: (GraphQLSchema, Callable[[str], bool], Callable[[str], bool]) -> str
    return (
        "\n\n".join(
            [_print_schema_definition(schema)]
            + [
                _print_directive(directive)
                for directive in schema.get_directives()
                if directive_filter(directive.name)
            ]
            + [
                _print_type(type)
                for typename, type in sorted(schema.get_type_map().items())
                if type_filter(typename)
            ]
        )
        + "\n"
    )


def _print_schema_definition(schema):
    # type: (GraphQLSchema) -> str
    operation_types = []

    query_type = schema.get_query_type()
    if query_type:
        operation_types.append("  query: {}".format(query_type))

    mutation_type = schema.get_mutation_type()
    if mutation_type:
        operation_types.append("  mutation: {}".format(mutation_type))

    subscription_type = schema.get_subscription_type()
    if subscription_type:
        operation_types.append("  subscription: {}".format(subscription_type))

    return "schema {{\n{}\n}}".format("\n".join(operation_types))


def _print_type(type):
    # type: (GraphQLType) -> str
    if isinstance(type, GraphQLScalarType):
        return _print_scalar(type)

    elif isinstance(type, GraphQLObjectType):
        return _print_object(type)

    elif isinstance(type, GraphQLInterfaceType):
        return _print_interface(type)

    elif isinstance(type, GraphQLUnionType):
        return _print_union(type)

    elif isinstance(type, GraphQLEnumType):
        return _print_enum(type)

    assert isinstance(type, GraphQLInputObjectType)
    return _print_input_object(type)


def _print_scalar(type):
    # type: (GraphQLScalarType) -> str
    return "scalar {}".format(type.name)


def _print_object(type):
    # type: (GraphQLObjectType) -> str
    interfaces = type.interfaces
    implemented_interfaces = (
        " implements {}".format(", ".join(i.name for i in interfaces))
        if interfaces
        else ""
    )

    return ("type {}{} {{\n" "{}\n" "}}").format(
        type.name, implemented_interfaces, _print_fields(type)
    )


def _print_interface(type):
    # type: (GraphQLInterfaceType) -> str
    return ("interface {} {{\n" "{}\n" "}}").format(type.name, _print_fields(type))


def _print_union(type):
    # type: (GraphQLUnionType) -> str
    return "union {} = {}".format(type.name, " | ".join(str(t) for t in type.types))


def _print_enum(type):
    # type: (GraphQLEnumType) -> str
    return ("enum {} {{\n" "{}\n" "}}").format(
        type.name, "\n".join("  " + v.name + _print_deprecated(v) for v in type.values)
    )


def _print_input_object(type):
    # type: (GraphQLInputObjectType) -> str
    return ("input {} {{\n" "{}\n" "}}").format(
        type.name,
        "\n".join(
            "  " + _print_input_value(name, field)
            for name, field in type.fields.items()
        ),
    )


def _print_fields(type):
    # type: (Union[GraphQLObjectType, GraphQLInterfaceType]) -> str
    return "\n".join(
        "  {}{}: {}{}".format(f_name, _print_args(f), f.type, _print_deprecated(f))
        for f_name, f in type.fields.items()
    )


def _print_deprecated(field_or_enum_value):
    # type: (Union[GraphQLField, GraphQLEnumValue]) -> str
    reason = field_or_enum_value.deprecation_reason

    if reason is None:
        return ""
    elif reason in ("", DEFAULT_DEPRECATION_REASON):
        return " @deprecated"
    else:
        return " @deprecated(reason: {})".format(print_ast(ast_from_value(reason)))


def _print_args(field_or_directives):
    # type: (Union[GraphQLField, GraphQLDirective]) -> str
    if not field_or_directives.args:
        return ""

    return "({})".format(
        ", ".join(
            _print_input_value(arg_name, arg)
            for arg_name, arg in field_or_directives.args.items()
        )
    )


def _print_input_value(name, arg):
    # type: (str, GraphQLArgument) -> str
    if arg.default_value is not None:
        default_value = " = " + print_ast(ast_from_value(arg.default_value, arg.type))
    else:
        default_value = ""

    return "{}: {}{}".format(name, arg.type, default_value)


def _print_directive(directive):
    # type: (GraphQLDirective) -> str
    return "directive @{}{} on {}".format(
        directive.name, _print_args(directive), " | ".join(directive.locations)
    )


__all__ = ["print_schema", "print_introspection_schema"]
