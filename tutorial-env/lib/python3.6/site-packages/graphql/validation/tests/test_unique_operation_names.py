from graphql.language.location import SourceLocation
from graphql.validation.rules import UniqueOperationNames

from .utils import expect_fails_rule, expect_passes_rule


def duplicate_op(op_name, l1, c1, l2, c2):
    return {
        "message": UniqueOperationNames.duplicate_operation_name_message(op_name),
        "locations": [SourceLocation(l1, c1), SourceLocation(l2, c2)],
    }


def test_no_operations():
    expect_passes_rule(
        UniqueOperationNames,
        """
      fragment fragA on Type {
        field
      }
    """,
    )


def test_one_anon_operation():
    expect_passes_rule(
        UniqueOperationNames,
        """
      {
        field
      }
    """,
    )


def test_one_named_operation():
    expect_passes_rule(
        UniqueOperationNames,
        """
      query Foo {
        field
      }
    """,
    )


def test_multiple_operations():
    expect_passes_rule(
        UniqueOperationNames,
        """
      query Foo {
        field
      }

      query Bar {
        field
      }
    """,
    )


def test_multiple_operations_of_different_types():
    expect_passes_rule(
        UniqueOperationNames,
        """
      query Foo {
        field
      }

      mutation Bar {
        field
      }

      subscription Baz {
        field
      }
    """,
    )


def test_fragment_and_operation_named_the_same():
    expect_passes_rule(
        UniqueOperationNames,
        """
      query Foo {
        ...Foo
      }
      fragment Foo on Type {
        field
      }
    """,
    )


def test_multiple_operations_of_same_name():
    expect_fails_rule(
        UniqueOperationNames,
        """
      query Foo {
        fieldA
      }
      query Foo {
        fieldB
      }
    """,
        [duplicate_op("Foo", 2, 13, 5, 13)],
    )


def test_multiple_ops_of_same_name_of_different_types_mutation():
    expect_fails_rule(
        UniqueOperationNames,
        """
      query Foo {
        fieldA
      }
      mutation Foo {
        fieldB
      }
    """,
        [duplicate_op("Foo", 2, 13, 5, 16)],
    )


def test_multiple_ops_of_same_name_of_different_types_subscription():
    expect_fails_rule(
        UniqueOperationNames,
        """
      query Foo {
        fieldA
      }
      subscription Foo {
        fieldB
      }
    """,
        [duplicate_op("Foo", 2, 13, 5, 20)],
    )
