from decimal import Decimal

import graphene
import pytest
from mock import patch

from .....checkout import CheckoutAuthorizeStatus, CheckoutChargeStatus
from .....checkout.calculations import fetch_checkout_data
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....order import OrderAuthorizeStatus, OrderChargeStatus, OrderEvents, OrderStatus
from .....order.utils import update_order_authorize_data, update_order_charge_data
from .....payment import TransactionEventType
from .....payment.error_codes import TransactionCreateErrorCode
from .....payment.models import TransactionItem
from ....core.utils import to_global_id_or_none
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import TransactionActionEnum, TransactionEventTypeEnum

TEST_SERVER_DOMAIN = "testserver.com"

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
                pspReference
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


def test_transaction_create_updates_order_authorize_amounts(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal("10")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
            "availableActions": available_actions,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
            "metadata": [metadata],
            "privateMetadata": [private_metadata],
            "externalUrl": external_url,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    order_with_lines.refresh_from_db()
    assert order_with_lines.total_authorized.amount == authorized_value
    assert order_with_lines.authorize_status == OrderAuthorizeStatus.PARTIAL
    assert order_with_lines.search_vector


def test_transaction_create_for_order_by_app(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal("10")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
            "availableActions": available_actions,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
            "metadata": [metadata],
            "privateMetadata": [private_metadata],
            "externalUrl": external_url,
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
    assert data["pspReference"] == psp_reference
    assert data["authorizedAmount"]["amount"] == authorized_value
    assert data["externalUrl"] == external_url
    assert data["createdBy"]["id"] == to_global_id_or_none(app_api_client.app)

    assert available_actions == list(map(str.upper, transaction.available_actions))
    assert psp_reference == transaction.psp_reference
    assert authorized_value == transaction.authorized_value
    assert transaction.metadata == {metadata["key"]: metadata["value"]}
    assert transaction.private_metadata == {
        private_metadata["key"]: private_metadata["value"]
    }
    assert transaction.app_identifier == app_api_client.app.identifier
    assert transaction.app == app_api_client.app
    assert transaction.user is None
    assert transaction.external_url == external_url


def test_transaction_create_for_order_updates_order_total_authorized_by_app(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    previously_authorized_value = Decimal("90")
    old_transaction = order_with_lines.payment_transactions.create(
        authorized_value=previously_authorized_value, currency=order_with_lines.currency
    )

    update_order_authorize_data(order_with_lines)

    authorized_value = Decimal("10")

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": "Credit Card",
            "pspReference": "PSP reference - 123",
            "availableActions": [],
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()
    transaction = order_with_lines.payment_transactions.exclude(
        id=old_transaction.id
    ).last()
    content = get_graphql_content(response)
    data = content["data"]["transactionCreate"]["transaction"]
    assert data["authorizedAmount"]["amount"] == authorized_value
    assert (
        order_with_lines.total_authorized_amount
        == previously_authorized_value + authorized_value
    )
    assert authorized_value == transaction.authorized_value


def test_transaction_create_for_order_updates_order_total_charged_by_app(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    previously_charged_value = Decimal("90")
    old_transaction = order_with_lines.payment_transactions.create(
        charged_value=previously_charged_value, currency=order_with_lines.currency
    )
    update_order_charge_data(order_with_lines)

    charged_value = Decimal("10")

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": "Credit Card",
            "pspReference": "PSP reference - 123",
            "availableActions": [],
            "amountCharged": {
                "amount": charged_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()
    transaction = order_with_lines.payment_transactions.exclude(
        id=old_transaction.id
    ).last()
    content = get_graphql_content(response)
    data = content["data"]["transactionCreate"]["transaction"]
    assert data["chargedAmount"]["amount"] == charged_value
    assert (
        order_with_lines.total_charged_amount
        == previously_charged_value + charged_value
    )
    assert charged_value == transaction.charged_value


def test_transaction_create_for_checkout_by_app(
    checkout_with_items, permission_manage_payments, app_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal("10")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"

    variables = {
        "id": graphene.Node.to_global_id("Checkout", checkout_with_items.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
            "availableActions": available_actions,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
            "metadata": [metadata],
            "privateMetadata": [private_metadata],
            "externalUrl": external_url,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    checkout_with_items.refresh_from_db()
    assert checkout_with_items.charge_status == CheckoutChargeStatus.NONE
    assert checkout_with_items.authorize_status == CheckoutAuthorizeStatus.PARTIAL

    transaction = checkout_with_items.payment_transactions.first()
    content = get_graphql_content(response)
    data = content["data"]["transactionCreate"]["transaction"]
    assert data["actions"] == available_actions
    assert data["pspReference"] == psp_reference
    assert data["authorizedAmount"]["amount"] == authorized_value
    assert data["externalUrl"] == external_url
    assert data["createdBy"]["id"] == to_global_id_or_none(app_api_client.app)

    assert available_actions == list(map(str.upper, transaction.available_actions))
    assert psp_reference == transaction.psp_reference
    assert authorized_value == transaction.authorized_value
    assert transaction.metadata == {metadata["key"]: metadata["value"]}
    assert transaction.private_metadata == {
        private_metadata["key"]: private_metadata["value"]
    }
    assert transaction.external_url == external_url
    assert transaction.app_identifier == app_api_client.app.identifier
    assert transaction.app == app_api_client.app
    assert transaction.user is None


@pytest.mark.parametrize(
    "amount_field_name, amount_db_field",
    [
        ("amountAuthorized", "authorized_value"),
        ("amountCharged", "charged_value"),
        ("amountCanceled", "canceled_value"),
        ("amountRefunded", "refunded_value"),
    ],
)
def test_transaction_create_calculate_amount_by_app(
    amount_field_name,
    amount_db_field,
    order_with_lines,
    permission_manage_payments,
    app_api_client,
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    expected_value = Decimal("10")

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
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


def test_transaction_create_multiple_amounts_provided_by_app(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal("10")
    charged_value = Decimal("11")
    refunded_value = Decimal("12")
    canceled_value = Decimal("13")

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
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
            "amountCanceled": {
                "amount": canceled_value,
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

    assert data["pspReference"] == psp_reference
    assert data["authorizedAmount"]["amount"] == authorized_value
    assert data["chargedAmount"]["amount"] == charged_value
    assert data["refundedAmount"]["amount"] == refunded_value
    assert data["canceledAmount"]["amount"] == canceled_value

    assert transaction.authorized_value == authorized_value
    assert transaction.charged_value == charged_value
    assert transaction.canceled_value == canceled_value
    assert transaction.refunded_value == refunded_value


def test_transaction_create_create_event_for_order_by_app(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal("10")
    transaction_reference = "transaction reference"
    transaction_name = "Processing transaction"

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
            "availableActions": available_actions,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
        },
        "transaction_event": {
            "pspReference": transaction_reference,
            "message": transaction_name,
        },
    }

    # when
    app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    assert order_with_lines.events.count() == 1
    event = order_with_lines.events.first()

    assert event.type == OrderEvents.TRANSACTION_EVENT
    assert event.parameters == {
        "message": transaction_name,
        "reference": transaction_reference,
    }


def test_transaction_create_missing_permission_by_app(order_with_lines, app_api_client):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal("10")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
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
        ("amountCanceled", "canceled_value"),
        ("amountRefunded", "refunded_value"),
    ],
)
def test_transaction_create_incorrect_currency_by_app(
    amount_field_name,
    amount_db_field,
    order_with_lines,
    permission_manage_payments,
    app_api_client,
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    expected_value = Decimal("10")

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
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


def test_transaction_create_empty_metadata_key_by_app(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal("10")
    metadata = {"key": "", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}
    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
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
    content = get_graphql_content(response, ignore_errors=True)
    assert not content["data"]["transactionCreate"]["transaction"]
    errors = content["data"]["transactionCreate"]["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == TransactionCreateErrorCode.METADATA_KEY_REQUIRED.name


def test_transaction_create_empty_private_metadata_key_by_app(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal("10")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "", "value": "321"}
    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
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
    content = get_graphql_content(response, ignore_errors=True)
    assert not content["data"]["transactionCreate"]["transaction"]
    errors = content["data"]["transactionCreate"]["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == TransactionCreateErrorCode.METADATA_KEY_REQUIRED.name


def test_creates_transaction_event_for_order_by_app(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = []
    authorized_value = Decimal("0")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}

    event_psp_reference = "PSP-ref"
    event_message = "Failed authorization"

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
            "availableActions": available_actions,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
            "metadata": [metadata],
            "privateMetadata": [private_metadata],
        },
        "transaction_event": {
            "pspReference": event_psp_reference,
            "message": event_message,
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
    assert event_data["message"] == event_message
    assert event_data["pspReference"] == event_psp_reference
    assert event_data["externalUrl"] == ""
    assert event_data["createdBy"]["id"] == to_global_id_or_none(app_api_client.app)

    assert transaction.events.count() == 1
    event = transaction.events.first()
    assert event.message == event_message
    assert event.psp_reference == event_psp_reference
    assert event.app_identifier == app_api_client.app.identifier
    assert event.app == app_api_client.app
    assert event.user is None


def test_creates_transaction_event_for_checkout_by_app(
    checkout_with_items, permission_manage_payments, app_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal("0")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}

    event_psp_reference = "PSP-ref"
    event_message = "Failed authorization"

    variables = {
        "id": graphene.Node.to_global_id("Checkout", checkout_with_items.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
            "availableActions": available_actions,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
            "metadata": [metadata],
            "privateMetadata": [private_metadata],
        },
        "transaction_event": {
            "pspReference": event_psp_reference,
            "message": event_message,
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
    assert event_data["message"] == event_message
    assert event_data["pspReference"] == event_psp_reference
    assert event_data["createdBy"]["id"] == to_global_id_or_none(app_api_client.app)

    assert transaction.events.count() == 1
    event = transaction.events.first()
    assert event.message == event_message
    assert event.psp_reference == event_psp_reference
    assert event.app_identifier == app_api_client.app.identifier
    assert event.app == app_api_client.app
    assert event.user is None


def test_transaction_create_for_order_by_staff(
    order_with_lines, permission_manage_payments, staff_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal("10")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
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
    transaction = order_with_lines.payment_transactions.first()
    content = get_graphql_content(response)
    data = content["data"]["transactionCreate"]["transaction"]
    assert data["actions"] == available_actions

    assert data["pspReference"] == psp_reference
    assert data["authorizedAmount"]["amount"] == authorized_value
    assert data["createdBy"]["id"] == to_global_id_or_none(staff_api_client.user)

    assert available_actions == list(map(str.upper, transaction.available_actions))
    assert psp_reference == transaction.psp_reference
    assert authorized_value == transaction.authorized_value
    assert transaction.metadata == {metadata["key"]: metadata["value"]}
    assert transaction.private_metadata == {
        private_metadata["key"]: private_metadata["value"]
    }
    assert transaction.user == staff_api_client.user
    assert not transaction.app_identifier
    assert not transaction.app


def test_transaction_create_for_order_updates_order_total_authorized_by_staff(
    order_with_lines, permission_manage_payments, staff_api_client
):
    # given
    previously_authorized_value = Decimal("90")
    old_transaction = order_with_lines.payment_transactions.create(
        authorized_value=previously_authorized_value, currency=order_with_lines.currency
    )

    update_order_authorize_data(order_with_lines)

    authorized_value = Decimal("10")

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": "Credit Card",
            "pspReference": "PSP reference - 123",
            "availableActions": [],
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()
    transaction = order_with_lines.payment_transactions.exclude(
        id=old_transaction.id
    ).last()
    content = get_graphql_content(response)
    data = content["data"]["transactionCreate"]["transaction"]
    assert data["authorizedAmount"]["amount"] == authorized_value
    assert (
        order_with_lines.total_authorized_amount
        == previously_authorized_value + authorized_value
    )
    assert authorized_value == transaction.authorized_value


def test_transaction_create_for_order_updates_order_total_charged_by_staff(
    order_with_lines, permission_manage_payments, staff_api_client
):
    # given
    previously_charged_value = Decimal("90")
    old_transaction = order_with_lines.payment_transactions.create(
        charged_value=previously_charged_value, currency=order_with_lines.currency
    )
    update_order_charge_data(order_with_lines)

    charged_value = Decimal("10")

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": "Credit Card",
            "pspReference": "PSP reference - 123",
            "availableActions": [],
            "amountCharged": {
                "amount": charged_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()
    transaction = order_with_lines.payment_transactions.exclude(
        id=old_transaction.id
    ).last()
    content = get_graphql_content(response)
    data = content["data"]["transactionCreate"]["transaction"]
    assert data["chargedAmount"]["amount"] == charged_value
    assert (
        order_with_lines.total_charged_amount
        == previously_charged_value + charged_value
    )
    assert charged_value == transaction.charged_value


def test_transaction_create_for_checkout_by_staff(
    checkout_with_items, permission_manage_payments, staff_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal("10")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}

    variables = {
        "id": graphene.Node.to_global_id("Checkout", checkout_with_items.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
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
    checkout_with_items.refresh_from_db()
    assert checkout_with_items.charge_status == CheckoutChargeStatus.NONE
    assert checkout_with_items.authorize_status == CheckoutAuthorizeStatus.PARTIAL
    transaction = checkout_with_items.payment_transactions.first()
    content = get_graphql_content(response)
    data = content["data"]["transactionCreate"]["transaction"]
    assert data["actions"] == available_actions

    assert data["pspReference"] == psp_reference
    assert data["authorizedAmount"]["amount"] == authorized_value
    assert data["createdBy"]["id"] == to_global_id_or_none(staff_api_client.user)

    assert available_actions == list(map(str.upper, transaction.available_actions))
    assert psp_reference == transaction.psp_reference
    assert authorized_value == transaction.authorized_value
    assert transaction.metadata == {metadata["key"]: metadata["value"]}
    assert transaction.private_metadata == {
        private_metadata["key"]: private_metadata["value"]
    }
    assert transaction.app_identifier is None
    assert transaction.app is None
    assert transaction.user == staff_api_client.user


@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
def test_transaction_create_for_checkout_fully_paid(
    mocked_checkout_fully_paid,
    checkout_with_prices,
    permission_manage_payments,
    staff_api_client,
    plugins_manager,
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
    ]
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}

    checkout = checkout_with_prices
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)

    variables = {
        "id": graphene.Node.to_global_id("Checkout", checkout.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
            "availableActions": available_actions,
            "amountCharged": {
                "amount": checkout_info.checkout.total.gross.amount,
                "currency": "USD",
            },
            "metadata": [metadata],
            "privateMetadata": [private_metadata],
        },
    }

    # when
    staff_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    checkout.refresh_from_db()
    assert checkout.charge_status == CheckoutChargeStatus.FULL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL

    mocked_checkout_fully_paid.assert_called_once_with(checkout)


@pytest.mark.parametrize(
    "amount_field_name, amount_db_field",
    [
        ("amountAuthorized", "authorized_value"),
        ("amountCharged", "charged_value"),
        ("amountCanceled", "canceled_value"),
        ("amountRefunded", "refunded_value"),
    ],
)
def test_transaction_create_calculate_amount_by_staff(
    amount_field_name,
    amount_db_field,
    order_with_lines,
    permission_manage_payments,
    staff_api_client,
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    expected_value = Decimal("10")

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
            "availableActions": [],
            amount_field_name: {
                "amount": expected_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction = TransactionItem.objects.first()
    get_graphql_content(response)

    assert getattr(transaction, amount_db_field) == expected_value


def test_transaction_create_multiple_amounts_provided_by_staff(
    order_with_lines, permission_manage_payments, staff_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal("10")
    charged_value = Decimal("11")
    refunded_value = Decimal("12")
    canceled_value = Decimal("13")

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
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
            "amountCanceled": {
                "amount": canceled_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction = TransactionItem.objects.first()
    content = get_graphql_content(response)
    data = content["data"]["transactionCreate"]["transaction"]
    assert data["actions"] == available_actions

    assert data["pspReference"] == psp_reference
    assert data["authorizedAmount"]["amount"] == authorized_value
    assert data["chargedAmount"]["amount"] == charged_value
    assert data["refundedAmount"]["amount"] == refunded_value
    assert data["canceledAmount"]["amount"] == canceled_value

    assert transaction.authorized_value == authorized_value
    assert transaction.charged_value == charged_value
    assert transaction.canceled_value == canceled_value
    assert transaction.refunded_value == refunded_value


def test_transaction_create_create_event_for_order_by_staff(
    order_with_lines, permission_manage_payments, staff_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal("10")
    transaction_reference = "transaction reference"
    transaction_name = "Processing transaction"

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
            "availableActions": available_actions,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
        },
        "transaction_event": {
            "pspReference": transaction_reference,
            "message": transaction_name,
        },
    }

    # when
    staff_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    event = order_with_lines.events.first()

    assert event.type == OrderEvents.TRANSACTION_EVENT
    assert event.parameters == {
        "message": transaction_name,
        "reference": transaction_reference,
    }


def test_transaction_create_missing_permission_by_staff(
    order_with_lines, staff_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal("10")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
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
    response = staff_api_client.post_graphql(MUTATION_TRANSACTION_CREATE, variables)

    # then
    assert_no_permission(response)


@pytest.mark.parametrize(
    "amount_field_name, amount_db_field",
    [
        ("amountAuthorized", "authorized_value"),
        ("amountCharged", "charged_value"),
        ("amountCanceled", "canceled_value"),
        ("amountRefunded", "refunded_value"),
    ],
)
def test_transaction_create_incorrect_currency_by_staff(
    amount_field_name,
    amount_db_field,
    order_with_lines,
    permission_manage_payments,
    staff_api_client,
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    expected_value = Decimal("10")

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
            "availableActions": [],
            amount_field_name: {
                "amount": expected_value,
                "currency": "PLN",
            },
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["transactionCreate"]
    assert data["errors"][0]["field"] == amount_field_name
    assert (
        data["errors"][0]["code"] == TransactionCreateErrorCode.INCORRECT_CURRENCY.name
    )


def test_transaction_create_empty_metadata_key_by_staff(
    order_with_lines, permission_manage_payments, staff_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal("10")
    metadata = {"key": "", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}
    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
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
    content = get_graphql_content(response, ignore_errors=True)
    assert not content["data"]["transactionCreate"]["transaction"]
    errors = content["data"]["transactionCreate"]["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == TransactionCreateErrorCode.METADATA_KEY_REQUIRED.name


def test_transaction_create_empty_private_metadata_key_by_staff(
    order_with_lines, permission_manage_payments, staff_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal("10")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "", "value": "321"}
    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
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
    content = get_graphql_content(response, ignore_errors=True)
    assert not content["data"]["transactionCreate"]["transaction"]
    errors = content["data"]["transactionCreate"]["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == TransactionCreateErrorCode.METADATA_KEY_REQUIRED.name


def test_creates_transaction_event_for_order_by_staff(
    order_with_lines, permission_manage_payments, staff_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = []
    authorized_value = Decimal("0")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}

    event_psp_reference = "PSP-ref"
    event_message = "Failed authorization"
    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
            "availableActions": available_actions,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
            "metadata": [metadata],
            "privateMetadata": [private_metadata],
        },
        "transaction_event": {
            "pspReference": event_psp_reference,
            "message": event_message,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction = order_with_lines.payment_transactions.first()
    content = get_graphql_content(response)
    data = content["data"]["transactionCreate"]["transaction"]

    events_data = data["events"]
    assert len(events_data) == 1
    event_data = events_data[0]
    assert event_data["message"] == event_message
    assert event_data["pspReference"] == event_psp_reference
    assert event_data["createdBy"]["id"] == to_global_id_or_none(staff_api_client.user)
    assert event_data["type"] == TransactionEventTypeEnum.INFO.name

    assert transaction.events.count() == 1
    event = transaction.events.first()
    assert event.message == event_message
    assert event.psp_reference == event_psp_reference
    assert event.user == staff_api_client.user
    assert event.app_identifier is None
    assert event.app is None
    assert event.type == TransactionEventType.INFO


def test_creates_transaction_event_for_checkout_by_staff(
    checkout_with_items, permission_manage_payments, staff_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal("10")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}

    event_psp_reference = "PSP-ref"
    event_message = "Failed authorization"

    variables = {
        "id": graphene.Node.to_global_id("Checkout", checkout_with_items.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
            "availableActions": available_actions,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
            "metadata": [metadata],
            "privateMetadata": [private_metadata],
        },
        "transaction_event": {
            "pspReference": event_psp_reference,
            "message": event_message,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction = checkout_with_items.payment_transactions.first()
    content = get_graphql_content(response)
    data = content["data"]["transactionCreate"]["transaction"]

    events_data = data["events"]
    assert len(events_data) == 2
    event_data = [
        event for event in events_data if event["pspReference"] == event_psp_reference
    ][0]
    assert event_data["message"] == event_message
    assert event_data["pspReference"] == event_psp_reference
    assert event_data["createdBy"]["id"] == to_global_id_or_none(staff_api_client.user)
    assert event_data["type"] == TransactionEventTypeEnum.INFO.name

    assert transaction.events.count() == 2
    event = transaction.events.exclude(
        type=TransactionEventType.AUTHORIZATION_SUCCESS
    ).first()
    assert event.message == event_message
    assert event.psp_reference == event_psp_reference
    assert event.user == staff_api_client.user
    assert event.app_identifier is None
    assert event.app is None
    assert event.type == TransactionEventType.INFO


def test_creates_transaction_automatically_confirm(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    order_with_lines.status = OrderStatus.UNCONFIRMED
    order_with_lines.save()
    order_with_lines.channel.automatically_confirm_all_new_orders = True
    order_with_lines.channel.save()

    name = "Credit Card"
    reference = "PSP reference - 123"
    available_actions = []
    authorized_value = Decimal("0")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}

    event_reference = "PSP-ref"
    event_message = "Test"
    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": reference,
            "availableActions": available_actions,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
            "metadata": [metadata],
            "privateMetadata": [private_metadata],
        },
        "transaction_event": {
            "pspReference": event_reference,
            "message": event_message,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)

    order_with_lines.refresh_from_db()
    assert order_with_lines.status == OrderStatus.UNFULFILLED


def test_transaction_create_external_url_incorrect_url_format_by_app(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal("10")
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test", "value": "321"}
    external_url = "incorrect"
    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
            "availableActions": available_actions,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
            "metadata": [metadata],
            "privateMetadata": [private_metadata],
            "externalUrl": external_url,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert not content["data"]["transactionCreate"]["transaction"]
    errors = content["data"]["transactionCreate"]["errors"]
    assert len(errors) == 1
    error = errors[0]
    assert error["code"] == TransactionCreateErrorCode.INVALID.name


def test_transaction_create_creates_calculation_events(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    psp_reference = "PSP reference - 123"
    available_actions = []
    authorized_value = Decimal("10")
    charged_value = Decimal("8")
    refunded_value = Decimal("5")
    canceled_value = Decimal("2")

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "pspReference": psp_reference,
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
            "amountCanceled": {
                "amount": canceled_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    order_with_lines.refresh_from_db()
    transaction = order_with_lines.payment_transactions.first()
    assert order_with_lines.total_authorized.amount == authorized_value
    assert order_with_lines.total_charged.amount == charged_value

    assert transaction.authorized_value == authorized_value
    assert transaction.charged_value == charged_value
    assert transaction.refunded_value == refunded_value
    assert transaction.canceled_value == canceled_value

    assert transaction.events.count() == 4
    authorize_event = transaction.events.filter(
        type=TransactionEventType.AUTHORIZATION_SUCCESS
    ).first()
    assert authorize_event
    assert authorize_event.amount.amount == authorized_value
    charge_event = transaction.events.filter(
        type=TransactionEventType.CHARGE_SUCCESS
    ).first()
    assert charge_event
    assert charge_event.amount.amount == charged_value

    refund_event = transaction.events.filter(
        type=TransactionEventType.REFUND_SUCCESS
    ).first()
    assert refund_event
    assert refund_event.amount.amount == refunded_value

    cancel_event = transaction.events.filter(
        type=TransactionEventType.CANCEL_SUCCESS
    ).first()
    assert cancel_event
    assert cancel_event.amount.amount == canceled_value


@patch("saleor.plugins.manager.PluginsManager.order_paid")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_paid")
def test_transaction_create_for_order_triggers_webhooks_when_fully_paid(
    mock_order_fully_paid,
    mock_order_updated,
    mock_order_paid,
    order_with_lines,
    permission_manage_payments,
    staff_api_client,
):
    # given
    charged_value = order_with_lines.total.gross.amount

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": "Credit Card",
            "pspReference": "PSP reference - 123",
            "availableActions": [],
            "amountCharged": {
                "amount": charged_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()
    get_graphql_content(response)

    assert order_with_lines.charge_status == OrderChargeStatus.FULL
    mock_order_fully_paid.assert_called_once_with(order_with_lines)
    mock_order_updated.assert_called_once_with(order_with_lines)
    mock_order_paid.assert_called_once_with(order_with_lines)


@patch("saleor.plugins.manager.PluginsManager.order_paid")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_paid")
def test_transaction_create_for_order_triggers_webhook_when_partially_paid(
    mock_order_fully_paid,
    mock_order_updated,
    mock_order_paid,
    order_with_lines,
    permission_manage_payments,
    staff_api_client,
):
    # given
    charged_value = Decimal("10")

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": "Credit Card",
            "pspReference": "PSP reference - 123",
            "availableActions": [],
            "amountCharged": {
                "amount": charged_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
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
def test_transaction_create_for_order_triggers_webhook_when_authorized(
    mock_order_fully_paid,
    mock_order_updated,
    order_with_lines,
    permission_manage_payments,
    staff_api_client,
):
    # given
    authorized_value = Decimal("10")

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": "Credit Card",
            "pspReference": "PSP reference - 123",
            "availableActions": [],
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
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
def test_transaction_create_for_order_triggers_webhooks_when_fully_refunded(
    mock_order_fully_refunded,
    mock_order_refunded,
    mock_order_updated,
    order_with_lines,
    permission_manage_payments,
    staff_api_client,
):
    # given
    refunded_value = order_with_lines.total.gross.amount

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": "Credit Card",
            "pspReference": "PSP reference - 123",
            "availableActions": [],
            "amountRefunded": {
                "amount": refunded_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()
    get_graphql_content(response)

    mock_order_fully_refunded.assert_called_once_with(order_with_lines)
    mock_order_refunded.assert_called_once_with(order_with_lines)
    mock_order_updated.assert_called_once_with(order_with_lines)


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_refunded")
@patch("saleor.plugins.manager.PluginsManager.order_fully_refunded")
def test_transaction_create_for_order_triggers_webhook_when_partially_refunded(
    mock_order_fully_refunded,
    mock_order_refunded,
    mock_order_updated,
    order_with_lines,
    permission_manage_payments,
    staff_api_client,
):
    # given
    refunded_value = Decimal("10")

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": "Credit Card",
            "pspReference": "PSP reference - 123",
            "availableActions": [],
            "amountRefunded": {
                "amount": refunded_value,
                "currency": "USD",
            },
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order_with_lines.refresh_from_db()
    get_graphql_content(response)

    assert not mock_order_fully_refunded.called
    mock_order_updated.assert_called_once_with(order_with_lines)
    mock_order_refunded.assert_called_once_with(order_with_lines)
