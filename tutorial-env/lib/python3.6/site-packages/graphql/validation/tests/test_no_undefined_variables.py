from graphql.language.location import SourceLocation
from graphql.validation.rules import NoUndefinedVariables

from .utils import expect_fails_rule, expect_passes_rule


def undefined_var(var_name, l1, c1, op_name, l2, c2):
    return {
        "message": NoUndefinedVariables.undefined_var_message(var_name, op_name),
        "locations": [SourceLocation(l1, c1), SourceLocation(l2, c2)],
    }


def test_all_varriables_defined():
    expect_passes_rule(
        NoUndefinedVariables,
        """
        query Foo($a: String, $b: String, $c: String) {
            field(a: $a, b: $b, c: $c)
        }
    """,
    )


def test_all_variables_deeply_defined():
    expect_passes_rule(
        NoUndefinedVariables,
        """
        query Foo($a: String, $b: String, $c: String) {
            field(a: $a) {
                field(b: $b) {
                    field(c: $c)
                }
            }
        }
    """,
    )


def test_all_variables_deeply_in_inline_fragments_defined():
    expect_passes_rule(
        NoUndefinedVariables,
        """
        query Foo($a: String, $b: String, $c: String) {
            ... on Type {
                field(a: $a) {
                    field(b: $b) {
                        ... on Type {
                            field(c: $c)
                        }
                    }
                }
            }
        }
    """,
    )


def test_all_variables_in_fragments_deeply_defined():
    expect_passes_rule(
        NoUndefinedVariables,
        """
        query Foo($a: String, $b: String, $c: String) {
            ...FragA
        }
        fragment FragA on Type {
            field(a: $a) {
                ...FragB
            }
        }
        fragment FragB on Type {
            field(b: $b) {
                ...FragC
            }
        }
        fragment FragC on Type {
            field(c: $c)
        }
    """,
    )


def test_variable_within_single_fragment_defined_in_multiple_operations():
    expect_passes_rule(
        NoUndefinedVariables,
        """
        query Foo($a: String) {
            ...FragA
        }
        query Bar($a: String) {
            ...FragA
        }
        fragment FragA on Type {
            field(a: $a)
        }
    """,
    )


def test_variable_within_fragments_defined_in_operations():
    expect_passes_rule(
        NoUndefinedVariables,
        """
        query Foo($a: String) {
            ...FragA
        }
        query Bar($b: String) {
            ...FragB
        }
        fragment FragA on Type {
            field(a: $a)
        }
        fragment FragB on Type {
            field(b: $b)
        }
    """,
    )


def test_variable_within_recursive_fragment_defined():
    expect_passes_rule(
        NoUndefinedVariables,
        """
        query Foo($a: String) {
            ...FragA
        }
        fragment FragA on Type {
            field(a: $a) {
                ...FragA
            }
        }
    """,
    )


def test_variable_not_defined():
    expect_fails_rule(
        NoUndefinedVariables,
        """
      query Foo($a: String, $b: String, $c: String) {
        field(a: $a, b: $b, c: $c, d: $d)
      }
    """,
        [undefined_var("d", 3, 39, "Foo", 2, 7)],
    )


def variable_not_defined_by_unnamed_query():
    expect_fails_rule(
        NoUndefinedVariables,
        """
      {
        field(a: $a)
      }
    """,
        [undefined_var("a", 3, 18, "", 2, 7)],
    )


def test_multiple_variables_not_defined():
    expect_fails_rule(
        NoUndefinedVariables,
        """
      query Foo($b: String) {
        field(a: $a, b: $b, c: $c)
      }
    """,
        [
            undefined_var("a", 3, 18, "Foo", 2, 7),
            undefined_var("c", 3, 32, "Foo", 2, 7),
        ],
    )


def test_variable_in_fragment_not_defined_by_unnamed_query():
    expect_fails_rule(
        NoUndefinedVariables,
        """
      {
        ...FragA
      }
      fragment FragA on Type {
        field(a: $a)
      }
    """,
        [undefined_var("a", 6, 18, "", 2, 7)],
    )


def test_variable_in_fragment_not_defined_by_operation():
    expect_fails_rule(
        NoUndefinedVariables,
        """
      query Foo($a: String, $b: String) {
        ...FragA
      }
      fragment FragA on Type {
        field(a: $a) {
          ...FragB
        }
      }
      fragment FragB on Type {
        field(b: $b) {
          ...FragC
        }
      }
      fragment FragC on Type {
        field(c: $c)
      }
    """,
        [undefined_var("c", 16, 18, "Foo", 2, 7)],
    )


def test_multiple_variables_in_fragments_not_defined():
    expect_fails_rule(
        NoUndefinedVariables,
        """
      query Foo($b: String) {
        ...FragA
      }
      fragment FragA on Type {
        field(a: $a) {
          ...FragB
        }
      }
      fragment FragB on Type {
        field(b: $b) {
          ...FragC
        }
      }
      fragment FragC on Type {
        field(c: $c)
      }
    """,
        [
            undefined_var("a", 6, 18, "Foo", 2, 7),
            undefined_var("c", 16, 18, "Foo", 2, 7),
        ],
    )


def test_single_variable_in_fragment_not_defined_by_multiple_operations():
    expect_fails_rule(
        NoUndefinedVariables,
        """
      query Foo($a: String) {
        ...FragAB
      }
      query Bar($a: String) {
        ...FragAB
      }
      fragment FragAB on Type {
        field(a: $a, b: $b)
      }
    """,
        [
            undefined_var("b", 9, 25, "Foo", 2, 7),
            undefined_var("b", 9, 25, "Bar", 5, 7),
        ],
    )


def test_variables_in_fragment_not_defined_by_multiple_operations():
    expect_fails_rule(
        NoUndefinedVariables,
        """
      query Foo($b: String) {
        ...FragAB
      }
      query Bar($a: String) {
        ...FragAB
      }
      fragment FragAB on Type {
        field(a: $a, b: $b)
      }
    """,
        [
            undefined_var("a", 9, 18, "Foo", 2, 7),
            undefined_var("b", 9, 25, "Bar", 5, 7),
        ],
    )


def test_variable_in_fragment_used_by_other_operation():
    expect_fails_rule(
        NoUndefinedVariables,
        """
      query Foo($b: String) {
        ...FragA
      }
      query Bar($a: String) {
        ...FragB
      }
      fragment FragA on Type {
        field(a: $a)
      }
      fragment FragB on Type {
        field(b: $b)
      }
    """,
        [
            undefined_var("a", 9, 18, "Foo", 2, 7),
            undefined_var("b", 12, 18, "Bar", 5, 7),
        ],
    )


def test_multiple_undefined_variables_produce_multiple_errors():
    expect_fails_rule(
        NoUndefinedVariables,
        """
      query Foo($b: String) {
        ...FragAB
      }
      query Bar($a: String) {
        ...FragAB
      }
      fragment FragAB on Type {
        field1(a: $a, b: $b)
        ...FragC
        field3(a: $a, b: $b)
      }
      fragment FragC on Type {
        field2(c: $c)
      }
    """,
        [
            undefined_var("a", 9, 19, "Foo", 2, 7),
            undefined_var("a", 11, 19, "Foo", 2, 7),
            undefined_var("c", 14, 19, "Foo", 2, 7),
            undefined_var("b", 9, 26, "Bar", 5, 7),
            undefined_var("b", 11, 26, "Bar", 5, 7),
            undefined_var("c", 14, 19, "Bar", 5, 7),
        ],
    )
