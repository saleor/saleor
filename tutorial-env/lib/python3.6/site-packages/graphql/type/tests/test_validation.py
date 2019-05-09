import re

from pytest import raises

from graphql.type import (
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
    GraphQLSchema,
    GraphQLString,
    GraphQLUnionType,
)
from graphql.type.definition import GraphQLArgument

_none = lambda *args: None
_true = lambda *args: True
_false = lambda *args: False

SomeScalarType = GraphQLScalarType(
    name="SomeScalar", serialize=_none, parse_value=_none, parse_literal=_none
)

SomeObjectType = GraphQLObjectType(
    name="SomeObject", fields={"f": GraphQLField(GraphQLString)}
)

ObjectWithIsTypeOf = GraphQLObjectType(
    name="ObjectWithIsTypeOf",
    is_type_of=_true,
    fields={"f": GraphQLField(GraphQLString)},
)

SomeUnionType = GraphQLUnionType(
    name="SomeUnion", resolve_type=_none, types=[SomeObjectType]
)

SomeInterfaceType = GraphQLInterfaceType(
    name="SomeInterface", resolve_type=_none, fields={"f": GraphQLField(GraphQLString)}
)

SomeEnumType = GraphQLEnumType(name="SomeEnum", values={"ONLY": GraphQLEnumValue()})

SomeInputObjectType = GraphQLInputObjectType(
    name="SomeInputObject",
    fields={"val": GraphQLInputObjectField(GraphQLString, default_value="hello")},
)


def with_modifiers(types):
    return (
        types
        + [GraphQLList(t) for t in types]
        + [GraphQLNonNull(t) for t in types]
        + [GraphQLNonNull(GraphQLList(t)) for t in types]
    )


output_types = with_modifiers(
    [
        GraphQLString,
        SomeScalarType,
        SomeEnumType,
        SomeObjectType,
        SomeUnionType,
        SomeInterfaceType,
    ]
)

not_output_types = with_modifiers([SomeInputObjectType]) + [str]

input_types = with_modifiers(
    [GraphQLString, SomeScalarType, SomeEnumType, SomeInputObjectType]
)

not_input_types = with_modifiers([SomeObjectType, SomeUnionType, SomeInterfaceType]) + [
    str
]


def schema_with_field_type(t):
    return GraphQLSchema(
        query=GraphQLObjectType(name="Query", fields={"f": GraphQLField(t)}), types=[t]
    )


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_ASchemaMustHaveObjectRootTypes:
    def test_accepts_a_schema_whose_query_type_is_an_object_type(self):
        assert GraphQLSchema(query=SomeObjectType)

    def test_accepts_a_schema_whose_query_and_mutation_types_are_object_types(self):
        MutationType = GraphQLObjectType(
            name="Mutation", fields={"edit": GraphQLField(GraphQLString)}
        )

        assert GraphQLSchema(query=SomeObjectType, mutation=MutationType)

    def test_accepts_a_schema_whose_query_and_subscription_types_are_object_types(self):
        SubscriptionType = GraphQLObjectType(
            name="Subscription", fields={"subscribe": GraphQLField(GraphQLString)}
        )

        assert GraphQLSchema(query=SomeObjectType, subscription=SubscriptionType)

    def test_rejects_a_schema_without_a_query_type(self):
        with raises(AssertionError) as excinfo:
            GraphQLSchema(query=None)

        assert str(excinfo.value) == "Schema query must be Object Type but got: None."

    def test_rejects_a_schema_whose_query_type_is_an_input_type(self):
        with raises(AssertionError) as excinfo:
            GraphQLSchema(query=SomeInputObjectType)

        assert (
            str(excinfo.value)
            == "Schema query must be Object Type but got: SomeInputObject."
        )

    def test_rejects_a_schema_whose_mutation_type_is_an_input_type(self):
        with raises(AssertionError) as excinfo:
            GraphQLSchema(query=SomeObjectType, mutation=SomeInputObjectType)

        assert (
            str(excinfo.value)
            == "Schema mutation must be Object Type but got: SomeInputObject."
        )

    def test_rejects_a_schema_whose_subscription_type_is_an_input_type(self):
        with raises(AssertionError) as excinfo:
            GraphQLSchema(query=SomeObjectType, subscription=SomeInputObjectType)

        assert (
            str(excinfo.value)
            == "Schema subscription must be Object Type but got: SomeInputObject."
        )

    def test_rejects_a_schema_whose_directives_are_incorrectly_typed(self):
        with raises(AssertionError) as excinfo:
            GraphQLSchema(query=SomeObjectType, directives=["somedirective"])

        assert (
            str(excinfo.value)
            == "Schema directives must be List[GraphQLDirective] if provided but got: "
            "['somedirective']."
        )


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_ASchemaMustContainUniquelyNamedTypes:
    def test_it_rejects_a_schema_which_defines_a_builtin_type(self):
        FakeString = GraphQLScalarType(name="String", serialize=_none)

        QueryType = GraphQLObjectType(
            name="Query",
            fields={
                "normal": GraphQLField(GraphQLString),
                "fake": GraphQLField(FakeString),
            },
        )

        with raises(AssertionError) as excinfo:
            GraphQLSchema(query=QueryType)

        assert (
            str(excinfo.value)
            == "Schema must contain unique named types but contains multiple types named "
            '"String".'
        )

    # noinspection PyUnusedLocal
    def test_it_rejects_a_schema_which_have_same_named_objects_implementing_an_interface(
        self
    ):
        AnotherInterface = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields={"f": GraphQLField(GraphQLString)},
        )

        FirstBadObject = GraphQLObjectType(
            name="BadObject",
            interfaces=[AnotherInterface],
            fields={"f": GraphQLField(GraphQLString)},
        )

        SecondBadObject = GraphQLObjectType(
            name="BadObject",
            interfaces=[AnotherInterface],
            fields={"f": GraphQLField(GraphQLString)},
        )

        QueryType = GraphQLObjectType(
            name="Query", fields={"iface": GraphQLField(AnotherInterface)}
        )

        with raises(AssertionError) as excinfo:
            GraphQLSchema(query=QueryType, types=[FirstBadObject, SecondBadObject])

        assert (
            str(excinfo.value)
            == "Schema must contain unique named types but contains multiple types named "
            '"BadObject".'
        )


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_ObjectsMustHaveFields:
    def test_accepts_an_object_type_with_fields_object(self):
        assert schema_with_field_type(
            GraphQLObjectType(
                name="SomeObject", fields={"f": GraphQLField(GraphQLString)}
            )
        )

    def test_accepts_an_object_type_with_a_field_function(self):
        assert schema_with_field_type(
            GraphQLObjectType(
                name="SomeObject", fields=lambda: {"f": GraphQLField(GraphQLString)}
            )
        )

    def test_rejects_an_object_type_with_missing_fields(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(GraphQLObjectType(name="SomeObject", fields=None))

        assert (
            str(excinfo.value)
            == "SomeObject fields must be a mapping (dict / OrderedDict) with field names "
            "as keys or a function which returns such a mapping."
        )

    def test_rejects_an_object_type_with_incorrectly_named_fields(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(
                GraphQLObjectType(
                    name="SomeObject",
                    fields={"bad-name-with-dashes": GraphQLField(GraphQLString)},
                )
            )

        assert (
            str(excinfo.value)
            == 'Names must match /^[_a-zA-Z][_a-zA-Z0-9]*$/ but "bad-name-with-dashes" does not.'
        )

    def test_rejects_an_object_type_with_incorrectly_typed_fields(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(
                GraphQLObjectType(
                    name="SomeObject", fields=[GraphQLField(GraphQLString)]
                )
            )

        assert (
            str(excinfo.value)
            == "SomeObject fields must be a mapping (dict / OrderedDict) with field names "
            "as keys or a function which returns such a mapping."
        )

    def test_rejects_an_object_type_with_empty_fields(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(GraphQLObjectType(name="SomeObject", fields={}))

        assert (
            str(excinfo.value)
            == "SomeObject fields must be a mapping (dict / OrderedDict) with field names "
            "as keys or a function which returns such a mapping."
        )

    def test_rejects_an_object_type_with_a_field_function_that_returns_nothing(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(GraphQLObjectType(name="SomeObject", fields=_none))

        assert (
            str(excinfo.value)
            == "SomeObject fields must be a mapping (dict / OrderedDict) with field names "
            "as keys or a function which returns such a mapping."
        )

    def test_rejects_an_object_type_with_a_field_function_that_returns_empty(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(
                GraphQLObjectType(name="SomeObject", fields=lambda: {})
            )

        assert (
            str(excinfo.value)
            == "SomeObject fields must be a mapping (dict / OrderedDict) with field names "
            "as keys or a function which returns such a mapping."
        )

    def test_rejects_an_object_type_with_a_field_with_an_invalid_value(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(
                GraphQLObjectType(name="SomeObject", fields={"f": "hello"})
            )

        assert str(excinfo.value) == "SomeObject.f must be an instance of GraphQLField."

    def test_rejects_an_object_type_with_a_field_function_with_an_invalid_value(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(
                GraphQLObjectType(name="SomeObject", fields=lambda: {"f": "hello"})
            )

        assert str(excinfo.value) == "SomeObject.f must be an instance of GraphQLField."


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_FieldArgsMustBeProperlyNamed:
    def test_accepts_field_args_with_valid_names(self):
        assert schema_with_field_type(
            GraphQLObjectType(
                name="SomeObject",
                fields={
                    "goodField": GraphQLField(
                        GraphQLString, args={"goodArg": GraphQLArgument(GraphQLString)}
                    )
                },
            )
        )

    def test_reject_field_args_with_invalid_names(self):
        with raises(AssertionError) as excinfo:
            assert schema_with_field_type(
                GraphQLObjectType(
                    name="SomeObject",
                    fields={
                        "badField": GraphQLField(
                            GraphQLString,
                            args={
                                "bad-name-with-dashes": GraphQLArgument(GraphQLString)
                            },
                        )
                    },
                )
            )

        assert (
            str(excinfo.value)
            == 'Names must match /^[_a-zA-Z][_a-zA-Z0-9]*$/ but "bad-name-with-dashes" does not.'
        )


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_FieldArgsMustBeObjects:
    def test_accepts_an_object_with_field_args(self):
        assert schema_with_field_type(
            GraphQLObjectType(
                name="SomeObject",
                fields={
                    "goodField": GraphQLField(
                        GraphQLString, args={"goodArg": GraphQLArgument(GraphQLString)}
                    )
                },
            )
        )

    def test_rejects_an_object_with_incorrectly_typed_field_args(self):
        with raises(AssertionError) as excinfo:
            assert schema_with_field_type(
                GraphQLObjectType(
                    name="SomeObject",
                    fields={
                        "badField": GraphQLField(
                            GraphQLString, args=[GraphQLArgument(GraphQLString)]
                        )
                    },
                )
            )

        assert (
            str(excinfo.value)
            == "SomeObject.badField args must be a mapping (dict / OrderedDict) with argument "
            "names as keys."
        )

    def test_rejects_an_object_with_incorrectly_typed_field_args_with_an_invalid_value(
        self
    ):
        with raises(AssertionError) as excinfo:
            assert schema_with_field_type(
                GraphQLObjectType(
                    name="SomeObject",
                    fields={
                        "badField": GraphQLField(
                            GraphQLString, args={"badArg": "I am bad!"}
                        )
                    },
                )
            )

        assert (
            str(excinfo.value)
            == "SomeObject.badField(badArg:) argument must be an instance of GraphQLArgument."
        )


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_ObjectInterfacesMustBeArray:
    def test_accepts_an_object_type_with_array_interface(self):
        AnotherInterfaceType = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields={"f": GraphQLField(GraphQLString)},
        )

        assert schema_with_field_type(
            GraphQLObjectType(
                name="SomeObject",
                interfaces=[AnotherInterfaceType],
                fields={"f": GraphQLField(GraphQLString)},
            )
        )

    def test_accepts_an_object_type_with_interfaces_as_a_function_returning_an_array(
        self
    ):
        AnotherInterfaceType = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields={"f": GraphQLField(GraphQLString)},
        )

        assert schema_with_field_type(
            GraphQLObjectType(
                name="SomeObject",
                interfaces=lambda: [AnotherInterfaceType],
                fields={"f": GraphQLField(GraphQLString)},
            )
        )

    def test_rejects_an_object_type_with_incorrectly_typed_interfaces(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(
                GraphQLObjectType(
                    name="SomeObject",
                    interfaces={},
                    fields={"f": GraphQLField(GraphQLString)},
                )
            )

        assert (
            str(excinfo.value)
            == "SomeObject interfaces must be a list/tuple or a function which returns a "
            "list/tuple."
        )

    def test_rejects_an_object_type_with_interfaces_as_a_function_returning_an_incorrect_type(
        self
    ):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(
                GraphQLObjectType(
                    name="SomeObject",
                    interfaces=lambda: {},
                    fields={"f": GraphQLField(GraphQLString)},
                )
            )

        assert (
            str(excinfo.value)
            == "SomeObject interfaces must be a list/tuple or a function which returns a "
            "list/tuple."
        )


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_UnionTypesMustBeArray:
    def test_accepts_a_union_type_with_aray_types(self):
        assert schema_with_field_type(
            GraphQLUnionType(
                name="SomeUnion", resolve_type=_none, types=[SomeObjectType]
            )
        )

    def test_rejects_a_union_without_types(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(
                GraphQLUnionType(name="SomeUnion", resolve_type=_none, types=[])
            )

        assert str(excinfo.value) == "Must provide types for Union SomeUnion."

    def test_rejects_a_union_type_with_empty_types(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(
                GraphQLUnionType(name="SomeUnion", resolve_type=_none, types=[])
            )

        assert str(excinfo.value) == "Must provide types for Union SomeUnion."

    def test_rejects_a_union_type_with_incorrectly_typed_types(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(
                GraphQLUnionType(
                    name="SomeUnion",
                    resolve_type=_none,
                    types={"SomeObjectType": SomeObjectType},
                )
            )

        assert str(excinfo.value) == "Must provide types for Union SomeUnion."


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_UnionTypesMustBeCallableThatReturnsArray:
    def test_accepts_a_union_type_with_aray_types(self):
        assert schema_with_field_type(
            GraphQLUnionType(
                name="SomeUnion", resolve_type=_none, types=lambda: [SomeObjectType]
            )
        )

    def test_rejects_a_union_type_with_empty_types(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(
                GraphQLUnionType(name="SomeUnion", resolve_type=_none, types=lambda: [])
            )

        assert str(excinfo.value) == "Must provide types for Union SomeUnion."

    def test_rejects_a_union_type_with_incorrectly_typed_types(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(
                GraphQLUnionType(
                    name="SomeUnion",
                    resolve_type=_none,
                    types=lambda: {"SomeObjectType": SomeObjectType},
                )
            )

        assert str(excinfo.value) == "Must provide types for Union SomeUnion."


def schema_with_input_object(input_object_type):
    return GraphQLSchema(
        query=GraphQLObjectType(
            name="Query",
            fields={
                "f": GraphQLField(
                    GraphQLString, args={"badArg": GraphQLArgument(input_object_type)}
                )
            },
        )
    )


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_InputObjectsMustHaveFields:
    def test_accepts_an_input_object_type_with_fields(self):
        assert schema_with_input_object(
            GraphQLInputObjectType(
                name="SomeInputObject",
                fields={"f": GraphQLInputObjectField(GraphQLString)},
            )
        )

    def test_accepts_an_input_object_type_with_field_function(self):
        assert schema_with_input_object(
            GraphQLInputObjectType(
                name="SomeInputObject",
                fields=lambda: {"f": GraphQLInputObjectField(GraphQLString)},
            )
        )

    def test_rejects_an_input_object_type_with_missing_fields(self):
        with raises(AssertionError) as excinfo:
            schema_with_input_object(
                GraphQLInputObjectType(name="SomeInputObject", fields=None)
            )

        assert (
            str(excinfo.value)
            == "SomeInputObject fields must be a mapping (dict / OrderedDict) with "
            "field names as keys or a function which returns such a mapping."
        )

    def test_rejects_an_input_object_type_with_incorrectly_typed_fields(self):
        with raises(AssertionError) as excinfo:
            schema_with_input_object(
                GraphQLInputObjectType(
                    name="SomeInputObject",
                    fields=[GraphQLInputObjectField(GraphQLString)],
                )
            )

        assert (
            str(excinfo.value)
            == "SomeInputObject fields must be a mapping (dict / OrderedDict) with "
            "field names as keys or a function which returns such a mapping."
        )

    def test_rejects_an_input_object_type_with_incorrectly_typed_field_value(self):
        with raises(AssertionError) as excinfo:
            schema_with_input_object(
                GraphQLInputObjectType(
                    name="SomeInputObject", fields={"f": GraphQLField(GraphQLString)}
                )
            )

        assert (
            str(excinfo.value)
            == "SomeInputObject.f must be an instance of GraphQLInputObjectField."
        )

    def test_rejects_an_input_object_type_with_fields_function_returning_incorrectly_typed_field_value(
        self
    ):
        with raises(AssertionError) as excinfo:
            schema_with_input_object(
                GraphQLInputObjectType(
                    name="SomeInputObject",
                    fields=lambda: {"f": GraphQLField(GraphQLString)},
                )
            )

        assert (
            str(excinfo.value)
            == "SomeInputObject.f must be an instance of GraphQLInputObjectField."
        )

    def test_rejects_an_input_object_type_with_empty_fields(self):
        with raises(AssertionError) as excinfo:
            schema_with_input_object(
                GraphQLInputObjectType(name="SomeInputObject", fields={})
            )

        assert (
            str(excinfo.value)
            == "SomeInputObject fields must be a mapping (dict / OrderedDict) with "
            "field names as keys or a function which returns such a mapping."
        )

    def test_rejects_an_input_object_type_with_a_field_function_that_returns_nothing(
        self
    ):
        with raises(AssertionError) as excinfo:
            schema_with_input_object(
                GraphQLInputObjectType(name="SomeInputObject", fields=_none)
            )

        assert (
            str(excinfo.value)
            == "SomeInputObject fields must be a mapping (dict / OrderedDict) with "
            "field names as keys or a function which returns such a mapping."
        )

    def test_rejects_an_input_object_type_with_a_field_function_that_returns_empty(
        self
    ):
        with raises(AssertionError) as excinfo:
            schema_with_input_object(
                GraphQLInputObjectType(name="SomeInputObject", fields=lambda: {})
            )

        assert (
            str(excinfo.value)
            == "SomeInputObject fields must be a mapping (dict / OrderedDict) with "
            "field names as keys or a function which returns such a mapping."
        )


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_ObjectTypesMustBeAssertable:
    def test_accepts_an_object_type_with_an_is_type_of_function(self):
        assert schema_with_field_type(
            GraphQLObjectType(
                name="AnotherObject",
                is_type_of=_true,
                fields={"f": GraphQLField(GraphQLString)},
            )
        )

    def test_rejects_an_object_type_with_an_incorrect_type_for_is_type_of(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(
                GraphQLObjectType(
                    name="AnotherObject",
                    is_type_of={},
                    fields={"f": GraphQLField(GraphQLString)},
                )
            )

        assert (
            str(excinfo.value)
            == 'AnotherObject must provide "is_type_of" as a function.'
        )


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_InterfaceTypesMustBeResolvable:
    def test_accepts_an_interface_type_defining_resolve_type(self):
        AnotherInterfaceType = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields={"f": GraphQLField(GraphQLString)},
        )

        assert schema_with_field_type(
            GraphQLObjectType(
                name="SomeObject",
                interfaces=[AnotherInterfaceType],
                fields={"f": GraphQLField(GraphQLString)},
            )
        )

    def test_accepts_an_interface_with_implementing_type_defining_is_type_of(self):
        AnotherInterfaceType = GraphQLInterfaceType(
            name="AnotherInterface", fields={"f": GraphQLField(GraphQLString)}
        )

        assert schema_with_field_type(
            GraphQLObjectType(
                name="SomeObject",
                is_type_of=_true,
                interfaces=[AnotherInterfaceType],
                fields={"f": GraphQLField(GraphQLString)},
            )
        )

    def test_accepts_an_interface_type_defining_resolve_type_with_implementing_type_defining_is_type_of(
        self
    ):
        AnotherInterfaceType = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields={"f": GraphQLField(GraphQLString)},
        )
        assert schema_with_field_type(
            GraphQLObjectType(
                name="SomeObject",
                is_type_of=_true,
                interfaces=[AnotherInterfaceType],
                fields={"f": GraphQLField(GraphQLString)},
            )
        )

    def test_rejects_an_interface_type_with_an_incorrect_type_for_resolve_type(self):
        with raises(AssertionError) as excinfo:
            GraphQLInterfaceType(
                name="AnotherInterface",
                resolve_type={},
                fields={"f": GraphQLField(GraphQLString)},
            )

        assert (
            str(excinfo.value)
            == 'AnotherInterface must provide "resolve_type" as a function.'
        )

    def test_rejects_an_interface_type_not_defining_resolve_type_with_implementing_type_not_defining_is_type_of(
        self
    ):
        AnotherInterfaceType = GraphQLInterfaceType(
            name="AnotherInterface", fields={"f": GraphQLField(GraphQLString)}
        )

        with raises(AssertionError) as excinfo:
            schema_with_field_type(
                GraphQLObjectType(
                    name="SomeObject",
                    interfaces=[AnotherInterfaceType],
                    fields={"f": GraphQLField(GraphQLString)},
                )
            )

        assert (
            str(excinfo.value)
            == 'Interface Type AnotherInterface does not provide a "resolve_type" function and '
            'implementing Type SomeObject does not provide a "is_type_of" function. '
            "There is no way to resolve this implementing type during execution."
        )


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_UnionTypesMustBeResolvable:
    def test_accepts_a_union_type_defining_resolve_type(self):
        assert schema_with_field_type(
            GraphQLUnionType(
                name="SomeUnion", resolve_type=_none, types=[SomeObjectType]
            )
        )

    def test_accepts_a_union_of_object_types_defining_is_type_of(self):
        assert schema_with_field_type(
            GraphQLUnionType(name="SomeUnion", types=[ObjectWithIsTypeOf])
        )

    def test_accepts_a_union_type_defning_resolve_type_of_objects_defning_is_type_of(
        self
    ):
        assert schema_with_field_type(
            GraphQLUnionType(
                name="SomeUnion", resolve_type=_none, types=[ObjectWithIsTypeOf]
            )
        )

    def test_rejects_an_interface_type_with_an_incorrect_type_for_resolve_type(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(
                GraphQLUnionType(
                    name="SomeUnion", resolve_type={}, types=[ObjectWithIsTypeOf]
                )
            )

        assert (
            str(excinfo.value) == 'SomeUnion must provide "resolve_type" as a function.'
        )

    def test_rejects_a_union_type_not_defining_resolve_type_of_object_types_not_defining_is_type_of(
        self
    ):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(
                GraphQLUnionType(name="SomeUnion", types=[SomeObjectType])
            )

        assert (
            str(excinfo.value)
            == 'Union Type SomeUnion does not provide a "resolve_type" function and possible '
            'Type SomeObject does not provide a "is_type_of" function. '
            "There is no way to resolve this possible type during execution."
        )


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_ScalarTypesMustBeSerializable:
    def test_accepts_a_scalar_type_defining_serialize(self):
        assert schema_with_field_type(
            GraphQLScalarType(name="SomeScalar", serialize=_none)
        )

    def test_rejects_a_scalar_type_not_defining_serialize(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(GraphQLScalarType(name="SomeScalar"))

        assert (
            str(excinfo.value)
            == 'SomeScalar must provide "serialize" function. If this custom Scalar is also '
            'used as an input type, ensure "parse_value" and "parse_literal" '
            "functions are also provided."
        )

    def test_rejects_a_scalar_type_defining_serialize_with_an_incorrect_type(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(GraphQLScalarType(name="SomeScalar", serialize={}))

        assert (
            str(excinfo.value)
            == 'SomeScalar must provide "serialize" function. If this custom Scalar is also '
            'used as an input type, ensure "parse_value" and "parse_literal" '
            "functions are also provided."
        )

    def test_accepts_scalar_type_defining_parse_value_and_parse_literal(self):
        assert schema_with_field_type(
            GraphQLScalarType(
                name="SomeScalar",
                serialize=_none,
                parse_literal=_none,
                parse_value=_none,
            )
        )

    def test_rejects_a_scalar_type_defining_parse_value_but_not_parse_literal(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(
                GraphQLScalarType(name="SomeScalar", serialize=_none, parse_value=_none)
            )

        assert (
            str(excinfo.value)
            == 'SomeScalar must provide both "parse_value" and "parse_literal" functions.'
        )

    def test_rejects_a_scalar_type_defining_parse_literal_but_not_parse_value(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(
                GraphQLScalarType(
                    name="SomeScalar", serialize=_none, parse_literal=_none
                )
            )

        assert (
            str(excinfo.value)
            == 'SomeScalar must provide both "parse_value" and "parse_literal" functions.'
        )

    def test_rejects_a_scalar_type_defining_parse_literal_and_parse_value_with_an_incorrect_type(
        self
    ):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(
                GraphQLScalarType(
                    name="SomeScalar", serialize=_none, parse_literal={}, parse_value={}
                )
            )

        assert (
            str(excinfo.value)
            == 'SomeScalar must provide both "parse_value" and "parse_literal" functions.'
        )


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_EnumTypesMustBeWellDefined:
    def test_accepts_a_well_defined_enum_type_with_empty_value_definition(self):
        assert GraphQLEnumType(
            name="SomeEnum",
            values={"FOO": GraphQLEnumValue(), "BAR": GraphQLEnumValue()},
        )

    def test_accepts_a_well_defined_enum_type_with_internal_value_definition(self):
        assert GraphQLEnumType(
            name="SomeEnum",
            values={"FOO": GraphQLEnumValue(10), "BAR": GraphQLEnumValue(20)},
        )

    def test_rejects_an_enum_without_values(self):
        with raises(AssertionError) as excinfo:
            GraphQLEnumType(name="SomeEnum", values=None)

        assert (
            str(excinfo.value)
            == "SomeEnum values must be a mapping (dict / OrderedDict) with value names as keys."
        )

    def test_rejects_an_enum_with_empty_values(self):
        with raises(AssertionError) as excinfo:
            GraphQLEnumType(name="SomeEnum", values={})
        assert (
            str(excinfo.value)
            == "SomeEnum values must be a mapping (dict / OrderedDict) with value names as keys."
        )

    def test_rejects_an_enum_with_incorrectly_typed_values(self):
        with raises(AssertionError) as excinfo:
            GraphQLEnumType(name="SomeEnum", values=[{"foo": GraphQLEnumValue(10)}])

        assert (
            str(excinfo.value)
            == "SomeEnum values must be a mapping (dict / OrderedDict) with value names as keys."
        )

    def test_rejects_an_enum_with_missing_value_definition(self):
        with raises(AssertionError) as excinfo:
            GraphQLEnumType(name="SomeEnum", values={"FOO": None})
        assert (
            str(excinfo.value)
            == "SomeEnum.FOO must be an instance of GraphQLEnumValue, but got: None"
        )

    def test_rejects_an_enum_with_incorrectly_typed_value_definition(self):
        with raises(AssertionError) as excinfo:
            GraphQLEnumType(name="SomeEnum", values={"FOO": 10})
        assert (
            str(excinfo.value)
            == "SomeEnum.FOO must be an instance of GraphQLEnumValue, but got: 10"
        )


def schema_with_object_field_of_type(field_type):
    BadObjectType = GraphQLObjectType(
        name="BadObject", fields={"badField": GraphQLField(field_type)}
    )

    return schema_with_field_type(BadObjectType)


def repr_type_as_syntax_safe_fn(_type):
    if isinstance(_type, GraphQLList):
        return "list_" + repr_type_as_syntax_safe_fn(_type.of_type)

    if isinstance(_type, GraphQLNonNull):
        return "non_null_" + repr_type_as_syntax_safe_fn(_type.of_type)

    return re.sub(r"[^a-zA-Z]", "_", str(_type)) + "_" + type(_type).__name__


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_ObjectFieldsMustHaveOutputTypes:
    def accepts(self, type):
        assert schema_with_object_field_of_type(type)

    for i, type in enumerate(output_types):
        exec(
            "def test_accepts_an_output_type_as_an_object_field_type_{}(self): self.accepts(output_types[{}])".format(
                repr_type_as_syntax_safe_fn(type), i
            )
        )

    def test_rejects_an_empty_object_field_type(self):
        with raises(AssertionError) as excinfo:
            schema_with_object_field_of_type(None)

        assert (
            str(excinfo.value)
            == "BadObject.badField field type must be Output Type but got: None."
        )

    def rejects(self, type):
        with raises(AssertionError) as excinfo:
            schema_with_object_field_of_type(type)

        assert str(
            excinfo.value
        ) == "BadObject.badField field type must be Output Type but got: {}.".format(
            type
        )

    for i, type in enumerate(not_output_types):
        exec(
            "def test_rejects_a_non_output_type_as_an_object_field_type_{}(self): self.rejects(not_output_types[{}])".format(
                repr_type_as_syntax_safe_fn(type), i
            )
        )


def schema_with_object_implementing_type(implemented_type):
    BadObjectType = GraphQLObjectType(
        name="BadObject",
        interfaces=[implemented_type],
        fields={"f": GraphQLField(GraphQLString)},
    )

    return schema_with_field_type(BadObjectType)


not_interface_types = with_modifiers(
    [SomeScalarType, SomeEnumType, SomeObjectType, SomeUnionType, SomeInputObjectType]
)


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_ObjectsCanOnlyImplementInterfaces:
    def test_accepts_an_object_implementing_an_interface(self):
        AnotherInterfaceType = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields={"f": GraphQLField(GraphQLString)},
        )

        assert schema_with_object_implementing_type(AnotherInterfaceType)

    def rejects(self, type):
        with raises(AssertionError) as excinfo:
            schema_with_object_implementing_type(type)

        assert str(
            excinfo.value
        ) == "BadObject may only implement Interface types, it cannot implement: {}.".format(
            type
        )

    for i, type in enumerate(not_interface_types):
        exec(
            "def test_rejects_an_object_implementing_a_non_interface_type_{}(self):"
            " self.rejects(not_interface_types[{}])".format(
                repr_type_as_syntax_safe_fn(type), i
            )
        )


not_object_types = with_modifiers(
    [
        SomeScalarType,
        SomeEnumType,
        SomeInterfaceType,
        SomeUnionType,
        SomeInputObjectType,
    ]
)


def schema_with_union_of_type(type):
    BadUnionType = GraphQLUnionType(name="BadUnion", resolve_type=_none, types=[type])

    return schema_with_field_type(BadUnionType)


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_UnionMustRepresentObjectTypes:
    def test_accepts_a_union_of_an_object_type(self):
        assert schema_with_union_of_type(SomeObjectType)

    def rejects(self, type):
        with raises(AssertionError) as excinfo:
            schema_with_union_of_type(type)

        assert str(
            excinfo.value
        ) == "BadUnion may only contain Object types, it cannot contain: {}.".format(
            type
        )

    for i, type in enumerate(not_object_types):
        exec(
            "def test_rejects_a_union_of_non_object_type_{}(self):"
            " self.rejects(not_object_types[{}])".format(
                repr_type_as_syntax_safe_fn(type), i
            )
        )


def schema_with_interface_field_of_type(field_type):
    BadInterfaceType = GraphQLInterfaceType(
        name="BadInterface", fields={"badField": GraphQLField(field_type)}
    )

    return schema_with_field_type(BadInterfaceType)


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_InterfaceFieldsMustHaveOutputTypes:
    def accepts(self, type):
        assert schema_with_interface_field_of_type(type)

    def rejects(self, type):
        with raises(AssertionError) as excinfo:
            schema_with_interface_field_of_type(type)

        assert str(
            excinfo.value
        ) == "BadInterface.badField field type must be Output Type but got: {}.".format(
            type
        )

    for i, type in enumerate(output_types):
        exec(
            "def test_accepts_an_output_type_as_an_interface_field_type_{}(self):"
            " self.accepts(output_types[{}])".format(
                repr_type_as_syntax_safe_fn(type), i
            )
        )

    def test_rejects_an_empty_interface_field_type(self):
        self.rejects(None)

    for i, type in enumerate(not_output_types):
        exec(
            "def test_rejects_a_non_output_type_as_an_interface_field_type_{}(self):"
            " self.rejects(not_output_types[{}])".format(
                repr_type_as_syntax_safe_fn(type), i
            )
        )


# noinspection PyMethodMayBeStatic,PyPep8Naming
def schema_with_arg_of_type(arg_type):
    BadObjectType = GraphQLObjectType(
        name="BadObject",
        fields={
            "badField": GraphQLField(
                type=GraphQLString, args={"badArg": GraphQLArgument(arg_type)}
            )
        },
    )

    return schema_with_field_type(BadObjectType)


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_FieldArgumentsMustHaveInputTypes:
    def accepts(self, type):
        assert schema_with_arg_of_type(type)

    def rejects(self, type):
        with raises(AssertionError) as excinfo:
            schema_with_arg_of_type(type)

        assert str(
            excinfo.value
        ) == "BadObject.badField(badArg:) argument type must be Input " "Type but got: {}.".format(
            type
        )

    for i, type in enumerate(input_types):
        exec(
            "def test_accepts_an_input_type_as_a_field_arg_type_{}(self):"
            " self.accepts(input_types[{}])".format(
                repr_type_as_syntax_safe_fn(type), i
            )
        )

    def test_rejects_an_empty_field_arg_type(self):
        self.rejects(None)

    for i, type in enumerate(not_input_types):
        exec(
            "def test_rejects_a_not_input_type_as_a_field_arg_type_{}(self):"
            " self.rejects(not_input_types[{}])".format(
                repr_type_as_syntax_safe_fn(type), i
            )
        )


def schema_with_input_field_of_type(input_field_type):
    BadInputObjectType = GraphQLInputObjectType(
        name="BadInputObject",
        fields={"badField": GraphQLInputObjectField(input_field_type)},
    )

    return GraphQLSchema(
        query=GraphQLObjectType(
            name="Query",
            fields={
                "f": GraphQLField(
                    type=GraphQLString,
                    args={"badArg": GraphQLArgument(BadInputObjectType)},
                )
            },
        )
    )


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_InputObjectFieldsMustHaveInputTypes:
    def accepts(self, type):
        assert schema_with_input_field_of_type(type)

    def rejects(self, type):
        with raises(AssertionError) as excinfo:
            schema_with_input_field_of_type(type)

        assert str(
            excinfo.value
        ) == "BadInputObject.badField field type must be Input Type but got: {}.".format(
            type
        )

    for i, type in enumerate(input_types):
        exec(
            "def test_accepts_an_input_type_as_an_input_field_type_{}(self):"
            " self.accepts(input_types[{}])".format(
                repr_type_as_syntax_safe_fn(type), i
            )
        )

    def test_rejects_an_empty_input_field_type(self):
        self.rejects(None)

    for i, type in enumerate(not_input_types):
        exec(
            "def test_rejects_non_input_type_as_an_input_field_type_{}(self):"
            " self.rejects(not_input_types[{}])".format(
                repr_type_as_syntax_safe_fn(type), i
            )
        )


types = with_modifiers(
    [
        GraphQLString,
        SomeScalarType,
        SomeObjectType,
        SomeUnionType,
        SomeInterfaceType,
        SomeEnumType,
        SomeInputObjectType,
    ]
)

not_types = [{}, str, None, object(), set(), (), []]


class TestTypeSystem_ListMustAcceptGraphQLTypes:
    def accepts(self, type):
        assert GraphQLList(type)

    def rejects(self, type):
        with raises(AssertionError) as excinfo:
            GraphQLList(type)

        assert str(
            excinfo.value
        ) == "Can only create List of a GraphQLType but got: {}.".format(type)

    for i, type in enumerate(types):
        exec(
            "def test_accepts_a_type_as_item_type_of_list_{}(self):"
            " self.accepts(types[{}])".format(repr_type_as_syntax_safe_fn(type), i)
        )

    for i, type in enumerate(not_types):
        exec(
            "def test_accepts_a_type_as_item_type_of_list_{}(self):"
            " self.rejects(not_types[{}])".format(repr_type_as_syntax_safe_fn(type), i)
        )


nullable_types = [
    GraphQLString,
    SomeScalarType,
    SomeObjectType,
    SomeUnionType,
    SomeInterfaceType,
    SomeEnumType,
    SomeInputObjectType,
    GraphQLList(GraphQLString),
    GraphQLList(GraphQLNonNull(GraphQLString)),
]

not_nullable_types = [GraphQLNonNull(GraphQLString), {}, str, None, []]


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_NonNullMustAcceptGraphQLTypes:
    def accepts(self, type):
        assert GraphQLNonNull(type)

    def rejects(self, type):
        with raises(AssertionError) as excinfo:
            GraphQLNonNull(type)

        assert str(
            excinfo.value
        ) == "Can only create NonNull of a Nullable GraphQLType but got: {}.".format(
            type
        )

    for i, type in enumerate(nullable_types):
        exec(
            "def test_accepts_a_type_as_nullable_type_of_not_null_{}(self):"
            " self.accepts(nullable_types[{}])".format(
                repr_type_as_syntax_safe_fn(type), i
            )
        )

    for i, type in enumerate(not_nullable_types):
        exec(
            "def test_rejects_a_non_type_as_nullable_type_of_non_null_{}(self):"
            " self.rejects(not_nullable_types[{}])".format(
                repr_type_as_syntax_safe_fn(type), i
            )
        )


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_ObjectsMustAdhereToInterfacesTheyImplement:
    def test_accepts_an_object_which_implements_an_interface(self):
        AnotherInterface = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields={
                "field": GraphQLField(
                    type=GraphQLString, args={"input": GraphQLArgument(GraphQLString)}
                )
            },
        )

        AnotherObject = GraphQLObjectType(
            name="AnotherObject",
            interfaces=[AnotherInterface],
            fields={
                "field": GraphQLField(
                    type=GraphQLString, args={"input": GraphQLArgument(GraphQLString)}
                )
            },
        )

        assert schema_with_field_type(AnotherObject)

    def test_accepts_an_object_which_implements_an_interface_along_with_more_fields(
        self
    ):
        AnotherInterface = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields={
                "field": GraphQLField(
                    type=GraphQLString, args={"input": GraphQLArgument(GraphQLString)}
                )
            },
        )

        AnotherObject = GraphQLObjectType(
            name="AnotherObject",
            interfaces=[AnotherInterface],
            fields={
                "field": GraphQLField(
                    type=GraphQLString, args={"input": GraphQLArgument(GraphQLString)}
                ),
                "anotherfield": GraphQLField(GraphQLString),
            },
        )

        assert schema_with_field_type(AnotherObject)

    def test_accepts_an_object_which_implements_an_interface_field_along_with_more_arguments(
        self
    ):
        AnotherInterface = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields={
                "field": GraphQLField(
                    type=GraphQLString, args={"input": GraphQLArgument(GraphQLString)}
                )
            },
        )

        AnotherObject = GraphQLObjectType(
            name="AnotherObject",
            interfaces=[AnotherInterface],
            fields={
                "field": GraphQLField(
                    type=GraphQLString,
                    args={
                        "input": GraphQLArgument(GraphQLString),
                        "anotherInput": GraphQLArgument(GraphQLString),
                    },
                )
            },
        )

        assert schema_with_field_type(AnotherObject)

    def test_rejects_an_object_which_implements_an_interface_field_along_with_additional_required_arguments(
        self
    ):
        AnotherInterface = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields={
                "field": GraphQLField(
                    type=GraphQLString, args={"input": GraphQLArgument(GraphQLString)}
                )
            },
        )

        AnotherObject = GraphQLObjectType(
            name="AnotherObject",
            interfaces=[AnotherInterface],
            fields={
                "field": GraphQLField(
                    type=GraphQLString,
                    args={
                        "input": GraphQLArgument(GraphQLString),
                        "anotherInput": GraphQLArgument(GraphQLNonNull(GraphQLString)),
                    },
                )
            },
        )

        with raises(AssertionError) as excinfo:
            schema_with_field_type(AnotherObject)

        assert (
            str(excinfo.value)
            == 'AnotherObject.field(anotherInput:) is of required type "String!" but '
            "is not also provided by the interface AnotherInterface.field."
        )

    def test_rejects_an_object_missing_an_interface_field(self):
        AnotherInterface = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields={
                "field": GraphQLField(
                    type=GraphQLString, args={"input": GraphQLArgument(GraphQLString)}
                )
            },
        )

        AnotherObject = GraphQLObjectType(
            name="AnotherObject",
            interfaces=[AnotherInterface],
            fields={"anotherfield": GraphQLField(GraphQLString)},
        )

        with raises(AssertionError) as excinfo:
            schema_with_field_type(AnotherObject)

        assert (
            str(excinfo.value)
            == '"AnotherInterface" expects field "field" but "AnotherObject" does not provide it.'
        )

    def test_rejects_an_object_with_an_incorrectly_typed_interface_field(self):
        AnotherInterface = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields={"field": GraphQLField(GraphQLString)},
        )
        AnotherObject = GraphQLObjectType(
            name="AnotherObject",
            interfaces=[AnotherInterface],
            fields={"field": GraphQLField(SomeScalarType)},
        )

        with raises(AssertionError) as excinfo:
            schema_with_field_type(AnotherObject)

        assert (
            str(excinfo.value) == 'AnotherInterface.field expects type "String" '
            'but AnotherObject.field provides type "SomeScalar".'
        )

    def test_rejects_an_object_missing_an_interface_argument(self):
        AnotherInterface = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields={
                "field": GraphQLField(
                    GraphQLString, args={"input": GraphQLArgument(GraphQLString)}
                )
            },
        )
        AnotherObject = GraphQLObjectType(
            name="AnotherObject",
            interfaces=[AnotherInterface],
            fields={"field": GraphQLField(GraphQLString)},
        )

        with raises(AssertionError) as excinfo:
            schema_with_field_type(AnotherObject)

        assert (
            str(excinfo.value) == 'AnotherInterface.field expects argument "input" '
            "but AnotherObject.field does not provide it."
        )

    def test_rejects_an_object_with_an_incorrectly_typed_interface_argument(self):
        AnotherInterface = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields={
                "field": GraphQLField(
                    GraphQLString, args={"input": GraphQLArgument(GraphQLString)}
                )
            },
        )
        AnotherObject = GraphQLObjectType(
            name="AnotherObject",
            interfaces=[AnotherInterface],
            fields={
                "field": GraphQLField(
                    GraphQLString, args={"input": GraphQLArgument(SomeScalarType)}
                )
            },
        )

        with raises(AssertionError) as excinfo:
            schema_with_field_type(AnotherObject)

        assert (
            str(excinfo.value)
            == 'AnotherInterface.field(input:) expects type "String" '
            'but AnotherObject.field(input:) provides type "SomeScalar".'
        )

    def test_rejects_an_object_with_an_incorrectly_typed_interface_field(self):
        AnotherInterface = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields={"field": GraphQLField(GraphQLString)},
        )
        AnotherObject = GraphQLObjectType(
            name="AnotherObject",
            interfaces=[AnotherInterface],
            fields={"field": GraphQLField(SomeScalarType)},
        )

        with raises(AssertionError) as excinfo:
            schema_with_field_type(AnotherObject)

        assert (
            str(excinfo.value) == 'AnotherInterface.field expects type "String" '
            'but AnotherObject.field provides type "SomeScalar".'
        )

    def test_rejects_an_object_with_a_differently_typed_Interface_field(self):
        TypeA = GraphQLObjectType(name="A", fields={"foo": GraphQLField(GraphQLString)})
        TypeB = GraphQLObjectType(name="B", fields={"foo": GraphQLField(GraphQLString)})
        AnotherInterface = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields={"field": GraphQLField(TypeA)},
        )
        AnotherObject = GraphQLObjectType(
            name="AnotherObject",
            interfaces=[AnotherInterface],
            fields={"field": GraphQLField(TypeB)},
        )

        with raises(AssertionError) as excinfo:
            schema_with_field_type(AnotherObject)

        assert (
            str(excinfo.value) == 'AnotherInterface.field expects type "A" but '
            'AnotherObject.field provides type "B".'
        )

    def test_accepts_an_object_with_a_subtyped_interface_field_interface(self):
        AnotherInterface = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields=lambda: {"field": GraphQLField(AnotherInterface)},
        )
        AnotherObject = GraphQLObjectType(
            name="AnotherObject",
            interfaces=[AnotherInterface],
            fields=lambda: {"field": GraphQLField(AnotherObject)},
        )

        assert schema_with_field_type(AnotherObject)

    def test_accepts_an_object_with_a_subtyped_interface_field_union(self):
        AnotherInterface = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields=lambda: {"field": GraphQLField(SomeUnionType)},
        )
        AnotherObject = GraphQLObjectType(
            name="AnotherObject",
            interfaces=[AnotherInterface],
            fields=lambda: {"field": GraphQLField(SomeObjectType)},
        )

        assert schema_with_field_type(AnotherObject)

    def test_accepts_an_object_with_an_equivalently_modified_interface_field_type(self):
        AnotherInterface = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields={"field": GraphQLField(GraphQLNonNull(GraphQLList(GraphQLString)))},
        )
        AnotherObject = GraphQLObjectType(
            name="AnotherObject",
            interfaces=[AnotherInterface],
            fields={"field": GraphQLField(GraphQLNonNull(GraphQLList(GraphQLString)))},
        )

        assert schema_with_field_type(AnotherObject)

    def test_rejects_an_object_with_a_non_list_interface_field_list_type(self):
        AnotherInterface = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields={"field": GraphQLField(GraphQLList(GraphQLString))},
        )
        AnotherObject = GraphQLObjectType(
            name="AnotherObject",
            interfaces=[AnotherInterface],
            fields={"field": GraphQLField(GraphQLString)},
        )

        with raises(AssertionError) as excinfo:
            schema_with_field_type(AnotherObject)

        assert (
            str(excinfo.value) == 'AnotherInterface.field expects type "[String]" '
            'but AnotherObject.field provides type "String".'
        )

    def test_rejects_a_object_with_a_list_interface_field_non_list_type(self):
        AnotherInterface = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields={"field": GraphQLField(GraphQLString)},
        )
        AnotherObject = GraphQLObjectType(
            name="AnotherObject",
            interfaces=[AnotherInterface],
            fields={"field": GraphQLField(GraphQLList(GraphQLString))},
        )

        with raises(AssertionError) as excinfo:
            schema_with_field_type(AnotherObject)

        assert (
            str(excinfo.value) == 'AnotherInterface.field expects type "String" '
            'but AnotherObject.field provides type "[String]".'
        )

    def test_accepts_an_object_with_a_subset_non_null_interface_field_type(self):
        AnotherInterface = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields={"field": GraphQLField(GraphQLString)},
        )
        AnotherObject = GraphQLObjectType(
            name="AnotherObject",
            interfaces=[AnotherInterface],
            fields={"field": GraphQLField(GraphQLNonNull(GraphQLString))},
        )

        assert schema_with_field_type(AnotherObject)

    def test_rejects_a_object_with_a_superset_nullable_interface_field_type(self):
        AnotherInterface = GraphQLInterfaceType(
            name="AnotherInterface",
            resolve_type=_none,
            fields={"field": GraphQLField(GraphQLNonNull(GraphQLString))},
        )
        AnotherObject = GraphQLObjectType(
            name="AnotherObject",
            interfaces=[AnotherInterface],
            fields={"field": GraphQLField(GraphQLString)},
        )

        with raises(AssertionError) as excinfo:
            schema_with_field_type(AnotherObject)

        assert (
            str(excinfo.value) == 'AnotherInterface.field expects type "String!" but '
            'AnotherObject.field provides type "String".'
        )
