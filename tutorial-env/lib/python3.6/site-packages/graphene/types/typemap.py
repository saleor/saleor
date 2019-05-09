import inspect
from collections import OrderedDict
from functools import partial

from graphql import (
    GraphQLArgument,
    GraphQLBoolean,
    GraphQLField,
    GraphQLFloat,
    GraphQLID,
    GraphQLInputObjectField,
    GraphQLInt,
    GraphQLList,
    GraphQLNonNull,
    GraphQLString,
)
from graphql.execution.executor import get_default_resolve_type_fn
from graphql.type import GraphQLEnumValue
from graphql.type.typemap import GraphQLTypeMap

from ..utils.get_unbound_function import get_unbound_function
from ..utils.str_converters import to_camel_case
from .definitions import (
    GrapheneEnumType,
    GrapheneGraphQLType,
    GrapheneInputObjectType,
    GrapheneInterfaceType,
    GrapheneObjectType,
    GrapheneScalarType,
    GrapheneUnionType,
)
from .dynamic import Dynamic
from .enum import Enum
from .field import Field
from .inputobjecttype import InputObjectType
from .interface import Interface
from .objecttype import ObjectType
from .resolver import get_default_resolver
from .scalars import ID, Boolean, Float, Int, Scalar, String
from .structures import List, NonNull
from .union import Union
from .utils import get_field_as


def is_graphene_type(_type):
    if isinstance(_type, (List, NonNull)):
        return True
    if inspect.isclass(_type) and issubclass(
        _type, (ObjectType, InputObjectType, Scalar, Interface, Union, Enum)
    ):
        return True


def resolve_type(resolve_type_func, map, type_name, root, info):
    _type = resolve_type_func(root, info)

    if not _type:
        return_type = map[type_name]
        return get_default_resolve_type_fn(root, info, return_type)

    if inspect.isclass(_type) and issubclass(_type, ObjectType):
        graphql_type = map.get(_type._meta.name)
        assert graphql_type, "Can't find type {} in schema".format(_type._meta.name)
        assert graphql_type.graphene_type == _type, (
            "The type {} does not match with the associated graphene type {}."
        ).format(_type, graphql_type.graphene_type)
        return graphql_type

    return _type


def is_type_of_from_possible_types(possible_types, root, info):
    return isinstance(root, possible_types)


class TypeMap(GraphQLTypeMap):
    def __init__(self, types, auto_camelcase=True, schema=None):
        self.auto_camelcase = auto_camelcase
        self.schema = schema
        super(TypeMap, self).__init__(types)

    def reducer(self, map, type):
        if not type:
            return map
        if inspect.isfunction(type):
            type = type()
        if is_graphene_type(type):
            return self.graphene_reducer(map, type)
        return GraphQLTypeMap.reducer(map, type)

    def graphene_reducer(self, map, type):
        if isinstance(type, (List, NonNull)):
            return self.reducer(map, type.of_type)
        if type._meta.name in map:
            _type = map[type._meta.name]
            if isinstance(_type, GrapheneGraphQLType):
                assert _type.graphene_type == type, (
                    "Found different types with the same name in the schema: {}, {}."
                ).format(_type.graphene_type, type)
            return map

        if issubclass(type, ObjectType):
            internal_type = self.construct_objecttype(map, type)
        elif issubclass(type, InputObjectType):
            internal_type = self.construct_inputobjecttype(map, type)
        elif issubclass(type, Interface):
            internal_type = self.construct_interface(map, type)
        elif issubclass(type, Scalar):
            internal_type = self.construct_scalar(map, type)
        elif issubclass(type, Enum):
            internal_type = self.construct_enum(map, type)
        elif issubclass(type, Union):
            internal_type = self.construct_union(map, type)
        else:
            raise Exception("Expected Graphene type, but received: {}.".format(type))

        return GraphQLTypeMap.reducer(map, internal_type)

    def construct_scalar(self, map, type):
        # We have a mapping to the original GraphQL types
        # so there are no collisions.
        _scalars = {
            String: GraphQLString,
            Int: GraphQLInt,
            Float: GraphQLFloat,
            Boolean: GraphQLBoolean,
            ID: GraphQLID,
        }
        if type in _scalars:
            return _scalars[type]

        return GrapheneScalarType(
            graphene_type=type,
            name=type._meta.name,
            description=type._meta.description,
            serialize=getattr(type, "serialize", None),
            parse_value=getattr(type, "parse_value", None),
            parse_literal=getattr(type, "parse_literal", None),
        )

    def construct_enum(self, map, type):
        values = OrderedDict()
        for name, value in type._meta.enum.__members__.items():
            description = getattr(value, "description", None)
            deprecation_reason = getattr(value, "deprecation_reason", None)
            if not description and callable(type._meta.description):
                description = type._meta.description(value)

            if not deprecation_reason and callable(type._meta.deprecation_reason):
                deprecation_reason = type._meta.deprecation_reason(value)

            values[name] = GraphQLEnumValue(
                name=name,
                value=value.value,
                description=description,
                deprecation_reason=deprecation_reason,
            )

        type_description = (
            type._meta.description(None)
            if callable(type._meta.description)
            else type._meta.description
        )

        return GrapheneEnumType(
            graphene_type=type,
            values=values,
            name=type._meta.name,
            description=type_description,
        )

    def construct_objecttype(self, map, type):
        if type._meta.name in map:
            _type = map[type._meta.name]
            if isinstance(_type, GrapheneGraphQLType):
                assert _type.graphene_type == type, (
                    "Found different types with the same name in the schema: {}, {}."
                ).format(_type.graphene_type, type)
            return _type

        def interfaces():
            interfaces = []
            for interface in type._meta.interfaces:
                self.graphene_reducer(map, interface)
                internal_type = map[interface._meta.name]
                assert internal_type.graphene_type == interface
                interfaces.append(internal_type)
            return interfaces

        if type._meta.possible_types:
            is_type_of = partial(
                is_type_of_from_possible_types, type._meta.possible_types
            )
        else:
            is_type_of = type.is_type_of

        return GrapheneObjectType(
            graphene_type=type,
            name=type._meta.name,
            description=type._meta.description,
            fields=partial(self.construct_fields_for_type, map, type),
            is_type_of=is_type_of,
            interfaces=interfaces,
        )

    def construct_interface(self, map, type):
        if type._meta.name in map:
            _type = map[type._meta.name]
            if isinstance(_type, GrapheneInterfaceType):
                assert _type.graphene_type == type, (
                    "Found different types with the same name in the schema: {}, {}."
                ).format(_type.graphene_type, type)
            return _type

        _resolve_type = None
        if type.resolve_type:
            _resolve_type = partial(
                resolve_type, type.resolve_type, map, type._meta.name
            )
        return GrapheneInterfaceType(
            graphene_type=type,
            name=type._meta.name,
            description=type._meta.description,
            fields=partial(self.construct_fields_for_type, map, type),
            resolve_type=_resolve_type,
        )

    def construct_inputobjecttype(self, map, type):
        return GrapheneInputObjectType(
            graphene_type=type,
            name=type._meta.name,
            description=type._meta.description,
            container_type=type._meta.container,
            fields=partial(
                self.construct_fields_for_type, map, type, is_input_type=True
            ),
        )

    def construct_union(self, map, type):
        _resolve_type = None
        if type.resolve_type:
            _resolve_type = partial(
                resolve_type, type.resolve_type, map, type._meta.name
            )

        def types():
            union_types = []
            for objecttype in type._meta.types:
                self.graphene_reducer(map, objecttype)
                internal_type = map[objecttype._meta.name]
                assert internal_type.graphene_type == objecttype
                union_types.append(internal_type)
            return union_types

        return GrapheneUnionType(
            graphene_type=type,
            name=type._meta.name,
            types=types,
            resolve_type=_resolve_type,
        )

    def get_name(self, name):
        if self.auto_camelcase:
            return to_camel_case(name)
        return name

    def construct_fields_for_type(self, map, type, is_input_type=False):
        fields = OrderedDict()
        for name, field in type._meta.fields.items():
            if isinstance(field, Dynamic):
                field = get_field_as(field.get_type(self.schema), _as=Field)
                if not field:
                    continue
            map = self.reducer(map, field.type)
            field_type = self.get_field_type(map, field.type)
            if is_input_type:
                _field = GraphQLInputObjectField(
                    field_type,
                    default_value=field.default_value,
                    out_name=name,
                    description=field.description,
                )
            else:
                args = OrderedDict()
                for arg_name, arg in field.args.items():
                    map = self.reducer(map, arg.type)
                    arg_type = self.get_field_type(map, arg.type)
                    processed_arg_name = arg.name or self.get_name(arg_name)
                    args[processed_arg_name] = GraphQLArgument(
                        arg_type,
                        out_name=arg_name,
                        description=arg.description,
                        default_value=arg.default_value,
                    )
                _field = GraphQLField(
                    field_type,
                    args=args,
                    resolver=field.get_resolver(
                        self.get_resolver_for_type(type, name, field.default_value)
                    ),
                    deprecation_reason=field.deprecation_reason,
                    description=field.description,
                )
            field_name = field.name or self.get_name(name)
            fields[field_name] = _field
        return fields

    def get_resolver_for_type(self, type, name, default_value):
        if not issubclass(type, ObjectType):
            return
        resolver = getattr(type, "resolve_{}".format(name), None)
        if not resolver:
            # If we don't find the resolver in the ObjectType class, then try to
            # find it in each of the interfaces
            interface_resolver = None
            for interface in type._meta.interfaces:
                if name not in interface._meta.fields:
                    continue
                interface_resolver = getattr(interface, "resolve_{}".format(name), None)
                if interface_resolver:
                    break
            resolver = interface_resolver

        # Only if is not decorated with classmethod
        if resolver:
            return get_unbound_function(resolver)

        default_resolver = type._meta.default_resolver or get_default_resolver()
        return partial(default_resolver, name, default_value)

    def get_field_type(self, map, type):
        if isinstance(type, List):
            return GraphQLList(self.get_field_type(map, type.of_type))
        if isinstance(type, NonNull):
            return GraphQLNonNull(self.get_field_type(map, type.of_type))
        return map.get(type._meta.name)
