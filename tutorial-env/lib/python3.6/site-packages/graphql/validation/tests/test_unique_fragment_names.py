from graphql.language.location import SourceLocation
from graphql.validation.rules import UniqueFragmentNames

from .utils import expect_fails_rule, expect_passes_rule


def duplicate_fragment(fragment_name, l1, c1, l2, c2):
    return {
        "message": UniqueFragmentNames.duplicate_fragment_name_message(fragment_name),
        "locations": [SourceLocation(l1, c1), SourceLocation(l2, c2)],
    }


def test_no_fragments():
    expect_passes_rule(
        UniqueFragmentNames,
        """
      {
        field
      }
    """,
    )


def test_one_fragment():
    expect_passes_rule(
        UniqueFragmentNames,
        """
      {
        ...fragA
      }
      fragment fragA on Type {
        field
      }
    """,
    )


def test_many_fragments():
    expect_passes_rule(
        UniqueFragmentNames,
        """
      {
        ...fragA
        ...fragB
        ...fragC
      }
      fragment fragA on Type {
        fieldA
      }
      fragment fragB on Type {
        fieldB
      }
      fragment fragC on Type {
        fieldC
      }
    """,
    )


def test_inline_fragments():
    expect_passes_rule(
        UniqueFragmentNames,
        """
      {
        ...on Type {
          fieldA
        }
        ...on Type {
          fieldB
        }
      }
    """,
    )


def test_fragment_operation_same_name():
    expect_passes_rule(
        UniqueFragmentNames,
        """
      query Foo {
        ...Foo
      }
      fragment Foo on Type {
        field
      }
    """,
    )


def test_fragments_same_name():
    expect_fails_rule(
        UniqueFragmentNames,
        """
        {
          ...fragA
        }
        fragment fragA on Type {
          fieldA
        }
        fragment fragA on Type {
          fieldB
        }
    """,
        [duplicate_fragment("fragA", 5, 18, 8, 18)],
    )


def test_fragments_same_name_no_ref():
    expect_fails_rule(
        UniqueFragmentNames,
        """
        fragment fragA on Type {
          fieldA
        }
        fragment fragA on Type {
          fieldB
        }
    """,
        [duplicate_fragment("fragA", 2, 18, 5, 18)],
    )
