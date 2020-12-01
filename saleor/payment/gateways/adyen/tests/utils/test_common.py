import json
from decimal import Decimal
from unittest import mock

import pytest
from prices import Money, TaxedMoney

from saleor.core.prices import quantize_price
from saleor.payment import PaymentError
from saleor.payment.gateways.adyen.utils.common import (
    append_klarna_data,
    from_adyen_price,
    get_payment_method_info,
    get_shopper_locale_value,
    request_data_for_gateway_config,
    request_data_for_payment,
    to_adyen_price,
    update_payment_with_action_required_data,
)
from saleor.payment.interface import PaymentMethodInfo


@pytest.mark.parametrize(
    "country_code, shopper_locale", [("JP", "ja_JP"), ("ZZ", "en_US"), ("US", "en_US")]
)
def test_get_shopper_locale_value(country_code, shopper_locale, settings):
    # when
    result = get_shopper_locale_value(country_code)

    # then
    assert result == shopper_locale


def test_append_klarna_data(
    dummy_payment_data, payment_dummy, checkout_ready_to_complete
):
    # given
    checkout_ready_to_complete.payments.add(payment_dummy)
    channel_id = checkout_ready_to_complete.channel_id
    line = checkout_ready_to_complete.lines.first()
    payment_data = {
        "reference": "test",
    }
    country_code = checkout_ready_to_complete.get_country()

    # when
    result = append_klarna_data(dummy_payment_data, payment_data)

    # then
    variant_channel_listing = line.variant.channel_listings.get(channel_id=channel_id)
    variant_price = variant_channel_listing.price_amount
    variant_currency = variant_channel_listing.currency
    total = to_adyen_price(variant_price * line.quantity, variant_currency)
    assert result == {
        "reference": "test",
        "shopperLocale": get_shopper_locale_value(country_code),
        "shopperReference": dummy_payment_data.customer_email,
        "countryCode": country_code,
        "lineItems": [
            {
                "description": f"{line.variant.product.name}, {line.variant.name}",
                "quantity": line.quantity,
                "id": line.variant.sku,
                "taxAmount": "0",
                "taxPercentage": 0,
                "amountExcludingTax": total,
                "amountIncludingTax": total,
            },
            {
                "amountExcludingTax": "1000",
                "amountIncludingTax": "1000",
                "description": "Shipping - DHL",
                "id": f"Shipping:{checkout_ready_to_complete.shipping_method.id}",
                "quantity": 1,
                "taxAmount": "0",
                "taxPercentage": 0,
            },
        ],
    }


@mock.patch("saleor.payment.gateways.adyen.utils.common.checkout_line_total")
def test_append_klarna_data_tax_included(
    mocked_checkout_line_total,
    dummy_payment_data,
    payment_dummy,
    checkout_ready_to_complete,
):
    # given
    net = Money(100, "USD")
    gross = Money(123, "USD")
    # tax 23 %
    mocked_checkout_line_total.return_value = quantize_price(
        TaxedMoney(net=net, gross=gross), "USD"
    )
    country_code = checkout_ready_to_complete.get_country()

    checkout_ready_to_complete.payments.add(payment_dummy)
    line = checkout_ready_to_complete.lines.first()
    payment_data = {
        "reference": "test",
    }

    # when
    result = append_klarna_data(dummy_payment_data, payment_data)

    # then

    expected_result = {
        "reference": "test",
        "shopperLocale": get_shopper_locale_value(country_code),
        "shopperReference": dummy_payment_data.customer_email,
        "countryCode": country_code,
        "lineItems": [
            {
                "description": f"{line.variant.product.name}, {line.variant.name}",
                "quantity": line.quantity,
                "id": line.variant.sku,
                "taxAmount": to_adyen_price((gross - net).amount, "USD"),
                "taxPercentage": 2300,
                "amountExcludingTax": to_adyen_price(net.amount, "USD"),
                "amountIncludingTax": to_adyen_price(gross.amount, "USD"),
            },
            {
                "amountExcludingTax": "1000",
                "amountIncludingTax": "1000",
                "description": "Shipping - DHL",
                "id": f"Shipping:{checkout_ready_to_complete.shipping_method.id}",
                "quantity": 1,
                "taxAmount": "0",
                "taxPercentage": 0,
            },
        ],
    }
    assert result == expected_result


def test_request_data_for_payment_payment_not_valid(dummy_payment_data):
    # given
    dummy_payment_data.data = {
        "originUrl": "https://www.example.com",
        "is_valid": False,
    }
    native_3d_secure = False

    # when
    with pytest.raises(PaymentError) as e:
        request_data_for_payment(
            dummy_payment_data,
            "https://www.example.com",
            "MerchantTestAccount",
            native_3d_secure,
        )

    # then
    assert str(e._excinfo[1]) == "Payment data are not valid."


def test_request_data_for_payment(dummy_payment_data):
    # given
    return_url = "https://www.example.com"
    merchant_account = "MerchantTestAccount"
    origin_url = "https://www.example.com"
    data = {
        "is_valid": True,
        "riskData": {"clientData": "test_client_data"},
        "paymentMethod": {"type": "scheme"},
        "browserInfo": {"acceptHeader": "*/*", "colorDepth": 30, "language": "pl"},
        "billingAddress": {"address": "test_address"},
        "shopperIP": "123",
        "originUrl": origin_url,
    }
    dummy_payment_data.data = data
    native_3d_secure = False

    # when
    result = request_data_for_payment(
        dummy_payment_data, return_url, merchant_account, native_3d_secure
    )

    # then
    assert result == {
        "amount": {
            "value": to_adyen_price(
                dummy_payment_data.amount, dummy_payment_data.currency
            ),
            "currency": dummy_payment_data.currency,
        },
        "reference": dummy_payment_data.graphql_payment_id,
        "paymentMethod": {"type": "scheme"},
        "returnUrl": return_url,
        "merchantAccount": merchant_account,
        "origin": return_url,
        "shopperIP": data["shopperIP"],
        "billingAddress": data["billingAddress"],
        "browserInfo": data["browserInfo"],
        "channel": "web",
        "shopperEmail": "example@test.com",
    }


def test_request_data_for_payment_native_3d_secure(dummy_payment_data):
    # given
    return_url = "https://www.example.com"
    merchant_account = "MerchantTestAccount"
    origin_url = "https://www.example.com"
    data = {
        "is_valid": True,
        "riskData": {"clientData": "test_client_data"},
        "paymentMethod": {"type": "scheme"},
        "browserInfo": {"acceptHeader": "*/*", "colorDepth": 30, "language": "pl"},
        "billingAddress": {"address": "test_address"},
        "shopperIP": "123",
        "originUrl": origin_url,
    }
    dummy_payment_data.data = data
    native_3d_secure = True

    # when
    result = request_data_for_payment(
        dummy_payment_data, return_url, merchant_account, native_3d_secure
    )

    # then
    assert result == {
        "amount": {
            "value": to_adyen_price(
                dummy_payment_data.amount, dummy_payment_data.currency
            ),
            "currency": dummy_payment_data.currency,
        },
        "reference": dummy_payment_data.graphql_payment_id,
        "paymentMethod": {"type": "scheme"},
        "returnUrl": return_url,
        "merchantAccount": merchant_account,
        "origin": origin_url,
        "shopperIP": data["shopperIP"],
        "billingAddress": data["billingAddress"],
        "browserInfo": data["browserInfo"],
        "channel": "web",
        "additionalData": {"allow3DS2": "true"},
        "shopperEmail": "example@test.com",
    }


def test_request_data_for_payment_channel_different_than_web(dummy_payment_data):
    # given
    return_url = "https://www.example.com"
    merchant_account = "MerchantTestAccount"
    data = {"is_valid": True, "paymentMethod": {"type": "scheme"}, "channel": "iOS"}
    dummy_payment_data.data = data
    native_3d_secure = True

    # when
    result = request_data_for_payment(
        dummy_payment_data, return_url, merchant_account, native_3d_secure
    )

    # then
    assert result == {
        "amount": {
            "value": to_adyen_price(
                dummy_payment_data.amount, dummy_payment_data.currency
            ),
            "currency": dummy_payment_data.currency,
        },
        "reference": dummy_payment_data.graphql_payment_id,
        "paymentMethod": {"type": "scheme"},
        "returnUrl": return_url,
        "merchantAccount": merchant_account,
        "channel": "iOS",
        "additionalData": {"allow3DS2": "true"},
        "shopperEmail": "example@test.com",
    }


@mock.patch("saleor.payment.gateways.adyen.utils.common.append_klarna_data")
def test_request_data_for_payment_append_klarna_data(
    append_klarna_data_mock, dummy_payment_data
):
    # given
    return_url = "https://www.example.com"
    merchant_account = "MerchantTestAccount"
    origin_url = "https://www.example.com"
    data = {
        "is_valid": True,
        "riskData": {"clientData": "test_client_data"},
        "paymentMethod": {"type": "klarna"},
        "browserInfo": {"acceptHeader": "*/*", "colorDepth": 30, "language": "pl"},
        "billingAddress": {"address": "test_address"},
        "shopperIP": "123",
        "originUrl": origin_url,
    }
    dummy_payment_data.data = data
    klarna_result = {
        "amount": {
            "value": to_adyen_price(
                dummy_payment_data.amount, dummy_payment_data.currency
            ),
            "currency": dummy_payment_data.currency,
        },
        "reference": dummy_payment_data.graphql_payment_id,
        "paymentMethod": {"type": "scheme"},
        "returnUrl": return_url,
        "merchantAccount": merchant_account,
        "origin": return_url,
        "shopperIP": data["shopperIP"],
        "billingAddress": data["billingAddress"],
        "browserInfo": data["browserInfo"],
        "shopperLocale": "test_shopper",
    }
    append_klarna_data_mock.return_value = klarna_result
    native_3d_secure = False
    # when
    result = request_data_for_payment(
        dummy_payment_data, return_url, merchant_account, native_3d_secure
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
def test_from_adyen_price(value, currency, expected_result):
    # when
    result = from_adyen_price(value, currency)

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
def test_to_adyen_price(value, currency, expected_result):
    # when
    result = to_adyen_price(value, currency)

    # then
    assert result == expected_result


def test_request_data_for_gateway_config(checkout_with_item, address):
    # given
    checkout_with_item.billing_address = address
    merchant_account = "test_account"

    # when
    response_config = request_data_for_gateway_config(
        checkout_with_item, merchant_account
    )

    # then
    assert response_config == {
        "merchantAccount": merchant_account,
        "countryCode": checkout_with_item.billing_address.country,
        "channel": "web",
        "amount": {"currency": "USD", "value": "3000"},
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
        "amount": {"currency": "USD", "value": "0"},
    }


def test_update_payment_with_action_required_data_empty_extra_data(
    payment_adyen_for_checkout,
):
    # given
    payment_adyen_for_checkout.extra_data = ""
    payment_adyen_for_checkout.save(update_fields=["extra_data"])

    action = {
        "paymentData": "test_data",
    }
    details = [
        {"key": "payload", "type": "text"},
        {"key": "secondParam", "type": "text"},
    ]

    # when
    update_payment_with_action_required_data(
        payment_adyen_for_checkout, action, details
    )

    # then
    payment_adyen_for_checkout.refresh_from_db()
    extra_data = json.loads(payment_adyen_for_checkout.extra_data)
    assert len(extra_data) == 1
    assert extra_data[0]["payment_data"] == action["paymentData"]
    assert set(extra_data[0]["parameters"]) == {"payload", "secondParam"}


def test_update_payment_with_action_required_data_extra_data_as_list(
    payment_adyen_for_checkout,
):
    # given
    payment_adyen_for_checkout.extra_data = json.dumps([{"test_data": "test"}])
    payment_adyen_for_checkout.save(update_fields=["extra_data"])

    action = {
        "paymentData": "test_data",
    }
    details = [
        {"key": "payload", "type": "text"},
        {"key": "secondParam", "type": "text"},
    ]

    # when
    update_payment_with_action_required_data(
        payment_adyen_for_checkout, action, details
    )

    # then
    payment_adyen_for_checkout.refresh_from_db()
    extra_data = json.loads(payment_adyen_for_checkout.extra_data)
    assert len(extra_data) == 2
    assert extra_data[1]["payment_data"] == action["paymentData"]
    assert set(extra_data[1]["parameters"]) == {"payload", "secondParam"}


def test_update_payment_with_action_required_data_extra_data_as_dict(
    payment_adyen_for_checkout,
):
    # given
    payment_adyen_for_checkout.extra_data = json.dumps({"test_data": "test"})
    payment_adyen_for_checkout.save(update_fields=["extra_data"])

    action = {
        "paymentData": "test_data",
    }
    details = [
        {"key": "payload", "type": "text"},
        {"key": "secondParam", "type": "text"},
    ]

    # when
    update_payment_with_action_required_data(
        payment_adyen_for_checkout, action, details
    )

    # then
    payment_adyen_for_checkout.refresh_from_db()
    extra_data = json.loads(payment_adyen_for_checkout.extra_data)
    assert len(extra_data) == 2
    assert extra_data[1]["payment_data"] == action["paymentData"]
    assert set(extra_data[1]["parameters"]) == {"payload", "secondParam"}


def test_get_payment_method_info(dummy_payment_data):
    # given
    data = {"paymentMethod": {"type": "klarna"}}
    dummy_payment_data.data = data

    api_call_result_mock = mock.Mock()
    message = {"additionalData": {"paymentMethod": "visa-test"}}
    api_call_result_mock.message = message

    # when
    payment_method_info = get_payment_method_info(
        dummy_payment_data, api_call_result_mock
    )

    # then
    assert payment_method_info == PaymentMethodInfo(
        brand=message["additionalData"]["paymentMethod"],
        type=data["paymentMethod"]["type"],
    )


def test_get_payment_method_info_scheme_payment_method_type(dummy_payment_data):
    # given
    data = {"paymentMethod": {"type": "scheme"}}
    dummy_payment_data.data = data

    api_call_result_mock = mock.Mock()
    message = {"additionalData": {"paymentMethod": "visa-test"}}
    api_call_result_mock.message = message

    # when
    payment_method_info = get_payment_method_info(
        dummy_payment_data, api_call_result_mock
    )

    # then
    assert payment_method_info == PaymentMethodInfo(
        brand=message["additionalData"]["paymentMethod"], type="card"
    )


def test_get_payment_method_info_no_additional_data(dummy_payment_data):
    # given
    data = {"paymentMethod": {"type": "scheme"}}
    dummy_payment_data.data = data

    api_call_result_mock = mock.Mock()
    message = {}
    api_call_result_mock.message = message

    # when
    payment_method_info = get_payment_method_info(
        dummy_payment_data, api_call_result_mock
    )

    # then
    assert payment_method_info == PaymentMethodInfo(type="card")
