from decimal import Decimal
from unittest.mock import patch

from django.utils import timezone

from .....payment.models import TransactionEvent
from .....payment.transaction_item_calculations import recalculate_transaction_amounts
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
        events {
            id
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
    transaction_item_created_by_app,
    app_api_client,
    permission_manage_payments,
):
    # given
    event_time = timezone.now()
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"
    message = "Sucesfull charge"
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction_id = to_global_id_or_none(transaction_item_created_by_app)
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

    event = TransactionEvent.objects.get()
    assert event.psp_reference == psp_reference
    assert event.type == TransactionEventTypeEnum.CHARGE_SUCCESS.value
    assert event.amount_value == amount
    assert event.currency == transaction_item_created_by_app.currency
    assert event.created_at == event_time
    assert event.external_url == external_url
    assert event.transaction == transaction_item_created_by_app
    assert event.app == app_api_client.app
    assert event.user is None


def test_transaction_event_report_by_user(
    transaction_item_created_by_user,
    staff_api_client,
    permission_manage_payments,
):
    # given
    event_time = timezone.now()
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"
    message = "Sucesfull charge"
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction_id = to_global_id_or_none(transaction_item_created_by_user)
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
    assert event.currency == transaction_item_created_by_user.currency
    assert event.created_at == event_time
    assert event.external_url == external_url
    assert event.transaction == transaction_item_created_by_user
    assert event.app is None
    assert event.user == staff_api_client.user

    transaction_item_created_by_user.refresh_from_db()
    assert transaction_item_created_by_user.available_actions == [
        TransactionActionEnum.CANCEL.value
    ]


def test_transaction_event_report_no_permission(
    transaction_item_created_by_app,
    app_api_client,
):
    # given
    transaction_id = to_global_id_or_none(transaction_item_created_by_app)
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
    second_app.save()
    transaction_item_created_by_app.app = second_app
    transaction_item_created_by_app.save(update_fields=["app"])

    transaction_id = to_global_id_or_none(transaction_item_created_by_app)
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
    transaction_id = to_global_id_or_none(transaction_item_created_by_app)
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
    transaction_item_created_by_app,
    app_api_client,
    permission_manage_payments,
):
    # given
    event_time = timezone.now()
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"
    message = "Sucesfull charge"
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    event_type = TransactionEventTypeEnum.CHARGE_SUCCESS
    already_existing_event = transaction_item_created_by_app.events.create(
        psp_reference=psp_reference,
        amount_value=amount,
        type=event_type.value,
        currency=transaction_item_created_by_app.currency,
    )
    transaction_id = to_global_id_or_none(transaction_item_created_by_app)
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

    assert TransactionEvent.objects.count() == 1


def test_transaction_event_report_incorrect_amount_for_already_existing(
    transaction_item_created_by_app,
    app_api_client,
    permission_manage_payments,
):
    # given
    event_time = timezone.now()
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"
    message = "Sucesfull charge"
    psp_reference = "111-abc"
    already_existing_amount = Decimal("11.00")
    new_amount = Decimal("12.00")
    event_type = TransactionEventTypeEnum.CHARGE_SUCCESS
    transaction_item_created_by_app.events.create(
        psp_reference=psp_reference,
        amount_value=already_existing_amount,
        type=event_type.value,
        currency=transaction_item_created_by_app.currency,
    )
    transaction_id = to_global_id_or_none(transaction_item_created_by_app)
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

    assert TransactionEvent.objects.count() == 1


@patch(
    "saleor.graphql.payment.mutations.recalculate_transaction_amounts",
    wraps=recalculate_transaction_amounts,
)
def test_transaction_event_report_calls_amount_recalculations(
    mocked_recalculation,
    transaction_item_created_by_app,
    app_api_client,
    permission_manage_payments,
):
    # given
    event_time = timezone.now()
    external_url = f"http://{TEST_SERVER_DOMAIN}/external-url"
    message = "Sucesfull charge"
    psp_reference = "111-abc"
    amount = Decimal("11.00")
    transaction_id = to_global_id_or_none(transaction_item_created_by_app)
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
    mocked_recalculation.assert_called_once_with(transaction_item_created_by_app)
    transaction_item_created_by_app.refresh_from_db()
    assert transaction_item_created_by_app.charged_value == amount
