from graphql.language.location import SourceLocation


def test_repr_source_location():
    # type: () -> None
    loc = SourceLocation(10, 25)
    assert repr(loc) == "SourceLocation(line=10, column=25)"
