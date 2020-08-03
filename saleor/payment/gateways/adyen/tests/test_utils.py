from decimal import Decimal
from unittest import mock

import pytest
from prices import Money, TaxedMoney

from .....core.prices import quantize_price
from .... import PaymentError
from ..utils import (
    append_klarna_data,
    convert_adyen_price_format,
    get_price_amount,
    get_shopper_locale_value,
    request_data_for_gateway_config,
    request_data_for_payment,
)


@pytest.mark.parametrize(
    "language_code, shopper_locale", [("ja", "ja_JP"), ("zz", "en_US"), ("en", "en_US")]
)
def test_get_shopper_locale_value(language_code, shopper_locale, settings):
    # given
    settings.LANGUAGE_CODE = language_code

    # when
    result = get_shopper_locale_value()

    # then
    assert result == shopper_locale


def test_append_klarna_data(dummy_payment_data, payment_dummy, checkout_with_item):
    # given
    checkout_with_item.payments.add(payment_dummy)
    line = checkout_with_item.lines.first()
    payment_data = {
        "reference": "test",
    }

    # when
    result = append_klarna_data(dummy_payment_data, payment_data)

    # then
    total = get_price_amount(
        line.variant.price_amount * line.quantity, line.variant.currency
    )
    assert result == {
        "reference": "test",
        "shopperLocale": "en_US",
        "shopperReference": dummy_payment_data.customer_email,
        "countryCode": str(checkout_with_item.country),
        "shopperEmail": dummy_payment_data.customer_email,
        "lineItems": [
            {
                "description": line.variant.product.description,
                "quantity": line.quantity,
                "id": line.variant.sku,
                "taxAmount": "0",
                "taxPercentage": 0,
                "amountExcludingTax": total,
                "amountIncludingTax": total,
            }
        ],
    }


@mock.patch("saleor.payment.gateways.adyen.utils.checkout_line_total")
def test_append_klarna_data_tax_included(
    mocked_checkout_line_total, dummy_payment_data, payment_dummy, checkout_with_item
):
    # given
    tax_percent = 5
    net = Money(10, "USD")
    gross = tax_percent * net / 100 + net
    mocked_checkout_line_total.return_value = quantize_price(
        TaxedMoney(net=net, gross=gross), "USD"
    )

    checkout_with_item.payments.add(payment_dummy)
    line = checkout_with_item.lines.first()
    payment_data = {
        "reference": "test",
    }

    # when
    result = append_klarna_data(dummy_payment_data, payment_data)

    # then
    assert result == {
        "reference": "test",
        "shopperLocale": "en_US",
        "shopperReference": dummy_payment_data.customer_email,
        "countryCode": str(checkout_with_item.country),
        "shopperEmail": dummy_payment_data.customer_email,
        "lineItems": [
            {
                "description": line.variant.product.description,
                "quantity": line.quantity,
                "id": line.variant.sku,
                "taxAmount": get_price_amount((gross - net).amount, "USD"),
                "taxPercentage": tax_percent,
                "amountExcludingTax": get_price_amount(net.amount, "USD"),
                "amountIncludingTax": get_price_amount(gross.amount, "USD"),
            }
        ],
    }


def test_request_data_for_payment_payment_not_valid(dummy_payment_data):
    # given
    dummy_payment_data.data = {
        "is_valid": False,
    }

    # when
    with pytest.raises(PaymentError) as e:
        request_data_for_payment(
            dummy_payment_data,
            "https://www.example.com",
            "MerchantTestAccount",
            "https://www.example.com",
        )

    # then
    assert str(e._excinfo[1]) == "Payment data are not valid"


def test_request_data_for_payment(dummy_payment_data):
    # given
    return_url = "https://www.example.com"
    merchant_account = "MerchantTestAccount"
    data = {
        "is_valid": True,
        "riskData": {"clientData": "test_client_data"},
        "paymentMethod": {"type": "scheme"},
        "browserInfo": {"acceptHeader": "*/*", "colorDepth": 30, "language": "pl"},
        "billingAddress": {"address": "test_address"},
        "shopperIP": "123",
    }
    dummy_payment_data.data = data

    # when
    result = request_data_for_payment(
        dummy_payment_data, return_url, merchant_account, return_url,
    )

    # then
    assert result == {
        "amount": {
            "value": get_price_amount(
                dummy_payment_data.amount, dummy_payment_data.currency
            ),
            "currency": dummy_payment_data.currency,
        },
        "reference": dummy_payment_data.payment_id,
        "paymentMethod": {"type": "scheme"},
        "returnUrl": return_url,
        "merchantAccount": merchant_account,
        "origin": return_url,
        "shopperIP": data["shopperIP"],
        "billingAddress": data["billingAddress"],
        "browserInfo": data["browserInfo"],
    }


@mock.patch("saleor.payment.gateways.adyen.utils.append_klarna_data")
def test_request_data_for_payment_append_klarna_data(
    append_klarna_data_mock, dummy_payment_data
):
    # given
    return_url = "https://www.example.com"
    merchant_account = "MerchantTestAccount"
    data = {
        "is_valid": True,
        "riskData": {"clientData": "test_client_data"},
        "paymentMethod": {"type": "klarna"},
        "browserInfo": {"acceptHeader": "*/*", "colorDepth": 30, "language": "pl"},
        "billingAddress": {"address": "test_address"},
        "shopperIP": "123",
    }
    dummy_payment_data.data = data
    klarna_result = {
        "amount": {
            "value": get_price_amount(
                dummy_payment_data.amount, dummy_payment_data.currency
            ),
            "currency": dummy_payment_data.currency,
        },
        "reference": dummy_payment_data.payment_id,
        "paymentMethod": {"type": "scheme"},
        "returnUrl": return_url,
        "merchantAccount": merchant_account,
        "origin": return_url,
        "shopperIP": data["shopperIP"],
        "billingAddress": data["billingAddress"],
        "browserInfo": data["browserInfo"],
        "shopperLocale": "test_shopper",
        "shopperEmail": "test_email",
    }
    append_klarna_data_mock.return_value = klarna_result

    # when
    result = request_data_for_payment(
        dummy_payment_data, return_url, merchant_account, return_url,
    )

    # then
    assert result == klarna_result


@pytest.mark.parametrize(
    "value, currency, expected_result",
    [
        (Decimal(1000), "EUR", Decimal(10)),
        (Decimal(1), "PLN", Decimal("0.01")),
        (Decimal(51), "US", Decimal("0.51")),
    ],
)
def test_convert_adyen_price_format(value, currency, expected_result):
    # when
    result = convert_adyen_price_format(value, currency)

    # then
    assert result == expected_result


@pytest.mark.parametrize(
    "value, currency, expected_result",
    [
        (Decimal(10), "EUR", "1000"),
        (Decimal(1), "PLN", "100"),
        (Decimal(100), "US", "10000"),
    ],
)
def test_get_price_amount(value, currency, expected_result):
    # when
    result = get_price_amount(value, currency)

    # then
    assert result == expected_result


def test_request_data_for_gateway_config(checkout, address):
    # given
    checkout.billing_address = address
    merchant_account = "test_account"

    # when
    response_config = request_data_for_gateway_config(checkout, merchant_account)

    # then
    assert response_config == {
        "merchantAccount": merchant_account,
        "countryCode": checkout.billing_address.country,
        "channel": "web",
    }


def test_request_data_for_gateway_config_no_country(checkout, address, settings):
    # given
    merchant_account = "test_account"

    # when
    response_config = request_data_for_gateway_config(checkout, merchant_account)

    # then
    assert response_config == {
        "merchantAccount": merchant_account,
        "countryCode": settings.DEFAULT_COUNTRY,
        "channel": "web",
    }
