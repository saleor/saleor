from pytest import raises

from graphql import GraphQLInt, parse
from graphql.utils.build_ast_schema import build_ast_schema
from graphql.utils.schema_printer import print_schema

from ...type import (
    GraphQLDeprecatedDirective,
    GraphQLIncludeDirective,
    GraphQLSkipDirective,
)


def cycle_output(body):
    """This function does a full cycle of going from a string with the contents of the DSL,
    parsed in a schema AST, materializing that schema AST into an in-memory GraphQLSchema,
    and then finally printing that GraphQL into the DSL"""
    ast = parse(body)
    schema = build_ast_schema(ast)
    return "\n" + print_schema(schema)


def test_simple_type():
    body = """
schema {
  query: HelloScalars
}

type HelloScalars {
  str: String
  int: Int
  float: Float
  id: ID
  bool: Boolean
}
"""
    output = cycle_output(body)
    assert output == body


def test_with_directives():
    body = """
schema {
  query: Hello
}

directive @foo(arg: Int) on FIELD

type Hello {
  str: String
}
"""
    output = cycle_output(body)
    assert output == body


def test_maintains_skip_and_include_directives():
    body = """
    schema {
        query: Hello
    }

    type Hello {
        str: String
    }
    """

    schema = build_ast_schema(parse(body))
    assert len(schema.get_directives()) == 3
    assert schema.get_directive("skip") == GraphQLSkipDirective
    assert schema.get_directive("include") == GraphQLIncludeDirective
    assert schema.get_directive("deprecated") == GraphQLDeprecatedDirective


def test_overriding_directives_excludes_specified():
    body = """
    schema {
        query: Hello
    }

    directive @skip on FIELD
    directive @include on FIELD
    directive @deprecated on FIELD_DEFINITION

    type Hello {
        str: String
    }
    """

    schema = build_ast_schema(parse(body))
    assert len(schema.get_directives()) == 3
    assert schema.get_directive("skip") != GraphQLSkipDirective
    assert schema.get_directive("skip") is not None
    assert schema.get_directive("include") != GraphQLIncludeDirective
    assert schema.get_directive("include") is not None
    assert schema.get_directive("deprecated") != GraphQLDeprecatedDirective
    assert schema.get_directive("deprecated") is not None


def test_overriding_skip_directive_excludes_built_in_one():
    body = """
    schema {
        query: Hello
    }

    directive @skip on FIELD

    type Hello {
        str: String
    }
    """

    schema = build_ast_schema(parse(body))
    assert len(schema.get_directives()) == 3
    assert schema.get_directive("skip") != GraphQLSkipDirective
    assert schema.get_directive("skip") is not None
    assert schema.get_directive("include") == GraphQLIncludeDirective
    assert schema.get_directive("deprecated") == GraphQLDeprecatedDirective


def test_overriding_include_directive_excludes_built_in_one():
    body = """
    schema {
        query: Hello
    }

    directive @include on FIELD

    type Hello {
        str: String
    }
    """

    schema = build_ast_schema(parse(body))
    assert len(schema.get_directives()) == 3
    assert schema.get_directive("skip") == GraphQLSkipDirective
    assert schema.get_directive("deprecated") == GraphQLDeprecatedDirective
    assert schema.get_directive("include") != GraphQLIncludeDirective
    assert schema.get_directive("include") is not None


def test_adding_directives_maintains_skip_and_include_directives():
    body = """
    schema {
        query: Hello
    }

    directive @foo(arg: Int) on FIELD

    type Hello {
        str: String
    }
    """

    schema = build_ast_schema(parse(body))
    assert len(schema.get_directives()) == 4
    assert schema.get_directive("skip") == GraphQLSkipDirective
    assert schema.get_directive("include") == GraphQLIncludeDirective
    assert schema.get_directive("deprecated") == GraphQLDeprecatedDirective


def test_type_modifiers():
    body = """
schema {
  query: HelloScalars
}

type HelloScalars {
  nonNullStr: String!
  listOfStrs: [String]
  listOfNonNullStrs: [String!]
  nonNullListOfStrs: [String]!
  nonNullListOfNonNullStrs: [String!]!
}
"""
    output = cycle_output(body)
    assert output == body


def test_recursive_type():
    body = """
schema {
  query: Recurse
}

type Recurse {
  str: String
  recurse: Recurse
}
"""
    output = cycle_output(body)
    assert output == body


def test_two_types_circular():
    body = """
schema {
  query: TypeOne
}

type TypeOne {
  str: String
  typeTwo: TypeTwo
}

type TypeTwo {
  str: String
  typeOne: TypeOne
}
"""
    output = cycle_output(body)
    assert output == body


def test_single_argument_field():
    body = """
schema {
  query: Hello
}

type Hello {
  str(int: Int): String
  floatToStr(float: Float): String
  idToStr(id: ID): String
  booleanToStr(bool: Boolean): String
  strToStr(bool: String): String
}
"""
    output = cycle_output(body)
    assert output == body


def test_simple_type_with_multiple_arguments():
    body = """
schema {
  query: Hello
}

type Hello {
  str(int: Int, bool: Boolean): String
}
"""
    output = cycle_output(body)
    assert output == body


def test_simple_type_with_interface():
    body = """
schema {
  query: HelloInterface
}

type HelloInterface implements WorldInterface {
  str: String
}

interface WorldInterface {
  str: String
}
"""
    output = cycle_output(body)
    assert output == body


def test_simple_output_enum():
    body = """
schema {
  query: OutputEnumRoot
}

enum Hello {
  WORLD
}

type OutputEnumRoot {
  hello: Hello
}
"""
    output = cycle_output(body)
    assert output == body


def test_simple_input_enum():
    body = """
schema {
  query: InputEnumRoot
}

enum Hello {
  WORLD
}

type InputEnumRoot {
  str(hello: Hello): String
}
"""
    output = cycle_output(body)
    assert output == body


def test_multiple_value_enum():
    body = """
schema {
  query: OutputEnumRoot
}

enum Hello {
  WO
  RLD
}

type OutputEnumRoot {
  hello: Hello
}
"""
    output = cycle_output(body)
    assert output == body


def test_simple_union():
    body = """
schema {
  query: Root
}

union Hello = World

type Root {
  hello: Hello
}

type World {
  str: String
}
"""
    output = cycle_output(body)
    assert output == body


def test_multiple_union():
    body = """
schema {
  query: Root
}

union Hello = WorldOne | WorldTwo

type Root {
  hello: Hello
}

type WorldOne {
  str: String
}

type WorldTwo {
  str: String
}
"""
    output = cycle_output(body)
    assert output == body


def test_custom_scalar():
    body = """
schema {
  query: Root
}

scalar CustomScalar

type Root {
  customScalar: CustomScalar
}
"""
    output = cycle_output(body)
    assert output == body


def test_input_object():
    body = """
schema {
  query: Root
}

input Input {
  int: Int
}

type Root {
  field(in: Input): String
}
"""
    output = cycle_output(body)
    assert output == body


def test_input_types_are_read():
    schema = build_ast_schema(
        parse(
            """
        schema {
            query: Query
        }

        type Query {
            field(input: Input): Int
        }

        input Input {
            id: Int
        }
    """
        )
    )

    input_type = schema.get_type("Input")
    assert input_type.fields["id"].type == GraphQLInt


def test_input_types_can_be_recursive():
    schema = build_ast_schema(
        parse(
            """
        schema {
            query: Query
        }

        type Query {
            field(input: Input): Int
        }

        input Input {
            id: Input
        }
    """
        )
    )

    input_type = schema.get_type("Input")
    assert input_type.fields["id"].type == input_type


def test_simple_argument_field_with_default():
    body = """
schema {
  query: Hello
}

type Hello {
  str(int: Int = 2): String
}
"""
    output = cycle_output(body)
    assert output == body


def test_simple_type_with_mutation():
    body = """
schema {
  query: HelloScalars
  mutation: Mutation
}

type HelloScalars {
  str: String
  int: Int
  bool: Boolean
}

type Mutation {
  addHelloScalars(str: String, int: Int, bool: Boolean): HelloScalars
}
"""
    output = cycle_output(body)
    assert output == body


def test_simple_type_with_subscription():
    body = """
schema {
  query: HelloScalars
  subscription: Subscription
}

type HelloScalars {
  str: String
  int: Int
  bool: Boolean
}

type Subscription {
  subscribeHelloScalars(str: String, int: Int, bool: Boolean): HelloScalars
}
"""
    output = cycle_output(body)
    assert output == body


def test_unreferenced_type_implementing_referenced_interface():
    body = """
schema {
  query: Query
}

type Concrete implements Iface {
  key: String
}

interface Iface {
  key: String
}

type Query {
  iface: Iface
}
"""
    output = cycle_output(body)
    assert output == body


def test_unreferenced_type_implementing_referenced_union():
    body = """
schema {
  query: Query
}

type Concrete {
  key: String
}

type Query {
  union: Union
}

union Union = Concrete
"""
    output = cycle_output(body)
    assert output == body


def test_supports_deprecated_directive():
    body = """
schema {
  query: Query
}

enum MyEnum {
  VALUE
  OLD_VALUE @deprecated
  OTHER_VALUE @deprecated(reason: "Terrible reasons")
}

type Query {
  field1: String @deprecated
  field2: Int @deprecated(reason: "Because I said so")
  enum: MyEnum
}
"""

    output = cycle_output(body)
    assert output == body


def test_requires_a_schema_definition():
    body = """
type Hello {
  bar: Bar
}
"""
    doc = parse(body)
    with raises(Exception) as excinfo:
        build_ast_schema(doc)

    assert "Must provide a schema definition." == str(excinfo.value)


def test_allows_only_a_single_schema_definition():
    body = """
schema {
  query: Hello
}

schema {
  query: Hello
}

type Hello {
  bar: Bar
}
"""
    doc = parse(body)
    with raises(Exception) as excinfo:
        build_ast_schema(doc)

    assert "Must provide only one schema definition." == str(excinfo.value)


def test_requires_a_query_type():
    body = """
schema {
  mutation: Hello
}

type Hello {
  bar: Bar
}
"""
    doc = parse(body)
    with raises(Exception) as excinfo:
        build_ast_schema(doc)

    assert "Must provide schema definition with query type." == str(excinfo.value)


def test_allows_only_a_single_query_type():
    body = """
schema {
  query: Hello
  query: Yellow
}

type Hello {
  bar: Bar
}

type Yellow {
  isColor: Boolean
}
"""
    doc = parse(body)
    with raises(Exception) as excinfo:
        build_ast_schema(doc)

    assert "Must provide only one query type in schema." == str(excinfo.value)


def test_allows_only_a_single_mutation_type():
    body = """
schema {
  query: Hello
  mutation: Hello
  mutation: Yellow
}

type Hello {
  bar: Bar
}

type Yellow {
  isColor: Boolean
}
"""
    doc = parse(body)
    with raises(Exception) as excinfo:
        build_ast_schema(doc)

    assert "Must provide only one mutation type in schema." == str(excinfo.value)


def test_allows_only_a_single_subscription_type():
    body = """
schema {
  query: Hello
  subscription: Hello
  subscription: Yellow
}

type Hello {
  bar: Bar
}

type Yellow {
  isColor: Boolean
}
"""
    doc = parse(body)
    with raises(Exception) as excinfo:
        build_ast_schema(doc)

    assert "Must provide only one subscription type in schema." == str(excinfo.value)


def test_unknown_type_referenced():
    body = """
schema {
  query: Hello
}

type Hello {
  bar: Bar
}
"""
    doc = parse(body)
    with raises(Exception) as excinfo:
        build_ast_schema(doc)

    assert 'Type "Bar" not found in document' in str(excinfo.value)


def test_unknown_type_in_union_list():
    body = """
schema {
  query: Hello
}

union TestUnion = Bar
type Hello { testUnion: TestUnion }
"""
    doc = parse(body)
    with raises(Exception) as excinfo:
        build_ast_schema(doc)

    assert 'Type "Bar" not found in document' in str(excinfo.value)


def test_unknown_query_type():
    body = """
schema {
  query: Wat
}

type Hello {
  str: String
}
"""
    doc = parse(body)
    with raises(Exception) as excinfo:
        build_ast_schema(doc)

    assert 'Specified query type "Wat" not found in document' in str(excinfo.value)


def test_unknown_mutation_type():
    body = """
schema {
  query: Hello
  mutation: Wat
}

type Hello {
  str: String
}
"""
    doc = parse(body)
    with raises(Exception) as excinfo:
        build_ast_schema(doc)

    assert 'Specified mutation type "Wat" not found in document' in str(excinfo.value)


def test_unknown_subscription_type():
    body = """
schema {
  query: Hello
  mutation: Wat
  subscription: Awesome
}

type Hello {
  str: String
}

type Wat {
  str: String
}
"""
    doc = parse(body)
    with raises(Exception) as excinfo:
        build_ast_schema(doc)

    assert 'Specified subscription type "Awesome" not found in document' in str(
        excinfo.value
    )


def test_does_not_consider_query_names():
    body = """
schema {
  query: Foo
}

type Hello {
  str: String
}
"""
    doc = parse(body)
    with raises(Exception) as excinfo:
        build_ast_schema(doc)

    assert 'Specified query type "Foo" not found in document' in str(excinfo.value)


def test_does_not_consider_fragment_names():
    body = """schema {
  query: Foo
}

fragment Foo on Type { field } """
    doc = parse(body)
    with raises(Exception) as excinfo:
        build_ast_schema(doc)

    assert 'Specified query type "Foo" not found in document' in str(excinfo.value)
