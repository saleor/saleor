import resource
from unittest.mock import patch

import pytest
from django.core.exceptions import ImproperlyConfigured

from ..rlimit import RLIMIT_TYPE, validate_and_set_rlimit


@patch("saleor.core.rlimit.resource.setrlimit")
def test_limit_passed_as_string(mock_setrlimit):
    # given
    soft_limit = "1000"
    hard_limit = "2000"
    expected_soft_limit = int(soft_limit) * 1000 * 1000
    expected_hard_limit = int(hard_limit) * 1000 * 1000

    # when
    validate_and_set_rlimit(soft_limit, hard_limit)

    # then
    mock_setrlimit.assert_called_once_with(
        RLIMIT_TYPE,
        (expected_soft_limit, expected_hard_limit),
    )


@patch("saleor.core.rlimit.resource.setrlimit")
def test_limit_passed_as_int(mock_setrlimit):
    # given
    soft_limit = 1000
    hard_limit = 2000
    expected_soft_limit = int(soft_limit) * 1000 * 1000
    expected_hard_limit = int(hard_limit) * 1000 * 1000

    # when
    validate_and_set_rlimit(soft_limit, hard_limit)

    # then
    mock_setrlimit.assert_called_once_with(
        RLIMIT_TYPE,
        (expected_soft_limit, expected_hard_limit),
    )


@patch("saleor.core.rlimit.resource.setrlimit")
def test_no_limits(mock_setrlimit):
    # given
    soft_limit = None
    hard_limit = None
    expected_soft_limit = resource.RLIM_INFINITY
    expected_hard_limit = resource.RLIM_INFINITY

    # when
    validate_and_set_rlimit(soft_limit, hard_limit)

    # then
    mock_setrlimit.assert_called_once_with(
        RLIMIT_TYPE,
        (expected_soft_limit, expected_hard_limit),
    )


@patch("saleor.core.rlimit.resource.setrlimit")
def test_only_soft_limit_set(mock_setrlimit):
    # given
    soft_limit = 1000
    hard_limit = None

    # when
    with pytest.raises(ImproperlyConfigured):
        validate_and_set_rlimit(soft_limit, hard_limit)

    # then
    mock_setrlimit.assert_not_called()


@patch("saleor.core.rlimit.resource.setrlimit")
def test_only_hard_limit_set(mock_setrlimit):
    # given
    soft_limit = None
    hard_limit = 1000

    # when
    with pytest.raises(ImproperlyConfigured):
        validate_and_set_rlimit(soft_limit, hard_limit)

    # then
    mock_setrlimit.assert_not_called()


@patch("saleor.core.rlimit.resource.setrlimit")
def test_negative_soft_limit(mock_setrlimit):
    # given
    soft_limit = -10
    hard_limit = 1000

    # when
    with pytest.raises(ImproperlyConfigured):
        validate_and_set_rlimit(soft_limit, hard_limit)

    # then
    mock_setrlimit.assert_not_called()


@patch("saleor.core.rlimit.resource.setrlimit")
def test_negative_hard_limit(mock_setrlimit):
    # given
    soft_limit = 1000
    hard_limit = -10

    # when
    with pytest.raises(ImproperlyConfigured):
        validate_and_set_rlimit(soft_limit, hard_limit)

    # then
    mock_setrlimit.assert_not_called()


@patch("saleor.core.rlimit.resource.setrlimit")
def test_invalid_soft_limit(mock_setrlimit):
    # given
    soft_limit = "invalid"
    hard_limit = 1000

    # when
    with pytest.raises(ImproperlyConfigured):
        validate_and_set_rlimit(soft_limit, hard_limit)

    # then
    mock_setrlimit.assert_not_called()


@patch("saleor.core.rlimit.resource.setrlimit")
def test_invalid_hard_limit(mock_setrlimit):
    # given
    soft_limit = 1000
    hard_limit = "invalid"

    # when
    with pytest.raises(ImproperlyConfigured):
        validate_and_set_rlimit(soft_limit, hard_limit)

    # then
    mock_setrlimit.assert_not_called()


@patch("saleor.core.rlimit.resource.setrlimit")
def test_soft_limit_greater_than_hard_limit(mock_setrlimit):
    # given
    soft_limit = 2000
    hard_limit = 1000

    # when
    with pytest.raises(ImproperlyConfigured):
        validate_and_set_rlimit(soft_limit, hard_limit)

    # then
    mock_setrlimit.assert_not_called()
