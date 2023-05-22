import decimal

import pytest
from pydantic import ValidationError

from ....core.taxes import TaxData, TaxLineData
from ..utils import parse_tax_data


def test_unsafe_parse_tax_line_data_success(tax_line_data_response):
    # when
    tax_line_data = TaxLineData.parse_obj(tax_line_data_response)

    # then
    assert not tax_line_data.total_gross_amount.compare(decimal.Decimal("12.34"))
    assert not tax_line_data.total_net_amount.compare(decimal.Decimal("12.34"))
    assert tax_line_data.tax_rate == decimal.Decimal("23")


def test_unsafe_parse_tax_line_data_keyerror(tax_line_data_response):
    # given
    tax_line_data_response["total_net_amount_v2"] = tax_line_data_response[
        "total_net_amount"
    ]
    del tax_line_data_response["total_net_amount"]

    # when
    with pytest.raises(ValidationError):
        TaxLineData.parse_obj(tax_line_data_response)


def test_unsafe_parse_tax_line_data_decimalexception(tax_line_data_response):
    # given
    tax_line_data_response["total_net_amount"] = "invalid value"

    # when
    with pytest.raises(ValidationError):
        TaxLineData.parse_obj(tax_line_data_response)


def test_unsafe_parse_tax_data_success(tax_data_response):
    # when
    tax_data = TaxData.parse_obj(tax_data_response)

    # then
    assert not tax_data.shipping_price_gross_amount.compare(decimal.Decimal("12.34"))
    assert not tax_data.shipping_price_net_amount.compare(decimal.Decimal("12.34"))
    assert tax_data.shipping_tax_rate == decimal.Decimal("23")
    assert len(tax_data.lines) == 5


def test_unsafe_parse_tax_data_keyerror(tax_data_response):
    # given
    tax_data_response["shipping_tax_rate_2"] = tax_data_response["shipping_tax_rate"]
    del tax_data_response["shipping_tax_rate"]

    # when
    with pytest.raises(ValidationError):
        TaxData.parse_obj(tax_data_response)


def test_unsafe_parse_tax_data_decimalexception(tax_data_response):
    # given
    tax_data_response["shipping_price_gross_amount"] = "invalid value"

    # when
    with pytest.raises(ValidationError):
        TaxData.parse_obj(tax_data_response)


def test_parse_tax_data_success(tax_data_response):
    # when
    tax_data = parse_tax_data(tax_data_response)

    # then
    assert isinstance(tax_data, TaxData)


def test_parse_tax_data_keyerror(tax_data_response):
    # given
    tax_data_response["shipping_tax_rate_2"] = tax_data_response["shipping_tax_rate"]
    del tax_data_response["shipping_tax_rate"]

    # when
    tax_data = parse_tax_data(tax_data_response)

    # then
    assert tax_data is None


def test_parse_tax_data_decimalexception(tax_data_response):
    # given
    tax_data_response["shipping_price_gross_amount"] = "invalid value"

    # when
    tax_data = parse_tax_data(tax_data_response)

    # then
    assert tax_data is None


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
    assert parse_tax_data(response_data) is None
