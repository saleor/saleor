from decimal import Decimal

import graphene
import pytest

from .....order import OrderEvents
from .....payment.error_codes import PaymentUpdateErrorCode
from .....payment.models import Payment
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import PaymentActionEnum

MUTATION_PAYMENT_UPDATE = """
mutation PaymentUpdate(
    $id: ID!,
    $transaction: TransactionInput,
    $payment: PaymentUpdateInput
    ){
    paymentUpdate(id: $id, transaction: $transaction, payment: $payment){
        payment{
                id
                actions
                reference
                type
                status
                modified
                created
                authorizedAmount{
                    amount
                    currency
                }
                voidedAmount{
                    currency
                    amount
                }
                capturedAmount{
                    currency
                    amount
                }
                refundedAmount{
                    currency
                    amount
                }
        }
        errors{
            field
            message
            code
        }
    }
}
"""


@pytest.fixture
def payment(order_with_lines):
    return Payment.objects.create(
        status="Authorized",
        type="Credit card",
        reference="PSP ref",
        available_actions=["capture", "void"],
        currency="USD",
        order_id=order_with_lines.pk,
        authorized_value=Decimal("10"),
    )


def test_payment_update_status(payment, permission_manage_payments, app_api_client):
    # given
    status = "Captured for 10$"

    variables = {
        "id": graphene.Node.to_global_id("Payment", payment.pk),
        "payment": {
            "status": status,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_PAYMENT_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    payment.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["paymentUpdate"]["payment"]
    assert data["status"] == status
    assert payment.status == status


def test_payment_update_type(payment, permission_manage_payments, app_api_client):
    # given
    type = "New credit card"

    variables = {
        "id": graphene.Node.to_global_id("Payment", payment.pk),
        "payment": {
            "type": type,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_PAYMENT_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    payment.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["paymentUpdate"]["payment"]
    assert data["type"] == type
    assert payment.type == type


def test_payment_update_reference(payment, permission_manage_payments, app_api_client):
    # given
    reference = "PSP:123AAA"

    variables = {
        "id": graphene.Node.to_global_id("Payment", payment.pk),
        "payment": {
            "reference": reference,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_PAYMENT_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    payment.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["paymentUpdate"]["payment"]
    assert data["reference"] == reference
    assert payment.reference == reference


def test_payment_update_available_actions(
    payment, permission_manage_payments, app_api_client
):
    # given
    available_actions = [PaymentActionEnum.REFUND.name]

    variables = {
        "id": graphene.Node.to_global_id("Payment", payment.pk),
        "payment": {
            "availableActions": available_actions,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_PAYMENT_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    payment.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["paymentUpdate"]["payment"]
    assert data["actions"] == available_actions
    assert payment.available_actions == ["refund"]


@pytest.mark.parametrize(
    "field_name, response_field, db_field_name, value",
    [
        ("amountAuthorized", "authorizedAmount", "authorized_value", Decimal("12")),
        ("amountCaptured", "capturedAmount", "captured_value", Decimal("13")),
        ("amountVoided", "voidedAmount", "voided_value", Decimal("14")),
        ("amountRefunded", "refundedAmount", "refunded_value", Decimal("15")),
    ],
)
def test_payment_update_amounts(
    field_name,
    response_field,
    db_field_name,
    value,
    payment,
    permission_manage_payments,
    app_api_client,
):
    # given

    variables = {
        "id": graphene.Node.to_global_id("Payment", payment.pk),
        "payment": {field_name: {"amount": value, "currency": "USD"}},
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_PAYMENT_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    payment.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["paymentUpdate"]["payment"]
    assert data[response_field]["amount"] == value
    assert getattr(payment, db_field_name) == value


def test_payment_update_multiple_amounts_provided(
    payment, permission_manage_payments, app_api_client
):
    # given
    authorized_value = Decimal("10")
    captured_value = Decimal("11")
    refunded_value = Decimal("12")
    voided_value = Decimal("13")

    variables = {
        "id": graphene.Node.to_global_id("Payment", payment.pk),
        "payment": {
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
            "amountCaptured": {
                "amount": captured_value,
                "currency": "USD",
            },
            "amountRefunded": {
                "amount": refunded_value,
                "currency": "USD",
            },
            "amountVoided": {
                "amount": voided_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_PAYMENT_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    payment = Payment.objects.first()
    content = get_graphql_content(response)
    data = content["data"]["paymentUpdate"]["payment"]
    assert data["authorizedAmount"]["amount"] == authorized_value
    assert data["capturedAmount"]["amount"] == captured_value
    assert data["refundedAmount"]["amount"] == refunded_value
    assert data["voidedAmount"]["amount"] == voided_value

    assert payment.authorized_value == authorized_value
    assert payment.captured_value == captured_value
    assert payment.voided_value == voided_value
    assert payment.refunded_value == refunded_value


def test_payment_create_for_order_missing_app_permission(payment, app_api_client):
    # given
    status = "Authorized for 10$"
    type = "Credit Card"

    variables = {
        "id": graphene.Node.to_global_id("Payment", payment.pk),
        "payment": {
            "status": status,
            "type": type,
        },
    }

    # when
    response = app_api_client.post_graphql(MUTATION_PAYMENT_UPDATE, variables)

    # then
    assert_no_permission(response)


@pytest.mark.parametrize(
    "amount_field_name, amount_db_field",
    [
        ("amountAuthorized", "authorized_value"),
        ("amountCaptured", "captured_value"),
        ("amountVoided", "voided_value"),
        ("amountRefunded", "refunded_value"),
    ],
)
def test_payment_create_incorrect_currency(
    amount_field_name,
    amount_db_field,
    payment,
    permission_manage_payments,
    app_api_client,
):
    # given
    expected_value = Decimal("10")

    variables = {
        "id": graphene.Node.to_global_id("Payment", payment.pk),
        "payment": {
            amount_field_name: {
                "amount": expected_value,
                "currency": "PLN",
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_PAYMENT_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentUpdate"]
    assert data["errors"][0]["field"] == amount_field_name
    assert data["errors"][0]["code"] == PaymentUpdateErrorCode.INCORRECT_CURRENCY.name


def test_payment_update_adds_payment_event_to_order(
    payment, order_with_lines, permission_manage_payments, app_api_client
):
    # given
    transaction_status = "PENDING"
    transaction_reference = "transaction reference"
    transaction_name = "Processing transaction"

    variables = {
        "id": graphene.Node.to_global_id("Payment", payment.pk),
        "transaction": {
            "status": transaction_status,
            "reference": transaction_reference,
            "name": transaction_name,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_PAYMENT_UPDATE, variables, permissions=[permission_manage_payments]
    )
    # then
    event = order_with_lines.events.first()
    content = get_graphql_content(response)
    data = content["data"]["paymentUpdate"]

    assert not data["errors"]
    assert event.type == OrderEvents.PAYMENT_EVENT
    assert event.parameters == {
        "message": transaction_name,
        "reference": transaction_reference,
        "status": transaction_status.lower(),
    }
