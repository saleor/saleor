import decimal

import pytest

from ....core.taxes import TaxData, TaxType
from ..utils import (
    _unsafe_parse_tax_data,
    _unsafe_parse_tax_line_data,
    parse_tax_codes,
    parse_tax_data,
)


def test_unsafe_parse_tax_line_data_success(tax_line_data_response):
    # when
    tax_line_data = _unsafe_parse_tax_line_data(tax_line_data_response)

    # then
    assert tax_line_data.id == tax_line_data_response["id"]
    assert tax_line_data.currency == tax_line_data_response["currency"]
    assert not tax_line_data.unit_net_amount.compare(
        decimal.Decimal(tax_line_data_response["unit_net_amount"])
    )
    assert not tax_line_data.unit_gross_amount.compare(
        decimal.Decimal(tax_line_data_response["unit_gross_amount"])
    )
    assert not tax_line_data.total_gross_amount.compare(
        decimal.Decimal(tax_line_data_response["total_gross_amount"])
    )
    assert not tax_line_data.total_net_amount.compare(
        decimal.Decimal(tax_line_data_response["total_net_amount"])
    )


def test_unsafe_parse_tax_line_data_keyerror(tax_line_data_response):
    # given
    tax_line_data_response["currencyy"] = tax_line_data_response["currency"]
    del tax_line_data_response["currency"]

    # when
    with pytest.raises(KeyError):
        _unsafe_parse_tax_line_data(tax_line_data_response)


def test_unsafe_parse_tax_line_data_decimalexception(tax_line_data_response):
    # given
    tax_line_data_response["unit_net_amount"] = "invalid value"

    # when
    with pytest.raises(decimal.DecimalException):
        _unsafe_parse_tax_line_data(tax_line_data_response)


def test_unsafe_parse_tax_data_success(tax_data_response):
    # when
    tax_data = _unsafe_parse_tax_data(tax_data_response)

    # then
    assert tax_data.currency == tax_data_response["currency"]
    assert not tax_data.total_net_amount.compare(
        decimal.Decimal(tax_data_response["total_net_amount"])
    )
    assert not tax_data.total_gross_amount.compare(
        decimal.Decimal(tax_data_response["total_gross_amount"])
    )
    assert not tax_data.subtotal_net_amount.compare(
        decimal.Decimal(tax_data_response["subtotal_net_amount"])
    )
    assert not tax_data.subtotal_gross_amount.compare(
        decimal.Decimal(tax_data_response["subtotal_gross_amount"])
    )
    assert not tax_data.shipping_price_gross_amount.compare(
        decimal.Decimal(tax_data_response["shipping_price_gross_amount"])
    )
    assert not tax_data.shipping_price_net_amount.compare(
        decimal.Decimal(tax_data_response["shipping_price_net_amount"])
    )
    assert tax_data.lines == [
        _unsafe_parse_tax_line_data(line) for line in tax_data_response["lines"]
    ]


def test_unsafe_parse_tax_data_keyerror(tax_data_response):
    # given
    tax_data_response["currencyy"] = tax_data_response["currency"]
    del tax_data_response["currency"]

    # when
    with pytest.raises(KeyError):
        _unsafe_parse_tax_data(tax_data_response)


def test_unsafe_parse_tax_data_decimalexception(tax_data_response):
    # given
    tax_data_response["total_gross_amount"] = "invalid value"

    # when
    with pytest.raises(decimal.DecimalException):
        _unsafe_parse_tax_data(tax_data_response)


def test_parse_tax_data_success(tax_data_response):
    # when
    tax_data = parse_tax_data(tax_data_response)

    # then
    assert isinstance(tax_data, TaxData)


def test_parse_tax_data_keyerror(tax_data_response):
    # given
    tax_data_response["currencyy"] = tax_data_response["currency"]
    del tax_data_response["currency"]

    # when
    tax_data = parse_tax_data(tax_data_response)

    # then
    assert tax_data is None


def test_parse_tax_data_decimalexception(tax_data_response):
    # given
    tax_data_response["total_gross_amount"] = "invalid value"

    # when
    tax_data = parse_tax_data(tax_data_response)

    # then
    assert tax_data is None


def test_parse_tax_codes_success(tax_codes_response):
    assert parse_tax_codes(tax_codes_response) == [
        TaxType(code=tax["code"], description=tax["description"])
        for tax in tax_codes_response
    ]


def test_parse_tax_codes_malformed():
    assert not parse_tax_codes({})


def test_parse_tax_codes_keyerror(tax_codes_response):
    # given
    tax_codes_response[0]["code_bad"] = tax_codes_response[0].pop("code")

    # when
    tax_codes = parse_tax_codes(tax_codes_response)

    # then
    assert not tax_codes


def test_parse_tax_codes_no_description(tax_codes_response):
    # given
    tax_codes_without_description_response = [
        {"code": tax["code"]} for tax in tax_codes_response
    ]

    # when
    tax_codes = parse_tax_codes(tax_codes_without_description_response)

    # then
    assert tax_codes == [
        TaxType(code=tax["code"], description=tax["code"]) for tax in tax_codes_response
    ]
