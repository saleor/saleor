from decimal import Decimal

import graphene
import pytest

from .....order import OrderEvents
from .....payment.error_codes import PaymentCreateErrorCode
from .....payment.models import Payment
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import PaymentActionEnum

MUTATION_PAYMENT_CREATE = """
mutation PaymentCrate(
    $id: ID!,
    $transaction: TransactionInput,
    $payment: PaymentCreateInput!
    ){
    paymentCreate(id: $id, transaction: $transaction, payment: $payment){
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


def test_payment_create_for_order(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    status = "Authorized for 10$"
    type = "Credit Card"
    reference = "PSP reference - 123"
    available_actions = [PaymentActionEnum.CAPTURE.name, PaymentActionEnum.VOID.name]
    authorized_value = Decimal("10")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "payment": {
            "status": status,
            "type": type,
            "reference": reference,
            "availableActions": available_actions,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
            "metadata": [metadata],
            "privateMetadata": [private_metadata],
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_PAYMENT_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    payment = order_with_lines.payments.first()
    content = get_graphql_content(response)
    data = content["data"]["paymentCreate"]["payment"]
    assert data["actions"] == available_actions
    assert data["status"] == status
    assert data["reference"] == reference
    assert data["authorizedAmount"]["amount"] == authorized_value

    assert available_actions == list(map(str.upper, payment.available_actions))
    assert status == payment.status
    assert reference == payment.reference
    assert authorized_value == payment.authorized_value
    assert payment.metadata == {metadata["key"]: metadata["value"]}
    assert payment.private_metadata == {
        private_metadata["key"]: private_metadata["value"]
    }


def test_payment_create_for_checkout(
    checkout_with_items, permission_manage_payments, app_api_client
):
    # given
    status = "Authorized for 10$"
    type = "Credit Card"
    reference = "PSP reference - 123"
    available_actions = [PaymentActionEnum.CAPTURE.name, PaymentActionEnum.VOID.name]
    authorized_value = Decimal("10")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}

    variables = {
        "id": graphene.Node.to_global_id("Checkout", checkout_with_items.pk),
        "payment": {
            "status": status,
            "type": type,
            "reference": reference,
            "availableActions": available_actions,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
            "metadata": [metadata],
            "privateMetadata": [private_metadata],
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_PAYMENT_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    payment = checkout_with_items.payments.first()
    content = get_graphql_content(response)
    data = content["data"]["paymentCreate"]["payment"]
    assert data["actions"] == available_actions
    assert data["status"] == status
    assert data["reference"] == reference
    assert data["authorizedAmount"]["amount"] == authorized_value

    assert available_actions == list(map(str.upper, payment.available_actions))
    assert status == payment.status
    assert reference == payment.reference
    assert authorized_value == payment.authorized_value
    assert payment.metadata == {metadata["key"]: metadata["value"]}
    assert payment.private_metadata == {
        private_metadata["key"]: private_metadata["value"]
    }


@pytest.mark.parametrize(
    "amount_field_name, amount_db_field",
    [
        ("amountAuthorized", "authorized_value"),
        ("amountCaptured", "captured_value"),
        ("amountVoided", "voided_value"),
        ("amountRefunded", "refunded_value"),
    ],
)
def test_payment_create_calculate_amount(
    amount_field_name,
    amount_db_field,
    order_with_lines,
    permission_manage_payments,
    app_api_client,
):
    # given
    status = "Authorized for 10$"
    type = "Credit Card"
    reference = "PSP reference - 123"
    expected_value = Decimal("10")

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "payment": {
            "status": status,
            "type": type,
            "reference": reference,
            "availableActions": [],
            amount_field_name: {
                "amount": expected_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_PAYMENT_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    payment = Payment.objects.first()
    get_graphql_content(response)

    assert getattr(payment, amount_db_field) == expected_value


def test_payment_create_multiple_amounts_provided(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    status = "Authorized for 10$"
    type = "Credit Card"
    reference = "PSP reference - 123"
    available_actions = [PaymentActionEnum.CAPTURE.name, PaymentActionEnum.VOID.name]
    authorized_value = Decimal("10")
    captured_value = Decimal("11")
    refunded_value = Decimal("12")
    voided_value = Decimal("13")

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "payment": {
            "status": status,
            "type": type,
            "reference": reference,
            "availableActions": available_actions,
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
        MUTATION_PAYMENT_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    payment = Payment.objects.first()
    content = get_graphql_content(response)
    data = content["data"]["paymentCreate"]["payment"]
    assert data["actions"] == available_actions
    assert data["status"] == status
    assert data["reference"] == reference
    assert data["authorizedAmount"]["amount"] == authorized_value
    assert data["capturedAmount"]["amount"] == captured_value
    assert data["refundedAmount"]["amount"] == refunded_value
    assert data["voidedAmount"]["amount"] == voided_value

    assert payment.authorized_value == authorized_value
    assert payment.captured_value == captured_value
    assert payment.voided_value == voided_value
    assert payment.refunded_value == refunded_value


def test_payment_create_create_event_for_order(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    status = "Authorized for 10$"
    type = "Credit Card"
    reference = "PSP reference - 123"
    available_actions = [PaymentActionEnum.CAPTURE.name, PaymentActionEnum.VOID.name]
    authorized_value = Decimal("10")
    transaction_status = "PENDING"
    transaction_reference = "transaction reference"
    transaction_name = "Processing transaction"

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "payment": {
            "status": status,
            "type": type,
            "reference": reference,
            "availableActions": available_actions,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
        },
        "transaction": {
            "status": transaction_status,
            "reference": transaction_reference,
            "name": transaction_name,
        },
    }

    # when
    app_api_client.post_graphql(
        MUTATION_PAYMENT_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    event = order_with_lines.events.first()

    assert event.type == OrderEvents.PAYMENT_EVENT
    assert event.parameters == {
        "message": transaction_name,
        "reference": transaction_reference,
        "status": transaction_status.lower(),
    }


def test_payment_create_missing_app_permission(order_with_lines, app_api_client):
    # given
    status = "Authorized for 10$"
    type = "Credit Card"
    reference = "PSP reference - 123"
    available_actions = [PaymentActionEnum.CAPTURE.name, PaymentActionEnum.VOID.name]
    authorized_value = Decimal("10")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "payment": {
            "status": status,
            "type": type,
            "reference": reference,
            "availableActions": available_actions,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
            "metadata": [metadata],
            "privateMetadata": [private_metadata],
        },
    }

    # when
    response = app_api_client.post_graphql(MUTATION_PAYMENT_CREATE, variables)

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
    order_with_lines,
    permission_manage_payments,
    app_api_client,
):
    # given
    status = "Authorized for 10$"
    type = "Credit Card"
    reference = "PSP reference - 123"
    expected_value = Decimal("10")

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "payment": {
            "status": status,
            "type": type,
            "reference": reference,
            "availableActions": [],
            amount_field_name: {
                "amount": expected_value,
                "currency": "PLN",
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_PAYMENT_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentCreate"]
    assert data["errors"][0]["field"] == amount_field_name
    assert data["errors"][0]["code"] == PaymentCreateErrorCode.INCORRECT_CURRENCY.name
