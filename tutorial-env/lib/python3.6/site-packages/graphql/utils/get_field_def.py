from ..type.definition import GraphQLInterfaceType, GraphQLObjectType, GraphQLUnionType
from ..type.introspection import (
    SchemaMetaFieldDef,
    TypeMetaFieldDef,
    TypeNameMetaFieldDef,
)

# Necessary for static type checking
if False:  # flake8: noqa
    from ..language.ast import Field
    from ..type.definition import GraphQLField, GraphQLInterfaceType, GraphQLObjectType
    from ..type.schema import GraphQLSchema
    from typing import Optional, Union


def get_field_def(
    schema,  # type: GraphQLSchema
    parent_type,  # type: Union[GraphQLInterfaceType, GraphQLObjectType]
    field_ast,  # type: Field
):
    # type: (...) -> Optional[GraphQLField]
    """Not exactly the same as the executor's definition of get_field_def, in this
    statically evaluated environment we do not always have an Object type,
    and need to handle Interface and Union types."""
    name = field_ast.name.value
    if name == "__schema" and schema.get_query_type() == parent_type:
        return SchemaMetaFieldDef

    elif name == "__type" and schema.get_query_type() == parent_type:
        return TypeMetaFieldDef

    elif name == "__typename" and isinstance(
        parent_type, (GraphQLObjectType, GraphQLInterfaceType, GraphQLUnionType)
    ):
        return TypeNameMetaFieldDef

    elif isinstance(parent_type, (GraphQLObjectType, GraphQLInterfaceType)):
        return parent_type.fields.get(name)
