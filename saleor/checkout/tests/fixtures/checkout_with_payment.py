import pytest

from ....payment import ChargeStatus, TransactionKind
from ....payment.models import Payment
from ....plugins.manager import get_plugins_manager
from ... import calculations
from ...fetch import fetch_checkout_info, fetch_checkout_lines
from ...utils import add_variant_to_checkout


@pytest.fixture
def checkout_with_payments(checkout):
    Payment.objects.bulk_create(
        [
            Payment(
                gateway="mirumee.payments.dummy", is_active=True, checkout=checkout
            ),
            Payment(
                gateway="mirumee.payments.dummy", is_active=False, checkout=checkout
            ),
        ]
    )
    return checkout


@pytest.fixture
def checkout_with_charged_payment(checkout_with_billing_address):
    checkout = checkout_with_billing_address
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
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


@pytest.fixture
def checkout_with_charged_payment_for_cc(checkout_with_billing_address_for_cc):
    checkout = checkout_with_billing_address_for_cc
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    manager = get_plugins_manager(allow_replica=False)
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


@pytest.fixture
def checkout_preorder_with_charged_payment(
    checkout_with_billing_address,
    preorder_variant_channel_threshold,
    preorder_variant_global_threshold,
):
    checkout = checkout_with_billing_address
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    add_variant_to_checkout(checkout_info, preorder_variant_channel_threshold, 1)
    add_variant_to_checkout(checkout_info, preorder_variant_global_threshold, 1)

    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager(allow_replica=False)
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


@pytest.fixture
def checkout_with_digital_line_with_charged_payment(
    checkout_with_billing_address, digital_content, site_settings
):
    checkout = checkout_with_billing_address
    variant = digital_content.product_variant

    site_settings.automatic_fulfillment_digital_products = True
    site_settings.save(update_fields=["automatic_fulfillment_digital_products"])

    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, variant, 1)
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
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
