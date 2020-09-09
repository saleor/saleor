from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from ..validators import validate_price_precision


@pytest.mark.parametrize(
    "value, currency",
    [
        (Decimal("1.1200"), "USD"),
        (Decimal("1.12"), "USD"),
        (Decimal("1"), "USD"),
        (Decimal("1"), "ISK"),
        (Decimal("1.00"), "ISK"),
        (Decimal("5.12"), None),
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
