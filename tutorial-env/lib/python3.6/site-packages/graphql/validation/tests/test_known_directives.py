from graphql.language.location import SourceLocation
from graphql.validation.rules import KnownDirectives

from .utils import expect_fails_rule, expect_passes_rule


def unknown_directive(directive_name, line, column):
    return {
        "message": KnownDirectives.unknown_directive_message(directive_name),
        "locations": [SourceLocation(line, column)],
    }


def misplaced_directive(directive_name, placement, line, column):
    return {
        "message": KnownDirectives.misplaced_directive_message(
            directive_name, placement
        ),
        "locations": [SourceLocation(line, column)],
    }


def test_with_no_directives():
    expect_passes_rule(
        KnownDirectives,
        """
      query Foo {
        name
        ...Frag
      }

      fragment Frag on Dog {
        name
      }
    """,
    )


def test_with_known_directives():
    expect_passes_rule(
        KnownDirectives,
        """
      {
        dog @include(if: true) {
          name
        }
        human @skip(if: false) {
          name
        }
      }
    """,
    )


def test_with_unknown_directive():
    expect_fails_rule(
        KnownDirectives,
        """
      {
        dog @unknown(directive: "value") {
          name
        }
      }
    """,
        [unknown_directive("unknown", 3, 13)],
    )


def test_with_many_unknown_directives():
    expect_fails_rule(
        KnownDirectives,
        """
      {
        dog @unknown(directive: "value") {
          name
        }
        human @unknown(directive: "value") {
          name
          pets @unknown(directive: "value") {
            name
          }
        }
      }
    """,
        [
            unknown_directive("unknown", 3, 13),
            unknown_directive("unknown", 6, 15),
            unknown_directive("unknown", 8, 16),
        ],
    )


def test_with_well_placed_directives():
    expect_passes_rule(
        KnownDirectives,
        """
      query Foo @onQuery{
        name @include(if: true)
        ...Frag @include(if: true)
        skippedField @skip(if: true)
        ...SkippedFrag @skip(if: true)
      }

      mutation Bar @onMutation {
        someField
      }
    """,
    )


def test_with_misplaced_directives():
    expect_fails_rule(
        KnownDirectives,
        """
      query Foo @include(if: true) {
        name @onQuery
        ...Frag @onQuery
      }

      mutation Bar @onQuery {
        someField
      }
    """,
        [
            misplaced_directive("include", "QUERY", 2, 17),
            misplaced_directive("onQuery", "FIELD", 3, 14),
            misplaced_directive("onQuery", "FRAGMENT_SPREAD", 4, 17),
            misplaced_directive("onQuery", "MUTATION", 7, 20),
        ],
    )


# within schema language


def test_within_schema_language_with_well_placed_directives():
    expect_passes_rule(
        KnownDirectives,
        """
      type MyObj implements MyInterface @onObject {
        myField(myArg: Int @onArgumentDefinition): String @onFieldDefinition
      }

      scalar MyScalar @onScalar

      interface MyInterface @onInterface {
        myField(myArg: Int @onArgumentDefinition): String @onFieldDefinition
      }

      union MyUnion @onUnion = MyObj | Other

      enum MyEnum @onEnum {
        MY_VALUE @onEnumValue
      }

      input MyInput @onInputObject {
        myField: Int @onInputFieldDefinition
      }

      schema @OnSchema {
        query: MyQuery
      }
    """,
    )


def test_within_schema_language_with_misplaced_directives():
    expect_fails_rule(
        KnownDirectives,
        """
        type MyObj implements MyInterface @onInterface {
          myField(myArg: Int @onInputFieldDefinition): String @onInputFieldDefinition
        }

        scalar MyScalar @onEnum

        interface MyInterface @onObject {
          myField(myArg: Int @onInputFieldDefinition): String @onInputFieldDefinition
        }

        union MyUnion @onEnumValue = MyObj | Other

        enum MyEnum @onScalar {
          MY_VALUE @onUnion
        }

        input MyInput @onEnum {
          myField: Int @onArgumentDefinition
        }

        schema @onObject {
          query: MyQuery
        }
    """,
        [
            misplaced_directive("onInterface", "OBJECT", 2, 43),
            misplaced_directive("onInputFieldDefinition", "ARGUMENT_DEFINITION", 3, 30),
            misplaced_directive("onInputFieldDefinition", "FIELD_DEFINITION", 3, 63),
            misplaced_directive("onEnum", "SCALAR", 6, 25),
            misplaced_directive("onObject", "INTERFACE", 8, 31),
            misplaced_directive("onInputFieldDefinition", "ARGUMENT_DEFINITION", 9, 30),
            misplaced_directive("onInputFieldDefinition", "FIELD_DEFINITION", 9, 63),
            misplaced_directive("onEnumValue", "UNION", 12, 23),
            misplaced_directive("onScalar", "ENUM", 14, 21),
            misplaced_directive("onUnion", "ENUM_VALUE", 15, 20),
            misplaced_directive("onEnum", "INPUT_OBJECT", 18, 23),
            misplaced_directive(
                "onArgumentDefinition", "INPUT_FIELD_DEFINITION", 19, 24
            ),
            misplaced_directive("onObject", "SCHEMA", 22, 16),
        ],
    )
