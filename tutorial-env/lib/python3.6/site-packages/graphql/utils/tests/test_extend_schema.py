from collections import OrderedDict

from pytest import raises

from graphql import parse
from graphql.execution import execute
from graphql.type import (
    GraphQLArgument,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLID,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
    GraphQLUnionType,
)
from graphql.utils.extend_schema import extend_schema
from graphql.utils.schema_printer import print_schema

# Test schema.
SomeInterfaceType = GraphQLInterfaceType(
    name="SomeInterface",
    resolve_type=lambda: FooType,
    fields=lambda: OrderedDict(
        [
            ("name", GraphQLField(GraphQLString)),
            ("some", GraphQLField(SomeInterfaceType)),
        ]
    ),
)


FooType = GraphQLObjectType(
    name="Foo",
    interfaces=[SomeInterfaceType],
    fields=lambda: OrderedDict(
        [
            ("name", GraphQLField(GraphQLString)),
            ("some", GraphQLField(SomeInterfaceType)),
            ("tree", GraphQLField(GraphQLNonNull(GraphQLList(FooType)))),
        ]
    ),
)

BarType = GraphQLObjectType(
    name="Bar",
    interfaces=[SomeInterfaceType],
    fields=lambda: OrderedDict(
        [
            ("name", GraphQLField(GraphQLString)),
            ("some", GraphQLField(SomeInterfaceType)),
            ("foo", GraphQLField(FooType)),
        ]
    ),
)

BizType = GraphQLObjectType(
    name="Biz", fields=lambda: OrderedDict([("fizz", GraphQLField(GraphQLString))])
)

SomeUnionType = GraphQLUnionType(
    name="SomeUnion", resolve_type=lambda: FooType, types=[FooType, BizType]
)

SomeEnumType = GraphQLEnumType(
    name="SomeEnum",
    values=OrderedDict([("ONE", GraphQLEnumValue(1)), ("TWO", GraphQLEnumValue(2))]),
)

test_schema = GraphQLSchema(
    query=GraphQLObjectType(
        name="Query",
        fields=lambda: OrderedDict(
            [
                ("foo", GraphQLField(FooType)),
                ("someUnion", GraphQLField(SomeUnionType)),
                ("someEnum", GraphQLField(SomeEnumType)),
                (
                    "someInterface",
                    GraphQLField(
                        SomeInterfaceType,
                        args={"id": GraphQLArgument(GraphQLNonNull(GraphQLID))},
                    ),
                ),
            ]
        ),
    ),
    types=[FooType, BarType],
)


def test_returns_original_schema_if_no_type_definitions():
    ast = parse("{ field }")
    extended_schema = extend_schema(test_schema, ast)
    assert extended_schema == test_schema


def test_extends_without_altering_original_schema():
    ast = parse(
        """
      extend type Query {
        newField: String
      }
    """
    )
    original_print = print_schema(test_schema)
    extended_schema = extend_schema(test_schema, ast)
    assert extend_schema != test_schema
    assert print_schema(test_schema) == original_print
    assert "newField" in print_schema(extended_schema)
    assert "newField" not in print_schema(test_schema)


def test_cannot_be_used_for_execution():
    ast = parse(
        """
      extend type Query {
        newField: String
      }
    """
    )
    extended_schema = extend_schema(test_schema, ast)
    clientQuery = parse("{ newField }")

    result = execute(extended_schema, clientQuery, object())
    assert result.data["newField"] is None
    assert str(result.errors[0]) == "Client Schema cannot be used for execution."


def test_extends_objects_by_adding_new_fields():
    ast = parse(
        """
      extend type Foo {
        newField: String
      }
    """
    )
    original_print = print_schema(test_schema)
    extended_schema = extend_schema(test_schema, ast)
    assert extended_schema != test_schema
    assert print_schema(test_schema) == original_print
    # print original_print
    assert (
        print_schema(extended_schema)
        == """schema {
  query: Query
}

type Bar implements SomeInterface {
  name: String
  some: SomeInterface
  foo: Foo
}

type Biz {
  fizz: String
}

type Foo implements SomeInterface {
  name: String
  some: SomeInterface
  tree: [Foo]!
  newField: String
}

type Query {
  foo: Foo
  someUnion: SomeUnion
  someEnum: SomeEnum
  someInterface(id: ID!): SomeInterface
}

enum SomeEnum {
  ONE
  TWO
}

interface SomeInterface {
  name: String
  some: SomeInterface
}

union SomeUnion = Foo | Biz
"""
    )


def test_extends_objects_by_adding_new_unused_types():
    ast = parse(
        """
      type Unused {
        someField: String
      }
    """
    )
    original_print = print_schema(test_schema)
    extended_schema = extend_schema(test_schema, ast)
    assert extended_schema != test_schema
    assert print_schema(test_schema) == original_print
    # print original_print
    assert (
        print_schema(extended_schema)
        == """schema {
  query: Query
}

type Bar implements SomeInterface {
  name: String
  some: SomeInterface
  foo: Foo
}

type Biz {
  fizz: String
}

type Foo implements SomeInterface {
  name: String
  some: SomeInterface
  tree: [Foo]!
}

type Query {
  foo: Foo
  someUnion: SomeUnion
  someEnum: SomeEnum
  someInterface(id: ID!): SomeInterface
}

enum SomeEnum {
  ONE
  TWO
}

interface SomeInterface {
  name: String
  some: SomeInterface
}

union SomeUnion = Foo | Biz

type Unused {
  someField: String
}
"""
    )


def test_extends_objects_by_adding_new_fields_with_arguments():
    ast = parse(
        """
      extend type Foo {
        newField(arg1: String, arg2: NewInputObj!): String
      }
      input NewInputObj {
        field1: Int
        field2: [Float]
        field3: String!
      }
    """
    )
    original_print = print_schema(test_schema)
    extended_schema = extend_schema(test_schema, ast)
    assert extended_schema != test_schema
    assert print_schema(test_schema) == original_print
    assert (
        print_schema(extended_schema)
        == """schema {
  query: Query
}

type Bar implements SomeInterface {
  name: String
  some: SomeInterface
  foo: Foo
}

type Biz {
  fizz: String
}

type Foo implements SomeInterface {
  name: String
  some: SomeInterface
  tree: [Foo]!
  newField(arg1: String, arg2: NewInputObj!): String
}

input NewInputObj {
  field1: Int
  field2: [Float]
  field3: String!
}

type Query {
  foo: Foo
  someUnion: SomeUnion
  someEnum: SomeEnum
  someInterface(id: ID!): SomeInterface
}

enum SomeEnum {
  ONE
  TWO
}

interface SomeInterface {
  name: String
  some: SomeInterface
}

union SomeUnion = Foo | Biz
"""
    )


def test_extends_objects_by_adding_new_fields_with_existing_types():
    ast = parse(
        """
      extend type Foo {
        newField(arg1: SomeEnum!): SomeEnum
      }
    """
    )
    original_print = print_schema(test_schema)
    extended_schema = extend_schema(test_schema, ast)
    assert extended_schema != test_schema
    assert print_schema(test_schema) == original_print
    assert (
        print_schema(extended_schema)
        == """schema {
  query: Query
}

type Bar implements SomeInterface {
  name: String
  some: SomeInterface
  foo: Foo
}

type Biz {
  fizz: String
}

type Foo implements SomeInterface {
  name: String
  some: SomeInterface
  tree: [Foo]!
  newField(arg1: SomeEnum!): SomeEnum
}

type Query {
  foo: Foo
  someUnion: SomeUnion
  someEnum: SomeEnum
  someInterface(id: ID!): SomeInterface
}

enum SomeEnum {
  ONE
  TWO
}

interface SomeInterface {
  name: String
  some: SomeInterface
}

union SomeUnion = Foo | Biz
"""
    )


def test_extends_objects_by_adding_implemented_interfaces():
    ast = parse(
        """
      extend type Biz implements SomeInterface {
        name: String
        some: SomeInterface
      }
    """
    )
    original_print = print_schema(test_schema)
    extended_schema = extend_schema(test_schema, ast)
    assert extended_schema != test_schema
    assert print_schema(test_schema) == original_print
    assert (
        print_schema(extended_schema)
        == """schema {
  query: Query
}

type Bar implements SomeInterface {
  name: String
  some: SomeInterface
  foo: Foo
}

type Biz implements SomeInterface {
  fizz: String
  name: String
  some: SomeInterface
}

type Foo implements SomeInterface {
  name: String
  some: SomeInterface
  tree: [Foo]!
}

type Query {
  foo: Foo
  someUnion: SomeUnion
  someEnum: SomeEnum
  someInterface(id: ID!): SomeInterface
}

enum SomeEnum {
  ONE
  TWO
}

interface SomeInterface {
  name: String
  some: SomeInterface
}

union SomeUnion = Foo | Biz
"""
    )


def test_extends_objects_by_adding_implemented_interfaces_2():
    ast = parse(
        """
      extend type Foo {
        newObject: NewObject
        newInterface: NewInterface
        newUnion: NewUnion
        newScalar: NewScalar
        newEnum: NewEnum
        newTree: [Foo]!
      }
      type NewObject implements NewInterface {
        baz: String
      }
      type NewOtherObject {
        fizz: Int
      }
      interface NewInterface {
        baz: String
      }
      union NewUnion = NewObject | NewOtherObject
      scalar NewScalar
      enum NewEnum {
        OPTION_A
        OPTION_B
      }
    """
    )
    original_print = print_schema(test_schema)
    extended_schema = extend_schema(test_schema, ast)
    assert extended_schema != test_schema
    assert print_schema(test_schema) == original_print
    assert (
        print_schema(extended_schema)
        == """schema {
  query: Query
}

type Bar implements SomeInterface {
  name: String
  some: SomeInterface
  foo: Foo
}

type Biz {
  fizz: String
}

type Foo implements SomeInterface {
  name: String
  some: SomeInterface
  tree: [Foo]!
  newObject: NewObject
  newInterface: NewInterface
  newUnion: NewUnion
  newScalar: NewScalar
  newEnum: NewEnum
  newTree: [Foo]!
}

enum NewEnum {
  OPTION_A
  OPTION_B
}

interface NewInterface {
  baz: String
}

type NewObject implements NewInterface {
  baz: String
}

type NewOtherObject {
  fizz: Int
}

scalar NewScalar

union NewUnion = NewObject | NewOtherObject

type Query {
  foo: Foo
  someUnion: SomeUnion
  someEnum: SomeEnum
  someInterface(id: ID!): SomeInterface
}

enum SomeEnum {
  ONE
  TWO
}

interface SomeInterface {
  name: String
  some: SomeInterface
}

union SomeUnion = Foo | Biz
"""
    )


def test_extends_objects_by_adding_implemented_new_interfaces():
    ast = parse(
        """
      extend type Foo implements NewInterface {
        baz: String
      }
      interface NewInterface {
        baz: String
      }
    """
    )
    original_print = print_schema(test_schema)
    extended_schema = extend_schema(test_schema, ast)
    assert extended_schema != test_schema
    assert print_schema(test_schema) == original_print
    assert (
        print_schema(extended_schema)
        == """schema {
  query: Query
}

type Bar implements SomeInterface {
  name: String
  some: SomeInterface
  foo: Foo
}

type Biz {
  fizz: String
}

type Foo implements SomeInterface, NewInterface {
  name: String
  some: SomeInterface
  tree: [Foo]!
  baz: String
}

interface NewInterface {
  baz: String
}

type Query {
  foo: Foo
  someUnion: SomeUnion
  someEnum: SomeEnum
  someInterface(id: ID!): SomeInterface
}

enum SomeEnum {
  ONE
  TWO
}

interface SomeInterface {
  name: String
  some: SomeInterface
}

union SomeUnion = Foo | Biz
"""
    )


def test_extends_objects_multiple_times():
    ast = parse(
        """
      extend type Biz implements NewInterface {
        buzz: String
      }
      extend type Biz implements SomeInterface {
        name: String
        some: SomeInterface
        newFieldA: Int
      }
      extend type Biz {
        newFieldA: Int
        newFieldB: Float
      }
      interface NewInterface {
        buzz: String
      }
    """
    )
    original_print = print_schema(test_schema)
    extended_schema = extend_schema(test_schema, ast)
    assert extended_schema != test_schema
    assert print_schema(test_schema) == original_print
    assert (
        print_schema(extended_schema)
        == """schema {
  query: Query
}

type Bar implements SomeInterface {
  name: String
  some: SomeInterface
  foo: Foo
}

type Biz implements NewInterface, SomeInterface {
  fizz: String
  buzz: String
  name: String
  some: SomeInterface
  newFieldA: Int
  newFieldB: Float
}

type Foo implements SomeInterface {
  name: String
  some: SomeInterface
  tree: [Foo]!
}

interface NewInterface {
  buzz: String
}

type Query {
  foo: Foo
  someUnion: SomeUnion
  someEnum: SomeEnum
  someInterface(id: ID!): SomeInterface
}

enum SomeEnum {
  ONE
  TWO
}

interface SomeInterface {
  name: String
  some: SomeInterface
}

union SomeUnion = Foo | Biz
"""
    )


def test_may_extend_mutations_and_subscriptions():
    mutationSchema = GraphQLSchema(
        query=GraphQLObjectType(
            "Query", fields=lambda: {"queryField": GraphQLField(GraphQLString)}
        ),
        mutation=GraphQLObjectType(
            "Mutation", fields={"mutationField": GraphQLField(GraphQLString)}
        ),
        subscription=GraphQLObjectType(
            "Subscription", fields={"subscriptionField": GraphQLField(GraphQLString)}
        ),
    )

    ast = parse(
        """
      extend type Query {
        newQueryField: Int
      }
      extend type Mutation {
        newMutationField: Int
      }
      extend type Subscription {
        newSubscriptionField: Int
      }
    """
    )
    original_print = print_schema(mutationSchema)
    extended_schema = extend_schema(mutationSchema, ast)
    assert extended_schema != mutationSchema
    assert print_schema(mutationSchema) == original_print
    assert (
        print_schema(extended_schema)
        == """schema {
  query: Query
  mutation: Mutation
  subscription: Subscription
}

type Mutation {
  mutationField: String
  newMutationField: Int
}

type Query {
  queryField: String
  newQueryField: Int
}

type Subscription {
  subscriptionField: String
  newSubscriptionField: Int
}
"""
    )


def test_does_not_allow_replacing_an_existing_type():
    ast = parse(
        """
      type Bar {
        baz: String
      }
    """
    )
    with raises(Exception) as exc_info:
        extend_schema(test_schema, ast)

    assert str(exc_info.value) == (
        'Type "Bar" already exists in the schema. It cannot also be defined '
        + "in this type definition."
    )


def test_does_not_allow_replacing_an_existing_field():
    ast = parse(
        """
      extend type Bar {
        foo: Foo
      }
    """
    )
    with raises(Exception) as exc_info:
        extend_schema(test_schema, ast)

    assert str(exc_info.value) == (
        'Field "Bar.foo" already exists in the schema. It cannot also be '
        + "defined in this type extension."
    )


def test_does_not_allow_replacing_an_existing_interface():
    ast = parse(
        """
      extend type Foo implements SomeInterface {
        otherField: String
      }
    """
    )
    with raises(Exception) as exc_info:
        extend_schema(test_schema, ast)

    assert str(exc_info.value) == (
        'Type "Foo" already implements "SomeInterface". It cannot also be '
        + "implemented in this type extension."
    )


def test_does_not_allow_referencing_an_unknown_type():
    ast = parse(
        """
      extend type Bar {
        quix: Quix
      }
    """
    )
    with raises(Exception) as exc_info:
        extend_schema(test_schema, ast)

    assert str(exc_info.value) == (
        'Unknown type: "Quix". Ensure that this type exists either in the '
        + "original schema, or is added in a type definition."
    )


def test_does_not_allow_extending_an_unknown_type():
    ast = parse(
        """
      extend type UnknownType {
        baz: String
      }
    """
    )
    with raises(Exception) as exc_info:
        extend_schema(test_schema, ast)

    assert str(exc_info.value) == (
        'Cannot extend type "UnknownType" because it does not exist in the '
        + "existing schema."
    )


def test_does_not_allow_extending_an_interface():
    ast = parse(
        """
      extend type SomeInterface {
        baz: String
      }
    """
    )
    with raises(Exception) as exc_info:
        extend_schema(test_schema, ast)

    assert str(exc_info.value) == 'Cannot extend non-object type "SomeInterface".'


def test_does_not_allow_extending_a_scalar():
    ast = parse(
        """
      extend type String {
        baz: String
      }
    """
    )
    with raises(Exception) as exc_info:
        extend_schema(test_schema, ast)

    assert str(exc_info.value) == 'Cannot extend non-object type "String".'
