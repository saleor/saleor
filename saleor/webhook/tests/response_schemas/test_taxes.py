from decimal import Decimal

import pytest
from pydantic import ValidationError

from ...response_schemas.taxes import LineCalculateTaxesSchema


@pytest.mark.parametrize(
    "data",
    [
        # Valid case
        {
            "tax_rate": Decimal("20.12"),
            "total_gross_amount": Decimal("100.33"),
            "total_net_amount": Decimal("80.00"),
        },
        {
            "tax_rate": "20.12",
            "total_gross_amount": "100.33",
            "total_net_amount": "80.23",
        },
        {
            "tax_rate": "20",
            "total_gross_amount": "100",
            "total_net_amount": "80",
        },
        {
            "tax_rate": 20,
            "total_gross_amount": 100,
            "total_net_amount": 80,
        },
    ],
)
def test_line_calculate_taxes_schema_valid(data):
    # when
    line_model = LineCalculateTaxesSchema.model_validate(data)

    # then
    assert line_model.tax_rate == Decimal(data["tax_rate"])
    assert line_model.total_gross_amount == Decimal(data["total_gross_amount"])
    assert line_model.total_net_amount == Decimal(data["total_net_amount"])


@pytest.mark.parametrize(
    "data",
    [
        # Negative tax_rate
        {
            "tax_rate": -5,
            "total_gross_amount": 100,
            "total_net_amount": Decimal("80.00"),
        },
        # Negative total_gross_amount
        {
            "tax_rate": 5,
            "total_gross_amount": -100,
            "total_net_amount": Decimal("80.00"),
        },
        # Negative total_net_amount
        {
            "tax_rate": 5,
            "total_gross_amount": 100,
            "total_net_amount": Decimal("-80.00"),
        },
        # Invalid tax_rate (greater than 100)
        {
            "tax_rate": Decimal("120.00"),
            "total_gross_amount": Decimal("100.00"),
            "total_net_amount": Decimal("80.00"),
        },
        # Invalid total_gross_amount (greater than MAXIMUM_PRICE)
        {
            "tax_rate": Decimal("20.00"),
            "total_gross_amount": 100000000000,
            "total_net_amount": Decimal("80.00"),
        },
        # Invalid total_net_amount (greater than MAXIMUM_PRICE)
        {
            "tax_rate": Decimal("20.00"),
            "total_gross_amount": Decimal("100.00"),
            "total_net_amount": Decimal("10000000000"),
        },
    ],
)
def test_line_calculate_taxes_schema_invalid(data):
    """Test LineCalculateTaxesSchema with invalid data."""
    with pytest.raises(ValidationError):
        LineCalculateTaxesSchema(**data)
