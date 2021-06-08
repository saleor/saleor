from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from graphql.error import GraphQLError

from ..validators import (
    validate_end_is_after_start,
    validate_one_of_args_is_in_query,
    validate_price_precision,
)


@pytest.mark.parametrize(
    "value, currency",
    [
        (Decimal("1.1200"), "USD"),
        (Decimal("1.12"), "USD"),
        (Decimal("1"), "USD"),
        (Decimal("1"), "ISK"),
        (Decimal("1.00"), "ISK"),
        (Decimal("5.12"), None),
        (Decimal("1000"), "USD"),
    ],
)
def test_validate_price_precision(value, currency):
    # when
    result = validate_price_precision(value, currency)

    # then
    assert result is None


@pytest.mark.parametrize(
    "value, currency",
    [
        (Decimal("1.1212"), "USD"),
        (Decimal("1.128"), "USD"),
        (Decimal("1.1"), "ISK"),
        (Decimal("1.11"), "ISK"),
        (Decimal("5.123"), None),
    ],
)
def test_validate_price_precision_raise_error(value, currency):
    with pytest.raises(ValidationError):
        validate_price_precision(value, currency)


def test_validate_end_is_after_start_raise_error():
    start_date = timezone.now() + timedelta(days=365)
    end_date = timezone.now() - timedelta(days=365)

    with pytest.raises(ValidationError) as error:
        validate_end_is_after_start(start_date, end_date)
    assert error.value.message == "End date cannot be before the start date."


def test_validate_one_of_args_is_in_query():
    assert validate_one_of_args_is_in_query("arg1", "present", "arg2", None) is None


def test_validate_one_of_args_is_in_query_false_args():
    with pytest.raises(GraphQLError) as error:
        validate_one_of_args_is_in_query("arg1", None, "arg2", "")
    assert (
        error.value.message == "At least one of arguments is required: 'arg1', 'arg2'."
    )


def test_validate_one_of_args_is_in_query_more_than_one_true():
    with pytest.raises(GraphQLError) as error:
        validate_one_of_args_is_in_query(
            "arg1", "present", "arg2", "present", "arg3", "present"
        )
    assert (
        error.value.message == "Argument 'arg1' cannot be combined with 'arg2', 'arg3'"
    )


def test_validate_one_of_args_is_in_query_single_arg():
    assert validate_one_of_args_is_in_query("arg1", "present") is None


def test_validate_one_of_args_is_in_query_single_arg_absent():
    with pytest.raises(GraphQLError) as error:
        validate_one_of_args_is_in_query("arg1", None) is None
    assert error.value.message == "At least one of arguments is required: 'arg1'."
