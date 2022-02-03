import pytest
from stripe.stripe_object import StripeObject

from .....checkout import calculations
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....plugins.manager import get_plugins_manager
from .....plugins.models import PluginConfiguration
from .... import TransactionKind
from ....models import Transaction
from ....utils import create_payment, price_to_minor_unit
from ..consts import SUCCESS_STATUS
from ..plugin import StripeGatewayPlugin


@pytest.fixture
def payment_stripe_for_checkout(checkout_with_items, address, shipping_method):
    checkout_with_items.billing_address = address
    checkout_with_items.shipping_address = address
    checkout_with_items.shipping_method = shipping_method
    checkout_with_items.email = "test@example.com"
    checkout_with_items.save()
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_items)
    checkout_info = fetch_checkout_info(checkout_with_items, lines, [], manager)
    total = calculations.calculate_checkout_total_with_gift_cards(
        manager, checkout_info, lines, address
    )
    payment = create_payment(
        gateway=StripeGatewayPlugin.PLUGIN_ID,
        payment_token="ABC",
        total=total.gross.amount,
        currency=checkout_with_items.currency,
        email=checkout_with_items.email,
        customer_ip_address="",
        checkout=checkout_with_items,
    )
    return payment


@pytest.fixture
def inactive_payment_stripe_for_checkout(payment_stripe_for_checkout):
    payment_stripe_for_checkout.is_active = False
    payment_stripe_for_checkout.save(update_fields=["is_active"])
    return payment_stripe_for_checkout


@pytest.fixture
def payment_stripe_for_order(payment_stripe_for_checkout, order_with_lines):
    payment_stripe_for_checkout.checkout = None
    payment_stripe_for_checkout.order = order_with_lines
    payment_stripe_for_checkout.total = order_with_lines.total_gross_amount
    payment_stripe_for_checkout.save()

    Transaction.objects.create(
        payment=payment_stripe_for_checkout,
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
    return payment_stripe_for_checkout


@pytest.fixture
def stripe_plugin(settings, monkeypatch, channel_USD):
    def fun(
        public_api_key=None,
        secret_api_key=None,
        webhook_endpoint_id="12345",
        webhook_secret_key="ABCD",
        active=True,
        auto_capture=True,
    ):
        public_api_key = public_api_key or "test_key"
        secret_api_key = secret_api_key or "secret_key"

        settings.PLUGINS = ["saleor.payment.gateways.stripe.plugin.StripeGatewayPlugin"]

        configuration = [
            {"name": "public_api_key", "value": public_api_key},
            {"name": "secret_api_key", "value": secret_api_key},
            {"name": "automatic_payment_capture", "value": auto_capture},
            {"name": "supported_currencies", "value": "USD"},
        ]
        if webhook_endpoint_id:
            configuration.append(
                {"name": "webhook_endpoint_id", "value": webhook_endpoint_id}
            )
        if webhook_secret_key:
            configuration.append(
                {"name": "webhook_secret_key", "value": webhook_secret_key}
            )
        PluginConfiguration.objects.create(
            identifier=StripeGatewayPlugin.PLUGIN_ID,
            name=StripeGatewayPlugin.PLUGIN_NAME,
            description="",
            active=active,
            channel=channel_USD,
            configuration=configuration,
        )

        manager = get_plugins_manager()
        return manager.plugins_per_channel[channel_USD.slug][0]

    return fun


@pytest.fixture
def stripe_payment_intent(payment_stripe_for_checkout):
    payment = payment_stripe_for_checkout
    payment_intent = StripeObject(id="ABC", last_response={})
    payment_intent["amount_received"] = price_to_minor_unit(
        payment.total, payment.currency
    )
    payment_intent["amount"] = price_to_minor_unit(payment.total, payment.currency)
    payment_intent["setup_future_usage"] = None
    payment_intent["currency"] = payment.currency
    payment_intent["status"] = SUCCESS_STATUS

    return payment_intent


@pytest.fixture
def stripe_payment_intent_with_details(stripe_payment_intent):
    intent = stripe_payment_intent

    intent["charges"] = {
        "data": [
            {
                "payment_method_details": {
                    "card": {
                        "brand": "visa",
                        "country": "IE",
                        "exp_month": 3,
                        "exp_year": 2030,
                        "fingerprint": "ZcPGL2hemVepaHp2",
                        "funding": "credit",
                        "installments": None,
                        "last4": "3220",
                        "network": "visa",
                        "three_d_secure": {
                            "authentication_flow": "challenge",
                            "result": "authenticated",
                            "result_reason": None,
                            "version": "2.1.0",
                        },
                        "wallet": None,
                    },
                    "type": "card",
                },
            }
        ]
    }

    return intent
