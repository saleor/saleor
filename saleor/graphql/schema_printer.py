"""Code ported from GraphQL Core 3.0.

Can be dropped once we upgrade from the legacy version of GraphQL Core.
"""

from collections.abc import Callable
from typing import cast

from graphql import (
    DEFAULT_DEPRECATION_REASON,
    GraphQLArgument,
    GraphQLDirective,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLNamedType,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLString,
    GraphQLUnionType,
    ValueNode,
    ast_from_value,
    print_ast,
)
from graphql.language.block_string import print_block_string
from graphql.language.print_string import print_string

__all__ = ["print_schema", "print_introspection_schema", "print_type"]

from ..webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType


def is_specified_directive(directive: GraphQLDirective) -> bool:
    return directive.name in ("skip", "include", "deprecated")


def print_schema(schema: GraphQLSchema) -> str:
    return print_filtered_schema(
        schema, lambda n: not is_specified_directive(n), is_defined_type
    )


def is_introspection_type(type_: GraphQLNamedType) -> bool:
    return type_.name.startswith("__")


def print_introspection_schema(schema: GraphQLSchema) -> str:
    return print_filtered_schema(schema, is_specified_directive, is_introspection_type)


_builtin_scalars = frozenset(["String", "Boolean", "Int", "Float", "ID"])


def is_specified_scalar_type(type_: GraphQLNamedType) -> bool:
    return type_.name in _builtin_scalars


def is_defined_type(type_: GraphQLNamedType) -> bool:
    return not is_specified_scalar_type(type_) and not is_introspection_type(type_)


def print_filtered_schema(
    schema: GraphQLSchema,
    directive_filter: Callable[[GraphQLDirective], bool],
    type_filter: Callable[[GraphQLNamedType], bool],
) -> str:
    directives = filter(directive_filter, schema.directives)
    types = filter(type_filter, cast(list[GraphQLNamedType], schema.type_map.values()))

    return "\n\n".join(
        (
            *filter(None, (print_schema_definition(schema),)),
            *map(print_directive, directives),
            *map(print_type, types),
        )
    )


def print_schema_definition(schema: GraphQLSchema) -> str | None:
    operation_types = []

    query_type = schema.query_type
    if query_type:
        operation_types.append(f"  query: {query_type.name}")

    mutation_type = schema.mutation_type
    if mutation_type:
        operation_types.append(f"  mutation: {mutation_type.name}")

    subscription_type = schema.subscription_type
    if subscription_type:
        operation_types.append(f"  subscription: {subscription_type.name}")

    return "schema {\n" + "\n".join(operation_types) + "\n}"


def is_schema_of_common_names(schema: GraphQLSchema) -> bool:
    """Check whether this schema uses the common naming convention.

    GraphQL schema define root types for each type of operation. These types are the
    same as any other type and can be named in any manner, however there is a common
    naming convention:

    schema {
      query: Query
      mutation: Mutation
      subscription: Subscription
    }

    When using this naming convention, the schema description can be omitted.
    """
    query_type = schema.query_type
    if query_type and query_type.name != "Query":
        return False

    mutation_type = schema.mutation_type
    if mutation_type and mutation_type.name != "Mutation":
        return False

    subscription_type = schema.subscription_type
    return not subscription_type or subscription_type.name == "Subscription"


def print_type(type_: GraphQLNamedType) -> str:
    if isinstance(type_, GraphQLScalarType):
        type_ = type_
        return print_scalar(type_)
    if isinstance(type_, GraphQLObjectType):
        type_ = type_
        return print_object(type_)
    if isinstance(type_, GraphQLInterfaceType):
        type_ = type_
        return print_interface(type_)
    if isinstance(type_, GraphQLUnionType):
        type_ = type_
        return print_union(type_)
    if isinstance(type_, GraphQLEnumType):
        type_ = type_
        return print_enum(type_)
    if isinstance(type_, GraphQLInputObjectType):
        type_ = type_
        return print_input_object(type_)

    # Not reachable. All possible types have been considered.
    raise TypeError(f"Unexpected type: {type_}.")


def print_scalar(type_: GraphQLScalarType) -> str:
    return print_description(type_) + f"scalar {type_.name}"


def print_implemented_interfaces(type_: GraphQLObjectType) -> str:
    interfaces = type_.interfaces
    return " implements " + " & ".join(i.name for i in interfaces) if interfaces else ""


def print_object(type_: GraphQLObjectType) -> str:
    return (
        print_description(type_)
        + f"type {type_.name}"
        + print_implemented_interfaces(type_)
        + print_fields(type_)
    )


def print_interface(type_: GraphQLInterfaceType) -> str:
    return print_description(type_) + f"interface {type_.name}" + print_fields(type_)


def print_union(type_: GraphQLUnionType) -> str:
    types = type_.types
    possible_types = " = " + " | ".join(t.name for t in types) if types else ""
    return print_description(type_) + f"union {type_.name}" + possible_types


def print_enum(type_: GraphQLEnumType) -> str:
    values = [
        print_description(v, "  ", not i)
        + f"  {v.value}"
        + print_deprecated(v.deprecation_reason)
        for i, v in enumerate(type_.values.values())
    ]
    return print_description(type_) + f"enum {type_.name}" + print_block(values)


def print_input_object(type_: GraphQLInputObjectType) -> str:
    fields = [
        print_description(field, "  ", not i) + "  " + print_input_value(name, field)
        for i, (name, field) in enumerate(type_.fields.items())
    ]
    return print_description(type_) + f"input {type_.name}" + print_block(fields)


def print_fields(type_: GraphQLObjectType | GraphQLInterfaceType) -> str:
    fields = [
        print_description(field, "  ", not i)
        + f"  {name}"
        + print_args(field.args, "  ")
        + f": {field.type}"
        + print_deprecated(field.deprecation_reason)
        for i, (name, field) in enumerate(type_.fields.items())
    ]
    return print_block(fields)


def print_block(items: list[str]) -> str:
    return " {\n" + "\n".join(items) + "\n}" if items else ""


def print_args(args: dict[str, GraphQLArgument], indentation: str = "") -> str:
    if not args:
        return ""

    # If every arg does not have a description, print them on one line.
    if not any(arg.description for arg in args.values()):
        return (
            "("
            + ", ".join(print_input_value(name, arg) for name, arg in args.items())
            + ")"
        )

    return (
        "(\n"
        + "\n".join(
            print_description(arg, f"  {indentation}", not i)
            + f"  {indentation}"
            + print_input_value(name, arg)
            for i, (name, arg) in enumerate(args.items())
        )
        + f"\n{indentation})"
    )


def print_input_value(name: str, arg: GraphQLArgument) -> str:
    default_ast = cast(ValueNode, ast_from_value(arg.default_value, arg.type))
    arg_decl = f"{name}: {arg.type}"
    if default_ast:
        arg_decl += f" = {print_ast(default_ast)}"

    return arg_decl


def print_directive(directive: GraphQLDirective) -> str:
    return (
        print_description(directive)
        + f"directive @{directive.name}"
        + print_args(directive.args)
        + " on "
        + " | ".join(location.name for location in directive.locations)
    )


def print_deprecated(reason: str | None) -> str:
    if reason is None:
        return ""
    if reason != DEFAULT_DEPRECATION_REASON:
        reason = print_string(reason)
        return f" @deprecated(reason: {reason})"
    return " @deprecated"


def is_printable_as_block_string(value: str) -> bool:
    """Check whether the given string is printable as a block string."""
    if not isinstance(value, str):
        value = str(value)  # resolve lazy string proxy object

    if not value:
        return True  # empty string is printable

    is_empty_line = True
    has_indent = False
    has_common_indent = True
    seen_non_empty_line = False

    for c in value:
        if c == "\n":
            if is_empty_line and not seen_non_empty_line:
                return False  # has leading new line
            seen_non_empty_line = True
            is_empty_line = True
            has_indent = False
        elif c in " \t":
            has_indent = has_indent or is_empty_line
        elif c <= "\x0f":
            return False
        else:
            has_common_indent = has_common_indent and has_indent
            is_empty_line = False

    if is_empty_line:
        return False  # has trailing empty lines

    if has_common_indent and seen_non_empty_line:
        return False  # has internal indent

    return True


def print_description(
    def_: (
        GraphQLArgument
        | GraphQLDirective
        | GraphQLEnumType
        | GraphQLEnumValue
        | GraphQLInputObjectType
        | GraphQLInterfaceType
        | GraphQLObjectType
        | GraphQLScalarType
        | GraphQLUnionType
    ),
    indentation: str = "",
    first_in_block: bool = True,
) -> str:
    description: str | None = def_.description
    if description is None:
        return ""

    description = description.rstrip()

    if is_printable_as_block_string(description):
        block_string = print_block_string(description)
    else:
        ast = cast(ValueNode, ast_from_value(description, GraphQLString))
        block_string = print_ast(ast)

    prefix = "\n" + indentation if indentation and not first_in_block else indentation

    return prefix + block_string.replace("\n", "\n" + indentation) + "\n"
