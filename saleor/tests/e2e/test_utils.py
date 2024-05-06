import json
from unittest.mock import Mock

from .utils import request_matcher


def test_equal_dicts():
    r1 = Mock(
        body=Mock(
            decode=Mock(return_value=json.dumps({"key1": "value1", "key2": "value2"}))
        )
    )
    r2 = Mock(
        body=Mock(
            decode=Mock(return_value=json.dumps({"key1": "value1", "key2": "value2"}))
        )
    )

    result = request_matcher(r1, r2)
    assert result is True


def test_unequal_dicts():
    r1 = Mock(
        body=Mock(
            decode=Mock(return_value=json.dumps({"key1": "value1", "key2": "value2"}))
        )
    )
    r2 = Mock(
        body=Mock(
            decode=Mock(return_value=json.dumps({"key1": "value1", "key2": "value3"}))
        )
    )

    result = request_matcher(r1, r2)
    assert result is False


def test_missing_key_in_r2():
    r1 = Mock(
        body=Mock(
            decode=Mock(return_value=json.dumps({"key1": "value1", "key2": "value2"}))
        )
    )
    r2 = Mock(body=Mock(decode=Mock(return_value=json.dumps({"key1": "value1"}))))

    result = request_matcher(r1, r2)
    assert result is False


def test_extra_key_in_r2():
    r1 = Mock(
        body=Mock(
            decode=Mock(return_value=json.dumps({"key1": "value1", "key2": "value2"}))
        )
    )
    r2 = Mock(
        body=Mock(
            decode=Mock(
                return_value=json.dumps(
                    {"key1": "value1", "key2": "value2", "key3": "value3"}
                )
            )
        )
    )

    result = request_matcher(r1, r2)
    assert result is False


def test_different_sorting_order_in_r2():
    r1 = Mock(
        body=Mock(
            decode=Mock(return_value=json.dumps({"key1": "value1", "key2": "value2"}))
        )
    )
    r2 = Mock(
        body=Mock(
            decode=Mock(return_value=json.dumps({"key2": "value2", "key1": "value1"}))
        )
    )

    result = request_matcher(r1, r2)
    assert result is True


def test_nested_keys():
    r1 = Mock(
        body=Mock(
            decode=Mock(
                return_value=json.dumps(
                    {
                        "key1": "value1",
                        "key2": {
                            "key3": "value3",
                            "key4": {
                                "key5": "value5",
                            },
                        },
                    }
                )
            )
        )
    )
    r2 = Mock(
        body=Mock(
            decode=Mock(
                return_value=json.dumps(
                    {
                        "key1": "value1",
                        "key2": {
                            "key3": "value3",
                            "key4": {
                                "key5": "value5",
                            },
                        },
                    }
                )
            )
        )
    )

    result = request_matcher(r1, r2)
    assert result is True
