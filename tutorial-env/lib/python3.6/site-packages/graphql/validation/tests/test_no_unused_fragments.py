from graphql.language.location import SourceLocation
from graphql.validation.rules import NoUnusedFragments

from .utils import expect_fails_rule, expect_passes_rule


def unused_fragment(fragment_name, line, column):
    return {
        "message": NoUnusedFragments.unused_fragment_message(fragment_name),
        "locations": [SourceLocation(line, column)],
    }


def test_all_fragment_names_are_used():
    expect_passes_rule(
        NoUnusedFragments,
        """
      {
        human(id: 4) {
          ...HumanFields1
          ... on Human {
            ...HumanFields2
          }
        }
      }
      fragment HumanFields1 on Human {
        name
        ...HumanFields3
      }
      fragment HumanFields2 on Human {
        name
      }
      fragment HumanFields3 on Human {
        name
      }
    """,
    )


def test_all_fragment_names_are_used_by_multiple_operations():
    expect_passes_rule(
        NoUnusedFragments,
        """
      query Foo {
        human(id: 4) {
          ...HumanFields1
        }
      }
      query Bar {
        human(id: 4) {
          ...HumanFields2
        }
      }
      fragment HumanFields1 on Human {
        name
        ...HumanFields3
      }
      fragment HumanFields2 on Human {
        name
      }
      fragment HumanFields3 on Human {
        name
      }
   """,
    )


def test_contains_unknown_fragments():
    expect_fails_rule(
        NoUnusedFragments,
        """
      query Foo {
        human(id: 4) {
          ...HumanFields1
        }
      }
      query Bar {
        human(id: 4) {
          ...HumanFields2
        }
      }
      fragment HumanFields1 on Human {
        name
        ...HumanFields3
      }
      fragment HumanFields2 on Human {
        name
      }
      fragment HumanFields3 on Human {
        name
      }
      fragment Unused1 on Human {
        name
      }
      fragment Unused2 on Human {
        name
      }
    """,
        [unused_fragment("Unused1", 22, 7), unused_fragment("Unused2", 25, 7)],
    )


def test_contains_unknown_fragments_with_ref_cycle():
    expect_fails_rule(
        NoUnusedFragments,
        """
      query Foo {
        human(id: 4) {
          ...HumanFields1
        }
      }
      query Bar {
        human(id: 4) {
          ...HumanFields2
        }
      }
      fragment HumanFields1 on Human {
        name
        ...HumanFields3
      }
      fragment HumanFields2 on Human {
        name
      }
      fragment HumanFields3 on Human {
        name
      }
      fragment Unused1 on Human {
        name
        ...Unused2
      }
      fragment Unused2 on Human {
        name
        ...Unused1
      }
    """,
        [unused_fragment("Unused1", 22, 7), unused_fragment("Unused2", 26, 7)],
    )


def test_contains_unknown_and_undefined_fragments():
    expect_fails_rule(
        NoUnusedFragments,
        """
      query Foo {
        human(id: 4) {
          ...bar
        }
      }
      fragment foo on Human {
        name
      }
    """,
        [unused_fragment("foo", 7, 7)],
    )
