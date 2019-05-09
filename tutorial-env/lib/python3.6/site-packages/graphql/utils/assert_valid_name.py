import re

NAME_PATTERN = r"^[_a-zA-Z][_a-zA-Z0-9]*$"
COMPILED_NAME_PATTERN = re.compile(NAME_PATTERN)


def assert_valid_name(name):
    # type: (str) -> None
    """Helper to assert that provided names are valid."""
    assert COMPILED_NAME_PATTERN.match(
        name
    ), 'Names must match /{}/ but "{}" does not.'.format(NAME_PATTERN, name)
    return None
