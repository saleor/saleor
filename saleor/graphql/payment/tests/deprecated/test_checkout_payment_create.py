import graphene

from .....checkout import calculations
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....payment.error_codes import PaymentErrorCode
from .....payment.models import ChargeStatus, Payment
from .....plugins.manager import get_plugins_manager
from ....tests.utils import get_graphql_content

DUMMY_GATEWAY = "mirumee.payments.dummy"

CREATE_PAYMENT_MUTATION = """
    mutation CheckoutPaymentCreate(
        $checkoutId: ID, $token: UUID, $input: PaymentInput!
    ) {
        checkoutPaymentCreate(checkoutId: $checkoutId, token: $token, input: $input) {
            payment {
                chargeStatus
            }
            errors {
                code
                field
            }
        }
    }
    """


def test_checkout_add_payment_by_checkout_id(
    user_api_client, checkout_without_shipping_required, address
):
    # given
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.save()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    variables = {
        "checkoutId": checkout_id,
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


def test_checkout_add_payment_neither_token_and_id_given(
    user_api_client, checkout_without_shipping_required, address
):
    # given
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    variables = {
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
    assert len(data["errors"]) == 1
    assert not data["payment"]
    assert data["errors"][0]["code"] == PaymentErrorCode.GRAPHQL_ERROR.name


def test_checkout_add_payment_both_token_and_id_given(
    user_api_client, checkout_without_shipping_required, address
):
    # given
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.save()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    variables = {
        "checkoutId": checkout_id,
        "token": checkout.token,
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
    assert len(data["errors"]) == 1
    assert not data["payment"]
    assert data["errors"][0]["code"] == PaymentErrorCode.GRAPHQL_ERROR.name
