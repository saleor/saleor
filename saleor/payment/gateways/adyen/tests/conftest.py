from decimal import Decimal
from unittest import mock

import Adyen
import pytest

from .....checkout import calculations
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....plugins.manager import get_plugins_manager
from .... import TransactionKind
from ....models import Transaction
from ....utils import create_payment
from ..plugin import AdyenGatewayPlugin


@pytest.fixture(scope="module")
def vcr_config():
    return {
        "filter_headers": [("x-api-key", "test_key")],
    }


@pytest.fixture
def adyen_plugin(settings, channel_USD):
    def fun(
        api_key=None,
        merchant_account=None,
        return_url=None,
        client_key=None,
        origin_url=None,
        adyen_auto_capture=None,
        auto_capture=None,
        apple_pay_cert=None,
    ):
        api_key = api_key or "test_key"
        merchant_account = merchant_account or "SaleorECOM"
        return_url = return_url or "http://127.0.0.1:3000/"
        client_key = client_key or "test_origin_key"
        origin_url = origin_url or "http://127.0.0.1:3000"
        adyen_auto_capture = adyen_auto_capture or False
        auto_capture = auto_capture or False
        settings.PLUGINS = ["saleor.payment.gateways.adyen.plugin.AdyenGatewayPlugin"]
        manager = get_plugins_manager()

        with mock.patch("saleor.payment.gateways.adyen.utils.apple_pay.requests.post"):
            manager.save_plugin_configuration(
                AdyenGatewayPlugin.PLUGIN_ID,
                channel_USD.slug,
                {
                    "active": True,
                    "configuration": [
                        {"name": "api-key", "value": api_key},
                        {"name": "merchant-account", "value": merchant_account},
                        {"name": "return-url", "value": return_url},
                        {"name": "client-key", "value": client_key},
                        {"name": "origin-url", "value": origin_url},
                        {"name": "adyen-auto-capture", "value": adyen_auto_capture},
                        {"name": "auto-capture", "value": auto_capture},
                        {"name": "supported-currencies", "value": "USD"},
                        {"name": "apple-pay-cert", "value": apple_pay_cert},
                    ],
                },
            )

        manager = get_plugins_manager()
        return manager.plugins_per_channel[channel_USD.slug][0]

    return fun


@pytest.fixture
def payment_adyen_for_checkout(checkout_with_items, address, shipping_method):
    checkout_with_items.billing_address = address
    checkout_with_items.shipping_address = address
    checkout_with_items.shipping_method = shipping_method
    checkout_with_items.save()
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_items)
    checkout_info = fetch_checkout_info(checkout_with_items, lines, [], manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    payment = create_payment(
        gateway=AdyenGatewayPlugin.PLUGIN_ID,
        payment_token="",
        total=total.gross.amount,
        currency=checkout_with_items.currency,
        email=checkout_with_items.email,
        customer_ip_address="",
        checkout=checkout_with_items,
        return_url="https://www.example.com",
    )
    return payment


@pytest.fixture
def inactive_payment_adyen_for_checkout(payment_adyen_for_checkout):
    payment_adyen_for_checkout.is_active = False
    payment_adyen_for_checkout.save(update_fields=["is_active"])
    return payment_adyen_for_checkout


@pytest.fixture
def payment_adyen_for_order(order_with_lines):
    payment = create_payment(
        gateway=AdyenGatewayPlugin.PLUGIN_ID,
        payment_token="",
        total=Decimal("80.00"),
        currency=order_with_lines.currency,
        email=order_with_lines.user_email,
        customer_ip_address="",
        checkout=None,
        order=order_with_lines,
        return_url="https://www.example.com",
    )

    Transaction.objects.create(
        payment=payment,
        action_required=False,
        kind=TransactionKind.AUTH,
        token="token",
        is_success=True,
        amount=order_with_lines.total_gross_amount,
        currency=order_with_lines.currency,
        error="",
        gateway_response={},
        action_required_data={},
    )
    return payment


@pytest.fixture()
def notification():
    def fun(
        event_code=None,
        success=None,
        psp_reference=None,
        merchant_reference=None,
        value=None,
    ):
        event_code = event_code or "AUTHORISATION"
        success = success or "true"
        psp_reference = psp_reference or "852595499936560C"
        merchant_reference = merchant_reference or "UGF5bWVudDoxNw=="
        value = value or 1130

        return {
            "additionalData": {},
            "eventCode": event_code,
            "success": success,
            "eventDate": "2019-06-28T18:03:50+01:00",
            "merchantAccountCode": "SaleorECOM",
            "pspReference": psp_reference,
            "merchantReference": merchant_reference,
            "amount": {"value": value, "currency": "USD"},
        }

    return fun


@pytest.fixture
def notification_with_hmac_signature():
    return {
        "additionalData": {
            "expiryDate": "12/2012",
            " NAME1 ": "VALUE1",
            "cardSummary": "7777",
            "totalFraudScore": "10",
            "hmacSignature": "D4bKVtjx5AlBL2eeQZIh1p7G1Lh6vWjzwkDlzC+PoMo=",
            "NAME2": "  VALUE2  ",
            "fraudCheck-6-ShopperIpUsage": "10",
        },
        "amount": {"currency": "GBP", "value": 20150},
        "eventCode": "AUTHORISATION",
        "eventDate": "2020-07-24T12:40:22+02:00",
        "merchantAccountCode": "SaleorPOS",
        "merchantReference": "8313842560770001",
        "paymentMethod": "visa",
        "pspReference": "test_AUTHORISATION_4",
        "reason": "REFUSED",
        "success": "false",
    }


@pytest.fixture
def adyen_payment_method():
    return {
        "type": "scheme",
        "encryptedCardNumber": "test_4646464646464644",
        "encryptedExpiryMonth": "test_03",
        "encryptedExpiryYear": "test_2030",
        "encryptedSecurityCode": "test_737",
    }


@pytest.fixture
def adyen_additional_data_for_3ds():
    user_agent = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)",
        "Chrome/89.0.4389.90 Safari/537.36",
    )
    return {
        "paymentMethod": {
            "type": "scheme",
            "encryptedCardNumber": "test_4917610000000000",
            "encryptedExpiryMonth": "test_03",
            "encryptedExpiryYear": "test_2030",
            "encryptedSecurityCode": "test_737",
            "brand": "visa",
        },
        "browserInfo": {
            "acceptHeader": "*/*",
            "colorDepth": 24,
            "language": "en-US",
            "javaEnabled": False,
            "screenHeight": 1080,
            "screenWidth": 1920,
            "userAgent": user_agent,
            "timeZoneOffset": -120,
        },
    }


@pytest.fixture
def adyen_additional_data_for_klarna():
    user_agent = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)",
        "Chrome/89.0.4389.90 Safari/537.36",
    )
    return {
        "paymentMethod": {
            "type": "klarna_account",
        },
        "browserInfo": {
            "acceptHeader": "*/*",
            "colorDepth": 24,
            "language": "en-US",
            "javaEnabled": False,
            "screenHeight": 1080,
            "screenWidth": 1920,
            "userAgent": user_agent,
            "timeZoneOffset": -120,
        },
    }


@pytest.fixture
def adyen_check_balance_response():
    return Adyen.client.AdyenResult(
        message={
            "pspReference": "851634546949980A",
            "resultCode": "Success",
            "balance": {"currency": "GBP", "value": 10000},
        }
    )
