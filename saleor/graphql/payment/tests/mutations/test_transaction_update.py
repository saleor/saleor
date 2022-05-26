from decimal import Decimal

import graphene
import pytest

from .....order import OrderEvents
from .....payment import TransactionStatus
from .....payment.error_codes import TransactionUpdateErrorCode
from .....payment.models import TransactionItem
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import TransactionActionEnum, TransactionStatusEnum

MUTATION_TRANSACTION_UPDATE = """
mutation TransactionUpdate(
    $id: ID!,
    $transaction_event: TransactionEventInput,
    $transaction: TransactionUpdateInput
    ){
    transactionUpdate(
            id: $id,
            transactionEvent: $transaction_event,
            transaction: $transaction
        ){
        transaction{
                id
                actions
                reference
                type
                status
                modifiedAt
                createdAt
                authorizedAmount{
                    amount
                    currency
                }
                voidedAmount{
                    currency
                    amount
                }
                chargedAmount{
                    currency
                    amount
                }
                refundedAmount{
                    currency
                    amount
                }
                events{
                   status
                   reference
                   name
                   createdAt
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
def transaction(order_with_lines):
    return TransactionItem.objects.create(
        status="Authorized",
        type="Credit card",
        reference="PSP ref",
        available_actions=["charge", "void"],
        currency="USD",
        order_id=order_with_lines.pk,
        authorized_value=Decimal("10"),
    )


def test_transaction_update_status(
    transaction, permission_manage_payments, app_api_client
):
    # given
    status = "Captured for 10$"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.pk),
        "transaction": {
            "status": status,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["status"] == status
    assert transaction.status == status


def test_transaction_update_type(
    transaction, permission_manage_payments, app_api_client
):
    # given
    type = "New credit card"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.pk),
        "transaction": {
            "type": type,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["type"] == type
    assert transaction.type == type


def test_transaction_update_reference(
    transaction, permission_manage_payments, app_api_client
):
    # given
    reference = "PSP:123AAA"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.pk),
        "transaction": {
            "reference": reference,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["reference"] == reference
    assert transaction.reference == reference


def test_transaction_update_available_actions(
    transaction, permission_manage_payments, app_api_client
):
    # given
    available_actions = [TransactionActionEnum.REFUND.name]

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.pk),
        "transaction": {
            "availableActions": available_actions,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["actions"] == available_actions
    assert transaction.available_actions == ["refund"]


@pytest.mark.parametrize(
    "field_name, response_field, db_field_name, value",
    [
        ("amountAuthorized", "authorizedAmount", "authorized_value", Decimal("12")),
        ("amountCharged", "chargedAmount", "charged_value", Decimal("13")),
        ("amountVoided", "voidedAmount", "voided_value", Decimal("14")),
        ("amountRefunded", "refundedAmount", "refunded_value", Decimal("15")),
    ],
)
def test_transaction_update_amounts(
    field_name,
    response_field,
    db_field_name,
    value,
    transaction,
    permission_manage_payments,
    app_api_client,
):
    # given

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.pk),
        "transaction": {field_name: {"amount": value, "currency": "USD"}},
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert data[response_field]["amount"] == value
    assert getattr(transaction, db_field_name) == value


def test_transaction_update_multiple_amounts_provided(
    transaction, permission_manage_payments, app_api_client
):
    # given
    authorized_value = Decimal("10")
    charged_value = Decimal("11")
    refunded_value = Decimal("12")
    voided_value = Decimal("13")

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.pk),
        "transaction": {
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
            "amountCharged": {
                "amount": charged_value,
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
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction = TransactionItem.objects.first()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["authorizedAmount"]["amount"] == authorized_value
    assert data["chargedAmount"]["amount"] == charged_value
    assert data["refundedAmount"]["amount"] == refunded_value
    assert data["voidedAmount"]["amount"] == voided_value

    assert transaction.authorized_value == authorized_value
    assert transaction.charged_value == charged_value
    assert transaction.voided_value == voided_value
    assert transaction.refunded_value == refunded_value


def test_transaction_update_permission_denied_for_staff(
    transaction, staff_api_client, permission_manage_payments
):
    # given
    status = "Authorized for 10$"
    type = "Credit Card"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.pk),
        "transaction": {
            "status": status,
            "type": type,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    assert_no_permission(response)


def test_transaction_update_for_order_missing_app_permission(
    transaction, app_api_client
):
    # given
    status = "Authorized for 10$"
    type = "Credit Card"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.pk),
        "transaction": {
            "status": status,
            "type": type,
        },
    }

    # when
    response = app_api_client.post_graphql(MUTATION_TRANSACTION_UPDATE, variables)

    # then
    assert_no_permission(response)


@pytest.mark.parametrize(
    "amount_field_name, amount_db_field",
    [
        ("amountAuthorized", "authorized_value"),
        ("amountCharged", "charged_value"),
        ("amountVoided", "voided_value"),
        ("amountRefunded", "refunded_value"),
    ],
)
def test_transaction_update_incorrect_currency(
    amount_field_name,
    amount_db_field,
    transaction,
    permission_manage_payments,
    app_api_client,
):
    # given
    expected_value = Decimal("10")

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.pk),
        "transaction": {
            amount_field_name: {
                "amount": expected_value,
                "currency": "PLN",
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]
    assert data["errors"][0]["field"] == amount_field_name
    assert (
        data["errors"][0]["code"] == TransactionUpdateErrorCode.INCORRECT_CURRENCY.name
    )


def test_transaction_update_adds_transaction_event_to_order(
    transaction, order_with_lines, permission_manage_payments, app_api_client
):
    # given
    transaction_status = "PENDING"
    transaction_reference = "transaction reference"
    transaction_name = "Processing transaction"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.pk),
        "transaction_event": {
            "status": transaction_status,
            "reference": transaction_reference,
            "name": transaction_name,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )
    # then
    event = order_with_lines.events.first()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]

    assert not data["errors"]
    assert event.type == OrderEvents.TRANSACTION_EVENT
    assert event.parameters == {
        "message": transaction_name,
        "reference": transaction_reference,
        "status": transaction_status.lower(),
    }


def test_creates_transaction_event_for_order(
    transaction, order_with_lines, permission_manage_payments, app_api_client
):
    # given
    transaction = order_with_lines.payment_transactions.first()
    event_status = TransactionStatus.FAILURE
    event_reference = "PSP-ref"
    event_name = "Failed authorization"
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.pk),
        "transaction_event": {
            "status": TransactionStatusEnum.FAILURE.name,
            "reference": event_reference,
            "name": event_name,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]

    events_data = data["events"]
    assert len(events_data) == 1
    event_data = events_data[0]
    assert event_data["name"] == event_name
    assert event_data["status"] == TransactionStatusEnum.FAILURE.name
    assert event_data["reference"] == event_reference

    assert transaction.events.count() == 1
    event = transaction.events.first()
    assert event.name == event_name
    assert event.status == event_status
    assert event.reference == event_reference
