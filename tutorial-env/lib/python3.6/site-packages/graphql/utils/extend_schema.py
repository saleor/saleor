from collections import defaultdict

from ..error import GraphQLError
from ..language import ast
from ..pyutils.ordereddict import OrderedDict
from ..type.definition import (
    GraphQLArgument,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLInputObjectField,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLUnionType,
)
from ..type.introspection import (
    __Directive,
    __DirectiveLocation,
    __EnumValue,
    __Field,
    __InputValue,
    __Schema,
    __Type,
    __TypeKind,
)
from ..type.scalars import (
    GraphQLBoolean,
    GraphQLFloat,
    GraphQLID,
    GraphQLInt,
    GraphQLString,
)
from ..type.schema import GraphQLSchema
from .value_from_ast import value_from_ast


def extend_schema(schema, documentAST=None):
    """Produces a new schema given an existing schema and a document which may
    contain GraphQL type extensions and definitions. The original schema will
    remain unaltered.

    Because a schema represents a graph of references, a schema cannot be
    extended without effectively making an entire copy. We do not know until it's
    too late if subgraphs remain unchanged.

    This algorithm copies the provided schema, applying extensions while
    producing the copy. The original schema remains unaltered."""

    assert isinstance(schema, GraphQLSchema), "Must provide valid GraphQLSchema"
    assert documentAST and isinstance(
        documentAST, ast.Document
    ), "Must provide valid Document AST"

    # Collect the type definitions and extensions found in the document.
    type_definition_map = {}
    type_extensions_map = defaultdict(list)

    for _def in documentAST.definitions:
        if isinstance(
            _def,
            (
                ast.ObjectTypeDefinition,
                ast.InterfaceTypeDefinition,
                ast.EnumTypeDefinition,
                ast.UnionTypeDefinition,
                ast.ScalarTypeDefinition,
                ast.InputObjectTypeDefinition,
            ),
        ):
            # Sanity check that none of the defined types conflict with the
            # schema's existing types.
            type_name = _def.name.value
            if schema.get_type(type_name):
                raise GraphQLError(
                    (
                        'Type "{}" already exists in the schema. It cannot also '
                        + "be defined in this type definition."
                    ).format(type_name),
                    [_def],
                )

            type_definition_map[type_name] = _def
        elif isinstance(_def, ast.TypeExtensionDefinition):
            # Sanity check that this type extension exists within the
            # schema's existing types.
            extended_type_name = _def.definition.name.value
            existing_type = schema.get_type(extended_type_name)
            if not existing_type:
                raise GraphQLError(
                    (
                        'Cannot extend type "{}" because it does not '
                        + "exist in the existing schema."
                    ).format(extended_type_name),
                    [_def.definition],
                )
            if not isinstance(existing_type, GraphQLObjectType):
                raise GraphQLError(
                    'Cannot extend non-object type "{}".'.format(extended_type_name),
                    [_def.definition],
                )

            type_extensions_map[extended_type_name].append(_def)

    # Below are functions used for producing this schema that have closed over
    # this scope and have access to the schema, cache, and newly defined types.

    def get_type_from_def(type_def):
        type = _get_named_type(type_def.name)
        assert type, "Invalid schema"
        return type

    def get_type_from_AST(astNode):
        type = _get_named_type(astNode.name.value)
        if not type:
            raise GraphQLError(
                (
                    'Unknown type: "{}". Ensure that this type exists '
                    + "either in the original schema, or is added in a type definition."
                ).format(astNode.name.value),
                [astNode],
            )
        return type

    # Given a name, returns a type from either the existing schema or an
    # added type.
    def _get_named_type(typeName):
        cached_type_def = type_def_cache.get(typeName)
        if cached_type_def:
            return cached_type_def

        existing_type = schema.get_type(typeName)
        if existing_type:
            type_def = extend_type(existing_type)
            type_def_cache[typeName] = type_def
            return type_def

        type_ast = type_definition_map.get(typeName)
        if type_ast:
            type_def = build_type(type_ast)
            type_def_cache[typeName] = type_def
            return type_def

    # Given a type's introspection result, construct the correct
    # GraphQLType instance.
    def extend_type(type):
        if isinstance(type, GraphQLObjectType):
            return extend_object_type(type)
        if isinstance(type, GraphQLInterfaceType):
            return extend_interface_type(type)
        if isinstance(type, GraphQLUnionType):
            return extend_union_type(type)
        return type

    def extend_object_type(type):
        return GraphQLObjectType(
            name=type.name,
            description=type.description,
            interfaces=lambda: extend_implemented_interfaces(type),
            fields=lambda: extend_field_map(type),
        )

    def extend_interface_type(type):
        return GraphQLInterfaceType(
            name=type.name,
            description=type.description,
            fields=lambda: extend_field_map(type),
            resolve_type=cannot_execute_client_schema,
        )

    def extend_union_type(type):
        return GraphQLUnionType(
            name=type.name,
            description=type.description,
            types=list(map(get_type_from_def, type.types)),
            resolve_type=cannot_execute_client_schema,
        )

    def extend_implemented_interfaces(type):
        interfaces = list(map(get_type_from_def, type.interfaces))

        # If there are any extensions to the interfaces, apply those here.
        extensions = type_extensions_map[type.name]
        for extension in extensions:
            for namedType in extension.definition.interfaces:
                interface_name = namedType.name.value
                if any([_def.name == interface_name for _def in interfaces]):
                    raise GraphQLError(
                        (
                            'Type "{}" already implements "{}". '
                            + "It cannot also be implemented in this type extension."
                        ).format(type.name, interface_name),
                        [namedType],
                    )
                interfaces.append(get_type_from_AST(namedType))

        return interfaces

    def extend_field_map(type):
        new_field_map = OrderedDict()
        old_field_map = type.fields
        for field_name, field in old_field_map.items():
            new_field_map[field_name] = GraphQLField(
                extend_field_type(field.type),
                description=field.description,
                deprecation_reason=field.deprecation_reason,
                args=field.args,
                resolver=cannot_execute_client_schema,
            )

        # If there are any extensions to the fields, apply those here.
        extensions = type_extensions_map[type.name]
        for extension in extensions:
            for field in extension.definition.fields:
                field_name = field.name.value
                if field_name in old_field_map:
                    raise GraphQLError(
                        (
                            'Field "{}.{}" already exists in the '
                            + "schema. It cannot also be defined in this type extension."
                        ).format(type.name, field_name),
                        [field],
                    )
                new_field_map[field_name] = GraphQLField(
                    build_field_type(field.type),
                    args=build_input_values(field.arguments),
                    resolver=cannot_execute_client_schema,
                )

        return new_field_map

    def extend_field_type(type):
        if isinstance(type, GraphQLList):
            return GraphQLList(extend_field_type(type.of_type))
        if isinstance(type, GraphQLNonNull):
            return GraphQLNonNull(extend_field_type(type.of_type))
        return get_type_from_def(type)

    def build_type(type_ast):
        _type_build = {
            ast.ObjectTypeDefinition: build_object_type,
            ast.InterfaceTypeDefinition: build_interface_type,
            ast.UnionTypeDefinition: build_union_type,
            ast.ScalarTypeDefinition: build_scalar_type,
            ast.EnumTypeDefinition: build_enum_type,
            ast.InputObjectTypeDefinition: build_input_object_type,
        }
        func = _type_build.get(type(type_ast))
        if func:
            return func(type_ast)

    def build_object_type(type_ast):
        return GraphQLObjectType(
            type_ast.name.value,
            interfaces=lambda: build_implemented_interfaces(type_ast),
            fields=lambda: build_field_map(type_ast),
        )

    def build_interface_type(type_ast):
        return GraphQLInterfaceType(
            type_ast.name.value,
            fields=lambda: build_field_map(type_ast),
            resolve_type=cannot_execute_client_schema,
        )

    def build_union_type(type_ast):
        return GraphQLUnionType(
            type_ast.name.value,
            types=list(map(get_type_from_AST, type_ast.types)),
            resolve_type=cannot_execute_client_schema,
        )

    def build_scalar_type(type_ast):
        return GraphQLScalarType(
            type_ast.name.value,
            serialize=lambda *args, **kwargs: None,
            # Note: validation calls the parse functions to determine if a
            # literal value is correct. Returning null would cause use of custom
            # scalars to always fail validation. Returning false causes them to
            # always pass validation.
            parse_value=lambda *args, **kwargs: False,
            parse_literal=lambda *args, **kwargs: False,
        )

    def build_enum_type(type_ast):
        return GraphQLEnumType(
            type_ast.name.value,
            values={v.name.value: GraphQLEnumValue() for v in type_ast.values},
        )

    def build_input_object_type(type_ast):
        return GraphQLInputObjectType(
            type_ast.name.value,
            fields=lambda: build_input_values(type_ast.fields, GraphQLInputObjectField),
        )

    def build_implemented_interfaces(type_ast):
        return list(map(get_type_from_AST, type_ast.interfaces))

    def build_field_map(type_ast):
        return {
            field.name.value: GraphQLField(
                build_field_type(field.type),
                args=build_input_values(field.arguments),
                resolver=cannot_execute_client_schema,
            )
            for field in type_ast.fields
        }

    def build_input_values(values, input_type=GraphQLArgument):
        input_values = OrderedDict()
        for value in values:
            type = build_field_type(value.type)
            input_values[value.name.value] = input_type(
                type, default_value=value_from_ast(value.default_value, type)
            )
        return input_values

    def build_field_type(type_ast):
        if isinstance(type_ast, ast.ListType):
            return GraphQLList(build_field_type(type_ast.type))
        if isinstance(type_ast, ast.NonNullType):
            return GraphQLNonNull(build_field_type(type_ast.type))
        return get_type_from_AST(type_ast)

    # If this document contains no new types, then return the same unmodified
    # GraphQLSchema instance.
    if not type_extensions_map and not type_definition_map:
        return schema

    # A cache to use to store the actual GraphQLType definition objects by name.
    # Initialize to the GraphQL built in scalars and introspection types. All
    # functions below are inline so that this type def cache is within the scope
    # of the closure.

    type_def_cache = {
        "String": GraphQLString,
        "Int": GraphQLInt,
        "Float": GraphQLFloat,
        "Boolean": GraphQLBoolean,
        "ID": GraphQLID,
        "__Schema": __Schema,
        "__Directive": __Directive,
        "__DirectiveLocation": __DirectiveLocation,
        "__Type": __Type,
        "__Field": __Field,
        "__InputValue": __InputValue,
        "__EnumValue": __EnumValue,
        "__TypeKind": __TypeKind,
    }

    # Get the root Query, Mutation, and Subscription types.
    query_type = get_type_from_def(schema.get_query_type())

    existing_mutation_type = schema.get_mutation_type()
    mutationType = (
        existing_mutation_type and get_type_from_def(existing_mutation_type) or None
    )

    existing_subscription_type = schema.get_subscription_type()
    subscription_type = (
        existing_subscription_type
        and get_type_from_def(existing_subscription_type)
        or None
    )

    # Iterate through all types, getting the type definition for each, ensuring
    # that any type not directly referenced by a field will get created.
    types = [get_type_from_def(_def) for _def in schema.get_type_map().values()]

    # Do the same with new types, appending to the list of defined types.
    types += [get_type_from_AST(_def) for _def in type_definition_map.values()]

    # Then produce and return a Schema with these types.
    return GraphQLSchema(
        query=query_type,
        mutation=mutationType,
        subscription=subscription_type,
        # Copy directives.
        directives=schema.get_directives(),
        types=types,
    )


def cannot_execute_client_schema(*args, **kwargs):
    raise Exception("Client Schema cannot be used for execution.")
