from decimal import Decimal
from unittest.mock import patch

import before_after
import graphene
import pytest

from .....checkout import calculations
from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.utils import add_variant_to_checkout
from .....payment import StorePaymentMethod
from .....payment.error_codes import PaymentErrorCode
from .....payment.interface import StorePaymentMethodEnum
from .....payment.models import ChargeStatus, Payment
from .....plugins.manager import get_plugins_manager
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

DUMMY_GATEWAY = "mirumee.payments.dummy"

CREATE_PAYMENT_MUTATION = """
    mutation CheckoutPaymentCreate(
        $id: ID,
        $input: PaymentInput!,
    ) {
        checkoutPaymentCreate(
            id: $id,
            input: $input,
        ) {
            payment {
                chargeStatus
            }
            errors {
                code
                field
                variants
            }
        }
    }
    """


def test_checkout_add_payment_without_shipping_method_and_not_shipping_required(
    user_api_client, checkout_without_shipping_required, address
):
    # given
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    # when
    variables = {
        "id": to_global_id_or_none(checkout),
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
        },
    }
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]
    assert not data["errors"]
    payment = Payment.objects.get()
    assert payment.checkout == checkout
    assert payment.is_active
    assert payment.token == "sample-token"
    assert payment.total == total.gross.amount
    assert payment.currency == total.gross.currency
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert payment.billing_address_1 == checkout.billing_address.street_address_1
    assert payment.billing_first_name == checkout.billing_address.first_name
    assert payment.billing_last_name == checkout.billing_address.last_name


def test_checkout_add_payment_without_shipping_method_with_shipping_required(
    user_api_client, checkout_with_shipping_required, address
):
    # given
    checkout = checkout_with_shipping_required

    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    variables = {
        "id": to_global_id_or_none(checkout),
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
        },
    }

    # when
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]

    assert data["errors"][0]["code"] == "SHIPPING_METHOD_NOT_SET"
    assert data["errors"][0]["field"] == "shippingMethod"


def test_checkout_add_payment_with_shipping_method_and_shipping_required(
    user_api_client, checkout_with_shipping_required, other_shipping_method, address
):
    # given
    checkout = checkout_with_shipping_required
    checkout.billing_address = address
    checkout.shipping_address = address
    checkout.shipping_method = other_shipping_method
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    variables = {
        "id": to_global_id_or_none(checkout),
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
        },
    }

    # when
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]

    assert not data["errors"]
    payment = Payment.objects.get()
    assert payment.checkout == checkout
    assert payment.is_active
    assert payment.token == "sample-token"
    assert payment.total == total.gross.amount
    assert payment.currency == total.gross.currency
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert payment.billing_address_1 == checkout.billing_address.street_address_1
    assert payment.billing_first_name == checkout.billing_address.first_name
    assert payment.billing_last_name == checkout.billing_address.last_name


def test_checkout_add_payment(
    user_api_client, checkout_without_shipping_required, address, customer_user
):
    # given
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.email = "old@example"
    checkout.user = customer_user
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    return_url = "https://www.example.com"
    variables = {
        "id": to_global_id_or_none(checkout),
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
            "returnUrl": return_url,
        },
    }

    # when
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]

    assert not data["errors"]
    payment = Payment.objects.get()
    assert payment.checkout == checkout
    assert payment.is_active
    assert payment.token == "sample-token"
    assert payment.total == total.gross.amount
    assert payment.currency == total.gross.currency
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert payment.billing_address_1 == checkout.billing_address.street_address_1
    assert payment.billing_first_name == checkout.billing_address.first_name
    assert payment.billing_last_name == checkout.billing_address.last_name
    assert payment.return_url == return_url
    assert payment.billing_email == customer_user.email


def test_checkout_add_payment_default_amount(
    user_api_client, checkout_without_shipping_required, address
):
    # given
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "input": {"gateway": DUMMY_GATEWAY, "token": "sample-token"},
    }

    # when
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]
    assert not data["errors"]
    payment = Payment.objects.get()
    assert payment.checkout == checkout
    assert payment.is_active
    assert payment.token == "sample-token"
    assert payment.total == total.gross.amount
    assert payment.currency == total.gross.currency
    assert payment.charge_status == ChargeStatus.NOT_CHARGED


def test_checkout_add_payment_bad_amount(
    user_api_client, checkout_without_shipping_required, address
):
    # given
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    variables = {
        "id": to_global_id_or_none(checkout),
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": str(total.gross.amount + Decimal(1)),
        },
    }

    # when
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]
    assert (
        data["errors"][0]["code"] == PaymentErrorCode.PARTIAL_PAYMENT_NOT_ALLOWED.name
    )


def test_checkout_add_payment_no_checkout_email(
    user_api_client, checkout_without_shipping_required, address, customer_user
):
    # given
    checkout = checkout_without_shipping_required
    checkout.email = None
    checkout.save(update_fields=["email"])

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    return_url = "https://www.example.com"
    variables = {
        "id": to_global_id_or_none(checkout),
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
            "returnUrl": return_url,
        },
    }

    # when
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]

    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == PaymentErrorCode.CHECKOUT_EMAIL_NOT_SET.name


@patch(
    "saleor.payment.gateways.dummy.plugin.DummyGatewayPlugin.CONFIGURATION_PER_CHANNEL",
    False,
)
def test_checkout_add_payment_not_supported_currency(
    user_api_client, checkout_without_shipping_required, address
):
    # given
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.currency = "EUR"
    checkout.save(update_fields=["billing_address", "currency"])

    variables = {
        "id": to_global_id_or_none(checkout),
        "input": {"gateway": DUMMY_GATEWAY, "token": "sample-token", "amount": "10.0"},
    }

    # when
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]
    assert data["errors"][0]["code"] == PaymentErrorCode.NOT_SUPPORTED_GATEWAY.name
    assert data["errors"][0]["field"] == "gateway"


def test_checkout_add_payment_not_existing_gateway(
    user_api_client, checkout_without_shipping_required, address
):
    # given
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.save(update_fields=["billing_address", "currency"])

    variables = {
        "id": to_global_id_or_none(checkout),
        "input": {"gateway": "not.existing", "token": "sample-token", "amount": "10.0"},
    }

    # when
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]
    assert data["errors"][0]["code"] == PaymentErrorCode.NOT_SUPPORTED_GATEWAY.name
    assert data["errors"][0]["field"] == "gateway"


@patch("saleor.payment.gateways.dummy.plugin.DummyGatewayPlugin.DEFAULT_ACTIVE", False)
def test_checkout_add_payment_gateway_inactive(
    user_api_client, checkout_without_shipping_required, address
):
    # given
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.save(update_fields=["billing_address", "currency"])

    variables = {
        "id": to_global_id_or_none(checkout),
        "input": {"gateway": DUMMY_GATEWAY, "token": "sample-token", "amount": "10.0"},
    }

    # when
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]
    assert data["errors"][0]["code"] == PaymentErrorCode.NOT_SUPPORTED_GATEWAY.name
    assert data["errors"][0]["field"] == "gateway"


def test_use_checkout_billing_address_as_payment_billing(
    user_api_client, checkout_without_shipping_required, address
):
    # given
    checkout = checkout_without_shipping_required
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    variables = {
        "id": to_global_id_or_none(checkout),
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
        },
    }

    # when
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]

    # check if proper error is returned if address is missing
    assert data["errors"][0]["field"] == "billingAddress"
    assert data["errors"][0]["code"] == PaymentErrorCode.BILLING_ADDRESS_NOT_SET.name

    # assign the address and try again
    address.street_address_1 = "spanish-inqusition"
    address.save()
    checkout.billing_address = address
    checkout.save()
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    get_graphql_content(response)

    checkout.refresh_from_db()
    assert checkout.payments.count() == 1
    payment = checkout.payments.first()
    assert payment.billing_address_1 == address.street_address_1


def test_create_payment_for_checkout_with_active_payments(
    checkout_with_payments, user_api_client, address, product_without_shipping
):
    # given
    checkout = checkout_with_payments
    address.street_address_1 = "spanish-inqusition"
    address.save()
    checkout.billing_address = address
    manager = get_plugins_manager()
    variant = product_without_shipping.variants.get()
    checkout_info = fetch_checkout_info(checkout, [], manager)
    add_variant_to_checkout(checkout_info, variant, 1)
    checkout.save()

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    variables = {
        "id": to_global_id_or_none(checkout),
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
        },
    }

    payments_count = checkout.payments.count()
    previous_active_payments = checkout.payments.filter(is_active=True)
    previous_active_payments_ids = list(
        previous_active_payments.values_list("pk", flat=True)
    )
    assert len(previous_active_payments_ids) > 0

    # when
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["checkoutPaymentCreate"]

    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.payments.all().count() == payments_count + 1
    active_payments = checkout.payments.all().filter(is_active=True)
    assert active_payments.count() == 1
    assert active_payments.first().pk not in previous_active_payments_ids


@pytest.mark.parametrize(
    "store",
    [
        StorePaymentMethodEnum.NONE,
        StorePaymentMethodEnum.ON_SESSION,
        StorePaymentMethodEnum.OFF_SESSION,
    ],
)
def test_create_payment_with_store(
    user_api_client, checkout_without_shipping_required, address, store
):
    # given
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    variables = {
        "id": to_global_id_or_none(checkout),
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
            "storePaymentMethod": store,
        },
    }

    # when
    user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)

    # then
    checkout.refresh_from_db()
    payment = checkout.payments.first()
    assert payment.store_payment_method == store.lower()


def test_create_payment_with_store_as_none(
    user_api_client, checkout_without_shipping_required, address
):
    # given
    store = None
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    variables = {
        "id": to_global_id_or_none(checkout),
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
            "storePaymentMethod": store,
        },
    }

    # when
    user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)

    # then
    checkout.refresh_from_db()
    payment = checkout.payments.first()
    assert payment.store_payment_method == StorePaymentMethod.NONE


@pytest.mark.parametrize(
    "metadata", [[{"key": f"key{i}", "value": f"value{i}"} for i in range(5)], [], None]
)
def test_create_payment_with_metadata(
    user_api_client, checkout_without_shipping_required, address, metadata
):
    # given
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    variables = {
        "id": to_global_id_or_none(checkout),
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
            "metadata": metadata,
        },
    }

    # when
    user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)

    # then
    checkout.refresh_from_db()
    payment = checkout.payments.first()
    assert payment.metadata == {m["key"]: m["value"] for m in metadata or {}}


def test_checkout_add_payment_no_variant_channel_listings(
    user_api_client, checkout_without_shipping_required, address, customer_user
):
    # given
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.email = "old@example"
    checkout.user = customer_user
    checkout.save()

    variant = checkout.lines.first().variant
    variant.product.channel_listings.filter(channel=checkout.channel_id).delete()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    return_url = "https://www.example.com"
    variables = {
        "id": to_global_id_or_none(checkout),
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
            "returnUrl": return_url,
        },
    }

    # when
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert errors[0]["field"] == "token"
    assert errors[0]["variants"] == [
        graphene.Node.to_global_id("ProductVariant", variant.pk)
    ]


def test_checkout_add_payment_no_product_channel_listings(
    user_api_client, checkout_without_shipping_required, address, customer_user
):
    # given
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.email = "old@example"
    checkout.user = customer_user
    checkout.save()

    variant = checkout.lines.first().variant
    variant.channel_listings.filter(channel=checkout.channel_id).delete()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    return_url = "https://www.example.com"
    variables = {
        "id": to_global_id_or_none(checkout),
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
            "returnUrl": return_url,
        },
    }

    # when
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert errors[0]["field"] == "token"
    assert errors[0]["variants"] == [
        graphene.Node.to_global_id("ProductVariant", variant.pk)
    ]


def test_checkout_add_payment_checkout_without_lines(
    user_api_client, checkout_without_shipping_required, address, customer_user
):
    # given
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.email = "old@example"
    checkout.user = customer_user
    checkout.save()

    checkout.lines.all().delete()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    return_url = "https://www.example.com"
    variables = {
        "id": to_global_id_or_none(checkout),
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
            "returnUrl": return_url,
        },
    }

    # when
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "lines"
    assert errors[0]["code"] == PaymentErrorCode.NO_CHECKOUT_LINES.name


def test_checkout_add_payment_run_multiple_times(
    user_api_client, checkout_without_shipping_required, address
):
    # given
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    variables = {
        "id": to_global_id_or_none(checkout),
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
        },
    }

    # call CheckoutPaymentCreate mutation during the first mutation call processing
    def call_payment_create_mutation(*args, **kwargs):
        user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)

    # when
    with before_after.before(
        "saleor.graphql.payment.mutations.payment."
        "checkout_payment_create.cancel_active_payments",
        call_payment_create_mutation,
    ):
        response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]
    assert not data["errors"]
    payments = Payment.objects.filter(checkout=checkout)
    assert payments.count() == 2
    assert payments.filter(is_active=True).count() == 1


def test_with_active_problems_flow(
    api_client,
    checkout_with_problems,
    shipping_method,
):
    # given
    channel = checkout_with_problems.channel
    channel.use_legacy_error_flow_for_checkout = False
    channel.save(update_fields=["use_legacy_error_flow_for_checkout"])

    return_url = "https://www.example.com"
    variables = {
        "id": to_global_id_or_none(checkout_with_problems),
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "returnUrl": return_url,
        },
    }

    # when
    response = api_client.post_graphql(
        CREATE_PAYMENT_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["checkoutPaymentCreate"]["errors"]
