from collections import OrderedDict
from rx import Observable
from graphql import graphql
from graphql.type import (
    GraphQLArgument,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLInt,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
)

ColorType = GraphQLEnumType(
    name="Color",
    values=OrderedDict(
        [
            ("RED", GraphQLEnumValue(0)),
            ("GREEN", GraphQLEnumValue(1)),
            ("BLUE", GraphQLEnumValue(2)),
        ]
    ),
)


def get_first(args, *keys):
    for key in keys:
        if key in args:
            return args[key]

    return None


QueryType = GraphQLObjectType(
    name="Query",
    fields={
        "colorEnum": GraphQLField(
            type=ColorType,
            args={
                "fromEnum": GraphQLArgument(ColorType),
                "fromInt": GraphQLArgument(GraphQLInt),
                "fromString": GraphQLArgument(GraphQLString),
            },
            resolver=lambda value, info, **args: get_first(
                args, "fromInt", "fromString", "fromEnum"
            ),
        ),
        "colorInt": GraphQLField(
            type=GraphQLInt,
            args={
                "fromEnum": GraphQLArgument(ColorType),
                "fromInt": GraphQLArgument(GraphQLInt),
            },
            resolver=lambda value, info, **args: get_first(args, "fromInt", "fromEnum"),
        ),
    },
)

MutationType = GraphQLObjectType(
    name="Mutation",
    fields={
        "favoriteEnum": GraphQLField(
            type=ColorType,
            args={"color": GraphQLArgument(ColorType)},
            resolver=lambda value, info, **args: args.get("color"),
        )
    },
)

SubscriptionType = GraphQLObjectType(
    name="Subscription",
    fields={
        "subscribeToEnum": GraphQLField(
            type=ColorType,
            args={"color": GraphQLArgument(ColorType)},
            resolver=lambda value, info, **args: Observable.from_([args.get("color")]),
        )
    },
)

Schema = GraphQLSchema(
    query=QueryType, mutation=MutationType, subscription=SubscriptionType
)


def test_accepts_enum_literals_as_input():
    result = graphql(Schema, "{ colorInt(fromEnum: GREEN) }")
    assert not result.errors
    assert result.data == {"colorInt": 1}


def test_enum_may_be_output_type():
    result = graphql(Schema, "{ colorEnum(fromInt: 1) }")
    assert not result.errors
    assert result.data == {"colorEnum": "GREEN"}


def test_enum_may_be_both_input_and_output_type():
    result = graphql(Schema, "{ colorEnum(fromEnum: GREEN) }")

    assert not result.errors
    assert result.data == {"colorEnum": "GREEN"}


def test_does_not_accept_string_literals():
    result = graphql(Schema, '{ colorEnum(fromEnum: "GREEN") }')
    assert not result.data
    assert (
        result.errors[0].message == 'Argument "fromEnum" has invalid value "GREEN".\n'
        'Expected type "Color", found "GREEN".'
    )


def test_does_not_accept_values_not_in_the_enum():
    result = graphql(Schema, "{ colorEnum(fromEnum: GREENISH) }")
    assert not result.data
    assert (
        result.errors[0].message == 'Argument "fromEnum" has invalid value GREENISH.\n'
        'Expected type "Color", found GREENISH.'
    )


def test_does_not_accept_values_with_incorrect_casing():
    result = graphql(Schema, "{ colorEnum(fromEnum: green) }")
    assert not result.data
    assert (
        result.errors[0].message == 'Argument "fromEnum" has invalid value green.\n'
        'Expected type "Color", found green.'
    )


def test_does_not_accept_incorrect_internal_value():
    result = graphql(Schema, '{ colorEnum(fromString: "GREEN") }')
    assert result.data == {"colorEnum": None}
    assert (
        result.errors[0].message == 'Expected a value of type "Color" '
        "but received: GREEN"
    )


def test_does_not_accept_internal_value_in_place_of_enum_literal():
    result = graphql(Schema, "{ colorEnum(fromEnum: 1) }")
    assert not result.data
    assert (
        result.errors[0].message == 'Argument "fromEnum" has invalid value 1.\n'
        'Expected type "Color", found 1.'
    )


def test_does_not_accept_enum_literal_in_place_of_int():
    result = graphql(Schema, "{ colorEnum(fromInt: GREEN) }")
    assert not result.data
    assert (
        result.errors[0].message == 'Argument "fromInt" has invalid value GREEN.\n'
        'Expected type "Int", found GREEN.'
    )


def test_accepts_json_string_as_enum_variable():
    result = graphql(
        Schema,
        "query test($color: Color!) { colorEnum(fromEnum: $color) }",
        variable_values={"color": "BLUE"},
    )
    assert not result.errors
    assert result.data == {"colorEnum": "BLUE"}


def test_accepts_enum_literals_as_input_arguments_to_mutations():
    result = graphql(
        Schema,
        "mutation x($color: Color!) { favoriteEnum(color: $color) }",
        variable_values={"color": "GREEN"},
    )
    assert not result.errors
    assert result.data == {"favoriteEnum": "GREEN"}


def test_accepts_enum_literals_as_input_arguments_to_subscriptions():
    result = graphql(
        Schema,
        "subscription x($color: Color!) { subscribeToEnum(color: $color) }",
        variable_values={"color": "GREEN"},
        allow_subscriptions=True,
    )
    assert isinstance(result, Observable)
    l = []
    result.subscribe(l.append)
    result = l[0]
    assert not result.errors
    assert result.data == {"subscribeToEnum": "GREEN"}


def test_does_not_accept_internal_value_as_enum_variable():
    result = graphql(
        Schema,
        "query test($color: Color!) { colorEnum(fromEnum: $color) }",
        variable_values={"color": 2},
    )
    assert not result.data
    assert (
        result.errors[0].message == 'Variable "$color" got invalid value 2.\n'
        'Expected type "Color", found 2.'
    )


def test_does_not_accept_string_variables_as_enum_input():
    result = graphql(
        Schema,
        "query test($color: String!) { colorEnum(fromEnum: $color) }",
        variable_values={"color": "BLUE"},
    )
    assert not result.data
    assert (
        result.errors[0].message
        == 'Variable "color" of type "String!" used in position expecting type "Color".'
    )


def test_does_not_accept_internal_value_as_enum_input():
    result = graphql(
        Schema,
        "query test($color: Int!) { colorEnum(fromEnum: $color) }",
        variable_values={"color": 2},
    )
    assert not result.data
    assert (
        result.errors[0].message
        == 'Variable "color" of type "Int!" used in position expecting type "Color".'
    )


def test_enum_value_may_have_an_internal_value_of_0():
    result = graphql(Schema, "{ colorEnum(fromEnum: RED) colorInt(fromEnum: RED) }")
    assert not result.errors
    assert result.data == {"colorEnum": "RED", "colorInt": 0}


def test_enum_inputs_may_be_nullable():
    result = graphql(Schema, "{ colorEnum colorInt }")
    assert not result.errors
    assert result.data == {"colorEnum": None, "colorInt": None}


def test_presents_a_get_values_api():
    values = ColorType.get_values()
    assert len(values) == 3
    assert values[0].name == "RED"
    assert values[0].value == 0
    assert values[1].name == "GREEN"
    assert values[1].value == 1
    assert values[2].name == "BLUE"
    assert values[2].value == 2


def test_presents_a_get_value_api():
    oneValue = ColorType.get_value("RED")
    assert oneValue.name == "RED"
    assert oneValue.value == 0

    badUsage = ColorType.get_value(0)
    assert badUsage is None


def test_sorts_values_if_not_using_ordered_dict():
    enum = GraphQLEnumType(
        name="Test",
        values={
            "c": GraphQLEnumValue(),
            "b": GraphQLEnumValue(),
            "a": GraphQLEnumValue(),
            "d": GraphQLEnumValue(),
        },
    )

    assert [v.name for v in enum.values] == ["a", "b", "c", "d"]


def test_does_not_sort_values_when_using_ordered_dict():
    enum = GraphQLEnumType(
        name="Test",
        values=OrderedDict(
            [
                ("c", GraphQLEnumValue()),
                ("b", GraphQLEnumValue()),
                ("a", GraphQLEnumValue()),
                ("d", GraphQLEnumValue()),
            ]
        ),
    )

    assert [v.name for v in enum.values] == ["c", "b", "a", "d"]
