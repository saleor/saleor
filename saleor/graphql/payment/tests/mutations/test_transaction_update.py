from decimal import Decimal
from unittest.mock import patch

import graphene
import pytest
from freezegun import freeze_time

from .....checkout import CheckoutAuthorizeStatus, CheckoutChargeStatus
from .....checkout.calculations import fetch_checkout_data
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....order import OrderAuthorizeStatus, OrderChargeStatus, OrderEvents, OrderStatus
from .....payment import TransactionEventType
from .....payment.error_codes import TransactionUpdateErrorCode
from .....payment.models import TransactionEvent, TransactionItem
from .....payment.transaction_item_calculations import recalculate_transaction_amounts
from ....core.utils import to_global_id_or_none
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import TransactionActionEnum

TEST_SERVER_DOMAIN = "testserver.com"

MUTATION_TRANSACTION_UPDATE = """
mutation TransactionUpdate(
    $id: ID
    $transaction_event: TransactionEventInput
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
                pspReference
                name
                message
                modifiedAt
                createdAt
                externalUrl
                authorizedAmount{
                    amount
                    currency
                }
                canceledAmount{
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
                privateMetadata{
                    key
                    value
                }
                metadata{
                    key
                    value
                }
                createdBy{
                    ... on User {
                        id
                    }
                    ... on App {
                        id
                    }
                }
                events{
                    pspReference
                    message
                    createdAt
                    externalUrl
                    amount{
                        amount
                        currency
                    }
                    type
                    createdBy{
                        ... on User {
                            id
                        }
                        ... on App {
                            id
                        }
                    }
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

MUTATION_TRANSACTION_UPDATE_BY_TOKEN = """
mutation TransactionUpdate(
    $token: UUID
    $transaction_event: TransactionEventInput
    $transaction: TransactionUpdateInput
    ){
    transactionUpdate(
            token: $token,
            transactionEvent: $transaction_event,
            transaction: $transaction
        ){
        transaction{
                id
                actions
                pspReference
                name
                message
                modifiedAt
                createdAt
                externalUrl
                authorizedAmount{
                    amount
                    currency
                }
                canceledAmount{
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
                privateMetadata{
                    key
                    value
                }
                metadata{
                    key
                    value
                }
                createdBy{
                    ... on User {
                        id
                    }
                    ... on App {
                        id
                    }
                }
                events{
                    pspReference
                    message
                    createdAt
                    externalUrl
                    amount{
                        amount
                        currency
                    }
                    type
                    createdBy{
                        ... on User {
                            id
                        }
                        ... on App {
                            id
                        }
                    }
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


def test_only_owner_can_update_its_transaction_by_app(
    transaction_item_created_by_app,
    permission_manage_payments,
    app_api_client,
    external_app,
):
    # given
    transaction = transaction_item_created_by_app
    transaction.app = None
    transaction.app_identifier = external_app.identifier
    transaction.save()

    message = "Captured for 10$"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "message": message,
        },
    }
    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    assert_no_permission(response)


def test_transaction_update_metadata_by_app(
    transaction_item_created_by_app, permission_manage_payments, app_api_client
):
    # given
    transaction = transaction_item_created_by_app

    meta_key = "key-name"
    meta_value = "key_value"
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "metadata": [{"key": meta_key, "value": meta_value}],
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
    assert len(data["metadata"]) == 1
    assert data["metadata"][0]["key"] == meta_key
    assert data["metadata"][0]["value"] == meta_value
    assert transaction_item_created_by_app.metadata == {meta_key: meta_value}


def test_transaction_update_metadata_by_app_null_value(
    transaction_item_created_by_app, permission_manage_payments, app_api_client
):
    # given
    transaction = transaction_item_created_by_app

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "metadata": None,
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
    assert len(data["metadata"]) == 0


def test_transaction_update_metadata_incorrect_key_by_app(
    transaction_item_created_by_app, permission_manage_payments, app_api_client
):
    # given
    transaction = transaction_item_created_by_app

    meta_key = ""
    meta_value = "key_value"
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "metadata": [{"key": meta_key, "value": meta_value}],
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert not content["data"]["transactionUpdate"]["transaction"]
    errors = content["data"]["transactionUpdate"]["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == TransactionUpdateErrorCode.METADATA_KEY_REQUIRED.name


def test_transaction_update_private_metadata_by_app(
    transaction_item_created_by_app, permission_manage_payments, app_api_client
):
    # given
    transaction = transaction_item_created_by_app

    meta_key = "key-name"
    meta_value = "key_value"
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "privateMetadata": [{"key": meta_key, "value": meta_value}],
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
    assert len(data["privateMetadata"]) == 1
    assert data["privateMetadata"][0]["key"] == meta_key
    assert data["privateMetadata"][0]["value"] == meta_value
    assert transaction_item_created_by_app.private_metadata == {meta_key: meta_value}


def test_transaction_update_private_metadata_by_app_null_value(
    transaction_item_created_by_app, permission_manage_payments, app_api_client
):
    # given
    transaction = transaction_item_created_by_app
    transaction.private_metadata = {"key": "value"}
    transaction.save(update_fields=["private_metadata"])

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "privateMetadata": None,
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
    assert len(data["privateMetadata"]) == 1


def test_transaction_update_private_metadata_incorrect_key_by_app(
    transaction_item_created_by_app, permission_manage_payments, app_api_client
):
    # given
    transaction = transaction_item_created_by_app

    meta_key = ""
    meta_value = "key_value"
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "privateMetadata": [{"key": meta_key, "value": meta_value}],
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert not content["data"]["transactionUpdate"]["transaction"]
    errors = content["data"]["transactionUpdate"]["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == TransactionUpdateErrorCode.METADATA_KEY_REQUIRED.name


def test_transaction_update_name_by_app(
    transaction_item_created_by_app, permission_manage_payments, app_api_client
):
    # given
    transaction = transaction_item_created_by_app
    name = "New credit card"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "name": name,
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
    assert data["name"] == name
    assert transaction.name == name


def test_transaction_update_name_by_app_via_token(
    transaction_item_created_by_app, permission_manage_payments, app_api_client
):
    # given
    transaction = transaction_item_created_by_app
    name = "New credit card"

    variables = {
        "token": transaction.token,
        "transaction": {
            "name": name,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE_BY_TOKEN,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    transaction.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["name"] == name
    assert transaction.name == name


def test_transaction_update_message_by_app(
    transaction_item_created_by_app, permission_manage_payments, app_api_client
):
    # given
    transaction = transaction_item_created_by_app
    message = "Message"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "message": message,
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
    assert data["message"] == message
    assert transaction.message == message


def test_transaction_update_psp_reference_by_app(
    transaction_item_created_by_app, permission_manage_payments, app_api_client
):
    # given
    psp_peference = "PSP:123AAA"
    transaction = transaction_item_created_by_app

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "pspReference": psp_peference,
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
    assert data["pspReference"] == psp_peference
    assert transaction.psp_reference == psp_peference
    assert transaction.order
    assert transaction.order.search_vector


def test_transaction_update_available_actions_by_app(
    transaction_item_created_by_app, permission_manage_payments, app_api_client
):
    # given
    transaction = transaction_item_created_by_app
    available_actions = [
        TransactionActionEnum.REFUND.name,
        TransactionActionEnum.REFUND.name,
    ]

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
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
    assert data["actions"] == list(set(available_actions))
    assert transaction.available_actions == [TransactionActionEnum.REFUND.value]


@pytest.mark.parametrize(
    ("field_name", "response_field", "db_field_name", "value"),
    [
        ("amountAuthorized", "authorizedAmount", "authorized_value", Decimal("12")),
        ("amountCharged", "chargedAmount", "charged_value", Decimal("13")),
        ("amountCanceled", "canceledAmount", "canceled_value", Decimal("14")),
        ("amountRefunded", "refundedAmount", "refunded_value", Decimal("15")),
    ],
)
def test_transaction_update_amounts_by_app(
    field_name,
    response_field,
    db_field_name,
    value,
    permission_manage_payments,
    app_api_client,
    transaction_item_generator,
    order,
    app,
):
    # given
    current_authorized_value = Decimal("1")
    current_charged_value = Decimal("2")
    current_refunded_value = Decimal("3")
    current_canceled_value = Decimal("4")

    transaction = transaction_item_generator(
        order_id=order.pk,
        app=app,
        authorized_value=current_authorized_value,
        charged_value=current_charged_value,
        canceled_value=current_canceled_value,
        refunded_value=current_refunded_value,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
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
    provided_amounts = {
        "authorized_value": current_authorized_value,
        "charged_value": current_charged_value,
        "refunded_value": current_refunded_value,
        "canceled_value": current_canceled_value,
        "authorize_pending_value": Decimal(0),
        "charge_pending_value": Decimal(0),
        "refund_pending_value": Decimal(0),
        "cancel_pending_value": Decimal(0),
    }
    provided_amounts[db_field_name] = value
    assert sum(
        [
            transaction.authorized_value,
            transaction.charged_value,
            transaction.refunded_value,
            transaction.canceled_value,
            transaction.authorize_pending_value,
            transaction.charge_pending_value,
            transaction.refund_pending_value,
            transaction.cancel_pending_value,
        ]
    ) == sum(provided_amounts.values())


def test_transaction_update_for_order_increases_order_total_authorized_by_app(
    order_with_lines,
    permission_manage_payments,
    app_api_client,
    transaction_item_generator,
    app,
):
    # given
    transaction = transaction_item_generator(
        order_id=order_with_lines.pk,
        app=app,
        authorized_value=Decimal("10"),
    )
    previously_authorized_value = Decimal("90")
    transaction_item_generator(
        order_id=order_with_lines.pk,
        app=app,
        authorized_value=previously_authorized_value,
    )

    authorized_value = transaction.authorized_value + Decimal("10")

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()
    transaction.refresh_from_db()
    content = get_graphql_content(response)

    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["authorizedAmount"]["amount"] == authorized_value
    assert (
        order_with_lines.total_authorized_amount
        == previously_authorized_value + authorized_value
    )
    assert authorized_value == transaction.authorized_value


def test_transaction_update_for_order_reduces_order_total_authorized_by_app(
    order_with_lines,
    permission_manage_payments,
    app_api_client,
    transaction_item_generator,
    app,
):
    # given
    transaction = transaction_item_generator(
        order_id=order_with_lines.pk,
        app=app,
        authorized_value=Decimal("10"),
    )
    previously_authorized_value = Decimal("90")
    transaction_item_generator(
        order_id=order_with_lines.pk,
        app=app,
        authorized_value=previously_authorized_value,
    )

    authorized_value = transaction.authorized_value - Decimal("5")

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()
    transaction.refresh_from_db()
    content = get_graphql_content(response)

    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["authorizedAmount"]["amount"] == authorized_value
    assert (
        order_with_lines.total_authorized_amount
        == previously_authorized_value + authorized_value
    )
    assert authorized_value == transaction.authorized_value


def test_transaction_update_for_order_reduces_transaction_authorized_to_zero_by_app(
    order_with_lines,
    permission_manage_payments,
    app_api_client,
    app,
    transaction_item_generator,
):
    # given
    transaction = transaction_item_generator(
        order_id=order_with_lines.pk,
        app=app,
        authorized_value=Decimal("10"),
    )
    previously_authorized_value = Decimal("90")
    transaction_item_generator(
        order_id=order_with_lines.pk,
        app=app,
        authorized_value=previously_authorized_value,
    )

    authorized_value = Decimal("0")

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()
    transaction.refresh_from_db()
    content = get_graphql_content(response)

    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["authorizedAmount"]["amount"] == authorized_value
    assert order_with_lines.total_authorized_amount == previously_authorized_value
    assert authorized_value == transaction.authorized_value


def test_transaction_update_for_order_increases_order_total_charged_by_app(
    order_with_lines,
    permission_manage_payments,
    app_api_client,
    transaction_item_generator,
    app,
):
    # given
    transaction = transaction_item_generator(
        order_id=order_with_lines.pk,
        app=app,
        charged_value=Decimal("10"),
    )
    previously_charged_value = Decimal("90")
    transaction_item_generator(
        order_id=order_with_lines.pk,
        app=app,
        charged_value=previously_charged_value,
    )

    charged_value = transaction.charged_value + Decimal("10")

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "amountCharged": {
                "amount": charged_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()
    transaction.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["chargedAmount"]["amount"] == charged_value
    assert (
        order_with_lines.total_charged_amount
        == previously_charged_value + charged_value
    )
    assert charged_value == transaction.charged_value


def test_transaction_update_for_order_reduces_order_total_charged_by_app(
    order_with_lines,
    permission_manage_payments,
    app_api_client,
    transaction_item_generator,
    app,
):
    # given
    transaction = transaction_item_generator(
        order_id=order_with_lines.pk,
        app=app,
        charged_value=Decimal("30"),
    )
    previously_charged_value = Decimal("90")
    transaction_item_generator(
        order_id=order_with_lines.pk,
        app=app,
        charged_value=previously_charged_value,
    )

    charged_value = transaction.charged_value - Decimal("5")

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "amountCharged": {
                "amount": charged_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()
    transaction.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["chargedAmount"]["amount"] == charged_value
    assert (
        order_with_lines.total_charged_amount
        == previously_charged_value + charged_value
    )
    assert charged_value == transaction.charged_value


def test_transaction_update_for_order_reduces_transaction_charged_to_zero_by_app(
    order_with_lines,
    permission_manage_payments,
    app_api_client,
    transaction_item_generator,
    app,
):
    # given
    transaction = transaction_item_generator(
        order_id=order_with_lines.pk,
        app=app,
        charged_value=Decimal("30"),
    )
    previously_charged_value = Decimal("90")
    transaction_item_generator(
        order_id=order_with_lines.pk,
        app=app,
        charged_value=previously_charged_value,
    )

    charged_value = Decimal("0")

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "amountCharged": {
                "amount": charged_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()
    transaction.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["chargedAmount"]["amount"] == charged_value
    assert order_with_lines.total_charged_amount == previously_charged_value
    assert charged_value == transaction.charged_value


def test_transaction_update_multiple_amounts_provided_by_app(
    permission_manage_payments, app_api_client, order, transaction_item_generator, app
):
    # given
    transaction = transaction_item_generator(
        order_id=order.pk,
        app=app,
        charged_value=Decimal("1"),
        authorized_value=Decimal("2"),
        refunded_value=Decimal("3"),
        canceled_value=Decimal("4"),
    )

    authorized_value = Decimal("10")
    charged_value = Decimal("11")
    refunded_value = Decimal("12")
    canceled_value = Decimal("13")

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
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
            "amountCanceled": {
                "amount": canceled_value,
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
    assert data["canceledAmount"]["amount"] == canceled_value

    assert transaction
    assert transaction.authorized_value == authorized_value
    assert transaction.charged_value == charged_value
    assert transaction.canceled_value == canceled_value
    assert transaction.refunded_value == refunded_value


def test_transaction_update_for_order_missing_permission_by_app(
    transaction_item_created_by_app, app_api_client
):
    # given
    transaction = transaction_item_created_by_app
    message = "Authorized for 10$"
    name = "Credit Card"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "message": message,
            "name": name,
        },
    }

    # when
    response = app_api_client.post_graphql(MUTATION_TRANSACTION_UPDATE, variables)

    # then
    assert_no_permission(response)


@pytest.mark.parametrize(
    ("amount_field_name", "amount_db_field"),
    [
        ("amountAuthorized", "authorized_value"),
        ("amountCharged", "charged_value"),
        ("amountCanceled", "canceled_value"),
        ("amountRefunded", "refunded_value"),
    ],
)
def test_transaction_update_incorrect_currency_by_app(
    amount_field_name,
    amount_db_field,
    transaction_item_created_by_app,
    permission_manage_payments,
    app_api_client,
):
    # given
    transaction = transaction_item_created_by_app
    expected_value = Decimal("10")

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
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


def test_transaction_update_adds_transaction_event_to_order_by_app(
    transaction_item_created_by_app,
    order_with_lines,
    permission_manage_payments,
    app_api_client,
):
    # given
    transaction = transaction_item_created_by_app
    transaction_reference = "transaction reference"
    transaction_name = "Processing transaction"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction_event": {
            "pspReference": transaction_reference,
            "message": transaction_name,
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
    }


def test_creates_transaction_event_for_order_by_app(
    transaction_item_created_by_app,
    order_with_lines,
    permission_manage_payments,
    app_api_client,
):
    # given

    transaction = order_with_lines.payment_transactions.first()
    event_reference = "PSP-ref"
    event_message = "Failed authorization"
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction_event": {
            "pspReference": event_reference,
            "message": event_message,
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
    assert len(events_data) == 2
    event_data = [
        event for event in events_data if event["pspReference"] == event_reference
    ][0]
    assert event_data["message"] == event_message
    assert event_data["createdBy"]["id"] == to_global_id_or_none(app_api_client.app)

    assert transaction.events.count() == 2
    event = transaction.events.filter(psp_reference=event_reference).first()
    assert event.message == event_message
    assert event.app_identifier == app_api_client.app.identifier
    assert event.user is None


def test_creates_transaction_event_by_reinstalled_app(
    transaction_item_created_by_app,
    order_with_lines,
    permission_manage_payments,
    app_api_client,
):
    # given
    transaction_item_created_by_app.app = None
    transaction_item_created_by_app.save()

    transaction = order_with_lines.payment_transactions.first()
    event_reference = "PSP-ref"
    event_message = "Failed authorization"
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction_event": {
            "pspReference": event_reference,
            "message": event_message,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)

    assert transaction.events.count() == 2
    event = transaction.events.filter(psp_reference=event_reference).first()
    assert event.message == event_message
    assert event.app_identifier == app_api_client.app.identifier
    assert event.user is None


def test_only_app_owner_can_update_its_transaction_by_staff(
    transaction_item_created_by_app,
    permission_manage_payments,
    staff_api_client,
):
    # given
    transaction = transaction_item_created_by_app

    message = "Captured for 10$"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "message": message,
        },
    }
    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    assert_no_permission(response)


def test_transaction_update_by_another_staff(
    transaction_item_created_by_user,
    permission_manage_payments,
    staff_api_client,
    admin_user,
):
    # given
    transaction = transaction_item_created_by_user
    transaction.user = admin_user
    transaction.save()

    message = "Captured for 10$"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "message": message,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert data
    assert transaction_item_created_by_user.user != staff_api_client.user
    assert len(data["events"]) == 1
    assert data["events"][0]["createdBy"]["id"] == graphene.Node.to_global_id(
        "User", staff_api_client.user.pk
    )


def test_transaction_update_metadata_by_staff(
    transaction_item_created_by_user, permission_manage_payments, staff_api_client
):
    # given
    transaction = transaction_item_created_by_user

    meta_key = "key-name"
    meta_value = "key_value"
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "metadata": [{"key": meta_key, "value": meta_value}],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert len(data["metadata"]) == 1
    assert data["metadata"][0]["key"] == meta_key
    assert data["metadata"][0]["value"] == meta_value
    assert transaction.metadata == {meta_key: meta_value}


def test_transaction_update_metadata_incorrect_key_by_staff(
    transaction_item_created_by_user, permission_manage_payments, staff_api_client
):
    # given
    transaction = transaction_item_created_by_user

    meta_key = ""
    meta_value = "key_value"
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "metadata": [{"key": meta_key, "value": meta_value}],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert not content["data"]["transactionUpdate"]["transaction"]
    errors = content["data"]["transactionUpdate"]["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == TransactionUpdateErrorCode.METADATA_KEY_REQUIRED.name


def test_transaction_update_private_metadata_by_staff(
    transaction_item_created_by_user, permission_manage_payments, staff_api_client
):
    # given
    transaction = transaction_item_created_by_user

    meta_key = "key-name"
    meta_value = "key_value"
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "privateMetadata": [{"key": meta_key, "value": meta_value}],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert len(data["privateMetadata"]) == 1
    assert data["privateMetadata"][0]["key"] == meta_key
    assert data["privateMetadata"][0]["value"] == meta_value
    assert transaction.private_metadata == {meta_key: meta_value}


def test_transaction_update_private_metadata_incorrect_key_by_staff(
    transaction_item_created_by_user, permission_manage_payments, staff_api_client
):
    # given
    transaction = transaction_item_created_by_user

    meta_key = ""
    meta_value = "key_value"
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "privateMetadata": [{"key": meta_key, "value": meta_value}],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert not content["data"]["transactionUpdate"]["transaction"]
    errors = content["data"]["transactionUpdate"]["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == TransactionUpdateErrorCode.METADATA_KEY_REQUIRED.name


def test_transaction_update_name_by_staff(
    transaction_item_created_by_user, permission_manage_payments, staff_api_client
):
    # given
    transaction = transaction_item_created_by_user
    name = "New credit card"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "name": name,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["name"] == name
    assert transaction.name == name


def test_transaction_update_message_by_staff(
    transaction_item_created_by_user, permission_manage_payments, staff_api_client
):
    # given
    transaction = transaction_item_created_by_user
    message = "Message"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "message": message,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["message"] == message
    assert transaction.message == message


def test_transaction_update_psp_reference_by_staff(
    transaction_item_created_by_user, permission_manage_payments, staff_api_client
):
    # given
    reference = "PSP:123AAA"
    transaction = transaction_item_created_by_user

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "pspReference": reference,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["pspReference"] == reference
    assert transaction.psp_reference == reference


def test_transaction_update_available_actions_by_staff(
    transaction_item_created_by_user, permission_manage_payments, staff_api_client
):
    # given
    transaction = transaction_item_created_by_user
    available_actions = [
        TransactionActionEnum.REFUND.name,
        TransactionActionEnum.REFUND.name,
    ]

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "availableActions": available_actions,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["actions"] == list(set(available_actions))
    assert transaction.available_actions == [TransactionActionEnum.REFUND.value]


@pytest.mark.parametrize(
    ("field_name", "response_field", "db_field_name", "value"),
    [
        ("amountAuthorized", "authorizedAmount", "authorized_value", Decimal("12")),
        ("amountCharged", "chargedAmount", "charged_value", Decimal("13")),
        ("amountCanceled", "canceledAmount", "canceled_value", Decimal("14")),
        ("amountRefunded", "refundedAmount", "refunded_value", Decimal("15")),
    ],
)
def test_transaction_update_amounts_by_staff(
    field_name,
    response_field,
    db_field_name,
    value,
    permission_manage_payments,
    staff_api_client,
    transaction_item_generator,
    staff_user,
):
    # given
    transaction = transaction_item_generator(user=staff_user)
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {field_name: {"amount": value, "currency": "USD"}},
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert data[response_field]["amount"] == value
    assert getattr(transaction, db_field_name) == value


def test_transaction_update_for_order_increases_order_total_authorized_by_staff(
    order_with_lines,
    permission_manage_payments,
    staff_api_client,
    transaction_item_generator,
    staff_user,
):
    # given
    previously_authorized_value = Decimal("90")
    transaction = transaction_item_generator(
        order_id=order_with_lines.pk,
        user=staff_user,
        authorized_value=Decimal("10"),
    )
    previously_authorized_value = Decimal("90")
    transaction_item_generator(
        order_id=order_with_lines.pk,
        user=staff_user,
        authorized_value=previously_authorized_value,
    )

    authorized_value = transaction.authorized_value + Decimal("10")

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()
    transaction.refresh_from_db()
    content = get_graphql_content(response)

    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["authorizedAmount"]["amount"] == authorized_value
    assert (
        order_with_lines.total_authorized_amount
        == previously_authorized_value + authorized_value
    )
    assert authorized_value == transaction.authorized_value


def test_transaction_update_for_order_reduces_order_total_authorized_by_staff(
    order_with_lines,
    permission_manage_payments,
    staff_api_client,
    transaction_item_generator,
    staff_user,
):
    # given
    transaction = transaction_item_generator(
        order_id=order_with_lines.pk,
        user=staff_user,
        authorized_value=Decimal("10"),
    )
    previously_authorized_value = Decimal("90")
    transaction_item_generator(
        order_id=order_with_lines.pk,
        user=staff_user,
        authorized_value=previously_authorized_value,
    )

    authorized_value = transaction.authorized_value - Decimal("5")

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()
    transaction.refresh_from_db()
    content = get_graphql_content(response)

    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["authorizedAmount"]["amount"] == authorized_value
    assert (
        order_with_lines.total_authorized_amount
        == previously_authorized_value + authorized_value
    )
    assert authorized_value == transaction.authorized_value


def test_transaction_update_for_order_reduces_transaction_authorized_to_zero_by_staff(
    order_with_lines,
    permission_manage_payments,
    staff_api_client,
    transaction_item_created_by_user,
    transaction_item_generator,
    staff_user,
):
    # given
    transaction = transaction_item_generator(
        order_id=order_with_lines.pk,
        user=staff_user,
        authorized_value=Decimal("10"),
    )
    previously_authorized_value = Decimal("90")
    transaction_item_generator(
        order_id=order_with_lines.pk,
        user=staff_user,
        authorized_value=previously_authorized_value,
    )

    authorized_value = Decimal("0")

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()
    transaction.refresh_from_db()
    content = get_graphql_content(response)

    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["authorizedAmount"]["amount"] == authorized_value
    assert order_with_lines.total_authorized_amount == previously_authorized_value
    assert authorized_value == transaction.authorized_value


def test_transaction_update_for_order_increases_order_total_charged_by_staff(
    order_with_lines,
    permission_manage_payments,
    staff_api_client,
    transaction_item_generator,
    staff_user,
):
    # given
    transaction = transaction_item_generator(
        order_id=order_with_lines.pk,
        user=staff_user,
        charged_value=Decimal("10"),
    )
    previously_charged_value = Decimal("90")
    transaction_item_generator(
        order_id=order_with_lines.pk,
        user=staff_user,
        charged_value=previously_charged_value,
    )
    charged_value = transaction.charged_value + Decimal("10")

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "amountCharged": {
                "amount": charged_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()
    transaction.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["chargedAmount"]["amount"] == charged_value
    assert (
        order_with_lines.total_charged_amount
        == previously_charged_value + charged_value
    )
    assert charged_value == transaction.charged_value


def test_transaction_update_for_order_reduces_order_total_charged_by_staff(
    order_with_lines,
    permission_manage_payments,
    staff_api_client,
    transaction_item_generator,
    staff_user,
):
    # given

    transaction = transaction_item_generator(
        order_id=order_with_lines.pk,
        user=staff_user,
        charged_value=Decimal("30"),
    )
    previously_charged_value = Decimal("90")
    transaction_item_generator(
        order_id=order_with_lines.pk,
        user=staff_user,
        charged_value=previously_charged_value,
    )
    charged_value = transaction.charged_value - Decimal("5")

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "amountCharged": {
                "amount": charged_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()
    transaction.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["chargedAmount"]["amount"] == charged_value
    assert (
        order_with_lines.total_charged_amount
        == previously_charged_value + charged_value
    )
    assert charged_value == transaction.charged_value


def test_transaction_update_for_order_reduces_transaction_charged_to_zero_by_staff(
    order_with_lines,
    permission_manage_payments,
    staff_api_client,
    transaction_item_generator,
    staff_user,
):
    # given
    transaction = transaction_item_generator(
        order_id=order_with_lines.pk,
        user=staff_user,
        charged_value=Decimal("30"),
    )
    previously_charged_value = Decimal("90")
    transaction_item_generator(
        order_id=order_with_lines.pk,
        user=staff_user,
        charged_value=previously_charged_value,
    )

    charged_value = Decimal("0")

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "amountCharged": {
                "amount": charged_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()
    transaction.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["chargedAmount"]["amount"] == charged_value
    assert order_with_lines.total_charged_amount == previously_charged_value
    assert charged_value == transaction.charged_value


def test_transaction_update_multiple_amounts_provided_by_staff(
    transaction_item_created_by_user, permission_manage_payments, staff_api_client
):
    # given
    transaction = transaction_item_created_by_user
    authorized_value = Decimal("10")
    charged_value = Decimal("11")
    refunded_value = Decimal("12")
    canceled_value = Decimal("13")

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
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
            "amountCanceled": {
                "amount": canceled_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction = TransactionItem.objects.first()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["authorizedAmount"]["amount"] == authorized_value
    assert data["chargedAmount"]["amount"] == charged_value
    assert data["refundedAmount"]["amount"] == refunded_value
    assert data["canceledAmount"]["amount"] == canceled_value

    assert transaction
    assert transaction.authorized_value == authorized_value
    assert transaction.charged_value == charged_value
    assert transaction.canceled_value == canceled_value
    assert transaction.refunded_value == refunded_value


def test_transaction_update_for_order_missing_permission_by_staff(
    transaction_item_created_by_user, staff_api_client
):
    # given
    transaction = transaction_item_created_by_user
    message = "Authorized for 10$"
    name = "Credit Card"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "message": message,
            "name": name,
        },
    }

    # when
    response = staff_api_client.post_graphql(MUTATION_TRANSACTION_UPDATE, variables)

    # then
    assert_no_permission(response)


@pytest.mark.parametrize(
    ("amount_field_name", "amount_db_field"),
    [
        ("amountAuthorized", "authorized_value"),
        ("amountCharged", "charged_value"),
        ("amountCanceled", "canceled_value"),
        ("amountRefunded", "refunded_value"),
    ],
)
def test_transaction_update_incorrect_currency_by_staff(
    amount_field_name,
    amount_db_field,
    transaction_item_created_by_user,
    permission_manage_payments,
    staff_api_client,
):
    # given
    transaction = transaction_item_created_by_user
    expected_value = Decimal("10")

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            amount_field_name: {
                "amount": expected_value,
                "currency": "PLN",
            },
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]
    assert data["errors"][0]["field"] == amount_field_name
    assert (
        data["errors"][0]["code"] == TransactionUpdateErrorCode.INCORRECT_CURRENCY.name
    )


def test_transaction_update_adds_transaction_event_to_order_by_staff(
    transaction_item_created_by_user,
    order_with_lines,
    permission_manage_payments,
    staff_api_client,
):
    # given
    transaction = transaction_item_created_by_user
    transaction_reference = "transaction reference"
    transaction_name = "Processing transaction"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction_event": {
            "pspReference": transaction_reference,
            "message": transaction_name,
        },
    }

    # when
    response = staff_api_client.post_graphql(
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
    }


def test_creates_transaction_event_for_order_by_staff(
    transaction_item_created_by_user,
    order_with_lines,
    permission_manage_payments,
    staff_api_client,
):
    # given

    transaction = order_with_lines.payment_transactions.first()
    event_reference = "PSP-ref"
    event_message = "Failed authorization"
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction_event": {
            "pspReference": event_reference,
            "message": event_message,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]

    events_data = data["events"]
    assert len(events_data) == 2
    event_data = [
        event for event in events_data if event["pspReference"] == event_reference
    ][0]
    assert event_data["message"] == event_message
    assert event_data["createdBy"]["id"] == to_global_id_or_none(staff_api_client.user)

    assert transaction.events.count() == 2
    event = transaction.events.filter(psp_reference=event_reference).first()
    assert event.message == event_message
    assert event.psp_reference == event_reference
    assert event.app_identifier is None
    assert event.user == staff_api_client.user


def test_transaction_raises_error_when_psp_reference_already_exists_by_staff(
    transaction_item_generator,
    order_with_lines,
    permission_manage_payments,
    staff_api_client,
    staff_user,
):
    # given
    psp_reference = "psp-ref"
    transaction = transaction_item_generator(
        order_id=order_with_lines.pk, user=staff_user, psp_reference=psp_reference
    )
    second_transaction = transaction_item_generator(
        order_id=order_with_lines.pk,
        user=staff_user,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", second_transaction.token),
        "transaction": {
            "pspReference": psp_reference,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    transaction = content["data"]["transactionUpdate"]["transaction"]
    errors = content["data"]["transactionUpdate"]["errors"]

    assert not transaction
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == TransactionUpdateErrorCode.UNIQUE.name
    assert error["field"] == "transaction"

    assert order_with_lines.payment_transactions.count() == 2
    assert TransactionEvent.objects.count() == 0


def test_transaction_raises_error_when_psp_reference_already_exists_by_app(
    transaction_item_generator,
    order_with_lines,
    permission_manage_payments,
    app_api_client,
    app,
):
    # given

    psp_reference = "psp-ref"
    transaction = transaction_item_generator(
        order_id=order_with_lines.pk, app=app, psp_reference=psp_reference
    )
    second_transaction = transaction_item_generator(
        order_id=order_with_lines.pk,
        app=app,
    )
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", second_transaction.token),
        "transaction": {
            "pspReference": psp_reference,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    transaction = content["data"]["transactionUpdate"]["transaction"]
    errors = content["data"]["transactionUpdate"]["errors"]

    assert not transaction
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == TransactionUpdateErrorCode.UNIQUE.name
    assert error["field"] == "transaction"

    assert order_with_lines.payment_transactions.count() == 2
    assert TransactionEvent.objects.count() == 0


def test_transaction_update_external_url_by_app(
    transaction_item_created_by_app, permission_manage_payments, app_api_client
):
    # given
    transaction = transaction_item_created_by_app
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "externalUrl": external_url,
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
    assert data["externalUrl"] == external_url
    assert transaction_item_created_by_app.external_url == external_url


def test_transaction_update_external_url_incorrect_url_format_by_app(
    transaction_item_created_by_app, permission_manage_payments, app_api_client
):
    # given
    transaction = transaction_item_created_by_app
    external_url = "incorrect"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "externalUrl": external_url,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert not content["data"]["transactionUpdate"]["transaction"]
    errors = content["data"]["transactionUpdate"]["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == TransactionUpdateErrorCode.INVALID.name


def test_transaction_update_external_url_by_staff(
    transaction_item_created_by_user, permission_manage_payments, staff_api_client
):
    # given
    transaction = transaction_item_created_by_user
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "externalUrl": external_url,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["transactionUpdate"]["transaction"]
    assert data["externalUrl"] == external_url
    assert transaction_item_created_by_user.external_url == external_url


def test_transaction_update_external_url_incorrect_url_format_by_staff(
    transaction_item_created_by_user, permission_manage_payments, staff_api_client
):
    # given
    transaction = transaction_item_created_by_user
    external_url = "incorrect"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "externalUrl": external_url,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert not content["data"]["transactionUpdate"]["transaction"]
    errors = content["data"]["transactionUpdate"]["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == TransactionUpdateErrorCode.INVALID.name


def test_transaction_update_creates_calculation_event(
    permission_manage_payments,
    app_api_client,
    transaction_item_generator,
    order,
    app,
):
    # given
    current_authorized_value = Decimal("1")
    current_charged_value = Decimal("2")
    current_canceled_value = Decimal("3")
    current_refunded_value = Decimal("4")
    transaction = transaction_item_generator(
        order_id=order.pk,
        app=app,
        authorized_value=current_authorized_value,
        charged_value=current_charged_value,
        canceled_value=current_canceled_value,
        refunded_value=current_refunded_value,
    )
    authorized_value = Decimal("20")
    charged_value = Decimal("17")
    canceled_value = Decimal("14")
    refunded_value = Decimal("15")

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
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
            "amountCanceled": {
                "amount": canceled_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction.refresh_from_db()
    get_graphql_content(response)

    order.refresh_from_db()
    transaction = order.payment_transactions.first()
    assert order.total_authorized.amount == authorized_value
    assert order.total_charged.amount == charged_value

    assert transaction.authorized_value == authorized_value
    assert transaction.charged_value == charged_value
    assert transaction.refunded_value == refunded_value
    assert transaction.canceled_value == canceled_value

    # 4 existing events and 4 newly created for new amounts
    assert transaction.events.count() == 8

    authorize_event = transaction.events.filter(
        type=TransactionEventType.AUTHORIZATION_ADJUSTMENT,
        amount_value=authorized_value,
    ).first()
    assert authorize_event

    charge_event = transaction.events.filter(
        type=TransactionEventType.CHARGE_SUCCESS,
        amount_value=charged_value - current_charged_value,
    ).first()
    assert charge_event

    refund_event = transaction.events.filter(
        type=TransactionEventType.REFUND_SUCCESS,
        amount_value=refunded_value - current_refunded_value,
    ).first()
    assert refund_event

    cancel_event = transaction.events.filter(
        type=TransactionEventType.CANCEL_SUCCESS,
        amount_value=canceled_value - current_canceled_value,
    ).first()
    assert cancel_event


@pytest.mark.parametrize(
    (
        "field_name",
        "response_field",
        "db_field_name",
        "value",
        "current_authorized_value",
        "current_charged_value",
        "current_canceled_value",
        "current_refunded_value",
    ),
    [
        (
            "amountAuthorized",
            "authorizedAmount",
            "authorized_value",
            Decimal("12"),
            Decimal("1"),
            Decimal("2"),
            Decimal("3"),
            Decimal("4"),
        ),
        (
            "amountAuthorized",
            "authorizedAmount",
            "authorized_value",
            Decimal("12"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
        ),
        (
            "amountAuthorized",
            "authorizedAmount",
            "authorized_value",
            Decimal("12"),
            Decimal("0"),
            Decimal("3"),
            Decimal("1"),
            Decimal("0"),
        ),
        (
            "amountAuthorized",
            "authorizedAmount",
            "authorized_value",
            Decimal("12"),
            Decimal("100"),
            Decimal("3"),
            Decimal("1"),
            Decimal("0"),
        ),
        (
            "amountAuthorized",
            "authorizedAmount",
            "authorized_value",
            Decimal("0"),
            Decimal("1"),
            Decimal("2"),
            Decimal("3"),
            Decimal("4"),
        ),
        (
            "amountAuthorized",
            "authorizedAmount",
            "authorized_value",
            Decimal("1"),
            Decimal("3"),
            Decimal("2"),
            Decimal("3"),
            Decimal("4"),
        ),
        (
            "amountCharged",
            "chargedAmount",
            "charged_value",
            Decimal("13"),
            Decimal("1"),
            Decimal("2"),
            Decimal("3"),
            Decimal("4"),
        ),
        (
            "amountCharged",
            "chargedAmount",
            "charged_value",
            Decimal("13"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
        ),
        (
            "amountCharged",
            "chargedAmount",
            "charged_value",
            Decimal("13"),
            Decimal("0"),
            Decimal("200"),
            Decimal("0"),
            Decimal("0"),
        ),
        (
            "amountCharged",
            "chargedAmount",
            "charged_value",
            Decimal("0"),
            Decimal("1"),
            Decimal("2"),
            Decimal("3"),
            Decimal("4"),
        ),
        (
            "amountCanceled",
            "canceledAmount",
            "canceled_value",
            Decimal("1"),
            Decimal("1"),
            Decimal("2"),
            Decimal("3"),
            Decimal("4"),
        ),
        (
            "amountCanceled",
            "canceledAmount",
            "canceled_value",
            Decimal("14"),
            Decimal("1"),
            Decimal("2"),
            Decimal("3"),
            Decimal("4"),
        ),
        (
            "amountCanceled",
            "canceledAmount",
            "canceled_value",
            Decimal("14"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
        ),
        (
            "amountCanceled",
            "canceledAmount",
            "canceled_value",
            Decimal("14"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("100"),
        ),
        (
            "amountCanceled",
            "canceledAmount",
            "canceled_value",
            Decimal("0"),
            Decimal("1"),
            Decimal("2"),
            Decimal("3"),
            Decimal("4"),
        ),
        (
            "amountRefunded",
            "refundedAmount",
            "refunded_value",
            Decimal("15"),
            Decimal("1"),
            Decimal("2"),
            Decimal("3"),
            Decimal("4"),
        ),
        (
            "amountRefunded",
            "refundedAmount",
            "refunded_value",
            Decimal("15"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
        ),
        (
            "amountRefunded",
            "refundedAmount",
            "refunded_value",
            Decimal("15"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("100"),
        ),
        (
            "amountRefunded",
            "refundedAmount",
            "refunded_value",
            Decimal("0"),
            Decimal("1"),
            Decimal("2"),
            Decimal("3"),
            Decimal("4"),
        ),
        (
            "amountRefunded",
            "refundedAmount",
            "refunded_value",
            Decimal("1"),
            Decimal("1"),
            Decimal("2"),
            Decimal("3"),
            Decimal("4"),
        ),
    ],
)
def test_transaction_update_amounts_are_correct(
    field_name,
    response_field,
    db_field_name,
    value,
    current_authorized_value,
    current_charged_value,
    current_canceled_value,
    current_refunded_value,
    permission_manage_payments,
    app_api_client,
    transaction_item_generator,
    order,
    app,
):
    # given
    transaction = transaction_item_generator(
        order_id=order.pk,
        app=app,
        authorized_value=current_authorized_value,
        charged_value=current_charged_value,
        canceled_value=current_canceled_value,
        refunded_value=current_refunded_value,
    )
    recalculate_transaction_amounts(transaction)

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
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
    provided_amounts = {
        "authorized_value": current_authorized_value,
        "charged_value": current_charged_value,
        "refunded_value": current_refunded_value,
        "canceled_value": current_canceled_value,
        "authorize_pending_value": Decimal(0),
        "charge_pending_value": Decimal(0),
        "refund_pending_value": Decimal(0),
        "cancel_pending_value": Decimal(0),
    }
    provided_amounts[db_field_name] = value
    assert sum(
        [
            transaction.authorized_value,
            transaction.charged_value,
            transaction.refunded_value,
            transaction.canceled_value,
            transaction.authorize_pending_value,
            transaction.charge_pending_value,
            transaction.refund_pending_value,
            transaction.cancel_pending_value,
        ]
    ) == sum(provided_amounts.values())


def test_transaction_update_for_checkout_updates_payment_statuses(
    checkout_with_items,
    permission_manage_payments,
    app_api_client,
    transaction_item_generator,
    app,
):
    # given
    current_authorized_value = Decimal("1")
    current_charged_value = Decimal("2")
    transaction = transaction_item_generator(
        checkout_id=checkout_with_items.pk,
        app=app,
        authorized_value=current_authorized_value,
        charged_value=current_charged_value,
    )
    authorized_value = Decimal("12")
    charged_value = Decimal("13")

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
            "amountCharged": {
                "amount": charged_value,
                "currency": "USD",
            },
        },
    }

    # when
    app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    checkout_with_items.refresh_from_db()
    assert checkout_with_items.charge_status == CheckoutChargeStatus.PARTIAL
    assert checkout_with_items.authorize_status == CheckoutAuthorizeStatus.PARTIAL


@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
def test_transaction_update_for_checkout_fully_paid(
    mocked_checkout_fully_paid,
    checkout_with_prices,
    permission_manage_payments,
    app_api_client,
    transaction_item_generator,
    app,
    plugins_manager,
):
    # given
    current_authorized_value = Decimal("1")
    current_charged_value = Decimal("2")
    transaction = transaction_item_generator(
        checkout_id=checkout_with_prices.pk,
        app=app,
        authorized_value=current_authorized_value,
        charged_value=current_charged_value,
    )

    checkout = checkout_with_prices
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "amountCharged": {
                "amount": checkout_info.checkout.total.gross.amount,
                "currency": "USD",
            },
        },
    }

    # when
    app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    checkout.refresh_from_db()
    assert checkout.charge_status == CheckoutChargeStatus.FULL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL

    mocked_checkout_fully_paid.assert_called_once_with(checkout)


def test_transaction_update_accepts_old_id_for_old_transaction(
    transaction_item_generator, permission_manage_payments, app_api_client
):
    # given
    transaction = transaction_item_generator(use_old_id=True)
    message = "Captured for 10$"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.pk),
        "transaction": {
            "message": message,
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
    assert data["message"] == message
    assert transaction.message == message


def test_transaction_update_doesnt_accept_old_id_for_new_transactions(
    transaction_item_generator, permission_manage_payments, app_api_client
):
    # given
    transaction = transaction_item_generator(use_old_id=False)
    message = "Captured for 10$"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.pk),
        "transaction": {
            "message": message,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["transactionUpdate"]["transaction"]
    errors = content["data"]["transactionUpdate"]["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == TransactionUpdateErrorCode.NOT_FOUND.name
    assert error["field"] == "id"


@pytest.mark.parametrize(
    ("auto_order_confirmation", "excpected_order_status"),
    [
        (True, OrderStatus.UNFULFILLED),
        (False, OrderStatus.UNCONFIRMED),
    ],
)
@patch("saleor.plugins.manager.PluginsManager.order_paid")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_paid")
def test_transaction_update_for_order_triggers_webhooks_when_fully_paid(
    mock_order_fully_paid,
    mock_order_updated,
    mock_order_paid,
    auto_order_confirmation,
    excpected_order_status,
    unconfirmed_order_with_lines,
    permission_manage_payments,
    app_api_client,
    app,
    transaction_item_generator,
):
    # given
    order = unconfirmed_order_with_lines
    order.channel.automatically_confirm_all_new_orders = auto_order_confirmation
    order.channel.save(update_fields=["automatically_confirm_all_new_orders"])
    current_authorized_value = Decimal("1")
    current_charged_value = Decimal("2")
    transaction = transaction_item_generator(
        order_id=order.pk,
        app=app,
        authorized_value=current_authorized_value,
        charged_value=current_charged_value,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "amountCharged": {
                "amount": order.total.gross.amount,
                "currency": "USD",
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order.refresh_from_db()
    get_graphql_content(response)

    assert order.status == excpected_order_status
    assert order.charge_status == OrderChargeStatus.FULL
    mock_order_fully_paid.assert_called_once_with(order)
    mock_order_updated.assert_called_once_with(order)
    mock_order_paid.assert_called_once_with(order)


@patch("saleor.plugins.manager.PluginsManager.order_paid")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_paid")
def test_transaction_update_for_order_triggers_webhook_when_partially_paid(
    mock_order_fully_paid,
    mock_order_updated,
    mock_order_paid,
    order_with_lines,
    permission_manage_payments,
    app_api_client,
    app,
    transaction_item_generator,
):
    # given
    current_authorized_value = Decimal("1")
    current_charged_value = Decimal("2")
    transaction = transaction_item_generator(
        order_id=order_with_lines.pk,
        app=app,
        authorized_value=current_authorized_value,
        charged_value=current_charged_value,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "amountCharged": {
                "amount": Decimal("10"),
                "currency": "USD",
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()

    get_graphql_content(response)

    assert order_with_lines.charge_status == OrderChargeStatus.PARTIAL
    assert not mock_order_fully_paid.called
    mock_order_updated.assert_called_once_with(order_with_lines)
    mock_order_paid.assert_called_once_with(order_with_lines)


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_paid")
def test_transaction_update_for_order_triggers_webhook_when_authorized(
    mock_order_fully_paid,
    mock_order_updated,
    order_with_lines,
    permission_manage_payments,
    app_api_client,
    app,
    transaction_item_generator,
):
    # given
    current_authorized_value = Decimal("1")
    current_charged_value = Decimal("2")
    transaction = transaction_item_generator(
        order_id=order_with_lines.pk,
        app=app,
        authorized_value=current_authorized_value,
        charged_value=current_charged_value,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "amountAuthorized": {
                "amount": Decimal("10"),
                "currency": "USD",
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()

    get_graphql_content(response)

    assert order_with_lines.authorize_status == OrderAuthorizeStatus.PARTIAL
    assert not mock_order_fully_paid.called
    mock_order_updated.assert_called_once_with(order_with_lines)


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_refunded")
@patch("saleor.plugins.manager.PluginsManager.order_fully_refunded")
def test_transaction_update_for_order_triggers_webhooks_when_fully_refunded(
    mock_order_fully_refunded,
    mock_order_refunded,
    mock_order_updated,
    order_with_lines,
    permission_manage_payments,
    app_api_client,
    app,
    transaction_item_generator,
):
    # given
    current_refunded_value = Decimal("2")
    transaction = transaction_item_generator(
        order_id=order_with_lines.pk,
        app=app,
        refunded_value=current_refunded_value,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "amountRefunded": {
                "amount": order_with_lines.total.gross.amount,
                "currency": "USD",
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()

    get_graphql_content(response)

    mock_order_refunded.assert_called_once_with(order_with_lines)
    mock_order_fully_refunded.assert_called_once_with(order_with_lines)
    mock_order_updated.assert_called_once_with(order_with_lines)


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_refunded")
@patch("saleor.plugins.manager.PluginsManager.order_fully_refunded")
def test_transaction_update_for_order_triggers_webhook_when_partially_refunded(
    mock_order_fully_refunded,
    mock_order_refunded,
    mock_order_updated,
    order_with_lines,
    permission_manage_payments,
    app_api_client,
    app,
    transaction_item_generator,
):
    # given
    current_refunded_value = Decimal("2")
    transaction = transaction_item_generator(
        order_id=order_with_lines.pk,
        app=app,
        refunded_value=current_refunded_value,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "amountRefunded": {
                "amount": Decimal("10"),
                "currency": "USD",
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()

    get_graphql_content(response)

    assert not mock_order_fully_refunded.called
    mock_order_updated.assert_called_once_with(order_with_lines)
    mock_order_refunded.assert_called_once_with(order_with_lines)


def test_transaction_update_by_app_assign_app_owner(
    transaction_item_generator, permission_manage_payments, app_api_client
):
    # given
    transaction = transaction_item_generator()
    name = "Captured for 10$"

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "name": name,
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
    assert data["createdBy"]["id"] == to_global_id_or_none(app_api_client.app)
    assert transaction.app_identifier == app_api_client.app.identifier
    assert transaction.app == app_api_client.app
    assert transaction.user is None


@freeze_time("2018-05-31 12:00:01")
def test_transaction_update_for_checkout_updates_last_transaction_modified_at(
    checkout_with_items,
    permission_manage_payments,
    app_api_client,
    transaction_item_generator,
    app,
):
    # given
    current_authorized_value = Decimal("1")
    current_charged_value = Decimal("2")
    transaction = transaction_item_generator(
        checkout_id=checkout_with_items.pk,
        app=app,
        authorized_value=current_authorized_value,
        charged_value=current_charged_value,
    )
    with freeze_time("2000-05-31 12:00:01"):
        transaction.save(update_fields=["modified_at"])
    previous_modified_at = transaction.modified_at
    checkout_with_items.last_transaction_modified_at = previous_modified_at
    checkout_with_items.save()

    authorized_value = Decimal("12")
    charged_value = Decimal("13")

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "transaction": {
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
            "amountCharged": {
                "amount": charged_value,
                "currency": "USD",
            },
        },
    }

    # when
    app_api_client.post_graphql(
        MUTATION_TRANSACTION_UPDATE, variables, permissions=[permission_manage_payments]
    )

    # then
    checkout_with_items.refresh_from_db()
    transaction.refresh_from_db()

    assert checkout_with_items.last_transaction_modified_at != previous_modified_at
    assert checkout_with_items.last_transaction_modified_at == transaction.modified_at
