from decimal import Decimal
from unittest.mock import patch

import graphene
import pytest
from freezegun import freeze_time

from .....checkout import CheckoutAuthorizeStatus, CheckoutChargeStatus
from .....checkout.calculations import fetch_checkout_data
from .....checkout.complete_checkout import create_order_from_checkout
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.models import Checkout
from .....order import OrderAuthorizeStatus, OrderChargeStatus, OrderEvents, OrderStatus
from .....order.models import Order
from .....order.utils import update_order_authorize_data, update_order_charge_data
from .....payment import PaymentMethodType, TransactionEventType
from .....payment.error_codes import TransactionCreateErrorCode
from .....payment.lock_objects import (
    get_checkout_and_transaction_item_locked_for_update,
    get_order_and_transaction_item_locked_for_update,
)
from .....payment.models import TransactionItem
from .....tests import race_condition
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
                paymentMethodDetails{
                    ...on CardPaymentMethodDetails{
                        __typename
                        name
                        brand
                        firstDigits
                        lastDigits
                        expMonth
                        expYear
                    }
                    ...on OtherPaymentMethodDetails{
                        __typename
                        name
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
    authorized_value = Decimal(10)
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
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal(10)
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
    available_actions = list(set(available_actions))

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


def test_transaction_create_for_order_by_app_metadata_null_value(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal(10)
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
            "metadata": None,
            "privateMetadata": None,
            "externalUrl": external_url,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    available_actions = list(set(available_actions))

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
    assert transaction.metadata == {}
    assert transaction.private_metadata == {}
    assert transaction.app_identifier == app_api_client.app.identifier
    assert transaction.app == app_api_client.app
    assert transaction.user is None
    assert transaction.external_url == external_url


def test_transaction_create_for_order_updates_order_total_authorized_by_app(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    previously_authorized_value = Decimal(90)
    old_transaction = order_with_lines.payment_transactions.create(
        authorized_value=previously_authorized_value, currency=order_with_lines.currency
    )

    update_order_authorize_data(order_with_lines)

    authorized_value = Decimal(10)

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
    previously_charged_value = Decimal(90)
    old_transaction = order_with_lines.payment_transactions.create(
        charged_value=previously_charged_value, currency=order_with_lines.currency
    )
    update_order_charge_data(order_with_lines)

    charged_value = Decimal(10)

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


@pytest.mark.parametrize("automatically_confirm_all_new_orders", [True, False])
def test_transaction_create_for_draft_order(
    automatically_confirm_all_new_orders,
    order_with_lines,
    permission_manage_payments,
    app_api_client,
):
    # given
    order_with_lines.status = OrderStatus.DRAFT
    order_with_lines.save(update_fields=["status"])

    channel = order_with_lines.channel
    channel.automatically_confirm_all_new_orders = automatically_confirm_all_new_orders
    channel.save(update_fields=["automatically_confirm_all_new_orders"])

    previously_charged_value = Decimal(90)
    old_transaction = order_with_lines.payment_transactions.create(
        charged_value=previously_charged_value, currency=order_with_lines.currency
    )
    update_order_charge_data(order_with_lines)

    charged_value = Decimal(10)

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": "Credit card",
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
    assert order_with_lines.status == OrderStatus.DRAFT


def test_transaction_create_for_checkout_by_app(
    checkout_with_prices, permission_manage_payments, app_api_client, plugins_manager
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal(10)
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"

    variables = {
        "id": graphene.Node.to_global_id("Checkout", checkout_with_prices.pk),
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
    checkout_with_prices.refresh_from_db()
    assert checkout_with_prices.charge_status == CheckoutChargeStatus.NONE
    assert checkout_with_prices.authorize_status == CheckoutAuthorizeStatus.PARTIAL

    available_actions = list(set(available_actions))

    transaction = checkout_with_prices.payment_transactions.first()
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


def test_transaction_create_for_checkout_by_app_metadata_null_value(
    checkout_with_prices, permission_manage_payments, app_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal(10)
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"

    variables = {
        "id": graphene.Node.to_global_id("Checkout", checkout_with_prices.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
            "availableActions": available_actions,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
            "metadata": None,
            "privateMetadata": None,
            "externalUrl": external_url,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    checkout_with_prices.refresh_from_db()
    assert checkout_with_prices.charge_status == CheckoutChargeStatus.NONE
    assert checkout_with_prices.authorize_status == CheckoutAuthorizeStatus.PARTIAL

    available_actions = list(set(available_actions))

    transaction = checkout_with_prices.payment_transactions.first()
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
    assert transaction.metadata == {}
    assert transaction.private_metadata == {}
    assert transaction.external_url == external_url
    assert transaction.app_identifier == app_api_client.app.identifier
    assert transaction.app == app_api_client.app
    assert transaction.user is None


@pytest.mark.parametrize(
    ("amount_field_name", "amount_db_field"),
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
    expected_value = Decimal(10)

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
    authorized_value = Decimal(10)
    charged_value = Decimal(11)
    refunded_value = Decimal(12)
    canceled_value = Decimal(13)

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
    authorized_value = Decimal(10)
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
    authorized_value = Decimal(10)
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
    ("amount_field_name", "amount_db_field"),
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
    expected_value = Decimal(10)

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
    authorized_value = Decimal(10)
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
    authorized_value = Decimal(10)
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
    authorized_value = Decimal(0)
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
    authorized_value = Decimal(0)
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
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal(10)
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
    available_actions = list(set(available_actions))

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
    previously_authorized_value = Decimal(90)
    old_transaction = order_with_lines.payment_transactions.create(
        authorized_value=previously_authorized_value, currency=order_with_lines.currency
    )

    update_order_authorize_data(order_with_lines)

    authorized_value = Decimal(10)

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
    previously_charged_value = Decimal(90)
    old_transaction = order_with_lines.payment_transactions.create(
        charged_value=previously_charged_value, currency=order_with_lines.currency
    )
    update_order_charge_data(order_with_lines)

    charged_value = Decimal(10)

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
    checkout_with_prices, permission_manage_payments, staff_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal(10)
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}

    variables = {
        "id": graphene.Node.to_global_id("Checkout", checkout_with_prices.pk),
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
    available_actions = list(set(available_actions))

    checkout_with_prices.refresh_from_db()
    assert checkout_with_prices.charge_status == CheckoutChargeStatus.NONE
    assert checkout_with_prices.authorize_status == CheckoutAuthorizeStatus.PARTIAL
    transaction = checkout_with_prices.payment_transactions.first()
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


@patch("saleor.checkout.tasks.automatic_checkout_completion_task.delay")
@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
def test_transaction_create_for_checkout_fully_paid(
    mocked_checkout_fully_paid,
    mocked_automatic_checkout_completion_task,
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

    assert checkout.channel.automatically_complete_fully_paid_checkouts is False

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

    mocked_checkout_fully_paid.assert_called_once_with(checkout, webhooks=set())
    mocked_automatic_checkout_completion_task.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
def test_transaction_create_for_checkout_fully_paid_automatic_completion(
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

    channel = checkout_info.channel
    channel.automatically_complete_fully_paid_checkouts = True
    channel.save(update_fields=["automatically_complete_fully_paid_checkouts"])

    checkout_token = checkout.pk

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
    mocked_checkout_fully_paid.assert_called_once_with(checkout, webhooks=set())
    with pytest.raises(Checkout.DoesNotExist):
        checkout.refresh_from_db()

    order = Order.objects.get(checkout_token=checkout_token)
    assert order.charge_status == CheckoutChargeStatus.FULL
    assert order.authorize_status == CheckoutAuthorizeStatus.FULL
    assert order.events.filter(
        type=OrderEvents.PLACED_AUTOMATICALLY_FROM_PAID_CHECKOUT
    ).exists()


@patch("saleor.checkout.tasks.automatic_checkout_completion_task.delay")
@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
def test_transaction_create_for_checkout_fully_authorized(
    mocked_checkout_fully_paid,
    mocked_automatic_checkout_completion_task,
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

    assert checkout.channel.automatically_complete_fully_paid_checkouts is False

    variables = {
        "id": graphene.Node.to_global_id("Checkout", checkout.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
            "availableActions": available_actions,
            "amountAuthorized": {
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
    assert checkout.charge_status == CheckoutChargeStatus.NONE
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL

    mocked_checkout_fully_paid.assert_not_called()
    mocked_automatic_checkout_completion_task.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
def test_transaction_create_for_checkout_fully_authorized_automatic_completion(
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

    channel = checkout_info.channel
    channel.automatically_complete_fully_paid_checkouts = True
    channel.save(update_fields=["automatically_complete_fully_paid_checkouts"])

    checkout_token = checkout.pk

    variables = {
        "id": graphene.Node.to_global_id("Checkout", checkout.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
            "availableActions": available_actions,
            "amountAuthorized": {
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
    mocked_checkout_fully_paid.assert_not_called()

    with pytest.raises(Checkout.DoesNotExist):
        checkout.refresh_from_db()

    order = Order.objects.get(checkout_token=checkout_token)
    assert order.charge_status == CheckoutChargeStatus.NONE
    assert order.authorize_status == CheckoutAuthorizeStatus.FULL
    assert order.events.filter(
        type=OrderEvents.PLACED_AUTOMATICALLY_FROM_PAID_CHECKOUT
    ).exists()


@pytest.mark.parametrize(
    ("amount_field_name", "amount_db_field"),
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
    expected_value = Decimal(10)

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
    authorized_value = Decimal(10)
    charged_value = Decimal(11)
    refunded_value = Decimal(12)
    canceled_value = Decimal(13)

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
    authorized_value = Decimal(10)
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
    authorized_value = Decimal(10)
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
    ("amount_field_name", "amount_db_field"),
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
    expected_value = Decimal(10)

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
    authorized_value = Decimal(10)
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
    authorized_value = Decimal(10)
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
    authorized_value = Decimal(0)
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
    authorized_value = Decimal(10)
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
    authorized_value = Decimal(0)
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
    authorized_value = Decimal(10)
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
    authorized_value = Decimal(10)
    charged_value = Decimal(8)
    refunded_value = Decimal(5)
    canceled_value = Decimal(2)

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
def test_transaction_create_for_order_triggers_webhooks_when_fully_paid(
    mock_order_fully_paid,
    mock_order_updated,
    mock_order_paid,
    auto_order_confirmation,
    excpected_order_status,
    unconfirmed_order_with_lines,
    permission_manage_payments,
    staff_api_client,
):
    # given
    order = unconfirmed_order_with_lines
    order.channel.automatically_confirm_all_new_orders = auto_order_confirmation
    order.channel.save(update_fields=["automatically_confirm_all_new_orders"])
    charged_value = order.total.gross.amount

    variables = {
        "id": graphene.Node.to_global_id("Order", order.pk),
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
    order.refresh_from_db()
    get_graphql_content(response)

    assert order.status == excpected_order_status
    assert order.charge_status == OrderChargeStatus.FULL
    mock_order_fully_paid.assert_called_once_with(order, webhooks=set())
    mock_order_updated.assert_called_once_with(order, webhooks=set())
    mock_order_paid.assert_called_once_with(order, webhooks=set())


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
    charged_value = Decimal(10)

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
    mock_order_updated.assert_called_once_with(order_with_lines, webhooks=set())
    mock_order_paid.assert_called_once_with(order_with_lines, webhooks=set())


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
    authorized_value = Decimal(10)

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
    mock_order_updated.assert_called_once_with(order_with_lines, webhooks=set())


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

    mock_order_fully_refunded.assert_called_once_with(order_with_lines, webhooks=set())
    mock_order_refunded.assert_called_once_with(order_with_lines, webhooks=set())
    mock_order_updated.assert_called_once_with(order_with_lines, webhooks=set())


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
    refunded_value = Decimal(10)

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
    mock_order_updated.assert_called_once_with(order_with_lines, webhooks=set())
    mock_order_refunded.assert_called_once_with(order_with_lines, webhooks=set())


@freeze_time("2018-05-31 12:00:01")
def test_transaction_create_for_checkout_updates_last_transaction_modified_at(
    checkout_with_items, permission_manage_payments, app_api_client
):
    # given
    assert checkout_with_items.last_transaction_modified_at is None
    psp_reference = "PSP reference - 123"
    authorized_value = Decimal(10)

    variables = {
        "id": graphene.Node.to_global_id("Checkout", checkout_with_items.pk),
        "transaction": {
            "pspReference": psp_reference,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
        },
    }

    # when
    app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    checkout_with_items.refresh_from_db()
    transaction = checkout_with_items.payment_transactions.first()

    assert checkout_with_items.last_transaction_modified_at == transaction.modified_at


def test_transaction_create_null_available_actions(
    checkout_with_items, permission_manage_payments, app_api_client
):
    # given
    authorized_value = Decimal(10)
    variables = {
        "id": graphene.Node.to_global_id("Checkout", checkout_with_items.pk),
        "transaction": {
            "pspReference": "PSP reference - 123",
            "availableActions": None,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
        },
    }

    # when
    app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    assert checkout_with_items.payment_transactions.first().available_actions == []


@pytest.mark.parametrize(
    ("amount_field_name", "transaction_field_name", "amount_db_field"),
    [
        ("amountAuthorized", "authorizedAmount", "authorized_value"),
        ("amountCharged", "chargedAmount", "charged_value"),
        ("amountCanceled", "canceledAmount", "canceled_value"),
        ("amountRefunded", "refundedAmount", "refunded_value"),
    ],
)
def test_transaction_create_amount_with_lot_of_decimal_places(
    amount_field_name,
    transaction_field_name,
    amount_db_field,
    order_with_lines,
    permission_manage_payments,
    app_api_client,
):
    # given
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
        TransactionActionEnum.CANCEL.name,
        TransactionActionEnum.CHARGE.name,
    ]
    value = Decimal("9.88789999")
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": "Credit Card",
            "pspReference": psp_reference,
            "availableActions": available_actions,
            amount_field_name: {
                "amount": value,
                "currency": "USD",
            },
            "externalUrl": external_url,
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    available_actions = set(available_actions)

    transaction = order_with_lines.payment_transactions.first()
    content = get_graphql_content(response)
    data = content["data"]["transactionCreate"]["transaction"]
    assert set(data["actions"]) == available_actions
    assert data["pspReference"] == psp_reference
    assert str(data[transaction_field_name]["amount"]) == str(round(value, 2))
    assert data["externalUrl"] == external_url
    assert data["createdBy"]["id"] == to_global_id_or_none(app_api_client.app)

    assert available_actions == set(map(str.upper, transaction.available_actions))
    assert psp_reference == transaction.psp_reference
    assert round(value, 2) == getattr(transaction, amount_db_field)
    assert transaction.app_identifier == app_api_client.app.identifier
    assert transaction.app == app_api_client.app
    assert transaction.user is None
    assert transaction.external_url == external_url


def test_transaction_create_create_event_message_limit_exceeded(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal(10)
    transaction_reference = "transaction reference"
    transaction_msg = "m" * 513

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
            "message": transaction_msg,
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
        "message": transaction_msg,
        "reference": transaction_reference,
    }

    transaction = order_with_lines.payment_transactions.first()
    event = transaction.events.last()
    assert event.message == transaction_msg[:511] + "…"
    assert event.psp_reference == transaction_reference


def test_transaction_create_create_event_message_is_empty(
    order_with_lines, permission_manage_payments, app_api_client
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal(10)
    transaction_reference = "transaction reference"
    transaction_msg = None

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
            "message": None,
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
        "message": transaction_msg,
        "reference": transaction_reference,
    }

    transaction = order_with_lines.payment_transactions.first()
    event = transaction.events.last()
    assert event.message == ""
    assert event.psp_reference == transaction_reference


@pytest.mark.parametrize(
    (
        "card_brand",
        "card_first_digits",
        "card_last_digits",
        "card_exp_month",
        "card_exp_year",
    ),
    [
        ("Brand", "1234", "5678", 12, 2025),
        (None, "1111", "0000", 1, 2001),
        (None, None, None, None, None),
        ("", "", "", None, None),
        (None, None, "1234", None, None),
    ],
)
def test_transaction_create_with_card_payment_method_details(
    card_brand,
    card_first_digits,
    card_last_digits,
    card_exp_month,
    card_exp_year,
    order_with_lines,
    permission_manage_payments,
    app_api_client,
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"

    authorized_value = Decimal(10)

    card_name = "Payment Method Name"

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
            "paymentMethodDetails": {
                "card": {
                    "name": card_name,
                    "brand": card_brand,
                    "firstDigits": card_first_digits,
                    "lastDigits": card_last_digits,
                    "expMonth": card_exp_month,
                    "expYear": card_exp_year,
                }
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction = order_with_lines.payment_transactions.first()
    content = get_graphql_content(response)
    transaction_data = content["data"]["transactionCreate"]["transaction"]
    assert transaction_data
    assert not content["data"]["transactionCreate"]["errors"]

    payment_method_details_data = transaction_data["paymentMethodDetails"]
    assert payment_method_details_data["__typename"] == "CardPaymentMethodDetails"
    assert payment_method_details_data["name"] == card_name
    assert payment_method_details_data["brand"] == card_brand
    assert payment_method_details_data["firstDigits"] == card_first_digits
    assert payment_method_details_data["lastDigits"] == card_last_digits
    assert payment_method_details_data["expMonth"] == card_exp_month
    assert payment_method_details_data["expYear"] == card_exp_year

    assert transaction.payment_method_type == PaymentMethodType.CARD
    assert transaction.payment_method_name == card_name
    assert transaction.cc_brand == card_brand
    assert transaction.cc_first_digits == card_first_digits
    assert transaction.cc_last_digits == card_last_digits
    assert transaction.cc_exp_month == card_exp_month
    assert transaction.cc_exp_year == card_exp_year


def test_transaction_create_with_other_payment_method_details(
    order_with_lines,
    permission_manage_payments,
    app_api_client,
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"

    authorized_value = Decimal(10)

    other_name = "Payment Method Name"

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
            "paymentMethodDetails": {
                "other": {
                    "name": other_name,
                }
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction = order_with_lines.payment_transactions.first()
    content = get_graphql_content(response)
    transaction_data = content["data"]["transactionCreate"]["transaction"]
    assert transaction_data
    assert not content["data"]["transactionCreate"]["errors"]

    payment_method_details_data = transaction_data["paymentMethodDetails"]
    assert payment_method_details_data["__typename"] == "OtherPaymentMethodDetails"
    assert payment_method_details_data["name"] == other_name

    transaction.refresh_from_db()
    assert transaction.payment_method_type == PaymentMethodType.OTHER
    assert transaction.payment_method_name == other_name
    assert transaction.cc_brand is None
    assert transaction.cc_first_digits is None
    assert transaction.cc_last_digits is None
    assert transaction.cc_exp_month is None
    assert transaction.cc_exp_year is None


def test_transaction_create_with_both_payment_method_details_inputs(
    order_with_lines,
    permission_manage_payments,
    app_api_client,
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"

    authorized_value = Decimal(10)

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
            "paymentMethodDetails": {
                "other": {
                    "name": "Other",
                },
                "card": {
                    "name": "Name",
                },
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    transaction_data = response["data"]["transactionCreate"]
    assert transaction_data["errors"]
    assert len(transaction_data["errors"]) == 1
    assert transaction_data["errors"][0]["code"] == "INVALID"


@pytest.mark.parametrize(
    (
        "card_brand_length",
        "card_first_digits",
        "card_last_digits",
        "card_exp_month",
        "card_exp_year",
        "card_name_length",
    ),
    [
        (41, "12345", "56780", 33, 12025, 257),
        (41, None, None, None, None, None),
        (None, "12345", None, None, None, None),
        (None, None, "56780", None, None, None),
        (None, None, None, 33, None, None),
        (None, None, None, None, 12025, None),
        (None, None, None, None, None, 257),
    ],
)
def test_transaction_create_with_invalid_card_payment_method_details(
    card_brand_length,
    card_first_digits,
    card_last_digits,
    card_exp_month,
    card_exp_year,
    card_name_length,
    order_with_lines,
    permission_manage_payments,
    app_api_client,
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"

    authorized_value = Decimal(10)

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
            "paymentMethodDetails": {
                "card": {
                    "name": "N" * (card_name_length or 0),
                    "brand": "B" * (card_brand_length or 0),
                    "firstDigits": card_first_digits,
                    "lastDigits": card_last_digits,
                    "expMonth": card_exp_month,
                    "expYear": card_exp_year,
                }
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    transaction_data = response["data"]["transactionCreate"]
    assert transaction_data["errors"]

    for error in transaction_data["errors"]:
        assert error["code"] == "INVALID"
        assert error["field"] == "paymentMethodDetails"


def test_transaction_create_with_invalid_other_payment_method_details(
    order_with_lines,
    permission_manage_payments,
    app_api_client,
):
    # given
    name = "Credit Card"
    psp_reference = "PSP reference - 123"

    authorized_value = Decimal(10)

    other_name = "Payment Method Name"

    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "transaction": {
            "name": name,
            "pspReference": psp_reference,
            "amountAuthorized": {
                "amount": authorized_value,
                "currency": "USD",
            },
            "paymentMethodDetails": {
                "other": {
                    "name": other_name * 256,
                }
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    transaction_data = response["data"]["transactionCreate"]
    assert transaction_data["errors"]
    assert len(transaction_data["errors"]) == 1
    error = transaction_data["errors"][0]
    assert error["code"] == "INVALID"
    assert error["field"] == "paymentMethodDetails"


# Test wrapped by `transaction=True` to ensure that `selector_for_update` is called in a database transaction.
@pytest.mark.django_db(transaction=True)
@patch(
    "saleor.graphql.payment.mutations.transaction.utils.get_order_and_transaction_item_locked_for_update",
    wraps=get_order_and_transaction_item_locked_for_update,
)
def test_lock_order_during_updating_order_amounts(
    mocked_get_order_and_transaction_item_locked_for_update,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
    order_with_lines,
):
    # given
    order = order_with_lines
    charged_value = order.total.gross.amount

    variables = {
        "id": graphene.Node.to_global_id("Order", order.pk),
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
    app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    order.refresh_from_db()
    transaction_pk = order.payment_transactions.get().pk
    assert order.total_charged.amount == charged_value
    assert order.charge_status == OrderChargeStatus.FULL
    assert order.authorize_status == OrderAuthorizeStatus.FULL
    mocked_get_order_and_transaction_item_locked_for_update.assert_called_once_with(
        order.pk, transaction_pk
    )


# Test wrapped by `transaction=True` to ensure that `selector_for_update` is called in a database transaction.
@pytest.mark.django_db(transaction=True)
@patch(
    "saleor.graphql.payment.mutations.transaction.utils.get_checkout_and_transaction_item_locked_for_update",
    wraps=get_checkout_and_transaction_item_locked_for_update,
)
def test_lock_checkout_during_updating_checkout_amounts(
    mocked_get_checkout_and_transaction_item_locked_for_update,
    app_api_client,
    permission_manage_payments,
    checkout_with_items,
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

    checkout = checkout_with_items
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)

    assert checkout.channel.automatically_complete_fully_paid_checkouts is False

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
    app_api_client.post_graphql(
        MUTATION_TRANSACTION_CREATE, variables, permissions=[permission_manage_payments]
    )

    # then
    checkout.refresh_from_db()
    transaction_pk = checkout.payment_transactions.get().pk
    assert checkout.charge_status == CheckoutChargeStatus.FULL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL
    mocked_get_checkout_and_transaction_item_locked_for_update.assert_called_once_with(
        checkout.pk, transaction_pk
    )


def test_transaction_create_create_checkout_completed_race_condition(
    app_api_client,
    permission_manage_payments,
    checkout_with_prices,
    plugins_manager,
):
    # given
    checkout = checkout_with_prices
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    name = "Credit Card"
    psp_reference = "PSP reference - 123"
    available_actions = [
        TransactionActionEnum.CHARGE.name,
        TransactionActionEnum.CHARGE.name,
    ]
    authorized_value = Decimal(checkout_info.checkout.total.gross.amount)
    metadata = {"key": "test-1", "value": "123"}
    private_metadata = {"key": "test-2", "value": "321"}
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"

    variables = {
        "id": graphene.Node.to_global_id("Checkout", checkout.pk),
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
    def complete_checkout(*args, **kwargs):
        create_order_from_checkout(
            checkout_info, plugins_manager, user=None, app=app_api_client.app
        )

    with race_condition.RunBefore(
        "saleor.graphql.payment.mutations.transaction.transaction_create.recalculate_transaction_amounts",
        complete_checkout,
    ):
        app_api_client.post_graphql(
            MUTATION_TRANSACTION_CREATE,
            variables,
            permissions=[permission_manage_payments],
        )

    # then
    order = Order.objects.get(checkout_token=checkout.pk)

    assert order.status == OrderStatus.UNFULFILLED
    assert order.charge_status == OrderChargeStatus.NONE
    assert order.authorize_status == OrderAuthorizeStatus.FULL
