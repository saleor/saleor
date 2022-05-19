from decimal import Decimal

import graphene
import pytest

from .....order import OrderEvents
from .....payment import TransactionStatus
from .....payment.error_codes import TransactionCreateErrorCode
from .....payment.models import TransactionItem
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import TransactionActionEnum, TransactionStatusEnum

MUTATION_TRANSACTION_CREATE = """
mutation TransactionCreate(
    $id: ID!,
    $transaction_event: TransactionEventInput,
    $transaction: TransactionCreateInput!
    ){
    transactionCreate(
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


def test_transaction_create_for_order(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    status = "Authorized for 10$"
    type = "Credit Card"
    reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
        TransactionActionEnum.VOID.name,
    ]
    authorized_value = Decimal("10")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
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
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction = order_with_lines.payment_transactions.first()
    content = get_graphql_content(response)
    data = content["data"]["transactionCreate"]["transaction"]
    assert data["actions"] == available_actions
    assert data["status"] == status
    assert data["reference"] == reference
    assert data["authorizedAmount"]["amount"] == authorized_value

    assert available_actions == list(map(str.upper, transaction.available_actions))
    assert status == transaction.status
    assert reference == transaction.reference
    assert authorized_value == transaction.authorized_value
    assert transaction.metadata == {metadata["key"]: metadata["value"]}
    assert transaction.private_metadata == {
        private_metadata["key"]: private_metadata["value"]
    }


def test_transaction_create_for_checkout(
    checkout_with_items, permission_manage_payments, app_api_client
):
    # given
    status = "Authorized for 10$"
    type = "Credit Card"
    reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
        TransactionActionEnum.VOID.name,
    ]
    authorized_value = Decimal("10")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}

    variables = {
        "id": graphene.Node.to_global_id("Checkout", checkout_with_items.pk),
        "transaction": {
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
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction = checkout_with_items.payment_transactions.first()
    content = get_graphql_content(response)
    data = content["data"]["transactionCreate"]["transaction"]
    assert data["actions"] == available_actions
    assert data["status"] == status
    assert data["reference"] == reference
    assert data["authorizedAmount"]["amount"] == authorized_value

    assert available_actions == list(map(str.upper, transaction.available_actions))
    assert status == transaction.status
    assert reference == transaction.reference
    assert authorized_value == transaction.authorized_value
    assert transaction.metadata == {metadata["key"]: metadata["value"]}
    assert transaction.private_metadata == {
        private_metadata["key"]: private_metadata["value"]
    }


@pytest.mark.parametrize(
    "amount_field_name, amount_db_field",
    [
        ("amountAuthorized", "authorized_value"),
        ("amountCharged", "charged_value"),
        ("amountVoided", "voided_value"),
        ("amountRefunded", "refunded_value"),
    ],
)
def test_transaction_create_calculate_amount(
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
        "transaction": {
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
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction = TransactionItem.objects.first()
    get_graphql_content(response)

    assert getattr(transaction, amount_db_field) == expected_value


def test_transaction_create_multiple_amounts_provided(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    status = "Authorized for 10$"
    type = "Credit Card"
    reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
        TransactionActionEnum.VOID.name,
    ]
    authorized_value = Decimal("10")
    charged_value = Decimal("11")
    refunded_value = Decimal("12")
    voided_value = Decimal("13")

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "status": status,
            "type": type,
            "reference": reference,
            "availableActions": available_actions,
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
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction = TransactionItem.objects.first()
    content = get_graphql_content(response)
    data = content["data"]["transactionCreate"]["transaction"]
    assert data["actions"] == available_actions
    assert data["status"] == status
    assert data["reference"] == reference
    assert data["authorizedAmount"]["amount"] == authorized_value
    assert data["chargedAmount"]["amount"] == charged_value
    assert data["refundedAmount"]["amount"] == refunded_value
    assert data["voidedAmount"]["amount"] == voided_value

    assert transaction.authorized_value == authorized_value
    assert transaction.charged_value == charged_value
    assert transaction.voided_value == voided_value
    assert transaction.refunded_value == refunded_value


def test_transaction_create_create_event_for_order(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    status = "Authorized for 10$"
    type = "Credit Card"
    reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
        TransactionActionEnum.VOID.name,
    ]
    authorized_value = Decimal("10")
    transaction_status = "PENDING"
    transaction_reference = "transaction reference"
    transaction_name = "Processing transaction"

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "status": status,
            "type": type,
            "reference": reference,
            "availableActions": available_actions,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
        },
        "transaction_event": {
            "status": transaction_status,
            "reference": transaction_reference,
            "name": transaction_name,
        },
    }

    # when
    app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    event = order_with_lines.events.first()

    assert event.type == OrderEvents.TRANSACTION_EVENT
    assert event.parameters == {
        "message": transaction_name,
        "reference": transaction_reference,
        "status": transaction_status.lower(),
    }


def test_transaction_create_permission_denied_for_staff(
    order_with_lines, staff_api_client, permission_manage_payments
):
    # given
    status = "Authorized for 10$"
    type = "Credit Card"
    reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
        TransactionActionEnum.VOID.name,
    ]
    authorized_value = Decimal("10")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
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
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    assert_no_permission(response)


def test_transaction_create_missing_app_permission(order_with_lines, app_api_client):
    # given
    status = "Authorized for 10$"
    type = "Credit Card"
    reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
        TransactionActionEnum.VOID.name,
    ]
    authorized_value = Decimal("10")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
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
    response = app_api_client.post_graphql(MUTATION_TRANSACTION_CREATE, variables)

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
def test_transaction_create_incorrect_currency(
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
        "transaction": {
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
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["transactionCreate"]
    assert data["errors"][0]["field"] == amount_field_name
    assert (
        data["errors"][0]["code"] == TransactionCreateErrorCode.INCORRECT_CURRENCY.name
    )


def test_creates_transaction_event_for_order(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    status = "Failed authorized for 10$"
    type = "Credit Card"
    reference = "PSP reference - 123"
    available_actions = []
    authorized_value = Decimal("0")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}

    event_status = TransactionStatus.FAILURE
    event_reference = "PSP-ref"
    event_name = "Failed authorization"
    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
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
        "transaction_event": {
            "status": TransactionStatusEnum.FAILURE.name,
            "reference": event_reference,
            "name": event_name,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction = order_with_lines.payment_transactions.first()
    content = get_graphql_content(response)
    data = content["data"]["transactionCreate"]["transaction"]

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


def test_creates_transaction_event_for_checkout(
    checkout_with_items, permission_manage_payments, app_api_client
):
    # given
    status = "Authorized for 10$"
    type = "Credit Card"
    reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
        TransactionActionEnum.VOID.name,
    ]
    authorized_value = Decimal("10")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}

    event_status = TransactionStatus.FAILURE
    event_reference = "PSP-ref"
    event_name = "Failed authorization"

    variables = {
        "id": graphene.Node.to_global_id("Checkout", checkout_with_items.pk),
        "transaction": {
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
        "transaction_event": {
            "status": TransactionStatusEnum.FAILURE.name,
            "reference": event_reference,
            "name": event_name,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction = checkout_with_items.payment_transactions.first()
    content = get_graphql_content(response)
    data = content["data"]["transactionCreate"]["transaction"]

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
