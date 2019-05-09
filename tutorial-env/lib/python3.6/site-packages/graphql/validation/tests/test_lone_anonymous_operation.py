from graphql.language.location import SourceLocation
from graphql.validation.rules import LoneAnonymousOperation

from .utils import expect_fails_rule, expect_passes_rule


def anon_not_alone(line, column):
    return {
        "message": LoneAnonymousOperation.anonymous_operation_not_alone_message(),
        "locations": [SourceLocation(line, column)],
    }


def test_no_operations():
    expect_passes_rule(
        LoneAnonymousOperation,
        """
      fragment fragA on Type {
        field
      }
    """,
    )


def test_one_anon_operation():
    expect_passes_rule(
        LoneAnonymousOperation,
        """
      {
        field
      }
    """,
    )


def test_multiple_named_operation():
    expect_passes_rule(
        LoneAnonymousOperation,
        """
      query Foo {
        field
      }

      query Bar {
        field
      }
    """,
    )


def test_anon_operation_with_fragment():
    expect_passes_rule(
        LoneAnonymousOperation,
        """
      {
        ...Foo
      }
      fragment Foo on Type {
        field
      }
    """,
    )


def test_multiple_anon_operations():
    expect_fails_rule(
        LoneAnonymousOperation,
        """
      {
        fieldA
      }
      {
        fieldB
      }
    """,
        [anon_not_alone(2, 7), anon_not_alone(5, 7)],
    )


def test_anon_operation_with_a_mutation():
    expect_fails_rule(
        LoneAnonymousOperation,
        """
      {
        fieldA
      }
      mutation Foo {
        fieldB
      }
    """,
        [anon_not_alone(2, 7)],
    )


def test_anon_operation_with_a_subscription():
    expect_fails_rule(
        LoneAnonymousOperation,
        """
      {
        fieldA
      }
      subscription Foo {
        fieldB
      }
    """,
        [anon_not_alone(2, 7)],
    )
