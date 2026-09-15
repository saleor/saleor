from decimal import Decimal

import graphene
import pytest

from .....payment import TransactionEventType
from .....payment.models import TransactionEvent
from .....payment.transaction_item_calculations import recalculate_transaction_amounts
from ....core.enums import TransactionEventReportErrorCode
from ....tests.utils import get_graphql_content
from ...enums import TransactionEventTypeEnum
from .test_transaction_event_report import MUTATION_DATA_FRAGMENT

MUTATION_REPORT_NO_AMOUNT = (
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


def test_cancel_request_deduces_authorized(
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    authorized_value = Decimal(100)
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=authorized_value
    )
    psp_reference = "111-abc"
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CANCEL_REQUEST.name,
        "pspReference": psp_reference,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_REPORT_NO_AMOUNT,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert not transaction_report_data["errors"]

    event = TransactionEvent.objects.get(
        psp_reference=psp_reference, type=TransactionEventType.CANCEL_REQUEST
    )
    assert event.amount_value == authorized_value


def test_cancel_success_deduces_request(
    transaction_item_generator,
    transaction_events_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    authorized_value = Decimal(100)
    requested_amount = Decimal(30)
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=authorized_value
    )
    psp_reference = "111-abc"
    transaction_events_generator(
        transaction=transaction,
        psp_references=[psp_reference],
        types=[TransactionEventType.CANCEL_REQUEST],
        amounts=[requested_amount],
    )
    # The pending cancel request reduces the authorized balance, so the success
    # amount must be taken from the request, not from `authorized_value`.
    recalculate_transaction_amounts(transaction)
    assert transaction.authorized_value == authorized_value - requested_amount

    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CANCEL_SUCCESS.name,
        "pspReference": psp_reference,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_REPORT_NO_AMOUNT,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert not transaction_report_data["errors"]

    event = TransactionEvent.objects.get(
        psp_reference=psp_reference, type=TransactionEventType.CANCEL_SUCCESS
    )
    assert event.amount_value == requested_amount


def test_cancel_success_matches_psp_reference(
    transaction_item_generator,
    transaction_events_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    authorized_value = Decimal(100)
    matching_request_amount = Decimal(25)
    other_request_amount = Decimal(40)
    matching_psp_reference = "psp-A"
    other_psp_reference = "psp-B"
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=authorized_value
    )
    transaction_events_generator(
        transaction=transaction,
        psp_references=[matching_psp_reference, other_psp_reference],
        types=[
            TransactionEventType.CANCEL_REQUEST,
            TransactionEventType.CANCEL_REQUEST,
        ],
        amounts=[matching_request_amount, other_request_amount],
    )
    recalculate_transaction_amounts(transaction)

    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CANCEL_SUCCESS.name,
        "pspReference": matching_psp_reference,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_REPORT_NO_AMOUNT,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert not transaction_report_data["errors"]

    event = TransactionEvent.objects.get(
        psp_reference=matching_psp_reference,
        type=TransactionEventType.CANCEL_SUCCESS,
    )
    assert event.amount_value == matching_request_amount


def test_cancel_success_without_request(
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    authorized_value = Decimal(50)
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=authorized_value
    )
    psp_reference = "111-abc"
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": TransactionEventTypeEnum.CANCEL_SUCCESS.name,
        "pspReference": psp_reference,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_REPORT_NO_AMOUNT,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert not transaction_report_data["errors"]

    event = TransactionEvent.objects.get(
        psp_reference=psp_reference, type=TransactionEventType.CANCEL_SUCCESS
    )
    assert event.amount_value == authorized_value


@pytest.mark.parametrize(
    "event_type",
    [
        TransactionEventTypeEnum.CANCEL_REQUEST.name,
        TransactionEventTypeEnum.CANCEL_SUCCESS.name,
    ],
)
def test_cancel_nothing_to_cancel_error(
    event_type,
    transaction_item_generator,
    app_api_client,
    permission_manage_payments,
):
    # given
    transaction = transaction_item_generator(
        app=app_api_client.app, authorized_value=Decimal(0)
    )
    psp_reference = "111-abc"
    transaction_id = graphene.Node.to_global_id("TransactionItem", transaction.token)
    variables = {
        "id": transaction_id,
        "type": event_type,
        "pspReference": psp_reference,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_REPORT_NO_AMOUNT,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    response = get_graphql_content(response)
    transaction_report_data = response["data"]["transactionEventReport"]
    assert not transaction_report_data["transactionEvent"]
    errors = transaction_report_data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "amount"
    assert errors[0]["code"] == TransactionEventReportErrorCode.REQUIRED.name
