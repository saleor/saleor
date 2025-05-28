import pytest
from pydantic import ValidationError

from ...core.taxes import TaxData
from ..transport.taxes import (
    parse_tax_data,
)


def test_parse_tax_data_success(tax_data_response):
    # given
    line_count = len(tax_data_response["lines"])

    # when
    tax_data = parse_tax_data(tax_data_response, line_count)

    # then
    assert isinstance(tax_data, TaxData)


def test_parse_tax_data_keyerror(tax_data_response):
    # given
    tax_data_response["shipping_tax_rate_2"] = tax_data_response["shipping_tax_rate"]
    del tax_data_response["shipping_tax_rate"]
    line_count = len(tax_data_response["lines"])

    # when & then
    with pytest.raises(ValidationError):
        parse_tax_data(tax_data_response, line_count)


def test_parse_tax_data_decimalexception(tax_data_response):
    # given
    tax_data_response["shipping_price_gross_amount"] = "invalid value"
    line_count = len(tax_data_response["lines"])

    # when & then
    with pytest.raises(ValidationError):
        parse_tax_data(tax_data_response, line_count)


@pytest.mark.parametrize(
    "response_data",
    [
        [],
        1.0,
        "text",
        None,
        {"lines": {}},
        {"lines": 1.0},
        {"lines": "text"},
        {"lines": None},
        {"lines": [[]]},
        {"lines": [1.0]},
        {"lines": ["text"]},
        {"lines": [None]},
    ],
)
def test_parse_tax_data_malformed(response_data):
    with pytest.raises(ValidationError):
        parse_tax_data(response_data, 1)
