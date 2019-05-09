from collections import OrderedDict
from py.test import raises

from graphql.type import (
    GraphQLArgument,
    GraphQLBoolean,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLInputObjectField,
    GraphQLInputObjectType,
    GraphQLInt,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
    GraphQLUnionType,
)
from graphql.type.definition import is_input_type, is_output_type

BlogImage = GraphQLObjectType(
    "Image",
    {
        "url": GraphQLField(GraphQLString),
        "width": GraphQLField(GraphQLInt),
        "height": GraphQLField(GraphQLInt),
    },
)

BlogAuthor = GraphQLObjectType(
    "Author",
    lambda: {
        "id": GraphQLField(GraphQLString),
        "name": GraphQLField(GraphQLString),
        "pic": GraphQLField(
            BlogImage,
            args={
                "width": GraphQLArgument(GraphQLInt),
                "height": GraphQLArgument(GraphQLInt),
            },
        ),
        "recentArticle": GraphQLField(BlogArticle),
    },
)

BlogArticle = GraphQLObjectType(
    "Article",
    lambda: {
        "id": GraphQLField(GraphQLString),
        "isPublished": GraphQLField(GraphQLBoolean),
        "author": GraphQLField(BlogAuthor),
        "title": GraphQLField(GraphQLString),
        "body": GraphQLField(GraphQLString),
    },
)

BlogQuery = GraphQLObjectType(
    "Query",
    {
        "article": GraphQLField(
            BlogArticle, args={"id": GraphQLArgument(GraphQLString)}
        ),
        "feed": GraphQLField(GraphQLList(BlogArticle)),
    },
)

BlogMutation = GraphQLObjectType(
    "Mutation", {"writeArticle": GraphQLField(BlogArticle)}
)

BlogSubscription = GraphQLObjectType(
    "Subscription",
    {
        "articleSubscribe": GraphQLField(
            args={"id": GraphQLArgument(GraphQLString)}, type=BlogArticle
        )
    },
)

ObjectType = GraphQLObjectType("Object", {})
InterfaceType = GraphQLInterfaceType("Interface")
UnionType = GraphQLUnionType("Union", [ObjectType], resolve_type=lambda: None)
EnumType = GraphQLEnumType("Enum", {"foo": GraphQLEnumValue()})
InputObjectType = GraphQLInputObjectType("InputObject", {})


def test_defines_a_query_only_schema():
    BlogSchema = GraphQLSchema(BlogQuery)

    assert BlogSchema.get_query_type() == BlogQuery

    article_field = BlogQuery.fields["article"]
    assert article_field.type == BlogArticle
    assert article_field.type.name == "Article"
    # assert article_field.name == 'article'

    article_field_type = article_field.type
    assert isinstance(article_field_type, GraphQLObjectType)

    title_field = article_field_type.fields["title"]
    # assert title_field.name == 'title'
    assert title_field.type == GraphQLString
    assert title_field.type.name == "String"

    author_field = article_field_type.fields["author"]
    author_field_type = author_field.type
    assert isinstance(author_field_type, GraphQLObjectType)
    recent_article_field = author_field_type.fields["recentArticle"]

    assert recent_article_field.type == BlogArticle

    feed_field = BlogQuery.fields["feed"]
    assert feed_field.type.of_type == BlogArticle
    # assert feed_field.name == 'feed'


def test_defines_a_mutation_schema():
    BlogSchema = GraphQLSchema(BlogQuery, BlogMutation)

    assert BlogSchema.get_mutation_type() == BlogMutation

    write_mutation = BlogMutation.fields["writeArticle"]
    assert write_mutation.type == BlogArticle
    assert write_mutation.type.name == "Article"
    # assert write_mutation.name == 'writeArticle'


def test_defines_a_subscription_schema():
    BlogSchema = GraphQLSchema(query=BlogQuery, subscription=BlogSubscription)

    assert BlogSchema.get_subscription_type() == BlogSubscription

    subscription = BlogSubscription.fields["articleSubscribe"]
    assert subscription.type == BlogArticle
    assert subscription.type.name == "Article"
    # assert subscription.name == 'articleSubscribe'


def test_defines_an_enum_type_with_deprecated_value():
    EnumTypeWithDeprecatedValue = GraphQLEnumType(
        "EnumWithDeprecatedValue",
        {"foo": GraphQLEnumValue(deprecation_reason="Just because")},
    )
    value = EnumTypeWithDeprecatedValue.get_values()[0]
    assert value.name == "foo"
    assert value.description is None
    assert value.is_deprecated is True
    assert value.deprecation_reason == "Just because"
    assert value.value == "foo"


def test_defines_an_enum_type_with_a_value_of_none():
    EnumTypeWithNoneValue = GraphQLEnumType(
        "EnumWithNullishValue", {"NULL": GraphQLEnumValue(None)}
    )

    value = EnumTypeWithNoneValue.get_values()[0]
    assert value.name == "NULL"
    assert value.description is None
    assert value.is_deprecated is False
    assert value.deprecation_reason is None
    assert value.value is None


def test_defines_an_object_type_with_deprecated_field():
    TypeWithDeprecatedField = GraphQLObjectType(
        "foo",
        fields={
            "bar": GraphQLField(
                type=GraphQLString, deprecation_reason="A terrible reason"
            )
        },
    )

    field = TypeWithDeprecatedField.fields["bar"]
    assert field.type == GraphQLString
    assert field.description is None
    assert field.deprecation_reason == "A terrible reason"
    assert field.is_deprecated is True
    # assert field.name == 'bar'
    assert field.args == OrderedDict()


def test_includes_nested_input_objects_in_the_map():
    NestedInputObject = GraphQLInputObjectType(
        name="NestedInputObject",
        fields={"value": GraphQLInputObjectField(GraphQLString)},
    )

    SomeInputObject = GraphQLInputObjectType(
        name="SomeInputObject",
        fields={"nested": GraphQLInputObjectField(NestedInputObject)},
    )

    SomeMutation = GraphQLObjectType(
        name="SomeMutation",
        fields={
            "mutateSomething": GraphQLField(
                type=BlogArticle, args={"input": GraphQLArgument(SomeInputObject)}
            )
        },
    )
    SomeSubscription = GraphQLObjectType(
        name="SomeSubscription",
        fields={
            "subscribeToSomething": GraphQLField(
                type=BlogArticle, args={"input": GraphQLArgument(SomeInputObject)}
            )
        },
    )

    schema = GraphQLSchema(
        query=BlogQuery, mutation=SomeMutation, subscription=SomeSubscription
    )

    assert schema.get_type_map()["NestedInputObject"] is NestedInputObject


def test_includes_interface_possible_types_in_the_type_map():
    SomeInterface = GraphQLInterfaceType(
        "SomeInterface", fields={"f": GraphQLField(GraphQLInt)}
    )
    SomeSubtype = GraphQLObjectType(
        name="SomeSubtype",
        fields={"f": GraphQLField(GraphQLInt)},
        interfaces=[SomeInterface],
        is_type_of=lambda: None,
    )
    schema = GraphQLSchema(
        query=GraphQLObjectType(
            name="Query", fields={"iface": GraphQLField(SomeInterface)}
        ),
        types=[SomeSubtype],
    )
    assert schema.get_type_map()["SomeSubtype"] == SomeSubtype


def test_includes_interfaces_thunk_subtypes_in_the_type_map():
    SomeInterface = GraphQLInterfaceType(
        name="SomeInterface", fields={"f": GraphQLField(GraphQLInt)}
    )

    SomeSubtype = GraphQLObjectType(
        name="SomeSubtype",
        fields={"f": GraphQLField(GraphQLInt)},
        interfaces=lambda: [SomeInterface],
        is_type_of=lambda: True,
    )

    schema = GraphQLSchema(
        query=GraphQLObjectType(
            name="Query", fields={"iface": GraphQLField(SomeInterface)}
        ),
        types=[SomeSubtype],
    )

    assert schema.get_type_map()["SomeSubtype"] is SomeSubtype


def test_stringifies_simple_types():
    assert str(GraphQLInt) == "Int"
    assert str(BlogArticle) == "Article"
    assert str(InterfaceType) == "Interface"
    assert str(UnionType) == "Union"
    assert str(EnumType) == "Enum"
    assert str(InputObjectType) == "InputObject"
    assert str(GraphQLNonNull(GraphQLInt)) == "Int!"
    assert str(GraphQLList(GraphQLInt)) == "[Int]"
    assert str(GraphQLNonNull(GraphQLList(GraphQLInt))) == "[Int]!"
    assert str(GraphQLList(GraphQLNonNull(GraphQLInt))) == "[Int!]"
    assert str(GraphQLList(GraphQLList(GraphQLInt))) == "[[Int]]"


def test_identifies_input_types():
    expected = (
        (GraphQLInt, True),
        (ObjectType, False),
        (InterfaceType, False),
        (UnionType, False),
        (EnumType, True),
        (InputObjectType, True),
    )

    for type, answer in expected:
        assert is_input_type(type) == answer
        assert is_input_type(GraphQLList(type)) == answer
        assert is_input_type(GraphQLNonNull(type)) == answer


def test_identifies_output_types():
    expected = (
        (GraphQLInt, True),
        (ObjectType, True),
        (InterfaceType, True),
        (UnionType, True),
        (EnumType, True),
        (InputObjectType, False),
    )

    for type, answer in expected:
        assert is_output_type(type) == answer
        assert is_output_type(GraphQLList(type)) == answer
        assert is_output_type(GraphQLNonNull(type)) == answer


def test_prohibits_nesting_nonnull_inside_nonnull():
    with raises(Exception) as excinfo:
        GraphQLNonNull(GraphQLNonNull(GraphQLInt))

    assert "Can only create NonNull of a Nullable GraphQLType but got: Int!." in str(
        excinfo.value
    )


def test_prohibits_putting_non_object_types_in_unions():
    bad_union_types = [
        GraphQLInt,
        GraphQLNonNull(GraphQLInt),
        GraphQLList(GraphQLInt),
        InterfaceType,
        UnionType,
        EnumType,
        InputObjectType,
    ]
    for x in bad_union_types:
        with raises(Exception) as excinfo:
            GraphQLSchema(
                GraphQLObjectType(
                    "Root",
                    fields={"union": GraphQLField(GraphQLUnionType("BadUnion", [x]))},
                )
            )

        assert "BadUnion may only contain Object types, it cannot contain: " + str(
            x
        ) + "." == str(excinfo.value)


def test_does_not_mutate_passed_field_definitions():
    fields = {
        "field1": GraphQLField(GraphQLString),
        "field2": GraphQLField(
            GraphQLString, args={"id": GraphQLArgument(GraphQLString)}
        ),
    }

    TestObject1 = GraphQLObjectType(name="Test1", fields=fields)
    TestObject2 = GraphQLObjectType(name="Test1", fields=fields)

    assert TestObject1.fields == TestObject2.fields
    assert fields == {
        "field1": GraphQLField(GraphQLString),
        "field2": GraphQLField(
            GraphQLString, args={"id": GraphQLArgument(GraphQLString)}
        ),
    }

    input_fields = {
        "field1": GraphQLInputObjectField(GraphQLString),
        "field2": GraphQLInputObjectField(GraphQLString),
    }

    TestInputObject1 = GraphQLInputObjectType(name="Test1", fields=input_fields)
    TestInputObject2 = GraphQLInputObjectType(name="Test2", fields=input_fields)

    assert TestInputObject1.fields == TestInputObject2.fields

    assert input_fields == {
        "field1": GraphQLInputObjectField(GraphQLString),
        "field2": GraphQLInputObjectField(GraphQLString),
    }


# def test_sorts_fields_and_argument_keys_if_not_using_ordered_dict():
#     fields = {
#         'b': GraphQLField(GraphQLString),
#         'c': GraphQLField(GraphQLString),
#         'a': GraphQLField(GraphQLString),
#         'd': GraphQLField(GraphQLString, args={
#             'q': GraphQLArgument(GraphQLString),
#             'x': GraphQLArgument(GraphQLString),
#             'v': GraphQLArgument(GraphQLString),
#             'a': GraphQLArgument(GraphQLString),
#             'n': GraphQLArgument(GraphQLString)
#         })
#     }

#     test_object = GraphQLObjectType(name='Test', fields=fields)
#     ordered_fields = test_object.fields
#     assert list(ordered_fields.keys()) == ['a', 'b', 'c', 'd']
#     field_with_args = test_object.fields.get('d')
#     assert list(field_with_args.args.keys()) == ['a', 'n', 'q', 'v', 'x']


def test_does_not_sort_fields_and_argument_keys_when_using_ordered_dict():
    fields = OrderedDict(
        [
            ("b", GraphQLField(GraphQLString)),
            ("c", GraphQLField(GraphQLString)),
            ("a", GraphQLField(GraphQLString)),
            (
                "d",
                GraphQLField(
                    GraphQLString,
                    args=OrderedDict(
                        [
                            ("q", GraphQLArgument(GraphQLString)),
                            ("x", GraphQLArgument(GraphQLString)),
                            ("v", GraphQLArgument(GraphQLString)),
                            ("a", GraphQLArgument(GraphQLString)),
                            ("n", GraphQLArgument(GraphQLString)),
                        ]
                    ),
                ),
            ),
        ]
    )

    test_object = GraphQLObjectType(name="Test", fields=fields)
    ordered_fields = test_object.fields
    assert list(ordered_fields.keys()) == ["b", "c", "a", "d"]
    field_with_args = test_object.fields.get("d")
    assert list(field_with_args.args.keys()) == ["q", "x", "v", "a", "n"]
