from ..language.parser import parse_value
from ..pyutils.ordereddict import OrderedDict
from ..type import (
    GraphQLArgument,
    GraphQLBoolean,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLFloat,
    GraphQLID,
    GraphQLInputObjectField,
    GraphQLInputObjectType,
    GraphQLInt,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLString,
    GraphQLUnionType,
    is_input_type,
    is_output_type,
)
from ..type.directives import DirectiveLocation, GraphQLDirective
from ..type.introspection import (
    TypeKind,
    __Directive,
    __DirectiveLocation,
    __EnumValue,
    __Field,
    __InputValue,
    __Schema,
    __Type,
    __TypeKind,
)
from .value_from_ast import value_from_ast


def _false(*_):
    return False


def _none(*_):
    return None


def no_execution(root, info, **args):
    raise Exception("Client Schema cannot be used for execution.")


def build_client_schema(introspection):
    schema_introspection = introspection["__schema"]

    type_introspection_map = {t["name"]: t for t in schema_introspection["types"]}

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

    def get_type(type_ref):
        kind = type_ref.get("kind")

        if kind == TypeKind.LIST:
            item_ref = type_ref.get("ofType")

            if not item_ref:
                raise Exception("Decorated type deeper than introspection query.")

            return GraphQLList(get_type(item_ref))

        elif kind == TypeKind.NON_NULL:
            nullable_ref = type_ref.get("ofType")
            if not nullable_ref:
                raise Exception("Decorated type deeper than introspection query.")

            return GraphQLNonNull(get_type(nullable_ref))

        return get_named_type(type_ref["name"])

    def get_named_type(type_name):
        if type_name in type_def_cache:
            return type_def_cache[type_name]

        type_introspection = type_introspection_map.get(type_name)
        if not type_introspection:
            raise Exception(
                "Invalid or incomplete schema, unknown type: {}. Ensure that a full introspection query "
                "is used in order to build a client schema.".format(type_name)
            )

        type_def = type_def_cache[type_name] = build_type(type_introspection)
        return type_def

    def get_input_type(type_ref):
        input_type = get_type(type_ref)
        assert is_input_type(
            input_type
        ), "Introspection must provide input type for arguments."
        return input_type

    def get_output_type(type_ref):
        output_type = get_type(type_ref)
        assert is_output_type(
            output_type
        ), "Introspection must provide output type for fields."
        return output_type

    def get_object_type(type_ref):
        object_type = get_type(type_ref)
        assert isinstance(
            object_type, GraphQLObjectType
        ), "Introspection must provide object type for possibleTypes."
        return object_type

    def get_interface_type(type_ref):
        interface_type = get_type(type_ref)
        assert isinstance(
            interface_type, GraphQLInterfaceType
        ), "Introspection must provide interface type for interfaces."
        return interface_type

    def build_type(type):
        type_kind = type.get("kind")
        handler = type_builders.get(type_kind)
        if not handler:
            raise Exception(
                "Invalid or incomplete schema, unknown kind: {}. Ensure that a full introspection query "
                "is used in order to build a client schema.".format(type_kind)
            )

        return handler(type)

    def build_scalar_def(scalar_introspection):
        return GraphQLScalarType(
            name=scalar_introspection["name"],
            description=scalar_introspection.get("description"),
            serialize=_none,
            parse_value=_false,
            parse_literal=_false,
        )

    def build_object_def(object_introspection):
        return GraphQLObjectType(
            name=object_introspection["name"],
            description=object_introspection.get("description"),
            interfaces=[
                get_interface_type(i)
                for i in object_introspection.get("interfaces", [])
            ],
            fields=lambda: build_field_def_map(object_introspection),
        )

    def build_interface_def(interface_introspection):
        return GraphQLInterfaceType(
            name=interface_introspection["name"],
            description=interface_introspection.get("description"),
            fields=lambda: build_field_def_map(interface_introspection),
            resolve_type=no_execution,
        )

    def build_union_def(union_introspection):
        return GraphQLUnionType(
            name=union_introspection["name"],
            description=union_introspection.get("description"),
            types=[
                get_object_type(t) for t in union_introspection.get("possibleTypes", [])
            ],
            resolve_type=no_execution,
        )

    def build_enum_def(enum_introspection):
        return GraphQLEnumType(
            name=enum_introspection["name"],
            description=enum_introspection.get("description"),
            values=OrderedDict(
                [
                    (
                        value_introspection["name"],
                        GraphQLEnumValue(
                            description=value_introspection.get("description"),
                            deprecation_reason=value_introspection.get(
                                "deprecationReason"
                            ),
                        ),
                    )
                    for value_introspection in enum_introspection.get("enumValues", [])
                ]
            ),
        )

    def build_input_object_def(input_object_introspection):
        return GraphQLInputObjectType(
            name=input_object_introspection["name"],
            description=input_object_introspection.get("description"),
            fields=lambda: build_input_value_def_map(
                input_object_introspection.get("inputFields"), GraphQLInputObjectField
            ),
        )

    type_builders = {
        TypeKind.SCALAR: build_scalar_def,
        TypeKind.OBJECT: build_object_def,
        TypeKind.INTERFACE: build_interface_def,
        TypeKind.UNION: build_union_def,
        TypeKind.ENUM: build_enum_def,
        TypeKind.INPUT_OBJECT: build_input_object_def,
    }

    def build_field_def_map(type_introspection):
        return OrderedDict(
            [
                (
                    f["name"],
                    GraphQLField(
                        type=get_output_type(f["type"]),
                        description=f.get("description"),
                        resolver=no_execution,
                        deprecation_reason=f.get("deprecationReason"),
                        args=build_input_value_def_map(f.get("args"), GraphQLArgument),
                    ),
                )
                for f in type_introspection.get("fields", [])
            ]
        )

    def build_default_value(f):
        default_value = f.get("defaultValue")
        if default_value is None:
            return None

        return value_from_ast(parse_value(default_value), get_input_type(f["type"]))

    def build_input_value_def_map(input_value_introspection, argument_type):
        return OrderedDict(
            [
                (f["name"], build_input_value(f, argument_type))
                for f in input_value_introspection
            ]
        )

    def build_input_value(input_value_introspection, argument_type):
        input_value = argument_type(
            description=input_value_introspection["description"],
            type=get_input_type(input_value_introspection["type"]),
            default_value=build_default_value(input_value_introspection),
        )
        return input_value

    def build_directive(directive_introspection):
        # Support deprecated `on****` fields for building `locations`, as this
        # is used by GraphiQL which may need to support outdated servers.
        locations = list(directive_introspection.get("locations", []))
        if not locations:
            locations = []
            if directive_introspection.get("onField", False):
                locations += list(DirectiveLocation.FIELD_LOCATIONS)
            if directive_introspection.get("onOperation", False):
                locations += list(DirectiveLocation.OPERATION_LOCATIONS)
            if directive_introspection.get("onFragment", False):
                locations += list(DirectiveLocation.FRAGMENT_LOCATIONS)

        return GraphQLDirective(
            name=directive_introspection["name"],
            description=directive_introspection.get("description"),
            # TODO: {} ?
            args=build_input_value_def_map(
                directive_introspection.get("args", {}), GraphQLArgument
            ),
            locations=locations,
        )

    # Iterate through all types, getting the type definition for each, ensuring
    # that any type not directly referenced by a field will get created.
    types = [
        get_named_type(type_introspection_name)
        for type_introspection_name in type_introspection_map.keys()
    ]

    query_type = get_object_type(schema_introspection["queryType"])
    mutation_type = (
        get_object_type(schema_introspection["mutationType"])
        if schema_introspection.get("mutationType")
        else None
    )
    subscription_type = (
        get_object_type(schema_introspection["subscriptionType"])
        if schema_introspection.get("subscriptionType")
        else None
    )

    directives = (
        [build_directive(d) for d in schema_introspection["directives"]]
        if schema_introspection["directives"]
        else []
    )

    return GraphQLSchema(
        query=query_type,
        mutation=mutation_type,
        subscription=subscription_type,
        directives=directives,
        types=types,
    )
