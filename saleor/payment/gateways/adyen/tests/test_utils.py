from unittest import mock

import pytest

from .... import PaymentError
from ..utils import (
    append_klarna_data,
    get_price_amount,
    get_shopper_locale_value,
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
