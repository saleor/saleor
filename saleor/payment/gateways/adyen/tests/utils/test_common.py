import json
from decimal import Decimal
from unittest import mock

import pytest
from prices import Money, TaxedMoney

from saleor.core.prices import quantize_price
from saleor.payment import PaymentError
from saleor.payment.gateways.adyen.utils.common import (
    append_checkout_details,
    get_payment_method_info,
    get_request_data_for_check_payment,
    get_shopper_locale_value,
    request_data_for_gateway_config,
    request_data_for_payment,
    update_payment_with_action_required_data,
)
from saleor.payment.interface import PaymentMethodInfo
from saleor.payment.utils import price_from_minor_unit, price_to_minor_unit

from ...utils.common import prepare_address_request_data


@pytest.mark.parametrize(
    "country_code, shopper_locale", [("JP", "ja_JP"), ("ZZ", "en_US"), ("US", "en_US")]
)
def test_get_shopper_locale_value(country_code, shopper_locale, settings):
    # when
    result = get_shopper_locale_value(country_code)

    # then
    assert result == shopper_locale


def test_append_checkout_details(
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
    result = append_checkout_details(dummy_payment_data, payment_data)

    # then
    variant_channel_listing = line.variant.channel_listings.get(channel_id=channel_id)
    variant_price = variant_channel_listing.price_amount
    variant_currency = variant_channel_listing.currency
    price = price_to_minor_unit(variant_price, variant_currency)

    assert result == {
        "reference": "test",
        "shopperLocale": get_shopper_locale_value(country_code),
        "countryCode": country_code,
        "lineItems": [
            {
                "description": f"{line.variant.product.name}, {line.variant.name}",
                "quantity": line.quantity,
                "id": line.variant.sku,
                "taxAmount": "0",
                "taxPercentage": 0,
                "amountExcludingTax": price,
                "amountIncludingTax": price,
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


def test_append_checkout_details_without_sku(
    dummy_payment_data, payment_dummy, checkout_ready_to_complete
):
    # given
    checkout_ready_to_complete.payments.add(payment_dummy)
    channel_id = checkout_ready_to_complete.channel_id
    line = checkout_ready_to_complete.lines.first()
    line.variant.sku = None
    line.variant.save()
    payment_data = {
        "reference": "test",
    }
    country_code = checkout_ready_to_complete.get_country()

    # when
    result = append_checkout_details(dummy_payment_data, payment_data)

    # then
    variant_channel_listing = line.variant.channel_listings.get(channel_id=channel_id)
    variant_price = variant_channel_listing.price_amount
    variant_currency = variant_channel_listing.currency
    price = price_to_minor_unit(variant_price, variant_currency)

    assert result == {
        "reference": "test",
        "shopperLocale": get_shopper_locale_value(country_code),
        "countryCode": country_code,
        "lineItems": [
            {
                "description": f"{line.variant.product.name}, {line.variant.name}",
                "quantity": line.quantity,
                "id": line.variant.get_global_id(),
                "taxAmount": "0",
                "taxPercentage": 0,
                "amountExcludingTax": price,
                "amountIncludingTax": price,
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


@mock.patch("saleor.plugins.manager.PluginsManager.calculate_checkout_line_total")
@mock.patch("saleor.plugins.manager.PluginsManager.calculate_checkout_line_unit_price")
def test_append_checkout_details_tax_included(
    mocked_calculate_checkout_line_unit_price,
    mocked_calculate_checkout_line_total,
    dummy_payment_data,
    payment_dummy,
    checkout_ready_to_complete,
):
    # given
    line = checkout_ready_to_complete.lines.first()
    quantity = line.quantity

    net = Money(100, "USD")
    gross = Money(123, "USD")
    # tax 23 %
    unit_price = quantize_price(TaxedMoney(net=net, gross=gross), "USD")
    total_price = quantize_price(
        TaxedMoney(net=net * quantity, gross=gross * quantity), "USD"
    )

    country_code = checkout_ready_to_complete.get_country()

    mocked_calculate_checkout_line_unit_price.return_value = unit_price
    mocked_calculate_checkout_line_total.return_value = total_price

    checkout_ready_to_complete.payments.add(payment_dummy)
    payment_data = {
        "reference": "test",
    }

    # when
    result = append_checkout_details(dummy_payment_data, payment_data)

    # then

    expected_result = {
        "reference": "test",
        "shopperLocale": get_shopper_locale_value(country_code),
        "countryCode": country_code,
        "lineItems": [
            {
                "description": f"{line.variant.product.name}, {line.variant.name}",
                "quantity": line.quantity,
                "id": line.variant.sku,
                "taxAmount": price_to_minor_unit((gross - net).amount, "USD"),
                "taxPercentage": 2300,
                "amountExcludingTax": price_to_minor_unit(net.amount, "USD"),
                "amountIncludingTax": price_to_minor_unit(gross.amount, "USD"),
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


def test_request_data_for_payment_payment_not_valid(
    dummy_payment_data, dummy_address_data
):
    # given
    dummy_payment_data.data = {
        "originUrl": "https://www.example.com",
        "is_valid": False,
    }
    dummy_payment_data.billing = dummy_address_data
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


def test_request_data_for_payment(dummy_payment_data, dummy_address_data):
    # given
    return_url = "https://www.example.com"
    merchant_account = "MerchantTestAccount"
    origin_url = "https://www.example.com"
    data = {
        "is_valid": True,
        "riskData": {"clientData": "test_client_data"},
        "paymentMethod": {"type": "scheme"},
        "browserInfo": {"acceptHeader": "*/*", "colorDepth": 30, "language": "pl"},
        "shopperIP": "123",
        "originUrl": origin_url,
    }
    dummy_payment_data.data = data
    dummy_payment_data.billing = dummy_address_data
    dummy_payment_data.shipping = dummy_address_data
    native_3d_secure = False

    # when
    result = request_data_for_payment(
        dummy_payment_data, return_url, merchant_account, native_3d_secure
    )

    # then
    assert result == {
        "amount": {
            "value": price_to_minor_unit(
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
        "browserInfo": data["browserInfo"],
        "channel": "web",
        "shopperEmail": "example@test.com",
        "shopperName": {
            "firstName": dummy_payment_data.billing.first_name,
            "lastName": dummy_payment_data.billing.last_name,
        },
        "shopperReference": "example@test.com",
        "deliveryAddress": {
            "city": "WROCŁAW",
            "country": "PL",
            "houseNumberOrName": "Mirumee Software",
            "postalCode": "53-601",
            "stateOrProvince": "ZZ",
            "street": "Tęczowa 7",
        },
        "billingAddress": {
            "city": "WROCŁAW",
            "country": "PL",
            "houseNumberOrName": "Mirumee Software",
            "postalCode": "53-601",
            "stateOrProvince": "ZZ",
            "street": "Tęczowa 7",
        },
    }


def test_request_data_for_payment_when_missing_city_address_field(
    dummy_payment_data, dummy_address_data
):
    # given
    return_url = "https://www.example.com"
    merchant_account = "MerchantTestAccount"
    origin_url = "https://www.example.com"
    data = {
        "is_valid": True,
        "riskData": {"clientData": "test_client_data"},
        "paymentMethod": {"type": "scheme"},
        "browserInfo": {"acceptHeader": "*/*", "colorDepth": 30, "language": "pl"},
        "shopperIP": "123",
        "originUrl": origin_url,
    }
    dummy_payment_data.data = data

    dummy_address_data.city = ""
    dummy_address_data.country_area = "Fallback_for_city"
    dummy_payment_data.billing = dummy_address_data
    dummy_payment_data.shipping = dummy_address_data
    native_3d_secure = False

    # when
    result = request_data_for_payment(
        dummy_payment_data, return_url, merchant_account, native_3d_secure
    )

    # then
    assert result["deliveryAddress"] == {
        "city": dummy_address_data.country_area,
        "country": "PL",
        "houseNumberOrName": "Mirumee Software",
        "postalCode": "53-601",
        "stateOrProvince": dummy_address_data.country_area,
        "street": "Tęczowa 7",
    }
    assert result["billingAddress"] == {
        "city": dummy_address_data.country_area,
        "country": "PL",
        "houseNumberOrName": "Mirumee Software",
        "postalCode": "53-601",
        "stateOrProvince": dummy_address_data.country_area,
        "street": "Tęczowa 7",
    }


def test_request_data_for_payment_when_missing_city_and_count_area(
    dummy_payment_data, dummy_address_data
):
    # given
    return_url = "https://www.example.com"
    merchant_account = "MerchantTestAccount"
    origin_url = "https://www.example.com"
    data = {
        "is_valid": True,
        "riskData": {"clientData": "test_client_data"},
        "paymentMethod": {"type": "scheme"},
        "browserInfo": {"acceptHeader": "*/*", "colorDepth": 30, "language": "pl"},
        "shopperIP": "123",
        "originUrl": origin_url,
    }
    dummy_payment_data.data = data

    dummy_address_data.city = ""
    dummy_address_data.country_area = ""
    dummy_payment_data.billing = dummy_address_data
    dummy_payment_data.shipping = dummy_address_data
    native_3d_secure = False

    # when
    result = request_data_for_payment(
        dummy_payment_data, return_url, merchant_account, native_3d_secure
    )

    # then
    assert result["deliveryAddress"] == {
        "city": "ZZ",
        "country": "PL",
        "houseNumberOrName": "Mirumee Software",
        "postalCode": "53-601",
        "stateOrProvince": "ZZ",
        "street": "Tęczowa 7",
    }
    assert result["billingAddress"] == {
        "city": "ZZ",
        "country": "PL",
        "houseNumberOrName": "Mirumee Software",
        "postalCode": "53-601",
        "stateOrProvince": "ZZ",
        "street": "Tęczowa 7",
    }


def test_request_data_for_payment_when_missing_postal_code(
    dummy_payment_data, dummy_address_data
):
    # given
    return_url = "https://www.example.com"
    merchant_account = "MerchantTestAccount"
    origin_url = "https://www.example.com"
    data = {
        "is_valid": True,
        "riskData": {"clientData": "test_client_data"},
        "paymentMethod": {"type": "scheme"},
        "browserInfo": {"acceptHeader": "*/*", "colorDepth": 30, "language": "pl"},
        "shopperIP": "123",
        "originUrl": origin_url,
    }
    dummy_payment_data.data = data

    dummy_address_data.postal_code = ""
    dummy_payment_data.billing = dummy_address_data
    dummy_payment_data.shipping = dummy_address_data
    native_3d_secure = False

    # when
    result = request_data_for_payment(
        dummy_payment_data, return_url, merchant_account, native_3d_secure
    )

    # then
    assert result["deliveryAddress"] == {
        "city": "WROCŁAW",
        "country": "PL",
        "houseNumberOrName": "Mirumee Software",
        "postalCode": "ZZ",
        "stateOrProvince": "ZZ",
        "street": "Tęczowa 7",
    }
    assert result["billingAddress"] == {
        "city": "WROCŁAW",
        "country": "PL",
        "houseNumberOrName": "Mirumee Software",
        "postalCode": "ZZ",
        "stateOrProvince": "ZZ",
        "street": "Tęczowa 7",
    }


def test_request_data_for_payment_without_shipping(
    dummy_payment_data, dummy_address_data
):
    # given
    return_url = "https://www.example.com"
    merchant_account = "MerchantTestAccount"
    origin_url = "https://www.example.com"
    data = {
        "is_valid": True,
        "riskData": {"clientData": "test_client_data"},
        "paymentMethod": {"type": "scheme"},
        "browserInfo": {"acceptHeader": "*/*", "colorDepth": 30, "language": "pl"},
        "shopperIP": "123",
        "originUrl": origin_url,
    }
    dummy_payment_data.data = data
    dummy_payment_data.billing = dummy_address_data
    dummy_payment_data.shipping = None
    native_3d_secure = False

    # when
    result = request_data_for_payment(
        dummy_payment_data, return_url, merchant_account, native_3d_secure
    )

    # then
    assert result == {
        "amount": {
            "value": price_to_minor_unit(
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
        "browserInfo": data["browserInfo"],
        "channel": "web",
        "shopperEmail": "example@test.com",
        "shopperName": {
            "firstName": dummy_payment_data.billing.first_name,
            "lastName": dummy_payment_data.billing.last_name,
        },
        "shopperReference": "example@test.com",
        "billingAddress": {
            "city": "WROCŁAW",
            "country": "PL",
            "houseNumberOrName": "Mirumee Software",
            "postalCode": "53-601",
            "stateOrProvince": "ZZ",
            "street": "Tęczowa 7",
        },
    }


def test_request_data_for_payment_native_3d_secure(
    dummy_payment_data, dummy_address_data
):
    # given
    return_url = "https://www.example.com"
    merchant_account = "MerchantTestAccount"
    origin_url = "https://www.example.com"
    data = {
        "is_valid": True,
        "riskData": {"clientData": "test_client_data"},
        "paymentMethod": {"type": "scheme"},
        "browserInfo": {"acceptHeader": "*/*", "colorDepth": 30, "language": "pl"},
        "shopperIP": "123",
        "originUrl": origin_url,
    }
    dummy_payment_data.data = data
    dummy_payment_data.shipping = dummy_address_data
    dummy_payment_data.billing = dummy_address_data
    native_3d_secure = True

    # when
    result = request_data_for_payment(
        dummy_payment_data, return_url, merchant_account, native_3d_secure
    )

    # then
    assert result == {
        "amount": {
            "value": price_to_minor_unit(
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
        "browserInfo": data["browserInfo"],
        "channel": "web",
        "additionalData": {"allow3DS2": "true"},
        "shopperEmail": "example@test.com",
        "shopperName": {
            "firstName": dummy_payment_data.billing.first_name,
            "lastName": dummy_payment_data.billing.last_name,
        },
        "shopperReference": "example@test.com",
        "deliveryAddress": {
            "city": "WROCŁAW",
            "country": "PL",
            "houseNumberOrName": "Mirumee Software",
            "postalCode": "53-601",
            "stateOrProvince": "ZZ",
            "street": "Tęczowa 7",
        },
        "billingAddress": {
            "city": "WROCŁAW",
            "country": "PL",
            "houseNumberOrName": "Mirumee Software",
            "postalCode": "53-601",
            "stateOrProvince": "ZZ",
            "street": "Tęczowa 7",
        },
    }


def test_request_data_for_payment_channel_different_than_web(
    dummy_payment_data, dummy_address_data
):
    # given
    return_url = "https://www.example.com"
    merchant_account = "MerchantTestAccount"
    data = {"is_valid": True, "paymentMethod": {"type": "scheme"}, "channel": "iOS"}
    dummy_payment_data.data = data
    dummy_payment_data.billing = dummy_address_data
    dummy_payment_data.shipping = dummy_address_data
    native_3d_secure = True

    # when
    result = request_data_for_payment(
        dummy_payment_data, return_url, merchant_account, native_3d_secure
    )

    # then
    assert result == {
        "amount": {
            "value": price_to_minor_unit(
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
        "shopperName": {
            "firstName": dummy_payment_data.billing.first_name,
            "lastName": dummy_payment_data.billing.last_name,
        },
        "shopperReference": "example@test.com",
        "deliveryAddress": {
            "city": "WROCŁAW",
            "country": "PL",
            "houseNumberOrName": "Mirumee Software",
            "postalCode": "53-601",
            "stateOrProvince": "ZZ",
            "street": "Tęczowa 7",
        },
        "billingAddress": {
            "city": "WROCŁAW",
            "country": "PL",
            "houseNumberOrName": "Mirumee Software",
            "postalCode": "53-601",
            "stateOrProvince": "ZZ",
            "street": "Tęczowa 7",
        },
    }


@pytest.mark.parametrize("method_type", ["klarna", "clearpay", "afterpaytouch"])
@mock.patch("saleor.payment.gateways.adyen.utils.common.append_checkout_details")
def test_request_data_for_payment_append_checkout_details(
    append_checkout_details_mock, method_type, dummy_payment_data, dummy_address_data
):
    # given
    return_url = "https://www.example.com"
    merchant_account = "MerchantTestAccount"
    origin_url = "https://www.example.com"
    data = {
        "is_valid": True,
        "riskData": {"clientData": "test_client_data"},
        "paymentMethod": {"type": method_type},
        "browserInfo": {"acceptHeader": "*/*", "colorDepth": 30, "language": "pl"},
        "shopperIP": "123",
        "originUrl": origin_url,
    }
    dummy_payment_data.data = data
    dummy_payment_data.billing = dummy_address_data
    dummy_payment_data.shipping = dummy_address_data

    checkout_details_result = {
        "amount": {
            "value": price_to_minor_unit(
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
        "browserInfo": data["browserInfo"],
        "shopperLocale": "test_shopper",
        "shopperName": {
            "firstName": dummy_payment_data.billing.first_name,
            "lastName": dummy_payment_data.billing.last_name,
        },
        "shopperReference": "example@test.com",
        "deliveryAddress": {
            "city": "WROCŁAW",
            "country": "PL",
            "houseNumberOrName": "Mirumee Software",
            "postalCode": "53-601",
            "stateOrProvince": "",
            "street": "Tęczowa 7",
        },
        "billingAddress": {
            "city": "WROCŁAW",
            "country": "PL",
            "houseNumberOrName": "Mirumee Software",
            "postalCode": "53-601",
            "stateOrProvince": "",
            "street": "Tęczowa 7",
        },
    }
    append_checkout_details_mock.return_value = checkout_details_result
    native_3d_secure = False
    # when
    result = request_data_for_payment(
        dummy_payment_data, return_url, merchant_account, native_3d_secure
    )

    # then
    assert result == checkout_details_result


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
    result = price_from_minor_unit(value, currency)

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
    result = price_to_minor_unit(value, currency)

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


def test_prepare_address_request_data_address_is_none():
    assert not prepare_address_request_data(None)


def test_prepare_address_request_data_without_city_country_code_and_areas(
    address_with_areas,
):
    address = address_with_areas
    address.city = ""
    address.country_area = ""
    address.city_area = ""
    address.country = ""
    address.postal_code = ""
    address.save(
        update_fields=["city", "country", "postal_code", "city_area", "country_area"]
    )
    address.refresh_from_db()

    result = prepare_address_request_data(address)

    assert result["city"] == "ZZ"
    assert result["country"] == "ZZ"
    assert result["houseNumberOrName"] == "Mirumee Software"
    assert result["postalCode"] == "ZZ"
    assert result["stateOrProvince"] == "ZZ"
    assert result["street"] == "Tęczowa 7"


def test_prepare_address_request_data_address_fulfilled(address_with_areas):
    result = prepare_address_request_data(address_with_areas)

    assert result["city"] == "WROCŁAW"
    assert result["country"] == "PL"
    assert result["houseNumberOrName"] == "Mirumee Software"
    assert result["postalCode"] == "53-601"
    assert result["stateOrProvince"] == "test_country_area"
    assert result["street"] == "Tęczowa 7"


def test_prepare_address_request_data_without_company_name_and_street_addr_2(
    address_with_areas,
):
    address = address_with_areas
    address.company_name = ""
    address.save(update_fields=["company_name"])
    address.refresh_from_db()

    result = prepare_address_request_data(address)

    assert result["city"] == "WROCŁAW"
    assert result["country"] == "PL"
    assert result["houseNumberOrName"] == ""
    assert result["postalCode"] == "53-601"
    assert result["stateOrProvince"] == "test_country_area"
    assert result["street"] == "Tęczowa 7"


def test_prepare_address_request_data_with_company_name_and_street_addr_2(
    address_with_areas,
):
    address = address_with_areas
    address.street_address_2 = "street_address_2"
    address.save(update_fields=["street_address_2"])
    address.refresh_from_db()

    result = prepare_address_request_data(address)

    assert result["city"] == "WROCŁAW"
    assert result["country"] == "PL"
    assert result["houseNumberOrName"] == "Mirumee Software"
    assert result["postalCode"] == "53-601"
    assert result["stateOrProvince"] == "test_country_area"
    assert result["street"] == "Tęczowa 7 street_address_2"


def test_prepare_address_request_data_without_company_with_street_addr_2(
    address_with_areas,
):
    address = address_with_areas
    address.company_name = ""
    address.street_address_2 = "street_address_2"
    address.save(update_fields=["company_name", "street_address_2"])
    address.refresh_from_db()

    result = prepare_address_request_data(address)

    assert result["city"] == "WROCŁAW"
    assert result["country"] == "PL"
    assert result["houseNumberOrName"] == "Tęczowa 7"
    assert result["postalCode"] == "53-601"
    assert result["stateOrProvince"] == "test_country_area"
    assert result["street"] == "street_address_2"


def test_prepare_address_request_data_with_country_area_without_city_area(
    address_with_areas,
):
    address = address_with_areas
    address.city_area = ""
    address.save(update_fields=["city_area"])
    address.refresh_from_db()

    result = prepare_address_request_data(address)

    assert result["city"] == "WROCŁAW"
    assert result["country"] == "PL"
    assert result["houseNumberOrName"] == "Mirumee Software"
    assert result["postalCode"] == "53-601"
    assert result["stateOrProvince"] == "test_country_area"
    assert result["street"] == "Tęczowa 7"


def test_prepare_address_request_data_with_city_area_without_country_area(
    address_with_areas,
):
    address = address_with_areas
    address.country_area = ""
    address.save(update_fields=["country_area"])
    address.refresh_from_db()

    result = prepare_address_request_data(address)

    assert result["city"] == "WROCŁAW"
    assert result["country"] == "PL"
    assert result["houseNumberOrName"] == "Mirumee Software"
    assert result["postalCode"] == "53-601"
    assert result["stateOrProvince"] == "ZZ"
    assert result["street"] == "Tęczowa 7"


def test_get_request_data_for_check_payment():
    data = get_request_data_for_check_payment(
        {
            "method": "test",
            "card": {
                "code": "1243456",
                "cvc": "123",
                "money": {"amount": Decimal(10.05), "currency": "EUR"},
            },
        },
        merchant_account="TEST_ACCOUNT",
    )

    assert data["merchantAccount"] == "TEST_ACCOUNT"
    assert data["paymentMethod"]["type"] == "test"
    assert data["paymentMethod"]["number"] == "1243456"
    assert data["paymentMethod"]["securityCode"] == "123"
    assert data["amount"]["value"] == "1005"
    assert data["amount"]["currency"] == "EUR"


def test_get_request_data_for_check_payment_without_money():
    data = get_request_data_for_check_payment(
        {"method": "test", "card": {"code": "1243456", "cvc": "123"}},
        merchant_account="TEST_ACCOUNT",
    )

    assert data["merchantAccount"] == "TEST_ACCOUNT"
    assert data["paymentMethod"]["type"] == "test"
    assert data["paymentMethod"]["number"] == "1243456"
    assert data["paymentMethod"]["securityCode"] == "123"


def test_get_request_data_for_check_payment_without_cvc():
    data = get_request_data_for_check_payment(
        {
            "method": "test",
            "card": {
                "code": "1243456",
                "money": {"amount": Decimal(10.05), "currency": "EUR"},
            },
        },
        merchant_account="TEST_ACCOUNT",
    )

    assert data["merchantAccount"] == "TEST_ACCOUNT"
    assert data["paymentMethod"]["type"] == "test"
    assert data["paymentMethod"]["number"] == "1243456"
    assert data["amount"]["value"] == "1005"
    assert data["amount"]["currency"] == "EUR"


def test_get_request_data_for_check_payment_without_cvc_and_money():
    data = get_request_data_for_check_payment(
        {"method": "test", "card": {"code": "1243456"}}, merchant_account="TEST_ACCOUNT"
    )

    assert data["merchantAccount"] == "TEST_ACCOUNT"
    assert data["paymentMethod"]["type"] == "test"
    assert data["paymentMethod"]["number"] == "1243456"
