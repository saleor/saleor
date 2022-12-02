import pytest

from .....checkout import calculations
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.models import CheckoutLine
from .....checkout.utils import add_variant_to_checkout, add_voucher_to_checkout
from .....payment import ChargeStatus, TransactionKind
from .....payment.models import Payment
from .....plugins.manager import get_plugins_manager


@pytest.fixture
def customer_checkout(customer_user, checkout_with_voucher_percentage_and_shipping):
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


@pytest.fixture
def checkout_with_variants_for_cc(checkout_for_cc, stocks_for_cc, product_variant_list):
    CheckoutLine.objects.bulk_create(
        [
            CheckoutLine(
                checkout=checkout_for_cc,
                variant=product_variant_list[0],
                quantity=1,
                currency="USD",
            ),
            CheckoutLine(
                checkout=checkout_for_cc,
                variant=product_variant_list[1],
                quantity=1,
                currency="USD",
            ),
        ]
    )
    return checkout_for_cc


@pytest.fixture()
def checkout_with_shipping_address(checkout_with_variants, address):
    checkout = checkout_with_variants

    checkout.shipping_address = address.get_copy()
    checkout.save()

    return checkout


@pytest.fixture()
def checkout_with_shipping_address_for_cc(checkout_with_variants_for_cc, address):
    checkout = checkout_with_variants_for_cc

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
def checkout_with_delivery_method_for_cc(
    warehouses_for_cc, checkout_with_shipping_address_for_cc
):
    checkout = checkout_with_shipping_address_for_cc
    checkout.collection_point = warehouses_for_cc[1]

    checkout.save()

    return checkout


@pytest.fixture()
def checkout_with_billing_address(checkout_with_shipping_method, address):
    checkout = checkout_with_shipping_method

    checkout.billing_address = address
    checkout.save()

    return checkout


@pytest.fixture()
def checkout_with_billing_address_for_cc(checkout_with_delivery_method_for_cc, address):
    checkout = checkout_with_delivery_method_for_cc

    checkout.billing_address = address
    checkout.save()

    return checkout


@pytest.fixture()
def checkout_with_voucher(checkout_with_billing_address, voucher):
    checkout = checkout_with_billing_address
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    add_voucher_to_checkout(manager, checkout_info, lines, voucher)
    return checkout


@pytest.fixture()
def checkout_with_charged_payment(checkout_with_voucher):
    checkout = checkout_with_voucher
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
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


@pytest.fixture()
def checkout_with_digital_line_with_charged_payment(
    checkout_with_billing_address, digital_content, site_settings
):
    checkout = checkout_with_billing_address
    variant = digital_content.product_variant

    site_settings.automatic_fulfillment_digital_products = True
    site_settings.save(update_fields=["automatic_fulfillment_digital_products"])

    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 1)
    manager = get_plugins_manager()
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


@pytest.fixture()
def checkout_with_charged_payment_for_cc(checkout_with_billing_address_for_cc):
    checkout = checkout_with_billing_address_for_cc
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
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


@pytest.fixture()
def checkout_preorder_with_charged_payment(
    checkout_with_billing_address,
    preorder_variant_channel_threshold,
    preorder_variant_global_threshold,
):
    checkout = checkout_with_billing_address
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    add_variant_to_checkout(checkout_info, preorder_variant_channel_threshold, 1)
    add_variant_to_checkout(checkout_info, preorder_variant_global_threshold, 1)

    lines, _ = fetch_checkout_lines(checkout)
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
