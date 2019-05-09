from graphql.language.location import SourceLocation
from graphql.validation.rules import ScalarLeafs

from .utils import expect_fails_rule, expect_passes_rule


def no_scalar_subselection(field, type, line, column):
    return {
        "message": ScalarLeafs.no_subselection_allowed_message(field, type),
        "locations": [SourceLocation(line, column)],
    }


def missing_obj_subselection(field, type, line, column):
    return {
        "message": ScalarLeafs.required_subselection_message(field, type),
        "locations": [SourceLocation(line, column)],
    }


def test_valid_scalar_selection():
    expect_passes_rule(
        ScalarLeafs,
        """
      fragment scalarSelection on Dog {
        barks
      }
    """,
    )


def test_object_type_missing_selection():
    expect_fails_rule(
        ScalarLeafs,
        """
      query directQueryOnObjectWithoutSubFields {
        human
      }
    """,
        [missing_obj_subselection("human", "Human", 3, 9)],
    )


def test_interface_type_missing_selection():
    expect_fails_rule(
        ScalarLeafs,
        """
      {
        human { pets }
      }
    """,
        [missing_obj_subselection("pets", "[Pet]", 3, 17)],
    )


def test_valid_scalar_selection_with_args():
    expect_passes_rule(
        ScalarLeafs,
        """
      fragment scalarSelectionWithArgs on Dog {
        doesKnowCommand(dogCommand: SIT)
      }
    """,
    )


def test_scalar_selection_not_allowed_on_boolean():
    expect_fails_rule(
        ScalarLeafs,
        """
      fragment scalarSelectionsNotAllowedOnBoolean on Dog {
        barks { sinceWhen }
      }
    """,
        [no_scalar_subselection("barks", "Boolean", 3, 15)],
    )


def test_scalar_selection_not_allowed_on_enum():
    expect_fails_rule(
        ScalarLeafs,
        """
      fragment scalarSelectionsNotAllowedOnEnum on Cat {
        furColor { inHexdec }
      }
    """,
        [no_scalar_subselection("furColor", "FurColor", 3, 18)],
    )


def test_scalar_selection_not_allowed_with_args():
    expect_fails_rule(
        ScalarLeafs,
        """
      fragment scalarSelectionsNotAllowedWithArgs on Dog {
        doesKnowCommand(dogCommand: SIT) { sinceWhen }
      }
    """,
        [no_scalar_subselection("doesKnowCommand", "Boolean", 3, 42)],
    )


def test_scalar_selection_not_allowed_with_directives():
    expect_fails_rule(
        ScalarLeafs,
        """
      fragment scalarSelectionsNotAllowedWithDirectives on Dog {
        name @include(if: true) { isAlsoHumanName }
      }
    """,
        [no_scalar_subselection("name", "String", 3, 33)],
    )


def test_scalar_selection_not_allowed_with_directives_and_args():
    expect_fails_rule(
        ScalarLeafs,
        """
      fragment scalarSelectionsNotAllowedWithDirectivesAndArgs on Dog {
        doesKnowCommand(dogCommand: SIT) @include(if: true) { sinceWhen }
      }
    """,
        [no_scalar_subselection("doesKnowCommand", "Boolean", 3, 61)],
    )
