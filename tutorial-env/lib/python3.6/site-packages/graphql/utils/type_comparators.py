from ..type.definition import (
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLUnionType,
    is_abstract_type,
)

# Necessary for static type checking
if False:  # flake8: noqa
    from ..type.definition import (
        GraphQLScalarType,
        GraphQLInterfaceType,
        GraphQLObjectType,
        GraphQLUnionType,
    )
    from ..type.typemap import GraphQLTypeMap
    from ..type.schema import GraphQLSchema
    from typing import Union


def is_equal_type(type_a, type_b):
    if type_a is type_b:
        return True

    if isinstance(type_a, GraphQLNonNull) and isinstance(type_b, GraphQLNonNull):
        return is_equal_type(type_a.of_type, type_b.of_type)

    if isinstance(type_a, GraphQLList) and isinstance(type_b, GraphQLList):
        return is_equal_type(type_a.of_type, type_b.of_type)

    return False


def is_type_sub_type_of(schema, maybe_subtype, super_type):
    # type: (Union[GraphQLSchema, GraphQLTypeMap], GraphQLScalarType, GraphQLScalarType) -> bool
    if maybe_subtype is super_type:
        return True

    if isinstance(super_type, GraphQLNonNull):
        if isinstance(maybe_subtype, GraphQLNonNull):
            return is_type_sub_type_of(
                schema, maybe_subtype.of_type, super_type.of_type
            )
        return False
    elif isinstance(maybe_subtype, GraphQLNonNull):
        return is_type_sub_type_of(schema, maybe_subtype.of_type, super_type)

    if isinstance(super_type, GraphQLList):
        if isinstance(maybe_subtype, GraphQLList):
            return is_type_sub_type_of(
                schema, maybe_subtype.of_type, super_type.of_type
            )
        return False
    elif isinstance(maybe_subtype, GraphQLList):
        return False

    if (
        is_abstract_type(super_type)
        and isinstance(maybe_subtype, GraphQLObjectType)
        and schema.is_possible_type(super_type, maybe_subtype)
    ):
        return True

    return False


def do_types_overlap(
    schema,  # type: GraphQLSchema
    t1,  # type: Union[GraphQLInterfaceType, GraphQLUnionType]
    t2,  # type: Union[GraphQLInterfaceType, GraphQLUnionType]
):
    # type: (...) -> bool
    # print 'do_types_overlap', t1, t2
    if t1 == t2:
        # print '1'
        return True

    if isinstance(t1, (GraphQLInterfaceType, GraphQLUnionType)):
        if isinstance(t2, (GraphQLInterfaceType, GraphQLUnionType)):
            # If both types are abstract, then determine if there is any intersection
            # between possible concrete types of each.
            s = any(
                [
                    schema.is_possible_type(t2, type)
                    for type in schema.get_possible_types(t1)
                ]
            )
            # print '2',s
            return s
        # Determine if the latter type is a possible concrete type of the former.
        r = schema.is_possible_type(t1, t2)
        # print '3', r
        return r

    if isinstance(t2, (GraphQLInterfaceType, GraphQLUnionType)):
        t = schema.is_possible_type(t2, t1)
        # print '4', t
        return t

    # print '5'
    return False
