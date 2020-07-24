from decimal import Decimal

import pytest

from .....plugins.manager import get_plugins_manager
from ....utils import create_payment
from ..plugin import AdyenGatewayPlugin


@pytest.fixture
def adyen_plugin(settings):
    def fun(
        api_key=None,
        merchant_account=None,
        return_url=None,
        origin_key=None,
        origin_url=None,
        auto_capture=None,
    ):
        api_key = api_key or "test_key"
        merchant_account = merchant_account or "SaleorECOM"
        return_url = return_url or "http://127.0.0.1:3000/"
        origin_key = origin_key or "test_origin_key"
        origin_url = origin_url or "http://127.0.0.1:3000"
        auto_capture = auto_capture or False
        settings.PLUGINS = ["saleor.payment.gateways.adyen.plugin.AdyenGatewayPlugin"]
        manager = get_plugins_manager()
        manager.save_plugin_configuration(
            AdyenGatewayPlugin.PLUGIN_ID,
            {
                "active": True,
                "configuration": [
                    {"name": "API key", "value": api_key},
                    {"name": "Merchant Account", "value": merchant_account},
                    {"name": "Return Url", "value": return_url},
                    {"name": "Origin Key", "value": origin_key},
                    {"name": "Origin Url", "value": origin_url},
                    {
                        "name": "Automatically mark payment as a capture",
                        "value": auto_capture,
                    },
                    {"name": "Supported currencies", "value": "USD"},
                ],
            },
        )

        manager = get_plugins_manager()
        return manager.plugins[0]

    return fun


@pytest.fixture
def payment_adyen_for_checkout(checkout_with_items, address):
    checkout_with_items.billing_address = address
    checkout_with_items.save()
    payment = create_payment(
        gateway=AdyenGatewayPlugin.PLUGIN_ID,
        payment_token="",
        total=Decimal("1234"),
        currency=checkout_with_items.currency,
        email=checkout_with_items.email,
        customer_ip_address="",
        checkout=checkout_with_items,
    )
    return payment


@pytest.fixture
def payment_adyen_for_order(payment_adyen_for_checkout, order_with_lines):
    payment_adyen_for_checkout.checkout = None
    payment_adyen_for_checkout.order = order_with_lines
    payment_adyen_for_checkout.save()
    return payment_adyen_for_checkout
