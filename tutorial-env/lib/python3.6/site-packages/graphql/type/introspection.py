from collections import OrderedDict, namedtuple

from ..language.printer import print_ast
from ..utils.ast_from_value import ast_from_value
from .definition import (
    GraphQLArgument,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLUnionType,
)
from .directives import DirectiveLocation
from .scalars import GraphQLBoolean, GraphQLString

# Necessary for static type checking
if False:  # flake8: noqa
    from ..execution.base import ResolveInfo
    from .definition import GraphQLInputObjectField
    from typing import Union, List, Optional, Any, Dict

InputField = namedtuple("InputField", ["name", "description", "type", "default_value"])
Field = namedtuple(
    "Field", ["name", "type", "description", "args", "deprecation_reason"]
)


def input_fields_to_list(input_fields):
    # type: (Dict[str, GraphQLInputObjectField]) -> List[InputField]
    fields = []
    for field_name, field in input_fields.items():
        fields.append(
            InputField(
                name=field_name,
                description=field.description,
                type=field.type,
                default_value=field.default_value,
            )
        )
    return fields


__Schema = GraphQLObjectType(
    "__Schema",
    description="A GraphQL Schema defines the capabilities of a GraphQL server. It "
    "exposes all available types and directives on the server, as well as "
    "the entry points for query, mutation and subscription operations.",
    fields=lambda: OrderedDict(
        [
            (
                "types",
                GraphQLField(
                    description="A list of all types supported by this server.",
                    type=GraphQLNonNull(
                        GraphQLList(GraphQLNonNull(__Type))  # type: ignore
                    ),
                    resolver=lambda schema, *_: schema.get_type_map().values(),
                ),
            ),
            (
                "queryType",
                GraphQLField(
                    description="The type that query operations will be rooted at.",
                    type=GraphQLNonNull(__Type),  # type: ignore
                    resolver=lambda schema, *_: schema.get_query_type(),
                ),
            ),
            (
                "mutationType",
                GraphQLField(
                    description="If this server supports mutation, the type that "
                    "mutation operations will be rooted at.",
                    type=__Type,  # type: ignore
                    resolver=lambda schema, *_: schema.get_mutation_type(),
                ),
            ),
            (
                "subscriptionType",
                GraphQLField(
                    description="If this server support subscription, the type "
                    "that subscription operations will be rooted at.",
                    type=__Type,  # type: ignore
                    resolver=lambda schema, *_: schema.get_subscription_type(),
                ),
            ),
            (
                "directives",
                GraphQLField(
                    description="A list of all directives supported by this server.",
                    type=GraphQLNonNull(
                        GraphQLList(GraphQLNonNull(__Directive))  # type: ignore
                    ),
                    resolver=lambda schema, *_: schema.get_directives(),
                ),
            ),
        ]
    ),
)

_on_operation_locations = set(DirectiveLocation.OPERATION_LOCATIONS)
_on_fragment_locations = set(DirectiveLocation.FRAGMENT_LOCATIONS)
_on_field_locations = set(DirectiveLocation.FIELD_LOCATIONS)

__Directive = GraphQLObjectType(
    "__Directive",
    description="A Directive provides a way to describe alternate runtime execution and "
    "type validation behavior in a GraphQL document."
    "\n\nIn some cases, you need to provide options to alter GraphQL's "
    "execution behavior in ways field arguments will not suffice, such as "
    "conditionally including or skipping a field. Directives provide this by "
    "describing additional information to the executor.",
    fields=lambda: OrderedDict(
        [
            ("name", GraphQLField(GraphQLNonNull(GraphQLString))),
            ("description", GraphQLField(GraphQLString)),
            (
                "locations",
                GraphQLField(
                    type=GraphQLNonNull(
                        GraphQLList(GraphQLNonNull(__DirectiveLocation))  # type: ignore
                    )
                ),
            ),
            (
                "args",
                GraphQLField(
                    type=GraphQLNonNull(
                        GraphQLList(GraphQLNonNull(__InputValue))  # type: ignore
                    ),
                    resolver=lambda directive, *args: input_fields_to_list(
                        directive.args
                    ),
                ),
            ),
            (
                "onOperation",
                GraphQLField(
                    type=GraphQLNonNull(GraphQLBoolean),
                    deprecation_reason="Use `locations`.",
                    resolver=lambda directive, *args: set(directive.locations)
                    & _on_operation_locations,
                ),
            ),
            (
                "onFragment",
                GraphQLField(
                    type=GraphQLNonNull(GraphQLBoolean),
                    deprecation_reason="Use `locations`.",
                    resolver=lambda directive, *args: set(directive.locations)
                    & _on_fragment_locations,
                ),
            ),
            (
                "onField",
                GraphQLField(
                    type=GraphQLNonNull(GraphQLBoolean),
                    deprecation_reason="Use `locations`.",
                    resolver=lambda directive, *args: set(directive.locations)
                    & _on_field_locations,
                ),
            ),
        ]
    ),
)

__DirectiveLocation = GraphQLEnumType(
    "__DirectiveLocation",
    description=(
        "A Directive can be adjacent to many parts of the GraphQL language, a "
        + "__DirectiveLocation describes one such possible adjacencies."
    ),
    values=OrderedDict(
        [
            (
                "QUERY",
                GraphQLEnumValue(
                    DirectiveLocation.QUERY,
                    description="Location adjacent to a query operation.",
                ),
            ),
            (
                "MUTATION",
                GraphQLEnumValue(
                    DirectiveLocation.MUTATION,
                    description="Location adjacent to a mutation operation.",
                ),
            ),
            (
                "SUBSCRIPTION",
                GraphQLEnumValue(
                    DirectiveLocation.SUBSCRIPTION,
                    description="Location adjacent to a subscription operation.",
                ),
            ),
            (
                "FIELD",
                GraphQLEnumValue(
                    DirectiveLocation.FIELD, description="Location adjacent to a field."
                ),
            ),
            (
                "FRAGMENT_DEFINITION",
                GraphQLEnumValue(
                    DirectiveLocation.FRAGMENT_DEFINITION,
                    description="Location adjacent to a fragment definition.",
                ),
            ),
            (
                "FRAGMENT_SPREAD",
                GraphQLEnumValue(
                    DirectiveLocation.FRAGMENT_SPREAD,
                    description="Location adjacent to a fragment spread.",
                ),
            ),
            (
                "INLINE_FRAGMENT",
                GraphQLEnumValue(
                    DirectiveLocation.INLINE_FRAGMENT,
                    description="Location adjacent to an inline fragment.",
                ),
            ),
            (
                "SCHEMA",
                GraphQLEnumValue(
                    DirectiveLocation.SCHEMA,
                    description="Location adjacent to a schema definition.",
                ),
            ),
            (
                "SCALAR",
                GraphQLEnumValue(
                    DirectiveLocation.SCALAR,
                    description="Location adjacent to a scalar definition.",
                ),
            ),
            (
                "OBJECT",
                GraphQLEnumValue(
                    DirectiveLocation.OBJECT,
                    description="Location adjacent to an object definition.",
                ),
            ),
            (
                "FIELD_DEFINITION",
                GraphQLEnumValue(
                    DirectiveLocation.FIELD_DEFINITION,
                    description="Location adjacent to a field definition.",
                ),
            ),
            (
                "ARGUMENT_DEFINITION",
                GraphQLEnumValue(
                    DirectiveLocation.ARGUMENT_DEFINITION,
                    description="Location adjacent to an argument definition.",
                ),
            ),
            (
                "INTERFACE",
                GraphQLEnumValue(
                    DirectiveLocation.INTERFACE,
                    description="Location adjacent to an interface definition.",
                ),
            ),
            (
                "UNION",
                GraphQLEnumValue(
                    DirectiveLocation.UNION,
                    description="Location adjacent to a union definition.",
                ),
            ),
            (
                "ENUM",
                GraphQLEnumValue(
                    DirectiveLocation.ENUM,
                    description="Location adjacent to an enum definition.",
                ),
            ),
            (
                "ENUM_VALUE",
                GraphQLEnumValue(
                    DirectiveLocation.ENUM_VALUE,
                    description="Location adjacent to an enum value definition.",
                ),
            ),
            (
                "INPUT_OBJECT",
                GraphQLEnumValue(
                    DirectiveLocation.INPUT_OBJECT,
                    description="Location adjacent to an input object definition.",
                ),
            ),
            (
                "INPUT_FIELD_DEFINITION",
                GraphQLEnumValue(
                    DirectiveLocation.INPUT_FIELD_DEFINITION,
                    description="Location adjacent to an input object field definition.",
                ),
            ),
        ]
    ),
)


class TypeKind(object):
    SCALAR = "SCALAR"
    OBJECT = "OBJECT"
    INTERFACE = "INTERFACE"
    UNION = "UNION"
    ENUM = "ENUM"
    INPUT_OBJECT = "INPUT_OBJECT"
    LIST = "LIST"
    NON_NULL = "NON_NULL"


class TypeFieldResolvers(object):
    _kinds = (
        (GraphQLScalarType, TypeKind.SCALAR),
        (GraphQLObjectType, TypeKind.OBJECT),
        (GraphQLInterfaceType, TypeKind.INTERFACE),
        (GraphQLUnionType, TypeKind.UNION),
        (GraphQLEnumType, TypeKind.ENUM),
        (GraphQLInputObjectType, TypeKind.INPUT_OBJECT),
        (GraphQLList, TypeKind.LIST),
        (GraphQLNonNull, TypeKind.NON_NULL),
    )

    @classmethod
    def kind(
        cls,
        type,  # type: Union[GraphQLInterfaceType, GraphQLUnionType]
        *_  # type: ResolveInfo
    ):
        # type: (...) -> str
        for klass, kind in cls._kinds:
            if isinstance(type, klass):
                return kind

        raise Exception("Unknown kind of type: {}".format(type))

    @staticmethod
    def fields(
        type,  # type: Union[GraphQLInterfaceType, GraphQLUnionType]
        info,  # type: ResolveInfo
        includeDeprecated=None,  # type: bool
    ):
        # type: (...) -> Optional[List[Field]]
        if isinstance(type, (GraphQLObjectType, GraphQLInterfaceType)):
            fields = []
            include_deprecated = includeDeprecated
            for field_name, field in type.fields.items():
                if field.deprecation_reason and not include_deprecated:
                    continue
                fields.append(
                    Field(
                        name=field_name,
                        description=field.description,
                        type=field.type,
                        args=field.args,
                        deprecation_reason=field.deprecation_reason,
                    )
                )
            return fields
        return None

    @staticmethod
    def interfaces(type, info):
        # type: (Optional[GraphQLObjectType], ResolveInfo) -> Optional[List[GraphQLInterfaceType]]
        if isinstance(type, GraphQLObjectType):
            return type.interfaces
        return None

    @staticmethod
    def possible_types(
        type,  # type: Union[GraphQLInterfaceType, GraphQLUnionType]
        info,  # type: ResolveInfo
        **args  # type: Any
    ):
        # type: (...) -> List[GraphQLObjectType]
        if isinstance(type, (GraphQLInterfaceType, GraphQLUnionType)):
            return info.schema.get_possible_types(type)

    @staticmethod
    def enum_values(
        type,  # type: GraphQLEnumType
        info,  # type: ResolveInfo
        includeDeprecated=None,  # type: bool
    ):
        # type: (...) -> Optional[List[GraphQLEnumValue]]
        if isinstance(type, GraphQLEnumType):
            values = type.values
            if not includeDeprecated:
                values = [v for v in values if not v.deprecation_reason]

            return values
        return None

    @staticmethod
    def input_fields(type, info):
        # type: (GraphQLInputObjectType, ResolveInfo) -> List[InputField]
        if isinstance(type, GraphQLInputObjectType):
            return input_fields_to_list(type.fields)


__Type = GraphQLObjectType(
    "__Type",
    description="The fundamental unit of any GraphQL Schema is the type. There are "
    "many kinds of types in GraphQL as represented by the `__TypeKind` enum."
    "\n\nDepending on the kind of a type, certain fields describe "
    "information about that type. Scalar types provide no information "
    "beyond a name and description, while Enum types provide their values. "
    "Object and Interface types provide the fields they describe. Abstract "
    "types, Union and Interface, provide the Object types possible "
    "at runtime. List and NonNull types compose other types.",
    fields=lambda: OrderedDict(
        [
            (
                "kind",
                GraphQLField(
                    type=GraphQLNonNull(__TypeKind),  # type: ignore
                    resolver=TypeFieldResolvers.kind,
                ),
            ),
            ("name", GraphQLField(GraphQLString)),
            ("description", GraphQLField(GraphQLString)),
            (
                "fields",
                GraphQLField(
                    type=GraphQLList(GraphQLNonNull(__Field)),  # type: ignore
                    args={
                        "includeDeprecated": GraphQLArgument(
                            GraphQLBoolean, default_value=False
                        )
                    },
                    resolver=TypeFieldResolvers.fields,
                ),
            ),
            (
                "interfaces",
                GraphQLField(
                    type=GraphQLList(GraphQLNonNull(__Type)),  # type: ignore
                    resolver=TypeFieldResolvers.interfaces,
                ),
            ),
            (
                "possibleTypes",
                GraphQLField(
                    type=GraphQLList(GraphQLNonNull(__Type)),  # type: ignore
                    resolver=TypeFieldResolvers.possible_types,
                ),
            ),
            (
                "enumValues",
                GraphQLField(
                    type=GraphQLList(GraphQLNonNull(__EnumValue)),  # type: ignore
                    args={
                        "includeDeprecated": GraphQLArgument(
                            GraphQLBoolean, default_value=False
                        )
                    },
                    resolver=TypeFieldResolvers.enum_values,
                ),
            ),
            (
                "inputFields",
                GraphQLField(
                    type=GraphQLList(GraphQLNonNull(__InputValue)),  # type: ignore
                    resolver=TypeFieldResolvers.input_fields,
                ),
            ),
            (
                "ofType",
                GraphQLField(
                    type=__Type,  # type: ignore
                    resolver=lambda type, *_: getattr(type, "of_type", None),
                ),
            ),
        ]
    ),
)

__Field = GraphQLObjectType(
    "__Field",
    description="Object and Interface types are described by a list of Fields, each of "
    "which has a name, potentially a list of arguments, and a return type.",
    fields=lambda: OrderedDict(
        [
            ("name", GraphQLField(GraphQLNonNull(GraphQLString))),
            ("description", GraphQLField(GraphQLString)),
            (
                "args",
                GraphQLField(
                    type=GraphQLNonNull(
                        GraphQLList(GraphQLNonNull(__InputValue))  # type: ignore
                    ),
                    resolver=lambda field, *_: input_fields_to_list(field.args),
                ),
            ),
            ("type", GraphQLField(GraphQLNonNull(__Type))),  # type: ignore
            (
                "isDeprecated",
                GraphQLField(
                    type=GraphQLNonNull(GraphQLBoolean),
                    resolver=lambda field, *_: bool(field.deprecation_reason),
                ),
            ),
            (
                "deprecationReason",
                GraphQLField(
                    type=GraphQLString,
                    resolver=lambda field, *_: field.deprecation_reason,
                ),
            ),
        ]
    ),
)

__InputValue = GraphQLObjectType(
    "__InputValue",
    description="Arguments provided to Fields or Directives and the input fields of an "
    "InputObject are represented as Input Values which describe their type "
    "and optionally a default value.",
    fields=lambda: OrderedDict(
        [
            ("name", GraphQLField(GraphQLNonNull(GraphQLString))),
            ("description", GraphQLField(GraphQLString)),
            ("type", GraphQLField(GraphQLNonNull(__Type))),
            (
                "defaultValue",
                GraphQLField(
                    type=GraphQLString,
                    resolver=lambda input_val, *_: None
                    if input_val.default_value is None
                    else print_ast(ast_from_value(input_val.default_value, input_val)),
                ),
            ),
        ]
    ),
)

__EnumValue = GraphQLObjectType(
    "__EnumValue",
    description="One possible value for a given Enum. Enum values are unique values, not "
    "a placeholder for a string or numeric value. However an Enum value is "
    "returned in a JSON response as a string.",
    fields=lambda: OrderedDict(
        [
            ("name", GraphQLField(GraphQLNonNull(GraphQLString))),
            ("description", GraphQLField(GraphQLString)),
            (
                "isDeprecated",
                GraphQLField(
                    type=GraphQLNonNull(GraphQLBoolean),
                    resolver=lambda field, *_: bool(field.deprecation_reason),
                ),
            ),
            (
                "deprecationReason",
                GraphQLField(
                    type=GraphQLString,
                    resolver=lambda enum_value, *_: enum_value.deprecation_reason,
                ),
            ),
        ]
    ),
)

__TypeKind = GraphQLEnumType(
    "__TypeKind",
    description="An enum describing what kind of type a given `__Type` is",
    values=OrderedDict(
        [
            (
                "SCALAR",
                GraphQLEnumValue(
                    TypeKind.SCALAR, description="Indicates this type is a scalar."
                ),
            ),
            (
                "OBJECT",
                GraphQLEnumValue(
                    TypeKind.OBJECT,
                    description="Indicates this type is an object. "
                    "`fields` and `interfaces` are valid fields.",
                ),
            ),
            (
                "INTERFACE",
                GraphQLEnumValue(
                    TypeKind.INTERFACE,
                    description="Indicates this type is an interface. "
                    "`fields` and `possibleTypes` are valid fields.",
                ),
            ),
            (
                "UNION",
                GraphQLEnumValue(
                    TypeKind.UNION,
                    description="Indicates this type is a union. "
                    "`possibleTypes` is a valid field.",
                ),
            ),
            (
                "ENUM",
                GraphQLEnumValue(
                    TypeKind.ENUM,
                    description="Indicates this type is an enum. "
                    "`enumValues` is a valid field.",
                ),
            ),
            (
                "INPUT_OBJECT",
                GraphQLEnumValue(
                    TypeKind.INPUT_OBJECT,
                    description="Indicates this type is an input object. "
                    "`inputFields` is a valid field.",
                ),
            ),
            (
                "LIST",
                GraphQLEnumValue(
                    TypeKind.LIST,
                    description="Indicates this type is a list. "
                    "`ofType` is a valid field.",
                ),
            ),
            (
                "NON_NULL",
                GraphQLEnumValue(
                    TypeKind.NON_NULL,
                    description="Indicates this type is a non-null. "
                    "`ofType` is a valid field.",
                ),
            ),
        ]
    ),
)

IntrospectionSchema = __Schema

SchemaMetaFieldDef = GraphQLField(
    # name='__schema',
    type=GraphQLNonNull(__Schema),
    description="Access the current type schema of this server.",
    resolver=lambda source, info, **args: info.schema,
    args={},
)

TypeMetaFieldDef = GraphQLField(
    type=__Type,
    # name='__type',
    description="Request the type information of a single type.",
    args={"name": GraphQLArgument(GraphQLNonNull(GraphQLString))},
    resolver=lambda source, info, **args: info.schema.get_type(args["name"]),
)

TypeNameMetaFieldDef = GraphQLField(
    type=GraphQLNonNull(GraphQLString),
    # name='__typename',
    description="The name of the current Object type at runtime.",
    resolver=lambda source, info, **args: info.parent_type.name,
    args={},
)
