from graphql.language.location import SourceLocation
from graphql.validation.rules import KnownFragmentNames

from .utils import expect_fails_rule, expect_passes_rule


def undefined_fragment(fragment_name, line, column):
    return {
        "message": KnownFragmentNames.unknown_fragment_message(fragment_name),
        "locations": [SourceLocation(line, column)],
    }


def test_known_fragment_names_are_valid():
    expect_passes_rule(
        KnownFragmentNames,
        """
    {
        human(id: 4) {
            ...HumanFields1
            ... on Human {
                ...HumanFields2
            }
            ... {
                name
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


def test_unknown_fragment_names_are_invalid():
    expect_fails_rule(
        KnownFragmentNames,
        """
    {
        human(id: 4) {
            ...UnknownFragment1
            ... on Human {
                ...UnknownFragment2
            }
        }
    }
    fragment HumanFields on Human {
        name
        ...UnknownFragment3
    }
    """,
        [
            undefined_fragment("UnknownFragment1", 4, 16),
            undefined_fragment("UnknownFragment2", 6, 20),
            undefined_fragment("UnknownFragment3", 12, 12),
        ],
    )
