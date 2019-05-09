import json

from .visitor import Visitor, visit

# Necessary for static type checking
if False:  # flake8: noqa
    from typing import Any, List, Optional, Union
    from graphql.language.ast import (
        Node,
        Name,
        Variable,
        Document,
        OperationDefinition,
        VariableDefinition,
        SelectionSet,
        Field,
        Argument,
        FragmentSpread,
        InlineFragment,
        FragmentDefinition,
        IntValue,
        StringValue,
        BooleanValue,
        EnumValue,
        ListValue,
        ObjectValue,
        ObjectField,
        Directive,
        NamedType,
        ListType,
        NonNullType,
        SchemaDefinition,
        OperationTypeDefinition,
        ScalarTypeDefinition,
        ObjectTypeDefinition,
        FieldDefinition,
        InputValueDefinition,
        InterfaceTypeDefinition,
        UnionTypeDefinition,
        EnumTypeDefinition,
        EnumValueDefinition,
        InputObjectTypeDefinition,
        TypeExtensionDefinition,
        DirectiveDefinition,
    )

__all__ = ["print_ast"]


def print_ast(ast):
    # type: (Node) -> str
    return visit(ast, PrintingVisitor())


class PrintingVisitor(Visitor):
    __slots__ = ()

    def leave_Name(self, node, *args):
        # type: (Any, *Any) -> str
        return node.value  # type: ignore

    def leave_Variable(self, node, *args):
        # type: (Any, *Any) -> str
        return "$" + node.name  # type: ignore

    def leave_Document(self, node, *args):
        # type: (Any, *Any) -> str
        return join(node.definitions, "\n\n") + "\n"  # type: ignore

    def leave_OperationDefinition(self, node, *args):
        # type: (Any, *Any) -> str
        name = node.name
        selection_set = node.selection_set
        op = node.operation
        var_defs = wrap("(", join(node.variable_definitions, ", "), ")")
        directives = join(node.directives, " ")

        if not name and not directives and not var_defs and op == "query":
            return selection_set

        return join([op, join([name, var_defs]), directives, selection_set], " ")

    def leave_VariableDefinition(self, node, *args):
        # type: (Any, *Any) -> str
        return node.variable + ": " + node.type + wrap(" = ", node.default_value)

    def leave_SelectionSet(self, node, *args):
        # type: (Any, *Any) -> str
        return block(node.selections)

    def leave_Field(self, node, *args):
        # type: (Any, *Any) -> str
        return join(
            [
                wrap("", node.alias, ": ")
                + node.name
                + wrap("(", join(node.arguments, ", "), ")"),
                join(node.directives, " "),
                node.selection_set,
            ],
            " ",
        )

    def leave_Argument(self, node, *args):
        # type: (Any, *Any) -> str
        return "{0.name}: {0.value}".format(node)

    # Fragments

    def leave_FragmentSpread(self, node, *args):
        # type: (Any, *Any) -> str
        return "..." + node.name + wrap(" ", join(node.directives, " "))

    def leave_InlineFragment(self, node, *args):
        # type: (Any, *Any) -> str
        return join(
            [
                "...",
                wrap("on ", node.type_condition),
                join(node.directives, ""),
                node.selection_set,
            ],
            " ",
        )

    def leave_FragmentDefinition(self, node, *args):
        # type: (Any, *Any) -> str
        return (
            "fragment {} on {} ".format(node.name, node.type_condition)
            + wrap("", join(node.directives, " "), " ")
            + node.selection_set
        )

    # Value

    def leave_IntValue(self, node, *args):
        # type: (Any, *Any) -> str
        return node.value

    def leave_FloatValue(self, node, *args):
        return node.value

    def leave_StringValue(self, node, *args):
        # type: (Any, *Any) -> str
        return json.dumps(node.value)

    def leave_BooleanValue(self, node, *args):
        # type: (Any, *Any) -> str
        return json.dumps(node.value)

    def leave_EnumValue(self, node, *args):
        # type: (Any, *Any) -> str
        return node.value

    def leave_ListValue(self, node, *args):
        # type: (Any, *Any) -> str
        return "[" + join(node.values, ", ") + "]"

    def leave_ObjectValue(self, node, *args):
        # type: (Any, *Any) -> str
        return "{" + join(node.fields, ", ") + "}"

    def leave_ObjectField(self, node, *args):
        # type: (Any, *Any) -> str
        return node.name + ": " + node.value

    # Directive

    def leave_Directive(self, node, *args):
        # type: (Any, *Any) -> str
        return "@" + node.name + wrap("(", join(node.arguments, ", "), ")")

    # Type

    def leave_NamedType(self, node, *args):
        # type: (Any, *Any) -> str
        return node.name

    def leave_ListType(self, node, *args):
        # type: (Any, *Any) -> str
        return "[" + node.type + "]"

    def leave_NonNullType(self, node, *args):
        # type: (Any, *Any) -> str
        return node.type + "!"

    # Type Definitions:

    def leave_SchemaDefinition(self, node, *args):
        # type: (Any, *Any) -> str
        return join(
            ["schema", join(node.directives, " "), block(node.operation_types)], " "
        )

    def leave_OperationTypeDefinition(self, node, *args):
        # type: (Any, *Any) -> str
        return "{}: {}".format(node.operation, node.type)

    def leave_ScalarTypeDefinition(self, node, *args):
        # type: (Any, *Any) -> str
        return "scalar " + node.name + wrap(" ", join(node.directives, " "))

    def leave_ObjectTypeDefinition(self, node, *args):
        # type: (Any, *Any) -> str
        return join(
            [
                "type",
                node.name,
                wrap("implements ", join(node.interfaces, ", ")),
                join(node.directives, " "),
                block(node.fields),
            ],
            " ",
        )

    def leave_FieldDefinition(self, node, *args):
        # type: (Any, *Any) -> str
        return (
            node.name
            + wrap("(", join(node.arguments, ", "), ")")
            + ": "
            + node.type
            + wrap(" ", join(node.directives, " "))
        )

    def leave_InputValueDefinition(self, node, *args):
        # type: (Any, *Any) -> str
        return (
            node.name
            + ": "
            + node.type
            + wrap(" = ", node.default_value)
            + wrap(" ", join(node.directives, " "))
        )

    def leave_InterfaceTypeDefinition(self, node, *args):
        # type: (Any, *Any) -> str
        return (
            "interface "
            + node.name
            + wrap(" ", join(node.directives, " "))
            + " "
            + block(node.fields)
        )

    def leave_UnionTypeDefinition(self, node, *args):
        # type: (Any, *Any) -> str
        return (
            "union "
            + node.name
            + wrap(" ", join(node.directives, " "))
            + " = "
            + join(node.types, " | ")
        )

    def leave_EnumTypeDefinition(self, node, *args):
        # type: (Any, *Any) -> str
        return (
            "enum "
            + node.name
            + wrap(" ", join(node.directives, " "))
            + " "
            + block(node.values)
        )

    def leave_EnumValueDefinition(self, node, *args):
        # type: (Any, *Any) -> str
        return node.name + wrap(" ", join(node.directives, " "))

    def leave_InputObjectTypeDefinition(self, node, *args):
        # type: (Any, *Any) -> str
        return (
            "input "
            + node.name
            + wrap(" ", join(node.directives, " "))
            + " "
            + block(node.fields)
        )

    def leave_TypeExtensionDefinition(self, node, *args):
        # type: (Any, *Any) -> str
        return "extend " + node.definition

    def leave_DirectiveDefinition(self, node, *args):
        # type: (Any, *Any) -> str
        return "directive @{}{} on {}".format(
            node.name,
            wrap("(", join(node.arguments, ", "), ")"),
            " | ".join(node.locations),
        )


def join(maybe_list, separator=""):
    # type: (Optional[List[str]], str) -> str
    if maybe_list:
        return separator.join(filter(None, maybe_list))
    return ""


def block(_list):
    # type: (List[str]) -> str
    """Given a list, print each item on its own line, wrapped in an indented "{ }" block."""
    if _list:
        return indent("{\n" + join(_list, "\n")) + "\n}"
    return "{}"


def wrap(start, maybe_str, end=""):
    # type: (str, Optional[str], str) -> str
    if maybe_str:
        return start + maybe_str + end
    return ""


def indent(maybe_str):
    # type: (Optional[str]) -> str
    if maybe_str:
        return maybe_str.replace("\n", "\n  ")
    return ""
