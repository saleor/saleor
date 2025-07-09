import datetime
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

import graphene
import pytest
from django.utils import timezone
from freezegun import freeze_time

from .....checkout import CheckoutAuthorizeStatus, CheckoutChargeStatus
from .....checkout.calculations import fetch_checkout_data
from .....checkout.complete_checkout import create_order_from_checkout
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.models import Checkout
from .....order import (
    OrderAuthorizeStatus,
    OrderChargeStatus,
    OrderEvents,
    OrderGrantedRefundStatus,
    OrderStatus,
)
from .....order.models import Order
from .....payment import OPTIONAL_AMOUNT_EVENTS, PaymentMethodType, TransactionEventType
from .....payment.lock_objects import (
    get_checkout_and_transaction_item_locked_for_update,
    get_order_and_transaction_item_locked_for_update,
)
from .....payment.models import TransactionEvent
from .....payment.transaction_item_calculations import recalculate_transaction_amounts
from .....tests import race_condition
from ....core.enums import TransactionEventReportErrorCode
from ....core.utils import to_global_id_or_none
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import TransactionActionEnum, TransactionEventTypeEnum

TEST_SERVER_DOMAIN = "testserver.com"

MUTATION_DATA_FRAGMENT = """
fragment TransactionEventData on TransactionEventReport {
    alreadyProcessed
    transaction {
        id
        actions
        pspReference
        events {
            id
        }
        createdBy {
            ... on User {
                id
            }
            ... on App {
                id
            }
        }
        metadata {
            key
            value
        }
        privateMetadata {
            key
            value
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
    }
    transactionEvent {
        id
        createdAt
        pspReference
        message
        externalUrl
        amount {
            currency
            amount
        }
        type
        createdBy {
            ... on User {
                id
            }
            ... on App {
                id
            }
        }
    }
    errors {
        field
        message
        code
    }
}
"""


def test_transaction_event_report_by_app(
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=Decimal(10)
    )
    event_time = timezone.now()
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"
    message = "Sucesfull charge"
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
        "time": event_time.isoformat(),
        "externalUrl": external_url,
        "message": message,
        "availableActions": [TransactionActionEnum.REFUND.name],
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
        $time: DateTime
        $externalUrl: String
        $message: String
        $availableActions: [TransactionActionEnum!]!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
            time: $time
            externalUrl: $externalUrl
            message: $message
            availableActions: $availableActions
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert transaction_report_data["alreadyProcessed"] is False

    event = TransactionEvent.objects.filter(
        type=TransactionEventType.CHARGE_SUCCESS
    ).first()
    assert event
    assert event.psp_reference == psp_reference
    assert event.type == TransactionEventTypeEnum.CHARGE_SUCCESS.value
    assert event.amount_value == amount
    assert event.currency == transaction.currency
    assert event.created_at == event_time
    assert event.external_url == external_url
    assert event.transaction == transaction
    assert event.app_identifier == app_api_client.app.identifier
    assert event.app == app_api_client.app
    assert event.user is None


def test_transaction_event_report_by_app_via_token(
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=Decimal(10)
    )
    event_time = timezone.now()
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"
    message = "Sucesfull charge"
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    variables = {
        "token": transaction.token,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
        "time": event_time.isoformat(),
        "externalUrl": external_url,
        "message": message,
        "availableActions": [TransactionActionEnum.REFUND.name],
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $token: UUID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
        $time: DateTime
        $externalUrl: String
        $message: String
        $availableActions: [TransactionActionEnum!]!
    ) {
        transactionEventReport(
            token: $token
            type: $type
            amount: $amount
            pspReference: $pspReference
            time: $time
            externalUrl: $externalUrl
            message: $message
            availableActions: $availableActions
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert transaction_report_data["alreadyProcessed"] is False

    event = TransactionEvent.objects.filter(
        type=TransactionEventType.CHARGE_SUCCESS
    ).first()
    assert event
    assert event.psp_reference == psp_reference
    assert event.type == TransactionEventTypeEnum.CHARGE_SUCCESS.value
    assert event.amount_value == amount
    assert event.currency == transaction.currency
    assert event.created_at == event_time
    assert event.external_url == external_url
    assert event.transaction == transaction
    assert event.app_identifier == app_api_client.app.identifier
    assert event.app == app_api_client.app
    assert event.user is None


def test_transaction_event_report_by_user(
    staff_api_client, permission_manage_payments, staff_user, transaction_item_generator
):
    # given
    transaction = transaction_item_generator(user=staff_user)
    event_time = timezone.now()
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"
    message = "Sucesfull charge"
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
        "time": event_time.isoformat(),
        "externalUrl": external_url,
        "message": message,
        "availableActions": [
            TransactionActionEnum.CANCEL.name,
            TransactionActionEnum.CANCEL.name,
        ],
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
        $time: DateTime
        $externalUrl: String
        $message: String
        $availableActions: [TransactionActionEnum!]!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
            time: $time
            externalUrl: $externalUrl
            message: $message
            availableActions: $availableActions
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)

    event = TransactionEvent.objects.get()
    assert event.psp_reference == psp_reference
    assert event.type == TransactionEventTypeEnum.CHARGE_SUCCESS.value
    assert event.amount_value == amount
    assert event.currency == transaction.currency
    assert event.created_at == event_time
    assert event.external_url == external_url
    assert event.transaction == transaction
    assert event.app_identifier is None
    assert event.app is None
    assert event.user == staff_api_client.user

    transaction.refresh_from_db()
    assert transaction.available_actions == [TransactionActionEnum.CANCEL.value]


def test_transaction_event_report_by_another_user(
    staff_api_client, permission_manage_payments, admin_user, transaction_item_generator
):
    # given
    transaction = transaction_item_generator(user=admin_user)
    event_time = timezone.now()
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"
    message = "Sucesfull charge"
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
        "time": event_time.isoformat(),
        "externalUrl": external_url,
        "message": message,
        "availableActions": [TransactionActionEnum.CANCEL.name],
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
       mutation TransactionEventReport(
           $id: ID
           $type: TransactionEventTypeEnum!
           $amount: PositiveDecimal!
           $pspReference: String!
           $time: DateTime
           $externalUrl: String
           $message: String
           $availableActions: [TransactionActionEnum!]!
       ) {
           transactionEventReport(
               id: $id
               type: $type
               amount: $amount
               pspReference: $pspReference
               time: $time
               externalUrl: $externalUrl
               message: $message
               availableActions: $availableActions
           ) {
               ...TransactionEventData
           }
       }
       """
    )
    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    event = TransactionEvent.objects.get()
    assert event.psp_reference == psp_reference
    assert event.type == TransactionEventTypeEnum.CHARGE_SUCCESS.value
    assert event.amount_value == amount
    assert event.currency == transaction.currency
    assert event.created_at == event_time
    assert event.external_url == external_url
    assert event.transaction == transaction
    assert event.app_identifier is None
    assert event.app is None
    assert transaction.user != staff_api_client.user
    assert event.user == staff_api_client.user

    transaction.refresh_from_db()
    assert transaction.available_actions == [TransactionActionEnum.CANCEL.value]


def test_transaction_event_report_amount_with_lot_of_decimal_places(
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=Decimal(10)
    )
    event_time = timezone.now()
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"
    message = "Sucesfull charge"
    psp_reference = "111-abc"
    amount = Decimal("10.454657657")
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
        "time": event_time.isoformat(),
        "externalUrl": external_url,
        "message": message,
        "availableActions": [TransactionActionEnum.REFUND.name],
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
        $time: DateTime
        $externalUrl: String
        $message: String
        $availableActions: [TransactionActionEnum!]!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
            time: $time
            externalUrl: $externalUrl
            message: $message
            availableActions: $availableActions
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert transaction_report_data["alreadyProcessed"] is False

    event = TransactionEvent.objects.filter(
        type=TransactionEventType.CHARGE_SUCCESS
    ).first()
    assert event
    assert event.psp_reference == psp_reference
    assert event.type == TransactionEventTypeEnum.CHARGE_SUCCESS.value
    assert event.amount_value == round(amount, 2)
    assert event.currency == transaction.currency
    assert event.created_at == event_time
    assert event.external_url == external_url
    assert event.transaction == transaction
    assert event.app_identifier == app_api_client.app.identifier
    assert event.app == app_api_client.app
    assert event.user is None


def test_transaction_event_report_no_permission(
    transaction_item_created_by_app,
    app_api_client,
):
    # given
    transaction_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item_created_by_app.token
    )
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": Decimal("11.00"),
        "pspReference": "111-abc",
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query,
        variables,
    )

    # then
    assert_no_permission(response)


def test_transaction_event_report_called_by_non_app_owner(
    transaction_item_created_by_app, app_api_client, permission_manage_payments
):
    # given
    second_app = app_api_client.app
    second_app.pk = None
    second_app.identifier = "different-identifier"
    second_app.uuid = uuid4()
    second_app.save()
    transaction_item_created_by_app.app_identifier = second_app.identifier
    transaction_item_created_by_app.app = None
    transaction_item_created_by_app.save(update_fields=["app_identifier", "app"])

    transaction_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item_created_by_app.token
    )
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": Decimal("11.00"),
        "pspReference": "111-abc",
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    assert_no_permission(response)


def test_transaction_event_report_called_by_non_user_owner(
    transaction_item_created_by_app, staff_api_client, permission_manage_payments
):
    # given
    transaction_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item_created_by_app.token
    )
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": Decimal("11.00"),
        "pspReference": "111-abc",
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    assert_no_permission(response)


def test_transaction_event_report_event_already_exists(
    transaction_item_generator, app_api_client, permission_manage_payments, app
):
    # given
    event_time = timezone.now()
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"
    message = "Sucesfull charge"
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    event_type = TransactionEventTypeEnum.CHARGE_SUCCESS
    transaction = transaction_item_generator(app=app, charged_value=amount)
    transaction.events.update(
        psp_reference=psp_reference,
    )

    already_existing_event = transaction.events.filter(
        type=TransactionEventType.CHARGE_SUCCESS
    ).get()
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": event_type.name,
        "amount": amount,
        "pspReference": psp_reference,
        "time": event_time.isoformat(),
        "externalUrl": external_url,
        "message": message,
        "availableActions": [TransactionActionEnum.REFUND.name],
    }

    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
        $time: DateTime
        $externalUrl: String
        $message: String
        $availableActions: [TransactionActionEnum!]!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
            time: $time
            externalUrl: $externalUrl
            message: $message
            availableActions: $availableActions
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert transaction_report_data["alreadyProcessed"] is True
    transaction_event_data = transaction_report_data["transactionEvent"]
    assert transaction_event_data["id"] == to_global_id_or_none(already_existing_event)

    assert (
        TransactionEvent.objects.filter(
            type=TransactionEventType.CHARGE_SUCCESS
        ).count()
        == 1
    )


def test_transaction_event_report_event_already_exists_updates_available_actions(
    transaction_item_generator, app_api_client, permission_manage_payments, app
):
    # given
    event_time = timezone.now()
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"
    message = "Sucesfull charge"
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    event_type = TransactionEventTypeEnum.CHARGE_SUCCESS
    transaction = transaction_item_generator(app=app, charged_value=amount)
    transaction.events.update(
        psp_reference=psp_reference,
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": event_type.name,
        "amount": amount,
        "pspReference": psp_reference,
        "time": event_time.isoformat(),
        "externalUrl": external_url,
        "message": message,
        "availableActions": [
            TransactionActionEnum.REFUND.name,
            TransactionActionEnum.CHARGE.name,
        ],
    }

    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID!
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
        $time: DateTime
        $externalUrl: String
        $message: String
        $availableActions: [TransactionActionEnum!]!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
            time: $time
            externalUrl: $externalUrl
            message: $message
            availableActions: $availableActions
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction.refresh_from_db()
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert transaction_report_data["alreadyProcessed"] is True
    assert set(transaction_report_data["transaction"]["actions"]) == {
        TransactionActionEnum.REFUND.name,
        TransactionActionEnum.CHARGE.name,
    }
    assert set(transaction.available_actions) == {
        TransactionActionEnum.REFUND.value,
        TransactionActionEnum.CHARGE.value,
    }


def test_event_already_exists_do_not_overwrite_actions_when_not_provided_in_input(
    transaction_item_generator, app_api_client, permission_manage_payments, app
):
    # given
    event_time = timezone.now()
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"
    message = "Sucesfull charge"
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    event_type = TransactionEventTypeEnum.CHARGE_SUCCESS
    transaction = transaction_item_generator(
        app=app,
        charged_value=amount,
        available_actions=[
            TransactionActionEnum.REFUND.value,
            TransactionActionEnum.CHARGE.value,
        ],
    )
    transaction.events.update(
        psp_reference=psp_reference,
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": event_type.name,
        "amount": amount,
        "pspReference": psp_reference,
        "time": event_time.isoformat(),
        "externalUrl": external_url,
        "message": message,
    }

    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID!
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
        $time: DateTime
        $externalUrl: String
        $message: String
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
            time: $time
            externalUrl: $externalUrl
            message: $message
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    transaction.refresh_from_db()
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert transaction_report_data["alreadyProcessed"] is True
    assert set(transaction_report_data["transaction"]["actions"]) == {
        TransactionActionEnum.REFUND.name,
        TransactionActionEnum.CHARGE.name,
    }
    assert set(transaction.available_actions) == {
        TransactionActionEnum.REFUND.value,
        TransactionActionEnum.CHARGE.value,
    }


def test_transaction_event_report_incorrect_amount_for_already_existing(
    app_api_client, permission_manage_payments, transaction_item_generator, app
):
    # given
    event_time = timezone.now()
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"
    message = "Sucesfull charge"
    psp_reference = "111-abc"
    already_existing_amount = Decimal("11.00")
    new_amount = Decimal("12.00")
    event_type = TransactionEventTypeEnum.CHARGE_SUCCESS
    transaction = transaction_item_generator(
        app=app, charged_value=already_existing_amount
    )
    transaction.events.update(
        psp_reference=psp_reference,
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)

    variables = {
        "id": transaction_id,
        "type": event_type.name,
        "amount": new_amount,
        "pspReference": psp_reference,
        "time": event_time.isoformat(),
        "externalUrl": external_url,
        "message": message,
        "availableActions": [TransactionActionEnum.REFUND.name],
    }

    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
        $time: DateTime
        $externalUrl: String
        $message: String
        $availableActions: [TransactionActionEnum!]!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
            time: $time
            externalUrl: $externalUrl
            message: $message
            availableActions: $availableActions
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    assert already_existing_amount != new_amount
    transaction_report_data = response["data"]["transactionEventReport"]

    assert len(transaction_report_data["errors"]) == 1
    error = transaction_report_data["errors"][0]
    assert error["code"] == TransactionEventReportErrorCode.INCORRECT_DETAILS.name
    assert error["field"] == "pspReference"

    assert TransactionEvent.objects.count() == 2
    event = TransactionEvent.objects.filter(
        type=TransactionEventTypeEnum.CHARGE_FAILURE.value
    ).first()
    assert event
    assert event.include_in_calculations is False


@patch(
    "saleor.graphql.payment.mutations.transaction.transaction_event_report."
    "recalculate_transaction_amounts",
    wraps=recalculate_transaction_amounts,
)
def test_transaction_event_report_calls_amount_recalculations(
    mocked_recalculation,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    event_time = timezone.now()
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"
    message = "Sucesfull charge"
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction = transaction_item_generator(app=app_api_client.app)
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
        "time": event_time.isoformat(),
        "externalUrl": external_url,
        "message": message,
        "availableActions": [TransactionActionEnum.REFUND.name],
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
        $time: DateTime
        $externalUrl: String
        $message: String
        $availableActions: [TransactionActionEnum!]!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
            time: $time
            externalUrl: $externalUrl
            message: $message
            availableActions: $availableActions
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    mocked_recalculation.assert_called_once_with(transaction, save=False)
    transaction.refresh_from_db()
    assert transaction.charged_value == amount


def test_transaction_event_updates_order_total_charged(
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
    order_with_lines,
):
    # given
    order = order_with_lines
    current_charged_value = Decimal(20)
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction = transaction_item_generator(app=app_api_client.app, order_id=order.pk)
    transaction_item_generator(
        app=app_api_client.app,
        order_id=order.pk,
        charged_value=current_charged_value,
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    order.refresh_from_db()

    assert order.total_charged.amount == current_charged_value + amount
    assert order.charge_status == OrderChargeStatus.PARTIAL


def test_transaction_event_updates_order_total_authorized(
    app_api_client,
    permission_manage_payments,
    order_with_lines,
    transaction_item_generator,
):
    # given
    order = order_with_lines
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction = transaction_item_generator(app=app_api_client.app, order_id=order.pk)
    transaction_item_generator(
        app=app_api_client.app,
        order_id=order.pk,
        authorized_value=order.total.gross.amount,
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.AUTHORIZATION_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    order.refresh_from_db()

    assert order.total_authorized.amount == order.total.gross.amount + amount
    assert order.authorize_status == OrderAuthorizeStatus.FULL


def test_transaction_event_updates_search_vector(
    app_api_client,
    permission_manage_payments,
    order_with_lines,
    transaction_item_generator,
):
    # given
    order = order_with_lines
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction = transaction_item_generator(app=app_api_client.app, order_id=order.pk)
    transaction_item_generator(
        app=app_api_client.app,
        order_id=order.pk,
        authorized_value=order.total.gross.amount,
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.AUTHORIZATION_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    order.refresh_from_db()

    assert order.search_vector


def test_transaction_event_report_authorize_event_already_exists(
    app_api_client, permission_manage_payments, transaction_item_generator
):
    # given
    event_time = timezone.now()
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"
    message = "Sucesfull charge"
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    event_type = TransactionEventTypeEnum.AUTHORIZATION_SUCCESS
    transaction = transaction_item_generator(
        app=app_api_client.app,
        authorized_value=amount + Decimal(1),
    )
    transaction.events.update(
        psp_reference="Different psp reference",
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": event_type.name,
        "amount": amount,
        "pspReference": psp_reference,
        "time": event_time.isoformat(),
        "externalUrl": external_url,
        "message": message,
        "availableActions": [TransactionActionEnum.REFUND.name],
    }

    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
        $time: DateTime
        $externalUrl: String
        $message: String
        $availableActions: [TransactionActionEnum!]!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
            time: $time
            externalUrl: $externalUrl
            message: $message
            availableActions: $availableActions
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert len(transaction_report_data["errors"]) == 1
    assert transaction_report_data["errors"][0]["field"] == "type"
    assert (
        transaction_report_data["errors"][0]["code"]
        == TransactionEventReportErrorCode.ALREADY_EXISTS.name
    )

    assert TransactionEvent.objects.count() == 2
    event = TransactionEvent.objects.filter(
        type=TransactionEventTypeEnum.AUTHORIZATION_FAILURE.value
    ).first()
    assert event
    assert event.include_in_calculations is False


def test_transaction_event_updates_checkout_payment_statuses(
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
    checkout_with_items,
    plugins_manager,
):
    # given
    checkout = checkout_with_items

    # Fetch checkout lines and info to recalculate checkout total prices
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    fetch_checkout_data(checkout_info, plugins_manager, lines)

    current_charged_value = Decimal(20)
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction = transaction_item_generator(
        app=app_api_client.app, checkout_id=checkout.pk
    )
    transaction_item_generator(
        app=app_api_client.app,
        checkout_id=checkout.pk,
        charged_value=current_charged_value,
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    checkout.refresh_from_db()

    assert checkout.charge_status == CheckoutChargeStatus.PARTIAL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.PARTIAL


@pytest.mark.parametrize(
    "current_last_transaction_modified_at",
    [None, datetime.datetime(2000, 5, 31, 12, 0, 0, tzinfo=datetime.UTC)],
)
@freeze_time("2018-05-31 12:00:01")
def test_transaction_event_updates_checkout_last_transaction_modified_at(
    current_last_transaction_modified_at,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
    checkout_with_items,
):
    # given
    checkout = checkout_with_items
    checkout.last_transaction_modified_at = current_last_transaction_modified_at
    checkout.save()

    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction = transaction_item_generator(
        app=app_api_client.app, checkout_id=checkout.pk
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    checkout.refresh_from_db()
    transaction.refresh_from_db()

    assert checkout.last_transaction_modified_at != current_last_transaction_modified_at
    assert checkout.last_transaction_modified_at == transaction.modified_at


@patch("saleor.checkout.tasks.automatic_checkout_completion_task.delay")
@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
def test_transaction_event_updates_checkout_full_paid_with_charged_amount(
    mocked_fully_paid,
    mocked_automatic_checkout_completion_task,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
    checkout_with_items,
    plugins_manager,
):
    # given
    checkout = checkout_with_items

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)

    assert checkout.channel.automatically_complete_fully_paid_checkouts is False

    psp_reference = "111-abc"
    transaction = transaction_item_generator(
        app=app_api_client.app, checkout_id=checkout.pk
    )
    transaction_item_generator(
        app=app_api_client.app,
        checkout_id=checkout.pk,
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": checkout_info.checkout.total.gross.amount,
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    checkout.refresh_from_db()

    assert checkout.charge_status == CheckoutChargeStatus.FULL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL
    mocked_fully_paid.assert_called_once_with(checkout, webhooks=set())
    mocked_automatic_checkout_completion_task.assert_not_called()


@patch("saleor.checkout.tasks.automatic_checkout_completion_task.delay")
@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
def test_transaction_event_updates_checkout_full_paid_with_pending_charge_amount(
    mocked_fully_paid,
    mocked_automatic_checkout_completion_task,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
    checkout_with_items,
    plugins_manager,
):
    # given
    checkout = checkout_with_items

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)
    psp_reference = "111-abc"
    transaction = transaction_item_generator(
        app=app_api_client.app, checkout_id=checkout.pk
    )
    transaction_item_generator(
        app=app_api_client.app,
        checkout_id=checkout.pk,
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_REQUEST.name,
        "amount": checkout_info.checkout.total.gross.amount,
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    checkout.refresh_from_db()

    assert checkout.charge_status == CheckoutChargeStatus.FULL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL
    mocked_fully_paid.assert_called_once_with(checkout, webhooks=set())
    mocked_automatic_checkout_completion_task.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
def test_transaction_event_updates_checkout_full_paid_automatic_completion(
    mocked_fully_paid,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
    checkout_with_prices,
    plugins_manager,
):
    # given
    checkout = checkout_with_prices

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)
    checkout_token = checkout.token

    channel = checkout_info.channel
    channel.automatically_complete_fully_paid_checkouts = True
    channel.save(update_fields=["automatically_complete_fully_paid_checkouts"])

    psp_reference = "111-abc"
    transaction = transaction_item_generator(
        app=app_api_client.app, checkout_id=checkout.pk
    )
    transaction_item_generator(
        app=app_api_client.app,
        checkout_id=checkout.pk,
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": checkout_info.checkout.total.gross.amount,
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    mocked_fully_paid.assert_called_once_with(checkout, webhooks=set())
    with pytest.raises(Checkout.DoesNotExist):
        checkout.refresh_from_db()

    order = Order.objects.get(checkout_token=checkout_token)
    assert order.charge_status == CheckoutChargeStatus.FULL
    assert order.authorize_status == CheckoutAuthorizeStatus.FULL
    assert order.events.filter(
        type=OrderEvents.PLACED_AUTOMATICALLY_FROM_PAID_CHECKOUT
    ).exists()

    mocked_fully_paid.assert_called_once_with(checkout, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
def test_transaction_event_updates_checkout_full_paid_pending_charge_automatic_complete(
    mocked_fully_paid,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
    checkout_with_prices,
    plugins_manager,
):
    # given
    checkout = checkout_with_prices

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)
    checkout_token = checkout.token

    channel = checkout_info.channel
    channel.automatically_complete_fully_paid_checkouts = True
    channel.save(update_fields=["automatically_complete_fully_paid_checkouts"])

    psp_reference = "111-abc"
    transaction = transaction_item_generator(
        app=app_api_client.app, checkout_id=checkout.pk
    )
    transaction_item_generator(
        app=app_api_client.app,
        checkout_id=checkout.pk,
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_REQUEST.name,
        "amount": checkout_info.checkout.total.gross.amount,
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    with pytest.raises(Checkout.DoesNotExist):
        checkout.refresh_from_db()

    order = Order.objects.get(checkout_token=checkout_token)
    assert order.charge_status == CheckoutChargeStatus.NONE
    assert order.authorize_status == CheckoutAuthorizeStatus.NONE

    mocked_fully_paid.assert_called_once_with(checkout, webhooks=set())


@patch("saleor.checkout.tasks.automatic_checkout_completion_task.delay")
@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
def test_transaction_event_updates_checkout_fully_authorized(
    mocked_fully_paid,
    mocked_automatic_checkout_completion_task,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
    checkout_with_prices,
    plugins_manager,
):
    # given
    checkout = checkout_with_prices

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)

    assert checkout.channel.automatically_complete_fully_paid_checkouts is False

    psp_reference = "111-abc"
    transaction = transaction_item_generator(
        app=app_api_client.app, checkout_id=checkout.pk
    )
    transaction_item_generator(
        app=app_api_client.app,
        checkout_id=checkout.pk,
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.AUTHORIZATION_SUCCESS.name,
        "amount": checkout_info.checkout.total.gross.amount,
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    checkout.refresh_from_db()

    assert checkout.charge_status == CheckoutChargeStatus.NONE
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL
    mocked_fully_paid.assert_not_called()
    mocked_automatic_checkout_completion_task.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
def test_transaction_event_updates_checkout_fully_authorized_automatic_complete(
    mocked_fully_paid,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
    checkout_with_prices,
    plugins_manager,
):
    # given
    checkout = checkout_with_prices

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)

    checkout_token = checkout.token

    channel = checkout_info.channel
    channel.automatically_complete_fully_paid_checkouts = True
    channel.save(update_fields=["automatically_complete_fully_paid_checkouts"])

    psp_reference = "111-abc"
    transaction = transaction_item_generator(
        app=app_api_client.app, checkout_id=checkout.pk
    )
    transaction_item_generator(
        app=app_api_client.app,
        checkout_id=checkout.pk,
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.AUTHORIZATION_SUCCESS.name,
        "amount": checkout_info.checkout.total.gross.amount,
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    with pytest.raises(Checkout.DoesNotExist):
        checkout.refresh_from_db()

    order = Order.objects.get(checkout_token=checkout_token)
    assert order.charge_status == CheckoutChargeStatus.NONE
    assert order.authorize_status == CheckoutAuthorizeStatus.FULL
    assert order.events.filter(
        type=OrderEvents.PLACED_AUTOMATICALLY_FROM_PAID_CHECKOUT
    ).exists()
    mocked_fully_paid.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
def test_transaction_event_updates_checkout_fully_authorized_pending_automatic_complete(
    mocked_fully_paid,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
    checkout_with_prices,
    plugins_manager,
):
    # given
    checkout = checkout_with_prices

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)

    checkout_token = checkout.token

    channel = checkout_info.channel
    channel.automatically_complete_fully_paid_checkouts = True
    channel.save(update_fields=["automatically_complete_fully_paid_checkouts"])

    psp_reference = "111-abc"
    transaction = transaction_item_generator(
        app=app_api_client.app, checkout_id=checkout.pk
    )
    transaction_item_generator(
        app=app_api_client.app,
        checkout_id=checkout.pk,
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.AUTHORIZATION_REQUEST.name,
        "amount": checkout_info.checkout.total.gross.amount,
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    with pytest.raises(Checkout.DoesNotExist):
        checkout.refresh_from_db()

    order = Order.objects.get(checkout_token=checkout_token)
    assert order.charge_status == CheckoutChargeStatus.NONE
    assert order.authorize_status == CheckoutAuthorizeStatus.NONE
    mocked_fully_paid.assert_not_called()


def test_transaction_event_report_with_info_event(
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=Decimal(10)
    )
    event_time = timezone.now()
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"
    message = "Sucesfull charge"
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.INFO.name,
        "amount": amount,
        "pspReference": psp_reference,
        "time": event_time.isoformat(),
        "externalUrl": external_url,
        "message": message,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
     mutation TransactionEventReport(
         $id: ID
         $type: TransactionEventTypeEnum!
         $amount: PositiveDecimal!
         $pspReference: String!
         $time: DateTime
         $externalUrl: String
         $message: String
     ) {
         transactionEventReport(
             id: $id
             type: $type
             amount: $amount
             pspReference: $pspReference
             time: $time
             externalUrl: $externalUrl
             message: $message
         ) {
             ...TransactionEventData
         }
     }
     """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert transaction_report_data["alreadyProcessed"] is False

    event = TransactionEvent.objects.filter(type=TransactionEventType.INFO).first()
    assert event
    assert event.psp_reference == psp_reference
    assert event.type == TransactionEventTypeEnum.INFO.value
    assert event.amount_value == amount
    assert event.currency == transaction.currency
    assert event.created_at == event_time
    assert event.external_url == external_url
    assert event.transaction == transaction
    assert event.app_identifier == app_api_client.app.identifier
    assert event.app == app_api_client.app


def test_transaction_event_report_accepts_old_id_for_old_transaction(
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=Decimal(10), use_old_id=True
    )
    event_time = timezone.now()
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"
    message = "Sucesfull charge"
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.id)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
        "time": event_time.isoformat(),
        "externalUrl": external_url,
        "message": message,
        "availableActions": [TransactionActionEnum.REFUND.name],
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
        $time: DateTime
        $externalUrl: String
        $message: String
        $availableActions: [TransactionActionEnum!]!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
            time: $time
            externalUrl: $externalUrl
            message: $message
            availableActions: $availableActions
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert transaction_report_data["alreadyProcessed"] is False

    event = TransactionEvent.objects.filter(
        type=TransactionEventType.CHARGE_SUCCESS
    ).first()
    assert event
    assert event.psp_reference == psp_reference
    assert event.type == TransactionEventTypeEnum.CHARGE_SUCCESS.value
    assert event.amount_value == amount
    assert event.currency == transaction.currency
    assert event.created_at == event_time
    assert event.external_url == external_url
    assert event.transaction == transaction
    assert event.app_identifier == app_api_client.app.identifier
    assert event.app == app_api_client.app
    assert event.user is None


def test_transaction_event_report_doesnt_accept_old_id_for_new_transaction(
    app_api_client, permission_manage_payments, transaction_item_generator, app
):
    # given
    event_time = timezone.now()
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"
    message = "Sucesfull charge"
    psp_reference = "111-abc"
    already_existing_amount = Decimal("11.00")
    new_amount = Decimal("12.00")
    event_type = TransactionEventTypeEnum.CHARGE_SUCCESS
    transaction = transaction_item_generator(
        app=app, charged_value=already_existing_amount, use_old_id=False
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.id)

    variables = {
        "id": transaction_id,
        "type": event_type.name,
        "amount": new_amount,
        "pspReference": psp_reference,
        "time": event_time.isoformat(),
        "externalUrl": external_url,
        "message": message,
        "availableActions": [TransactionActionEnum.REFUND.name],
    }

    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
        $time: DateTime
        $externalUrl: String
        $message: String
        $availableActions: [TransactionActionEnum!]!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
            time: $time
            externalUrl: $externalUrl
            message: $message
            availableActions: $availableActions
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    assert already_existing_amount != new_amount
    transaction_report_data = response["data"]["transactionEventReport"]

    assert len(transaction_report_data["errors"]) == 1
    error = transaction_report_data["errors"][0]
    assert error["code"] == TransactionEventReportErrorCode.NOT_FOUND.name
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
def test_transaction_event_report_for_order_triggers_webhooks_when_fully_paid(
    mock_order_fully_paid,
    mock_order_updated,
    mock_order_paid,
    auto_order_confirmation,
    excpected_order_status,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
    unconfirmed_order_with_lines,
):
    # given
    order = unconfirmed_order_with_lines
    order.channel.automatically_confirm_all_new_orders = auto_order_confirmation
    order.channel.save(update_fields=["automatically_confirm_all_new_orders"])
    psp_reference = "111-abc"
    transaction = transaction_item_generator(app=app_api_client.app, order_id=order.pk)
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": order.total.gross.amount,
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    order.refresh_from_db()

    assert order.status == excpected_order_status
    assert order.charge_status == OrderChargeStatus.FULL
    mock_order_fully_paid.assert_called_once_with(order, webhooks=set())
    mock_order_updated.assert_called_once_with(order, webhooks=set())
    mock_order_paid.assert_called_once_with(order, webhooks=set())


@pytest.mark.parametrize(
    ("auto_order_confirmation"),
    [True, False],
)
@patch("saleor.plugins.manager.PluginsManager.order_paid")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_paid")
def test_transaction_event_report_for_draft_order_triggers_webhooks_when_fully_paid(
    mock_order_fully_paid,
    mock_order_updated,
    mock_order_paid,
    auto_order_confirmation,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
    draft_order,
):
    # given
    order = draft_order
    order.channel.automatically_confirm_all_new_orders = auto_order_confirmation
    order.channel.save(update_fields=["automatically_confirm_all_new_orders"])
    psp_reference = "111-abc"
    transaction = transaction_item_generator(app=app_api_client.app, order_id=order.pk)
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": order.total.gross.amount,
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    order.refresh_from_db()

    assert order.status == OrderStatus.DRAFT
    assert order.charge_status == OrderChargeStatus.FULL
    mock_order_fully_paid.assert_called_once_with(order, webhooks=set())
    mock_order_updated.assert_called_once_with(order, webhooks=set())
    mock_order_paid.assert_called_once_with(order, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_paid")
def test_transaction_event_report_for_order_triggers_webhooks_when_partially_paid(
    mock_order_fully_paid,
    mock_order_updated,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
    order_with_lines,
):
    # given
    order = order_with_lines
    psp_reference = "111-abc"
    transaction = transaction_item_generator(app=app_api_client.app, order_id=order.pk)
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": Decimal(10),
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    order.refresh_from_db()

    assert order.charge_status == OrderChargeStatus.PARTIAL
    assert not mock_order_fully_paid.called
    mock_order_updated.assert_called_once_with(order, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_paid")
def test_transaction_event_report_for_order_triggers_webhooks_when_partially_authorized(
    mock_order_fully_paid,
    mock_order_updated,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
    order_with_lines,
):
    # given
    order = order_with_lines
    psp_reference = "111-abc"
    transaction = transaction_item_generator(app=app_api_client.app, order_id=order.pk)
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.AUTHORIZATION_SUCCESS.name,
        "amount": Decimal(10),
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    order.refresh_from_db()

    assert order.authorize_status == OrderAuthorizeStatus.PARTIAL
    assert not mock_order_fully_paid.called
    mock_order_updated.assert_called_once_with(order, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_paid")
def test_transaction_event_report_for_order_triggers_webhooks_when_fully_authorized(
    mock_order_fully_paid,
    mock_order_updated,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
    order_with_lines,
):
    # given
    order = order_with_lines
    psp_reference = "111-abc"
    transaction = transaction_item_generator(app=app_api_client.app, order_id=order.pk)
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.AUTHORIZATION_SUCCESS.name,
        "amount": order.total.gross.amount,
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    order.refresh_from_db()

    assert order.authorize_status == OrderAuthorizeStatus.FULL
    assert not mock_order_fully_paid.called
    mock_order_updated.assert_called_once_with(order, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_refunded")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_refunded")
def test_transaction_event_report_for_order_triggers_webhooks_when_fully_refunded(
    mock_order_fully_refunded,
    mock_order_updated,
    mock_order_refunded,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
    order_with_lines,
):
    # given
    order = order_with_lines
    psp_reference = "111-abc"
    transaction = transaction_item_generator(app=app_api_client.app, order_id=order.pk)
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.REFUND_SUCCESS.name,
        "amount": order.total.gross.amount,
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    order.refresh_from_db()

    mock_order_fully_refunded.assert_called_once_with(order, webhooks=set())
    mock_order_updated.assert_called_once_with(order, webhooks=set())
    mock_order_refunded.assert_called_once_with(order, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_refunded")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_refunded")
def test_transaction_event_report_for_order_triggers_webhooks_when_partially_refunded(
    mock_order_fully_refunded,
    mock_order_updated,
    mock_order_refunded,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
    order_with_lines,
):
    # given
    order = order_with_lines
    psp_reference = "111-abc"
    transaction = transaction_item_generator(app=app_api_client.app, order_id=order.pk)
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.REFUND_SUCCESS.name,
        "amount": Decimal(10),
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    order.refresh_from_db()

    assert not mock_order_fully_refunded.called
    mock_order_refunded.assert_called_once_with(order, webhooks=set())
    mock_order_updated.assert_called_once_with(order, webhooks=set())


def test_transaction_event_report_by_app_assign_app_owner(
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(authorized_value=Decimal(10))
    event_time = timezone.now()
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"
    message = "Sucesfull charge"
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
        "time": event_time.isoformat(),
        "externalUrl": external_url,
        "message": message,
        "availableActions": [TransactionActionEnum.REFUND.name],
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
        $time: DateTime
        $externalUrl: String
        $message: String
        $availableActions: [TransactionActionEnum!]!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
            time: $time
            externalUrl: $externalUrl
            message: $message
            availableActions: $availableActions
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    transaction.refresh_from_db()

    assert transaction_report_data["transaction"]["createdBy"][
        "id"
    ] == to_global_id_or_none(app_api_client.app)
    assert transaction.app_identifier == app_api_client.app.identifier
    assert transaction.app == app_api_client.app
    assert transaction.user is None


@pytest.mark.parametrize(
    ("transaction_psp_reference", "expected_transaction_psp_reference"),
    [
        (None, "psp_reference_from_event"),
        ("", "psp_reference_from_event"),
        ("psp_reference_from_transaction", "psp_reference_from_transaction"),
    ],
)
def test_transaction_event_report_assign_transaction_psp_reference_if_missing(
    transaction_psp_reference,
    expected_transaction_psp_reference,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(
        authorized_value=Decimal(10), psp_reference=transaction_psp_reference
    )
    amount = Decimal("11.00")
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": expected_transaction_psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    transaction.refresh_from_db()

    assert (
        transaction_report_data["transaction"]["pspReference"]
        == expected_transaction_psp_reference
    )
    assert transaction.psp_reference == expected_transaction_psp_reference


@pytest.mark.parametrize(
    ("event_type", "expected_status"),
    [
        (TransactionEventTypeEnum.REFUND_SUCCESS, OrderGrantedRefundStatus.SUCCESS),
        (TransactionEventTypeEnum.REFUND_FAILURE, OrderGrantedRefundStatus.FAILURE),
        (TransactionEventTypeEnum.REFUND_REVERSE, OrderGrantedRefundStatus.NONE),
    ],
)
def test_transaction_event_report_updates_granted_refund_status_when_needed(
    event_type,
    expected_status,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
    order,
):
    # given
    amount = Decimal("11.00")
    transaction = transaction_item_generator(
        app=app_api_client.app, charged_value=Decimal(10), order_id=order.pk
    )
    granted_refund = order.granted_refunds.create(
        amount_value=amount, currency=order.currency, transaction_item=transaction
    )
    psp_reference = "111-abc"

    transaction.events.create(
        psp_reference=psp_reference,
        amount_value=amount,
        currency=transaction.currency,
        type=TransactionEventType.REFUND_REQUEST,
        include_in_calculations=True,
        related_granted_refund=granted_refund,
    )

    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": event_type.name,
        "amount": amount,
        "pspReference": psp_reference,
        "availableActions": [],
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
        $availableActions: [TransactionActionEnum!]!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
            availableActions: $availableActions
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    granted_refund.refresh_from_db()
    assert granted_refund.status == expected_status


@pytest.mark.parametrize("event_type", list(OPTIONAL_AMOUNT_EVENTS))
def test_transaction_event_report_missing_amount(
    event_type,
    transaction_item_generator,
    transaction_events_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=Decimal(10)
    )
    psp_reference = "111-abc"
    expected_amount = 10
    event_types = [
        TransactionEventType.AUTHORIZATION_SUCCESS,
        TransactionEventType.CHARGE_SUCCESS,
        TransactionEventType.REFUND_SUCCESS,
    ]
    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            psp_reference,
        ]
        * len(event_types),
        types=event_types,
        amounts=[
            expected_amount,
        ]
        * len(event_types),
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": event_type.upper(),
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert not transaction_report_data["errors"]
    assert transaction_report_data["alreadyProcessed"] is False

    event = TransactionEvent.objects.last()
    assert event
    assert event.psp_reference == psp_reference
    assert event.type == event_type
    expected_amount = (
        expected_amount if event_type != TransactionEventType.INFO else Decimal(0)
    )
    assert event.amount_value == expected_amount
    assert event.currency == transaction.currency
    assert event.transaction == transaction
    assert event.app_identifier == app_api_client.app.identifier
    assert event.app == app_api_client.app
    assert event.user is None


@pytest.mark.parametrize(
    "event_type",
    [
        event_type
        for event_type in OPTIONAL_AMOUNT_EVENTS
        if event_type != TransactionEventType.INFO
    ],
)
def test_transaction_event_report_missing_amount_not_deduced_error_raised(
    event_type,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=Decimal(10)
    )
    psp_reference = "111-abc"
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": event_type.upper(),
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert not transaction_report_data["transactionEvent"]
    errors = transaction_report_data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "amount"
    assert errors[0]["code"] == TransactionEventReportErrorCode.REQUIRED.name


@pytest.mark.parametrize(
    "event_type",
    [
        event_type[0]
        for event_type in TransactionEventType.CHOICES
        if event_type[0] not in OPTIONAL_AMOUNT_EVENTS
    ],
)
def test_transaction_event_report_missing_amount_error_raised(
    event_type,
    transaction_item_generator,
    transaction_events_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=Decimal(10)
    )
    psp_reference = "111-abc"
    amount = 10
    event_types = [
        TransactionEventType.AUTHORIZATION_SUCCESS,
        TransactionEventType.CHARGE_SUCCESS,
        TransactionEventType.REFUND_SUCCESS,
    ]
    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            psp_reference,
        ]
        * len(event_types),
        types=event_types,
        amounts=[
            amount,
        ]
        * len(event_types),
    )

    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": event_type.upper(),
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert not transaction_report_data["transactionEvent"]
    errors = transaction_report_data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "amount"
    assert errors[0]["code"] == TransactionEventReportErrorCode.REQUIRED.name


@patch("saleor.plugins.manager.PluginsManager.transaction_item_metadata_updated")
def test_transaction_event_report_update_transaction_metadata(
    transaction_item_metadata_updated_mock,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=Decimal(10)
    )
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    metadata = {"key": "test key", "value": "test value"}
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
        "transactionMetadata": [metadata],
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
        $transactionMetadata: [MetadataInput!]
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
            transactionMetadata: $transactionMetadata
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert transaction_report_data["alreadyProcessed"] is False

    transaction_data = transaction_report_data["transaction"]
    assert len(transaction_data["metadata"]) == 1
    assert transaction_data["metadata"][0] == metadata

    event = TransactionEvent.objects.filter(
        type=TransactionEventType.CHARGE_SUCCESS
    ).first()
    assert event
    assert event.psp_reference == psp_reference
    assert event.type == TransactionEventTypeEnum.CHARGE_SUCCESS.value
    assert event.amount_value == amount
    assert event.currency == transaction.currency
    assert event.transaction == transaction
    assert event.app_identifier == app_api_client.app.identifier
    assert event.app == app_api_client.app
    assert event.user is None
    transaction_item_metadata_updated_mock.assert_called_once_with(transaction)


@patch("saleor.plugins.manager.PluginsManager.transaction_item_metadata_updated")
def test_transaction_event_report_metadata_not_provided(
    transaction_item_metadata_updated_mock,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=Decimal(10)
    )
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
        "transactionMetadata": [],
        "transactionPrivateMetadata": [],
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
        $transactionMetadata: [MetadataInput!]
        $transactionPrivateMetadata: [MetadataInput!]
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
            transactionMetadata: $transactionMetadata
            transactionPrivateMetadata: $transactionPrivateMetadata
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert transaction_report_data["alreadyProcessed"] is False

    transaction_data = transaction_report_data["transaction"]
    assert len(transaction_data["metadata"]) == 0

    event = TransactionEvent.objects.filter(
        type=TransactionEventType.CHARGE_SUCCESS
    ).first()
    assert event
    assert event.psp_reference == psp_reference
    assert event.type == TransactionEventTypeEnum.CHARGE_SUCCESS.value
    assert event.amount_value == amount
    assert event.currency == transaction.currency
    assert event.transaction == transaction
    assert event.app_identifier == app_api_client.app.identifier
    assert event.app == app_api_client.app
    assert event.user is None
    transaction_item_metadata_updated_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.transaction_item_metadata_updated")
def test_transaction_event_report_update_transaction_private_metadata(
    transaction_item_metadata_updated_mock,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=Decimal(10)
    )
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    private_metadata = {"key": "test key", "value": "test value"}
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
        "transactionPrivateMetadata": [private_metadata],
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
        $transactionPrivateMetadata: [MetadataInput!]
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
            transactionPrivateMetadata: $transactionPrivateMetadata
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert transaction_report_data["alreadyProcessed"] is False

    transaction_data = transaction_report_data["transaction"]
    assert len(transaction_data["privateMetadata"]) == 1
    assert transaction_data["privateMetadata"][0] == private_metadata

    event = TransactionEvent.objects.filter(
        type=TransactionEventType.CHARGE_SUCCESS
    ).first()
    assert event
    assert event.psp_reference == psp_reference
    assert event.type == TransactionEventTypeEnum.CHARGE_SUCCESS.value
    assert event.amount_value == amount
    assert event.currency == transaction.currency
    assert event.transaction == transaction
    assert event.app_identifier == app_api_client.app.identifier
    assert event.app == app_api_client.app
    assert event.user is None
    transaction_item_metadata_updated_mock.assert_not_called()


def test_transaction_event_report_message_limit_exceeded(
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=Decimal(10)
    )
    event_time = timezone.now()
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"
    message = "m" * 550
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
        "time": event_time.isoformat(),
        "externalUrl": external_url,
        "message": message,
        "availableActions": [TransactionActionEnum.REFUND.name],
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
        $time: DateTime
        $externalUrl: String
        $message: String
        $availableActions: [TransactionActionEnum!]!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
            time: $time
            externalUrl: $externalUrl
            message: $message
            availableActions: $availableActions
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert transaction_report_data["alreadyProcessed"] is False

    event = TransactionEvent.objects.filter(
        type=TransactionEventType.CHARGE_SUCCESS
    ).first()
    assert event
    assert event.psp_reference == psp_reference
    assert event.type == TransactionEventTypeEnum.CHARGE_SUCCESS.value
    assert event.amount_value == amount
    assert event.currency == transaction.currency
    assert event.created_at == event_time
    assert event.external_url == external_url
    assert event.transaction == transaction
    assert event.app_identifier == app_api_client.app.identifier
    assert event.app == app_api_client.app
    assert event.user is None
    assert event.message == message[:511] + "…"


def test_transaction_event_report_empty_message(
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=Decimal(10)
    )
    event_time = timezone.now()
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"
    message = None
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
        "time": event_time.isoformat(),
        "externalUrl": external_url,
        "message": message,
        "availableActions": [TransactionActionEnum.REFUND.name],
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
        $time: DateTime
        $externalUrl: String
        $message: String
        $availableActions: [TransactionActionEnum!]!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
            time: $time
            externalUrl: $externalUrl
            message: $message
            availableActions: $availableActions
        ) {
            ...TransactionEventData
        }
    }
    """
    )
    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert transaction_report_data["alreadyProcessed"] is False

    event = TransactionEvent.objects.filter(
        type=TransactionEventType.CHARGE_SUCCESS
    ).first()
    assert event
    assert event.psp_reference == psp_reference
    assert event.type == TransactionEventTypeEnum.CHARGE_SUCCESS.value
    assert event.amount_value == amount
    assert event.currency == transaction.currency
    assert event.created_at == event_time
    assert event.external_url == external_url
    assert event.transaction == transaction
    assert event.app_identifier == app_api_client.app.identifier
    assert event.app == app_api_client.app
    assert event.user is None
    assert event.message == ""


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
    psp_reference = "111-abc"
    amount = order.total.gross.amount
    transaction = transaction_item_generator(
        app=app_api_client.app,
        order_id=order.pk,
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )

    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    order.refresh_from_db()

    assert order.total_charged.amount == amount
    assert order.charge_status == OrderChargeStatus.FULL
    assert order.authorize_status == OrderAuthorizeStatus.FULL
    mocked_get_order_and_transaction_item_locked_for_update.assert_called_once_with(
        order.pk, transaction.pk
    )


@patch(
    "saleor.graphql.payment.mutations.transaction.utils.get_checkout_and_transaction_item_locked_for_update",
    wraps=get_checkout_and_transaction_item_locked_for_update,
)
def test_lock_checkout_during_updating_checkout_amounts(
    mocked_get_checkout_and_transaction_item_locked_for_update,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
    checkout_with_items,
    plugins_manager,
):
    # given
    checkout = checkout_with_items

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)

    psp_reference = "111-abc"
    transaction = transaction_item_generator(
        app=app_api_client.app, checkout_id=checkout.pk
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": checkout_info.checkout.total.gross.amount,
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )

    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_payments]
    )

    # then
    get_graphql_content(response)
    checkout.refresh_from_db()

    assert checkout.charge_status == CheckoutChargeStatus.FULL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL
    mocked_get_checkout_and_transaction_item_locked_for_update.assert_called_once_with(
        checkout.pk, transaction.pk
    )


def test_transaction_event_report_checkout_completed_race_condition(
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
    checkout_with_items,
    plugins_manager,
):
    # given
    checkout = checkout_with_items

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)

    psp_reference = "111-abc"
    transaction = transaction_item_generator(
        app=app_api_client.app, checkout_id=checkout.pk
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": checkout_info.checkout.total.gross.amount,
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
        ) {
            ...TransactionEventData
        }
    }
    """
    )

    # when
    def complete_checkout(*args, **kwargs):
        create_order_from_checkout(
            checkout_info, plugins_manager, user=None, app=app_api_client.app
        )

    with race_condition.RunBefore(
        "saleor.graphql.payment.mutations.transaction.transaction_event_report.recalculate_transaction_amounts",
        complete_checkout,
    ):
        response = app_api_client.post_graphql(
            query, variables, permissions=[permission_manage_payments]
        )

    # then
    get_graphql_content(response)
    order = Order.objects.get(checkout_token=checkout.pk)

    assert order.status == OrderStatus.UNFULFILLED
    assert order.charge_status == OrderChargeStatus.FULL
    assert order.total_charged.amount == checkout.total.gross.amount


TRANSACTION_EVENT_REPORT_WITH_CARD_PAYMENT_METHOD_DETAILS_QUERY = (
    MUTATION_DATA_FRAGMENT
    + """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
        $paymentMethodDetails: PaymentMethodDetailsInput
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
            paymentMethodDetails: $paymentMethodDetails
        ) {
            ...TransactionEventData
        }
    }
    """
)


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
def test_transaction_event_report_with_card_payment_method_details(
    card_brand,
    card_first_digits,
    card_last_digits,
    card_exp_month,
    card_exp_year,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=Decimal(10)
    )
    transaction.payment_method_type = PaymentMethodType.CARD
    transaction.payment_method_name = "Payment Method Name"
    transaction.cc_brand = None
    transaction.cc_first_digits = "1111"
    transaction.cc_last_digits = "0000"
    transaction.cc_exp_month = 6
    transaction.cc_exp_year = 2010
    transaction.save()

    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)

    card_name = "Payment Method Name"

    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
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
    }
    # when
    response = app_api_client.post_graphql(
        TRANSACTION_EVENT_REPORT_WITH_CARD_PAYMENT_METHOD_DETAILS_QUERY,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert not transaction_report_data["errors"]

    transaction_data = transaction_report_data["transaction"]
    assert transaction_data
    payment_method_details_data = transaction_data["paymentMethodDetails"]
    assert payment_method_details_data["__typename"] == "CardPaymentMethodDetails"
    assert payment_method_details_data["name"] == card_name
    assert payment_method_details_data["brand"] == card_brand
    assert payment_method_details_data["firstDigits"] == card_first_digits
    assert payment_method_details_data["lastDigits"] == card_last_digits
    assert payment_method_details_data["expMonth"] == card_exp_month
    assert payment_method_details_data["expYear"] == card_exp_year

    transaction.refresh_from_db()
    assert transaction.payment_method_type == PaymentMethodType.CARD
    assert transaction.payment_method_name == card_name
    assert transaction.cc_brand == card_brand
    assert transaction.cc_first_digits == card_first_digits
    assert transaction.cc_last_digits == card_last_digits
    assert transaction.cc_exp_month == card_exp_month
    assert transaction.cc_exp_year == card_exp_year


def test_transaction_event_report_with_other_payment_method_details(
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=Decimal(10)
    )
    transaction.payment_method_type = PaymentMethodType.CARD
    transaction.payment_method_name = "Payment Method Name"
    transaction.cc_brand = None
    transaction.cc_first_digits = "1111"
    transaction.cc_last_digits = "0000"
    transaction.cc_exp_month = 6
    transaction.cc_exp_year = 2010
    transaction.save()

    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)

    other_name = "Payment Method Name"

    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
        "paymentMethodDetails": {
            "other": {
                "name": other_name,
            }
        },
    }

    # when
    response = app_api_client.post_graphql(
        TRANSACTION_EVENT_REPORT_WITH_CARD_PAYMENT_METHOD_DETAILS_QUERY,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert not transaction_report_data["errors"]

    transaction_data = transaction_report_data["transaction"]
    assert transaction_data

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


def test_transaction_event_report_with_both_payment_method_details_inputs(
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=Decimal(10)
    )

    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)

    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
        "paymentMethodDetails": {
            "other": {
                "name": "Other",
            },
            "card": {
                "name": "Name",
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        TRANSACTION_EVENT_REPORT_WITH_CARD_PAYMENT_METHOD_DETAILS_QUERY,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert transaction_report_data["errors"]
    assert len(transaction_report_data["errors"]) == 1
    assert transaction_report_data["errors"][0]["code"] == "INVALID"


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
def test_transaction_event_report_with_invalid_card_payment_method_details(
    card_brand_length,
    card_first_digits,
    card_last_digits,
    card_exp_month,
    card_exp_year,
    card_name_length,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=Decimal(10)
    )

    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)

    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
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
    }

    # when
    response = app_api_client.post_graphql(
        TRANSACTION_EVENT_REPORT_WITH_CARD_PAYMENT_METHOD_DETAILS_QUERY,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert transaction_report_data["errors"]

    for error in transaction_report_data["errors"]:
        assert error["code"] == "INVALID"
        assert error["field"] == "paymentMethodDetails"


def test_transaction_event_report_with_invalid_other_payment_method_details(
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=Decimal(10)
    )

    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)

    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": amount,
        "pspReference": psp_reference,
        "paymentMethodDetails": {
            "other": {
                "name": "N" * 257,
            }
        },
    }

    # when
    response = app_api_client.post_graphql(
        TRANSACTION_EVENT_REPORT_WITH_CARD_PAYMENT_METHOD_DETAILS_QUERY,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert transaction_report_data["errors"]
    assert len(transaction_report_data["errors"]) == 1
    error = transaction_report_data["errors"][0]
    assert error["code"] == "INVALID"
    assert error["field"] == "paymentMethodDetails"


def test_transaction_event_report_event_already_exists_updates_card_payment_method_details(
    transaction_item_generator, app_api_client, permission_manage_payments, app
):
    # given
    card_name = "Name"
    card_brand = "Brand"
    card_first_digits = "1234"
    card_last_digits = "5678"
    card_exp_month = 12
    card_exp_year = 2025

    psp_reference = "111-abc"
    amount = Decimal("11.00")
    event_type = TransactionEventTypeEnum.CHARGE_SUCCESS
    transaction = transaction_item_generator(app=app, charged_value=amount)
    transaction.events.update(
        psp_reference=psp_reference,
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": event_type.name,
        "amount": amount,
        "pspReference": psp_reference,
        "paymentMethodDetails": {
            "card": {
                "name": card_name,
                "brand": card_brand,
                "firstDigits": card_first_digits,
                "lastDigits": card_last_digits,
                "expMonth": card_exp_month,
                "expYear": card_exp_year,
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        TRANSACTION_EVENT_REPORT_WITH_CARD_PAYMENT_METHOD_DETAILS_QUERY,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    transaction.refresh_from_db()
    response = get_graphql_content(response)
    assert not response["data"]["transactionEventReport"]["errors"]
    transaction_report_data = response["data"]["transactionEventReport"]
    transaction_data = transaction_report_data["transaction"]
    assert transaction_data
    payment_method_details_data = transaction_data["paymentMethodDetails"]
    assert payment_method_details_data["__typename"] == "CardPaymentMethodDetails"
    assert payment_method_details_data["name"] == card_name
    assert payment_method_details_data["brand"] == card_brand
    assert payment_method_details_data["firstDigits"] == card_first_digits
    assert payment_method_details_data["lastDigits"] == card_last_digits
    assert payment_method_details_data["expMonth"] == card_exp_month
    assert payment_method_details_data["expYear"] == card_exp_year

    transaction.refresh_from_db()
    assert transaction.payment_method_type == PaymentMethodType.CARD
    assert transaction.payment_method_name == card_name
    assert transaction.cc_brand == card_brand
    assert transaction.cc_first_digits == card_first_digits
    assert transaction.cc_last_digits == card_last_digits
    assert transaction.cc_exp_month == card_exp_month
    assert transaction.cc_exp_year == card_exp_year


def test_transaction_event_report_event_already_exists_updates_other_payment_method_details(
    transaction_item_generator, app_api_client, permission_manage_payments, app
):
    # given
    payment_method_name = "Payment Method Name"

    psp_reference = "111-abc"
    amount = Decimal("11.00")
    event_type = TransactionEventTypeEnum.CHARGE_SUCCESS
    transaction = transaction_item_generator(app=app, charged_value=amount)
    transaction.events.update(
        psp_reference=psp_reference,
    )
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": event_type.name,
        "amount": amount,
        "pspReference": psp_reference,
        "paymentMethodDetails": {
            "other": {
                "name": payment_method_name,
            },
        },
    }

    # when
    response = app_api_client.post_graphql(
        TRANSACTION_EVENT_REPORT_WITH_CARD_PAYMENT_METHOD_DETAILS_QUERY,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    transaction.refresh_from_db()
    response = get_graphql_content(response)
    assert not response["data"]["transactionEventReport"]["errors"]
    transaction_report_data = response["data"]["transactionEventReport"]
    transaction_data = transaction_report_data["transaction"]
    assert transaction_data
    payment_method_details_data = transaction_data["paymentMethodDetails"]
    assert payment_method_details_data["__typename"] == "OtherPaymentMethodDetails"
    assert payment_method_details_data["name"] == payment_method_name

    transaction.refresh_from_db()
    assert transaction.payment_method_type == PaymentMethodType.OTHER
    assert transaction.payment_method_name == payment_method_name
