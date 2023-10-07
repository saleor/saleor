from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

import graphene
import pytest
from django.utils import timezone

from .....checkout import CheckoutAuthorizeStatus, CheckoutChargeStatus
from .....checkout.calculations import fetch_checkout_data
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....payment import TransactionEventType
from .....payment.models import TransactionEvent
from .....payment.transaction_item_calculations import recalculate_transaction_amounts
from ....core.enums import TransactionEventReportErrorCode
from ....core.utils import to_global_id_or_none
from ....order.enums import OrderAuthorizeStatusEnum, OrderChargeStatusEnum
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
        app=app_api_client.app, authorized_value=Decimal("10")
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
        $id: ID!
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
        $id: ID!
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
        $id: ID!
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
    assert set(transaction_report_data["transaction"]["actions"]) == set(
        [
            TransactionActionEnum.REFUND.name,
            TransactionActionEnum.CHARGE.name,
        ]
    )
    assert set(transaction.available_actions) == set(
        [TransactionActionEnum.REFUND.value, TransactionActionEnum.CHARGE.value]
    )


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
    assert set(transaction_report_data["transaction"]["actions"]) == set(
        [
            TransactionActionEnum.REFUND.name,
            TransactionActionEnum.CHARGE.name,
        ]
    )
    assert set(transaction.available_actions) == set(
        [TransactionActionEnum.REFUND.value, TransactionActionEnum.CHARGE.value]
    )


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
    current_charged_value = Decimal("20")
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
        $id: ID!
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
    assert order.charge_status == OrderChargeStatusEnum.PARTIAL.value


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
        $id: ID!
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
    assert order.authorize_status == OrderAuthorizeStatusEnum.FULL.value


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
        $id: ID!
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
):
    # given
    checkout = checkout_with_items
    current_charged_value = Decimal("20")
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
        $id: ID!
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


@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
def test_transaction_event_updates_checkout_full_paid_with_charged_amount(
    mocked_fully_paid,
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
        "type": TransactionEventTypeEnum.CHARGE_SUCCESS.name,
        "amount": checkout_info.checkout.total.gross.amount,
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID!
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
    mocked_fully_paid.assert_called_once_with(checkout)


@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
def test_transaction_event_updates_checkout_full_paid_with_pending_charge_amount(
    mocked_fully_paid,
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
        $id: ID!
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
    mocked_fully_paid.assert_called_once_with(checkout)


def test_transaction_event_report_with_info_event(
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=Decimal("10")
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
        app=app_api_client.app, authorized_value=Decimal("10"), use_old_id=True
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
    response = get_graphql_content(response)
    assert already_existing_amount != new_amount
    transaction_report_data = response["data"]["transactionEventReport"]

    assert len(transaction_report_data["errors"]) == 1
    error = transaction_report_data["errors"][0]
    assert error["code"] == TransactionEventReportErrorCode.NOT_FOUND.name
    assert error["field"] == "id"


@patch("saleor.plugins.manager.PluginsManager.order_paid")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
@patch("saleor.plugins.manager.PluginsManager.order_fully_paid")
def test_transaction_event_report_for_order_triggers_webhooks_when_fully_paid(
    mock_order_fully_paid,
    mock_order_updated,
    mock_order_paid,
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
        "amount": order.total.gross.amount,
        "pspReference": psp_reference,
    }
    query = (
        MUTATION_DATA_FRAGMENT
        + """
    mutation TransactionEventReport(
        $id: ID!
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

    assert order.charge_status == OrderChargeStatusEnum.FULL.value
    mock_order_fully_paid.assert_called_once_with(order)
    mock_order_updated.assert_called_once_with(order)
    mock_order_paid.assert_called_once_with(order)


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
        $id: ID!
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

    assert order.charge_status == OrderChargeStatusEnum.PARTIAL.value
    assert not mock_order_fully_paid.called
    mock_order_updated.assert_called_once_with(order)


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
        $id: ID!
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

    assert order.authorize_status == OrderAuthorizeStatusEnum.PARTIAL.value
    assert not mock_order_fully_paid.called
    mock_order_updated.assert_called_once_with(order)


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
        $id: ID!
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

    assert order.authorize_status == OrderAuthorizeStatusEnum.FULL.value
    assert not mock_order_fully_paid.called
    mock_order_updated.assert_called_once_with(order)


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
        $id: ID!
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

    mock_order_fully_refunded.assert_called_once_with(order)
    mock_order_updated.assert_called_once_with(order)
    mock_order_refunded.assert_called_once_with(order)


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
        $id: ID!
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
    mock_order_refunded.assert_called_once_with(order)
    mock_order_updated.assert_called_once_with(order)


def test_transaction_event_report_by_app_assign_app_owner(
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(authorized_value=Decimal("10"))
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
    "transaction_psp_reference, expected_transaction_psp_reference",
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
        authorized_value=Decimal("10"), psp_reference=transaction_psp_reference
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
        $id: ID!
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
