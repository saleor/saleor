from graphql.language.location import SourceLocation
from graphql.validation.rules import PossibleFragmentSpreads

from .utils import expect_fails_rule, expect_passes_rule


def error(frag_name, parent_type, frag_type, line, column):
    return {
        "message": PossibleFragmentSpreads.type_incompatible_spread_message(
            frag_name, parent_type, frag_type
        ),
        "locations": [SourceLocation(line, column)],
    }


def error_anon(parent_type, frag_type, line, column):
    return {
        "message": PossibleFragmentSpreads.type_incompatible_anon_spread_message(
            parent_type, frag_type
        ),
        "locations": [SourceLocation(line, column)],
    }


def test_same_object():
    expect_passes_rule(
        PossibleFragmentSpreads,
        """
      fragment objectWithinObject on Dog { ...dogFragment }
      fragment dogFragment on Dog { barkVolume }
    """,
    )


def test_same_object_inline_frag():
    expect_passes_rule(
        PossibleFragmentSpreads,
        """
      fragment objectWithinObjectAnon on Dog { ... on Dog { barkVolume } }
    """,
    )


def test_object_into_implemented_interface():
    expect_passes_rule(
        PossibleFragmentSpreads,
        """
      fragment objectWithinInterface on Pet { ...dogFragment }
      fragment dogFragment on Dog { barkVolume }
    """,
    )


def test_object_into_containing_union():
    expect_passes_rule(
        PossibleFragmentSpreads,
        """
      fragment objectWithinUnion on CatOrDog { ...dogFragment }
      fragment dogFragment on Dog { barkVolume }
    """,
    )


def test_union_into_contained_object():
    expect_passes_rule(
        PossibleFragmentSpreads,
        """
      fragment unionWithinObject on Dog { ...catOrDogFragment }
      fragment catOrDogFragment on CatOrDog { __typename }
    """,
    )


def test_union_into_overlapping_interface():
    expect_passes_rule(
        PossibleFragmentSpreads,
        """
      fragment unionWithinInterface on Pet { ...catOrDogFragment }
      fragment catOrDogFragment on CatOrDog { __typename }
    """,
    )


def test_union_into_overlapping_union():
    expect_passes_rule(
        PossibleFragmentSpreads,
        """
      fragment unionWithinUnion on DogOrHuman { ...catOrDogFragment }
      fragment catOrDogFragment on CatOrDog { __typename }
    """,
    )


def test_interface_into_implemented_object():
    expect_passes_rule(
        PossibleFragmentSpreads,
        """
      fragment interfaceWithinObject on Dog { ...petFragment }
      fragment petFragment on Pet { name }
    """,
    )


def test_interface_into_overlapping_interface():
    expect_passes_rule(
        PossibleFragmentSpreads,
        """
      fragment interfaceWithinInterface on Pet { ...beingFragment }
      fragment beingFragment on Being { name }
    """,
    )


def test_interface_into_overlapping_interface_in_inline_fragment():
    expect_passes_rule(
        PossibleFragmentSpreads,
        """
      fragment interfaceWithinInterface on Pet { ... on Being { name } }
    """,
    )


def test_interface_into_overlapping_union():
    expect_passes_rule(
        PossibleFragmentSpreads,
        """
      fragment interfaceWithinUnion on CatOrDog { ...petFragment }
      fragment petFragment on Pet { name }
    """,
    )


def test_different_object_into_object():
    expect_fails_rule(
        PossibleFragmentSpreads,
        """
      fragment invalidObjectWithinObject on Cat { ...dogFragment }
      fragment dogFragment on Dog { barkVolume }
    """,
        [error("dogFragment", "Cat", "Dog", 2, 51)],
    )


def test_different_object_into_object_in_inline_fragment():
    expect_fails_rule(
        PossibleFragmentSpreads,
        """
      fragment invalidObjectWithinObjectAnon on Cat {
        ... on Dog { barkVolume }
      }
    """,
        [error_anon("Cat", "Dog", 3, 9)],
    )


def test_object_into_not_implementing_interface():
    expect_fails_rule(
        PossibleFragmentSpreads,
        """
      fragment invalidObjectWithinInterface on Pet { ...humanFragment }
      fragment humanFragment on Human { pets { name } }
    """,
        [error("humanFragment", "Pet", "Human", 2, 54)],
    )


def test_object_into_not_containing_union():
    expect_fails_rule(
        PossibleFragmentSpreads,
        """
      fragment invalidObjectWithinUnion on CatOrDog { ...humanFragment }
      fragment humanFragment on Human { pets { name } }
    """,
        [error("humanFragment", "CatOrDog", "Human", 2, 55)],
    )


def test_union_into_not_contained_object():
    expect_fails_rule(
        PossibleFragmentSpreads,
        """
      fragment invalidUnionWithinObject on Human { ...catOrDogFragment }
      fragment catOrDogFragment on CatOrDog { __typename }
    """,
        [error("catOrDogFragment", "Human", "CatOrDog", 2, 52)],
    )


def test_union_into_non_overlapping_interface():
    expect_fails_rule(
        PossibleFragmentSpreads,
        """
      fragment invalidUnionWithinInterface on Pet { ...humanOrAlienFragment }
      fragment humanOrAlienFragment on HumanOrAlien { __typename }
    """,
        [error("humanOrAlienFragment", "Pet", "HumanOrAlien", 2, 53)],
    )


def test_union_into_non_overlapping_union():
    expect_fails_rule(
        PossibleFragmentSpreads,
        """
      fragment invalidUnionWithinUnion on CatOrDog { ...humanOrAlienFragment }
      fragment humanOrAlienFragment on HumanOrAlien { __typename }
    """,
        [error("humanOrAlienFragment", "CatOrDog", "HumanOrAlien", 2, 54)],
    )


def test_interface_into_non_implementing_object():
    expect_fails_rule(
        PossibleFragmentSpreads,
        """
      fragment invalidInterfaceWithinObject on Cat { ...intelligentFragment }
      fragment intelligentFragment on Intelligent { iq }
    """,
        [error("intelligentFragment", "Cat", "Intelligent", 2, 54)],
    )


def test_interface_into_non_overlapping_interface():
    expect_fails_rule(
        PossibleFragmentSpreads,
        """
      fragment invalidInterfaceWithinInterface on Pet {
        ...intelligentFragment
      }
      fragment intelligentFragment on Intelligent { iq }
    """,
        [error("intelligentFragment", "Pet", "Intelligent", 3, 9)],
    )


def test_interface_into_non_overlapping_interface_in_inline_fragment():
    expect_fails_rule(
        PossibleFragmentSpreads,
        """
      fragment invalidInterfaceWithinInterfaceAnon on Pet {
        ...on Intelligent { iq }
      }
    """,
        [error_anon("Pet", "Intelligent", 3, 9)],
    )


def test_interface_into_non_overlapping_union():
    expect_fails_rule(
        PossibleFragmentSpreads,
        """
      fragment invalidInterfaceWithinUnion on HumanOrAlien { ...petFragment }
      fragment petFragment on Pet { name }
    """,
        [error("petFragment", "HumanOrAlien", "Pet", 2, 62)],
    )
