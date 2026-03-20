import pydantic_core
import pytest


@pytest.fixture
def no_link_rel(cleaner_settings):
    """Disable ``rel`` attribute for links.

    This disables appending `rel="noopener noreferrer"` to link which simplifies
    tests.
    """
    cleaner_settings.link_rel = None


def assert_pydantic_errors(
    exc: pydantic_core.ValidationError, expected_errors: list[dict]
) -> None:
    actual_errors = exc.errors()
    assert len(actual_errors) == len(expected_errors)
    for idx, err in enumerate(actual_errors):
        for k, v in expected_errors[idx].items():
            assert err[k] == v
