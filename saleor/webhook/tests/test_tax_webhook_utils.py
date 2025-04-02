import decimal

import pytest
from pydantic import ValidationError

from ...core.taxes import TaxData
from ..transport.utils import (
    _unsafe_parse_tax_line_data,
    parse_tax_data,
)


def test_unsafe_parse_tax_line_data_success(tax_line_data_response):
    # when
    tax_line_data = _unsafe_parse_tax_line_data(tax_line_data_response)

    # then
    assert not tax_line_data.total_gross_amount.compare(
        decimal.Decimal(tax_line_data_response["total_gross_amount"])
    )
    assert not tax_line_data.total_net_amount.compare(
        decimal.Decimal(tax_line_data_response["total_net_amount"])
    )
    assert tax_line_data.tax_rate == tax_line_data_response["tax_rate"]


def test_unsafe_parse_tax_line_data_keyerror(tax_line_data_response):
    # given
    tax_line_data_response["total_net_amount_v2"] = tax_line_data_response[
        "total_net_amount"
    ]
    del tax_line_data_response["total_net_amount"]

    # when
    with pytest.raises(KeyError):
        _unsafe_parse_tax_line_data(tax_line_data_response)


def test_unsafe_parse_tax_line_data_decimalexception(tax_line_data_response):
    # given
    tax_line_data_response["total_net_amount"] = "invalid value"

    # when
    with pytest.raises(decimal.DecimalException):
        _unsafe_parse_tax_line_data(tax_line_data_response)


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
