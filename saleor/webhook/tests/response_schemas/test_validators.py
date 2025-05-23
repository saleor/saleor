import pytest

from saleor.webhook.response_schemas.utils.validators import lower_values


@pytest.mark.parametrize(
    ("input_value", "expected_output"),
    [
        ("HELLO", "hello"),
        ("world", "world"),
        (["HELLO", "WORLD"], ["hello", "world"]),
        (["Python", "TEST"], ["python", "test"]),
        ([], []),
        (None, None),
        (["MiXeD", "CaSe"], ["mixed", "case"]),
    ],
)
def test_lower_values(input_value, expected_output):
    assert lower_values(input_value) == expected_output
