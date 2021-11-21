from unittest.mock import MagicMock

import pytest

from .....app.models import App
from .....checkout import calculations
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.utils import add_variant_to_checkout, add_voucher_to_checkout
from .....payment import ChargeStatus, TransactionKind
from .....payment.models import Payment
from .....plugins.manager import get_plugins_manager
from .....webhook.event_types import WebhookEventType
from .....webhook.models import Webhook


@pytest.fixture
def mock_webhook_plugin_with_shipping_app(
    settings,
    permission_manage_checkouts,
    permission_manage_payments,
    monkeypatch,
    shipping_methods_for_channel_factory,
):
    # Create additional shipping methods available in the channel
    shipping_methods_for_channel_factory(5)

    # Mock http requests as we are focusing on testing database access
    response = MagicMock()
    response.json.return_value = {}
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: response)
    monkeypatch.setattr(
        "saleor.plugins.webhook.utils.parse_list_payment_gateways_response",
        lambda *args, **kwargs: [],
    )
    monkeypatch.setattr(
        "saleor.plugins.webhook.utils.get_excluded_shipping_methods_from_response",
        lambda *args, **kwargs: [],
    )

    # Enable webhook plugin
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    # Create multiple apps with a shipping webhook
    for i in range(3):
        app = App.objects.create(name=f"Benchmark App {i}", is_active=True)
        app.tokens.create(name="Default")
        app.permissions.add(permission_manage_checkouts)
        app.permissions.add(permission_manage_payments)
        webhook = Webhook.objects.create(
            name="shipping-webhook-1",
            app=app,
            target_url="https://gateway.com/api/",
        )
        webhook.events.create(
            event_type=WebhookEventType.CHECKOUT_FILTER_SHIPPING_METHODS,
            webhook=webhook,
        )
        webhook.events.create(
            event_type=WebhookEventType.PAYMENT_LIST_GATEWAYS,
            webhook=webhook,
        )


@pytest.fixture
def customer_checkout(
    customer_user,
    checkout_with_voucher_percentage_and_shipping,
):
    checkout_with_voucher_percentage_and_shipping.user = customer_user
    checkout_with_voucher_percentage_and_shipping.save()
    return checkout_with_voucher_percentage_and_shipping


@pytest.fixture()
def checkout_with_variants(
    checkout,
    stock,
    product_with_default_variant,
    product_with_single_variant,
    product_with_two_variants,
):
    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())

    add_variant_to_checkout(
        checkout_info, product_with_default_variant.variants.get(), 1
    )
    add_variant_to_checkout(
        checkout_info, product_with_single_variant.variants.get(), 10
    )
    add_variant_to_checkout(
        checkout_info, product_with_two_variants.variants.first(), 3
    )
    add_variant_to_checkout(checkout_info, product_with_two_variants.variants.last(), 5)

    checkout.save()
    return checkout


@pytest.fixture()
def checkout_with_shipping_address(checkout_with_variants, address):
    checkout = checkout_with_variants

    checkout.shipping_address = address.get_copy()
    checkout.save()

    return checkout


@pytest.fixture()
def checkout_with_shipping_method(checkout_with_shipping_address, shipping_method):
    checkout = checkout_with_shipping_address

    checkout.shipping_method = shipping_method
    checkout.save()

    return checkout


@pytest.fixture()
def checkout_with_billing_address(checkout_with_shipping_method, address):
    checkout = checkout_with_shipping_method

    checkout.billing_address = address
    checkout.save()

    return checkout


@pytest.fixture()
def checkout_with_voucher(checkout_with_billing_address, voucher):
    checkout = checkout_with_billing_address
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    add_voucher_to_checkout(manager, checkout_info, lines, voucher)
    return checkout


@pytest.fixture()
def checkout_with_charged_payment(checkout_with_voucher):
    checkout = checkout_with_voucher
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout_with_voucher, lines, [], manager)
    manager = get_plugins_manager()
    taxed_total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    payment = Payment.objects.create(
        gateway="mirumee.payments.dummy",
        is_active=True,
        total=taxed_total.gross.amount,
        currency="USD",
    )

    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.checkout = checkout
    payment.save()

    payment.transactions.create(
        amount=payment.total,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
    )

    return checkout
