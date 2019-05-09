

from ..argument import Argument
from ..enum import Enum
from ..field import Field
from ..inputfield import InputField
from ..inputobjecttype import InputObjectType
from ..interface import Interface
from ..objecttype import ObjectType
from ..scalars import Boolean, Int, String
from ..schema import Schema
from ..structures import List, NonNull
from ..union import Union


class Image(ObjectType):
    url = String()
    width = Int()
    height = Int()


class Author(ObjectType):
    id = String()
    name = String()
    pic = Field(Image, width=Int(), height=Int())
    recent_article = Field(lambda: Article)


class Article(ObjectType):
    id = String()
    is_published = Boolean()
    author = Field(Author)
    title = String()
    body = String()


class Query(ObjectType):
    article = Field(Article, id=String())
    feed = List(Article)


class Mutation(ObjectType):
    write_article = Field(Article)


class Subscription(ObjectType):
    article_subscribe = Field(Article, id=String())


class MyObjectType(ObjectType):
    pass


class MyInterface(Interface):
    pass


class MyUnion(Union):
    class Meta:
        types = (Article,)


class MyEnum(Enum):
    foo = "foo"


class MyInputObjectType(InputObjectType):
    pass


def test_defines_a_query_only_schema():
    blog_schema = Schema(Query)

    assert blog_schema.get_query_type().graphene_type == Query

    article_field = Query._meta.fields["article"]
    assert article_field.type == Article
    assert article_field.type._meta.name == "Article"

    article_field_type = article_field.type
    assert issubclass(article_field_type, ObjectType)

    title_field = article_field_type._meta.fields["title"]
    assert title_field.type == String

    author_field = article_field_type._meta.fields["author"]
    author_field_type = author_field.type
    assert issubclass(author_field_type, ObjectType)
    recent_article_field = author_field_type._meta.fields["recent_article"]

    assert recent_article_field.type == Article

    feed_field = Query._meta.fields["feed"]
    assert feed_field.type.of_type == Article


def test_defines_a_mutation_schema():
    blog_schema = Schema(Query, mutation=Mutation)

    assert blog_schema.get_mutation_type().graphene_type == Mutation

    write_mutation = Mutation._meta.fields["write_article"]
    assert write_mutation.type == Article
    assert write_mutation.type._meta.name == "Article"


def test_defines_a_subscription_schema():
    blog_schema = Schema(Query, subscription=Subscription)

    assert blog_schema.get_subscription_type().graphene_type == Subscription

    subscription = Subscription._meta.fields["article_subscribe"]
    assert subscription.type == Article
    assert subscription.type._meta.name == "Article"


def test_includes_nested_input_objects_in_the_map():
    class NestedInputObject(InputObjectType):
        value = String()

    class SomeInputObject(InputObjectType):
        nested = InputField(NestedInputObject)

    class SomeMutation(Mutation):
        mutate_something = Field(Article, input=Argument(SomeInputObject))

    class SomeSubscription(Mutation):
        subscribe_to_something = Field(Article, input=Argument(SomeInputObject))

    schema = Schema(query=Query, mutation=SomeMutation, subscription=SomeSubscription)

    assert schema.get_type_map()["NestedInputObject"].graphene_type is NestedInputObject


def test_includes_interfaces_thunk_subtypes_in_the_type_map():
    class SomeInterface(Interface):
        f = Int()

    class SomeSubtype(ObjectType):
        class Meta:
            interfaces = (SomeInterface,)

    class Query(ObjectType):
        iface = Field(lambda: SomeInterface)

    schema = Schema(query=Query, types=[SomeSubtype])

    assert schema.get_type_map()["SomeSubtype"].graphene_type is SomeSubtype


def test_includes_types_in_union():
    class SomeType(ObjectType):
        a = String()

    class OtherType(ObjectType):
        b = String()

    class MyUnion(Union):
        class Meta:
            types = (SomeType, OtherType)

    class Query(ObjectType):
        union = Field(MyUnion)

    schema = Schema(query=Query)

    assert schema.get_type_map()["OtherType"].graphene_type is OtherType
    assert schema.get_type_map()["SomeType"].graphene_type is SomeType


def test_maps_enum():
    class SomeType(ObjectType):
        a = String()

    class OtherType(ObjectType):
        b = String()

    class MyUnion(Union):
        class Meta:
            types = (SomeType, OtherType)

    class Query(ObjectType):
        union = Field(MyUnion)

    schema = Schema(query=Query)

    assert schema.get_type_map()["OtherType"].graphene_type is OtherType
    assert schema.get_type_map()["SomeType"].graphene_type is SomeType


def test_includes_interfaces_subtypes_in_the_type_map():
    class SomeInterface(Interface):
        f = Int()

    class SomeSubtype(ObjectType):
        class Meta:
            interfaces = (SomeInterface,)

    class Query(ObjectType):
        iface = Field(SomeInterface)

    schema = Schema(query=Query, types=[SomeSubtype])

    assert schema.get_type_map()["SomeSubtype"].graphene_type is SomeSubtype


def test_stringifies_simple_types():
    assert str(Int) == "Int"
    assert str(Article) == "Article"
    assert str(MyInterface) == "MyInterface"
    assert str(MyUnion) == "MyUnion"
    assert str(MyEnum) == "MyEnum"
    assert str(MyInputObjectType) == "MyInputObjectType"
    assert str(NonNull(Int)) == "Int!"
    assert str(List(Int)) == "[Int]"
    assert str(NonNull(List(Int))) == "[Int]!"
    assert str(List(NonNull(Int))) == "[Int!]"
    assert str(List(List(Int))) == "[[Int]]"


# def test_identifies_input_types():
#     expected = (
#         (GraphQLInt, True),
#         (ObjectType, False),
#         (InterfaceType, False),
#         (UnionType, False),
#         (EnumType, True),
#         (InputObjectType, True)
#     )

#     for type, answer in expected:
#         assert is_input_type(type) == answer
#         assert is_input_type(GraphQLList(type)) == answer
#         assert is_input_type(GraphQLNonNull(type)) == answer


# def test_identifies_output_types():
#     expected = (
#         (GraphQLInt, True),
#         (ObjectType, True),
#         (InterfaceType, True),
#         (UnionType, True),
#         (EnumType, True),
#         (InputObjectType, False)
#     )

#     for type, answer in expected:
#         assert is_output_type(type) == answer
#         assert is_output_type(GraphQLList(type)) == answer
#         assert is_output_type(GraphQLNonNull(type)) == answer


# def test_prohibits_nesting_nonnull_inside_nonnull():
#     with raises(Exception) as excinfo:
#         GraphQLNonNull(GraphQLNonNull(GraphQLInt))

#     assert 'Can only create NonNull of a Nullable GraphQLType but got: Int!.' in str(excinfo.value)


# def test_prohibits_putting_non_object_types_in_unions():
#     bad_union_types = [
#         GraphQLInt,
#         GraphQLNonNull(GraphQLInt),
#         GraphQLList(GraphQLInt),
#         InterfaceType,
#         UnionType,
#         EnumType,
#         InputObjectType
#     ]
#     for x in bad_union_types:
#         with raises(Exception) as excinfo:
#             GraphQLSchema(
#                 GraphQLObjectType(
#                     'Root',
#                     fields={
#                         'union': GraphQLField(GraphQLUnionType('BadUnion', [x]))
#                     }
#                 )
#             )

#         assert 'BadUnion may only contain Object types, it cannot contain: ' + str(x) + '.' \
#                == str(excinfo.value)


def test_does_not_mutate_passed_field_definitions():
    class CommonFields(object):
        field1 = String()
        field2 = String(id=String())

    class TestObject1(CommonFields, ObjectType):
        pass

    class TestObject2(CommonFields, ObjectType):
        pass

    assert TestObject1._meta.fields == TestObject2._meta.fields

    class CommonFields(object):
        field1 = String()
        field2 = String()

    class TestInputObject1(CommonFields, InputObjectType):
        pass

    class TestInputObject2(CommonFields, InputObjectType):
        pass

    assert TestInputObject1._meta.fields == TestInputObject2._meta.fields
