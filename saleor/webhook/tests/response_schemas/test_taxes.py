from decimal import Decimal

import pytest
from pydantic import ValidationError

from ....core.prices import MAXIMUM_PRICE
from ...response_schemas.taxes import CalculateTaxesSchema, LineCalculateTaxesSchema


@pytest.mark.parametrize(
    "data",
    [
        # Decimal values
        {
            "tax_rate": Decimal("20.12"),
            "total_gross_amount": Decimal("100.33"),
            "total_net_amount": Decimal("80.00"),
        },
        # String values with decimal points
        {
            "tax_rate": "120.12",
            "total_gross_amount": "100.33",
            "total_net_amount": "80.23",
        },
        # String values
        {
            "tax_rate": "20",
            "total_gross_amount": "100",
            "total_net_amount": "80",
        },
        # Integer values
        {
            "tax_rate": 20,
            "total_gross_amount": 100,
            "total_net_amount": 80,
        },
        # Float values
        {
            "tax_rate": 20.11,
            "total_gross_amount": 100.21,
            "total_net_amount": 80.32,
        },
    ],
)
def test_line_calculate_taxes_schema_valid(data):
    # when
    line_model = LineCalculateTaxesSchema.model_validate(data)

    # then
    assert line_model.tax_rate == Decimal(str(data["tax_rate"]))
    assert line_model.total_gross_amount == Decimal(str(data["total_gross_amount"]))
    assert line_model.total_net_amount == Decimal(str(data["total_net_amount"]))


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
        # Negative tax_rate
        {
            "tax_rate": Decimal("-120.00"),
            "total_gross_amount": Decimal("100.00"),
            "total_net_amount": Decimal("80.00"),
        },
        # Invalid total_gross_amount (greater than MAXIMUM_PRICE)
        {
            "tax_rate": Decimal("20.00"),
            "total_gross_amount": 100000000000000000000,
            "total_net_amount": Decimal("80.00"),
        },
        # Invalid total_net_amount (greater than MAXIMUM_PRICE)
        {
            "tax_rate": Decimal("20.00"),
            "total_gross_amount": Decimal("100.00"),
            "total_net_amount": Decimal(100000000000000000000),
        },
    ],
)
def test_line_calculate_taxes_schema_invalid(data):
    """Test LineCalculateTaxesSchema with invalid data."""
    with pytest.raises(ValidationError) as e:
        LineCalculateTaxesSchema(**data)

    assert len(e.value.errors()) == 1


@pytest.mark.parametrize(
    "data",
    [
        {
            "shipping_tax_rate": Decimal("10.00"),
            "shipping_price_gross_amount": Decimal("110.00"),
            "shipping_price_net_amount": Decimal("100.00"),
            "lines": [
                {
                    "tax_rate": Decimal("20.00"),
                    "total_gross_amount": Decimal("120.00"),
                    "total_net_amount": Decimal("100.00"),
                },
                {
                    "tax_rate": "15.00",
                    "total_gross_amount": "115.00",
                    "total_net_amount": "100.00",
                },
            ],
        },
        {
            "shipping_tax_rate": 110,
            "shipping_price_gross_amount": 110,
            "shipping_price_net_amount": 100,
            "lines": [],
        },
        {
            "shipping_tax_rate": "10.00",
            "shipping_price_gross_amount": "110.00",
            "shipping_price_net_amount": "100.00",
            "lines": [
                {
                    "tax_rate": "20.00",
                    "total_gross_amount": "120.00",
                    "total_net_amount": "100.00",
                },
            ],
        },
    ],
)
def test_calculate_taxes_schema_valid(data):
    # given
    expected_line_count = len(data["lines"])

    # when
    calculate_taxes_model = CalculateTaxesSchema.model_validate(
        data, context={"expected_line_count": expected_line_count}
    )

    # then
    assert calculate_taxes_model.shipping_tax_rate == Decimal(data["shipping_tax_rate"])
    assert calculate_taxes_model.shipping_price_gross_amount == Decimal(
        data["shipping_price_gross_amount"]
    )
    assert calculate_taxes_model.shipping_price_net_amount == Decimal(
        data["shipping_price_net_amount"]
    )
    assert len(calculate_taxes_model.lines) == expected_line_count


@pytest.mark.parametrize(
    ("data", "expected_line_count"),
    [
        # Invalid case with mismatched line count
        (
            {
                "shipping_tax_rate": Decimal("10.00"),
                "shipping_price_gross_amount": Decimal("110.00"),
                "shipping_price_net_amount": Decimal("100.00"),
                "lines": [
                    {
                        "tax_rate": Decimal("20.00"),
                        "total_gross_amount": Decimal("120.00"),
                        "total_net_amount": Decimal("100.00"),
                    }
                ],
            },
            2,
        ),
        # Invalid case with negative shipping_price_gross_amount
        (
            {
                "shipping_tax_rate": Decimal("10.00"),
                "shipping_price_gross_amount": -111,
                "shipping_price_net_amount": Decimal("100.00"),
                "lines": [],
            },
            0,
        ),
        # Invalid case with negative shipping_price_net_amount
        (
            {
                "shipping_tax_rate": 10,
                "shipping_price_gross_amount": 111,
                "shipping_price_net_amount": -100,
                "lines": [],
            },
            0,
        ),
        # Invalid case with negative shipping_tax_rate
        (
            {
                "shipping_tax_rate": -Decimal("120.00"),
                "shipping_price_gross_amount": "110",
                "shipping_price_net_amount": "100",
                "lines": [
                    {
                        "tax_rate": Decimal("20.00"),
                        "total_gross_amount": Decimal("120.00"),
                        "total_net_amount": Decimal("100.00"),
                    }
                ],
            },
            1,
        ),
        # Invalid case with shipping_price_gross_amount (greater than MAXIMUM_PRICE)
        (
            {
                "shipping_tax_rate": Decimal("100.00"),
                "shipping_price_gross_amount": MAXIMUM_PRICE + 1,
                "shipping_price_net_amount": "100",
                "lines": [
                    {
                        "tax_rate": Decimal("20.00"),
                        "total_gross_amount": Decimal("120.00"),
                        "total_net_amount": Decimal("100.00"),
                    }
                ],
            },
            1,
        ),
        # Invalid case with shipping_price_net_amount (greater than MAXIMUM_PRICE)
        (
            {
                "shipping_tax_rate": Decimal("100.00"),
                "shipping_price_gross_amount": "100",
                "shipping_price_net_amount": MAXIMUM_PRICE + 1,
                "lines": [
                    {
                        "tax_rate": Decimal("20.00"),
                        "total_gross_amount": Decimal("120.00"),
                        "total_net_amount": Decimal("100.00"),
                    }
                ],
            },
            1,
        ),
    ],
)
def test_calculate_taxes_schema_invalid(data, expected_line_count):
    """Test CalculateTaxesSchema with invalid data."""
    with pytest.raises(ValidationError) as e:
        CalculateTaxesSchema.model_validate(
            data, context={"expected_line_count": expected_line_count}
        )

    assert len(e.value.errors()) == 1


def test_calculate_taxes_schema_missing_context():
    """Test CalculateTaxesSchema with invalid data."""
    # given
    data = {}

    # when & then
    with pytest.raises(ValidationError):
        CalculateTaxesSchema.model_validate(data)
