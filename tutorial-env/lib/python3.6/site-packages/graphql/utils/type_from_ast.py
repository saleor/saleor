from ..language import ast
from ..type.definition import GraphQLList, GraphQLNonNull

# Necessary for static type checking
if False:  # flake8: noqa
    from ..language.ast import ListType, NamedType, NonNullType
    from ..type.definition import GraphQLNamedType
    from ..type.schema import GraphQLSchema
    from typing import Any, Union


def type_from_ast(schema, type_node):
    # type: (GraphQLSchema, Union[ListType, NamedType, NonNullType]) -> Union[GraphQLList, GraphQLNonNull, GraphQLNamedType]
    if isinstance(type_node, ast.ListType):
        inner_type = type_from_ast(schema, type_node.type)
        return inner_type and GraphQLList(inner_type)

    elif isinstance(type_node, ast.NonNullType):
        inner_type = type_from_ast(schema, type_node.type)
        return inner_type and GraphQLNonNull(inner_type)  # type: ignore

    elif isinstance(type_node, ast.NamedType):
        schema_type = schema.get_type(type_node.name.value)
        return schema_type  # type: ignore

    raise Exception("Unexpected type kind: {type_kind}".format(type_kind=type_node))
