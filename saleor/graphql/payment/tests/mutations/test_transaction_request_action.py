from decimal import Decimal
from unittest.mock import patch

import graphene
import pytest

from .....checkout import CheckoutAuthorizeStatus
from .....checkout.payment_utils import update_checkout_payment_statuses
from .....giftcard import GiftCardEvents
from .....giftcard.const import GIFT_CARD_PAYMENT_GATEWAY_ID
from .....giftcard.models import GiftCardEvent
from .....order import OrderEvents
from .....payment import TransactionAction, TransactionEventType
from .....payment.interface import TransactionActionData
from .....payment.models import TransactionEvent, TransactionItem
from .....tests.e2e.utils import assign_permissions
from .....webhook.event_types import WebhookEventSyncType
from ....core.enums import TransactionRequestActionErrorCode
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
)
from ...enums import TransactionActionEnum

MUTATION_TRANSACTION_REQUEST_ACTION = """
mutation TransactionRequestAction(
    $id: ID
    $action_type: TransactionActionEnum!
    $amount: PositiveDecimal
    $refund_reason: String
    $refund_reason_reference: ID
    ){
    transactionRequestAction(
            id: $id,
            actionType: $action_type,
            amount: $amount,
            refundReason: $refund_reason,
            refundReasonReference: $refund_reason_reference
        ){
        transaction{
                id
                actions
                pspReference
                modifiedAt
                createdAt
                authorizedAmount{
                    amount
                    currency
                }
                chargedAmount{
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

MUTATION_TRANSACTION_REQUEST_ACTION_BY_TOKEN = """
mutation TransactionRequestAction(
    $token: UUID
    $action_type: TransactionActionEnum!
    $amount: PositiveDecimal
    $reason: String
    $reason_reference: ID
    ){
    transactionRequestAction(
            token: $token,
            actionType: $action_type,
            amount: $amount,
            refundReason: $reason,
            refundReasonReference: $reason_reference
        ){
        transaction{
                id
                actions
                pspReference
                modifiedAt
                createdAt
                authorizedAmount{
                    amount
                    currency
                }
                chargedAmount{
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


def test_transaction_request_action_missing_permission(
    app_api_client, order_with_lines, permission_manage_orders
):
    # given

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["charge", "cancel"],
        currency="USD",
        order_id=order_with_lines.pk,
        authorized_value=Decimal(10),
    )
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.CANCEL.name,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
        permissions=[permission_manage_orders],
    )

    # then
    assert_no_permission(response)


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
def test_transaction_request_action_missing_event(
    mocked_is_active,
    staff_api_client,
    permission_group_manage_orders,
    permission_manage_payments,
    permission_group_no_perms_all_channels,
    order,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    authorization_value = Decimal(10)
    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["charge", "cancel"],
        currency="USD",
        order_id=order.pk,
        authorized_value=authorization_value,
    )
    mocked_is_active.side_effect = [False, False]

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.CANCEL.name,
    }
    permission_group_no_perms_all_channels.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
        permissions=(permission_manage_payments,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["transactionRequestAction"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == (
        "No app or plugin is configured to handle payment action requests."
    )
    code_enum = TransactionRequestActionErrorCode
    assert data["errors"][0]["code"] == (
        code_enum.MISSING_TRANSACTION_ACTION_REQUEST_WEBHOOK.name
    )

    assert mocked_is_active.called


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_charge_requested")
def test_transaction_request_action_amount_with_lot_of_decimal_places(
    mocked_payment_action_request,
    mocked_is_active,
    order_with_lines,
    app_api_client,
    permission_manage_payments,
):
    # given
    mocked_is_active.side_effect = [True, False]

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=[],
        currency="USD",
        order_id=order_with_lines.pk,
        authorized_value=Decimal(10),
    )

    charge_amount = Decimal("9.12345678")
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.CHARGE.name,
        "amount": charge_amount,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    get_graphql_content(response)

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.CHARGE_REQUEST
    ).first()

    assert mocked_is_active.called
    assert request_event
    mocked_payment_action_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.CHARGE,
            action_value=round(charge_amount, 2),
            event=request_event,
            transaction_app_owner=None,
        ),
        order_with_lines.channel.slug,
    )

    event = order_with_lines.events.first()
    assert event.type == OrderEvents.TRANSACTION_CHARGE_REQUESTED
    assert Decimal(event.parameters["amount"]) == round(charge_amount, 2)
    assert event.parameters["reference"] == transaction.psp_reference

    assert TransactionEvent.objects.get(
        transaction=transaction,
        type=TransactionEventType.CHARGE_REQUEST,
        amount_value=round(charge_amount, 2),
    )


@pytest.mark.parametrize(
    ("charge_amount", "expected_called_charge_amount"),
    [
        (Decimal("8.00"), Decimal("8.00")),
        (None, Decimal("10.00")),
        (Decimal(100), Decimal("10.00")),
    ],
)
@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_charge_requested")
def test_transaction_request_charge_for_order(
    mocked_payment_action_request,
    mocked_is_active,
    charge_amount,
    expected_called_charge_amount,
    order_with_lines,
    app_api_client,
    permission_manage_payments,
    transaction_request_webhook,
    app,
):
    # given
    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED
    )
    mocked_is_active.return_value = False

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["charge", "cancel"],
        currency="USD",
        order_id=order_with_lines.pk,
        authorized_value=Decimal(10),
        app_identifier=transaction_request_webhook.app.identifier,
        app=transaction_request_webhook.app,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.CHARGE.name,
        "amount": charge_amount,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    get_graphql_content(response)

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.CHARGE_REQUEST,
    ).first()

    assert request_event
    assert mocked_is_active.called
    mocked_payment_action_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.CHARGE,
            action_value=expected_called_charge_amount,
            event=request_event,
            transaction_app_owner=transaction_request_webhook.app,
        ),
        order_with_lines.channel.slug,
    )

    event = order_with_lines.events.first()
    assert event.type == OrderEvents.TRANSACTION_CHARGE_REQUESTED
    assert Decimal(event.parameters["amount"]) == expected_called_charge_amount
    assert event.parameters["reference"] == transaction.psp_reference

    assert TransactionEvent.objects.get(
        transaction=transaction,
        type=TransactionEventType.CHARGE_REQUEST,
        amount_value=expected_called_charge_amount,
    )


@pytest.mark.parametrize(
    ("charge_amount", "expected_called_charge_amount"),
    [
        (Decimal("8.00"), Decimal("8.00")),
        (None, Decimal("10.00")),
        (Decimal(100), Decimal("10.00")),
    ],
)
@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_charge_requested")
def test_transaction_request_charge_for_order_via_token(
    mocked_payment_action_request,
    mocked_is_active,
    charge_amount,
    expected_called_charge_amount,
    order_with_lines,
    app_api_client,
    permission_manage_payments,
    transaction_request_webhook,
    app,
):
    # given
    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED
    )
    mocked_is_active.return_value = False

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["charge", "cancel"],
        currency="USD",
        order_id=order_with_lines.pk,
        authorized_value=Decimal(10),
        app_identifier=transaction_request_webhook.app.identifier,
        app=transaction_request_webhook.app,
    )

    variables = {
        "token": transaction.token,
        "action_type": TransactionActionEnum.CHARGE.name,
        "amount": charge_amount,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION_BY_TOKEN,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    get_graphql_content(response)

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.CHARGE_REQUEST,
    ).first()

    assert request_event
    assert mocked_is_active.called
    mocked_payment_action_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.CHARGE,
            action_value=expected_called_charge_amount,
            event=request_event,
            transaction_app_owner=transaction_request_webhook.app,
        ),
        order_with_lines.channel.slug,
    )

    event = order_with_lines.events.first()
    assert event.type == OrderEvents.TRANSACTION_CHARGE_REQUESTED
    assert Decimal(event.parameters["amount"]) == expected_called_charge_amount
    assert event.parameters["reference"] == transaction.psp_reference

    assert TransactionEvent.objects.get(
        transaction=transaction,
        type=TransactionEventType.CHARGE_REQUEST,
        amount_value=expected_called_charge_amount,
    )


@pytest.mark.parametrize(
    ("refund_amount", "expected_called_refund_amount"),
    [
        (Decimal("8.00"), Decimal("8.00")),
        (None, Decimal("10.00")),
        (Decimal(100), Decimal("10.00")),
    ],
)
@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_refund_requested")
def test_transaction_request_refund_for_order(
    mocked_payment_action_request,
    mocked_is_active,
    refund_amount,
    expected_called_refund_amount,
    order_with_lines,
    app_api_client,
    permission_manage_payments,
    transaction_request_webhook,
):
    # given
    mocked_is_active.return_value = False

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED
    )

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        order_id=order_with_lines.pk,
        charged_value=Decimal(10),
        app_identifier=transaction_request_webhook.app.identifier,
        app=transaction_request_webhook.app,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.REFUND.name,
        "amount": refund_amount,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    get_graphql_content(response)
    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.REFUND_REQUEST,
    ).first()
    assert request_event
    assert mocked_is_active.called
    mocked_payment_action_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.REFUND,
            action_value=expected_called_refund_amount,
            event=request_event,
            transaction_app_owner=transaction_request_webhook.app,
        ),
        order_with_lines.channel.slug,
    )

    event = order_with_lines.events.first()
    assert event.type == OrderEvents.TRANSACTION_REFUND_REQUESTED
    assert Decimal(event.parameters["amount"]) == expected_called_refund_amount
    assert event.parameters["reference"] == transaction.psp_reference

    assert TransactionEvent.objects.get(
        transaction=transaction,
        type=TransactionEventType.REFUND_REQUEST,
        amount_value=expected_called_refund_amount,
    )


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_cancelation_requested")
def test_transaction_request_cancelation_for_order(
    mocked_payment_action_request,
    mocked_is_active,
    order_with_lines,
    app_api_client,
    permission_manage_payments,
    transaction_request_webhook,
):
    # given
    mocked_is_active.return_value = False

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_CANCELATION_REQUESTED
    )

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["charge", "cancel"],
        currency="USD",
        order_id=order_with_lines.pk,
        authorized_value=Decimal(10),
        app_identifier=transaction_request_webhook.app.identifier,
        app=transaction_request_webhook.app,
    )
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.CANCEL.name,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    get_graphql_content(response)

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.CANCEL_REQUEST,
    ).first()

    assert request_event
    assert mocked_is_active.called
    mocked_payment_action_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.CANCEL,
            action_value=transaction.authorized_value,
            event=request_event,
            transaction_app_owner=transaction_request_webhook.app,
        ),
        order_with_lines.channel.slug,
    )

    event = order_with_lines.events.first()
    assert event.type == OrderEvents.TRANSACTION_CANCEL_REQUESTED
    assert event.parameters["reference"] == transaction.psp_reference

    assert TransactionEvent.objects.get(
        transaction=transaction,
        type=TransactionEventType.CANCEL_REQUEST,
        amount_value=transaction.authorized_value,
    )


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_cancelation_requested")
def test_transaction_request_cancelation_for_checkout(
    mocked_payment_action_request,
    mocked_is_active,
    checkout,
    app_api_client,
    permission_manage_payments,
    transaction_request_webhook,
):
    # given
    mocked_is_active.return_value = False

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_CANCELATION_REQUESTED
    )
    expected_amount = Decimal(10)
    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["charge", "cancel"],
        currency="USD",
        checkout_id=checkout.pk,
        authorized_value=expected_amount,
        app_identifier=transaction_request_webhook.app.identifier,
        app=transaction_request_webhook.app,
    )
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.CANCEL.name,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    get_graphql_content(response)

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.CANCEL_REQUEST,
    ).first()

    assert request_event
    assert mocked_is_active.called
    mocked_payment_action_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.CANCEL,
            action_value=expected_amount,
            event=request_event,
            transaction_app_owner=transaction_request_webhook.app,
        ),
        checkout.channel.slug,
    )

    assert TransactionEvent.objects.get(
        transaction=transaction,
        type=TransactionEventType.CANCEL_REQUEST,
        amount_value=expected_amount,
    )


@pytest.mark.parametrize(
    ("charge_amount", "expected_called_charge_amount"),
    [
        (Decimal("8.00"), Decimal("8.00")),
        (None, Decimal("10.00")),
        (Decimal(100), Decimal("10.00")),
    ],
)
@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_charge_requested")
def test_transaction_request_charge_for_checkout(
    mocked_payment_action_request,
    mocked_is_active,
    charge_amount,
    expected_called_charge_amount,
    checkout,
    app_api_client,
    permission_manage_payments,
    transaction_request_webhook,
):
    # given
    mocked_is_active.side_effect = [True, False]

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED
    )

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["charge", "cancel"],
        currency="USD",
        checkout_id=checkout.pk,
        authorized_value=Decimal(10),
        app_identifier=transaction_request_webhook.app.identifier,
        app=transaction_request_webhook.app,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.CHARGE.name,
        "amount": charge_amount,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    get_graphql_content(response)
    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.CHARGE_REQUEST,
    ).first()

    assert request_event
    assert mocked_is_active.called
    mocked_payment_action_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.CHARGE,
            action_value=expected_called_charge_amount,
            event=request_event,
            transaction_app_owner=transaction_request_webhook.app,
        ),
        checkout.channel.slug,
    )

    assert TransactionEvent.objects.get(
        transaction=transaction,
        type=TransactionEventType.CHARGE_REQUEST,
        amount_value=expected_called_charge_amount,
    )


@pytest.mark.parametrize(
    ("refund_amount", "expected_called_refund_amount"),
    [
        (Decimal("8.00"), Decimal("8.00")),
        (None, Decimal("10.00")),
        (Decimal(100), Decimal("10.00")),
    ],
)
@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_refund_requested")
def test_transaction_request_refund_for_checkout(
    mocked_payment_action_request,
    mocked_is_active,
    refund_amount,
    expected_called_refund_amount,
    checkout,
    app_api_client,
    permission_manage_payments,
    transaction_request_webhook,
):
    # given
    mocked_is_active.return_value = False

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED
    )

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        checkout_id=checkout.pk,
        charged_value=Decimal(10),
        app_identifier=transaction_request_webhook.app.identifier,
        app=transaction_request_webhook.app,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.REFUND.name,
        "amount": refund_amount,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    get_graphql_content(response)
    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.REFUND_REQUEST,
    ).first()

    assert request_event
    assert mocked_is_active.called
    mocked_payment_action_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.REFUND,
            action_value=expected_called_refund_amount,
            event=request_event,
            transaction_app_owner=transaction_request_webhook.app,
        ),
        checkout.channel.slug,
    )

    assert TransactionEvent.objects.get(
        transaction=transaction,
        type=TransactionEventType.REFUND_REQUEST,
        amount_value=expected_called_refund_amount,
    )


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_refund_requested")
def test_transaction_request_refund_when_app_reinstalled(
    mocked_payment_action_request,
    mocked_is_active,
    checkout,
    app_api_client,
    permission_manage_payments,
    transaction_request_webhook,
):
    # given
    refund_amount = Decimal("8.00")
    expected_called_refund_amount = Decimal("8.00")
    mocked_is_active.return_value = False

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED
    )

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        checkout_id=checkout.pk,
        charged_value=Decimal(10),
        app_identifier=transaction_request_webhook.app.identifier,
        app=None,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.REFUND.name,
        "amount": refund_amount,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    get_graphql_content(response)
    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.REFUND_REQUEST,
    ).first()

    assert request_event
    assert mocked_is_active.called
    mocked_payment_action_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.REFUND,
            action_value=expected_called_refund_amount,
            event=request_event,
            transaction_app_owner=transaction_request_webhook.app,
        ),
        checkout.channel.slug,
    )

    assert TransactionEvent.objects.get(
        transaction=transaction,
        type=TransactionEventType.REFUND_REQUEST,
        amount_value=expected_called_refund_amount,
    )


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_refund_requested")
def test_transaction_request_uses_handle_payment_permission(
    mocked_payment_action_request,
    mocked_is_active,
    checkout,
    app_api_client,
    permission_manage_payments,
    transaction_request_webhook,
):
    # given
    mocked_is_active.return_value = False

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED
    )

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        checkout_id=checkout.pk,
        charged_value=Decimal(10),
        app_identifier=transaction_request_webhook.app.identifier,
        app=transaction_request_webhook.app,
    )
    refund_amount = Decimal(1)
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.REFUND.name,
        "amount": refund_amount,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    get_graphql_content(response)

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.REFUND_REQUEST,
    ).first()

    assert request_event
    assert mocked_is_active.called
    mocked_payment_action_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction,
            action_type=TransactionAction.REFUND,
            action_value=refund_amount,
            event=request_event,
            transaction_app_owner=transaction_request_webhook.app,
        ),
        checkout.channel.slug,
    )


def test_transaction_request_missing_permission(
    app_api_client, order_with_lines, transaction_request_webhook
):
    # given

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_CANCELATION_REQUESTED
    )

    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["charge", "cancel"],
        currency="USD",
        order_id=order_with_lines.pk,
        authorized_value=Decimal(10),
        app_identifier=transaction_request_webhook.app.identifier,
        app=transaction_request_webhook.app,
    )
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.CANCEL.name,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION, variables, permissions=[]
    )

    # then
    assert_no_permission(response)


@patch("saleor.payment.gateway.get_webhooks_for_event")
@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
def test_transaction_request_missing_event(
    mocked_is_active,
    mocked_get_webhooks,
    staff_api_client,
    permission_manage_payments,
    permission_group_no_perms_all_channels,
    order,
    app,
):
    # given
    authorization_value = Decimal(10)
    transaction = TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["charge", "cancel"],
        currency="USD",
        order_id=order.pk,
        authorized_value=authorization_value,
        app_identifier=app.identifier,
        app=app,
    )

    mocked_get_webhooks.return_value = []
    mocked_is_active.return_value = False

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.CANCEL.name,
    }
    permission_group_no_perms_all_channels.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
        permissions=[
            permission_manage_payments,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["transactionRequestAction"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == (
        "No app or plugin is configured to handle payment action requests."
    )
    code_enum = TransactionRequestActionErrorCode
    assert data["errors"][0]["code"] == (
        code_enum.MISSING_TRANSACTION_ACTION_REQUEST_WEBHOOK.name
    )

    assert mocked_is_active.called
    assert mocked_get_webhooks.called
    mocked_get_webhooks.assert_called_once_with(
        event_type=WebhookEventSyncType.TRANSACTION_CANCELATION_REQUESTED,
        apps_ids=[app.id],
    )


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_refund_requested")
def test_transaction_request_refund_sets_app_to_request_event(
    mocked_payment_action_request,
    mocked_is_active,
    checkout,
    app_api_client,
    permission_manage_payments,
    transaction_request_webhook,
    transaction_item_generator,
):
    # given
    mocked_is_active.return_value = False

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        charged_value=Decimal(10),
        app=transaction_request_webhook.app,
    )
    refund_amount = Decimal(1)
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.REFUND.name,
        "amount": refund_amount,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    get_graphql_content(response)

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.REFUND_REQUEST,
    ).first()

    assert request_event
    assert request_event.app.id == app_api_client.app.id
    assert request_event.app_identifier == app_api_client.app.identifier
    assert request_event.user is None


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_refund_requested")
def test_transaction_request_refund_sets_user_to_request_event(
    mocked_payment_action_request,
    mocked_is_active,
    checkout,
    staff_api_client,
    permission_manage_payments,
    transaction_request_webhook,
    transaction_item_generator,
    permission_group_handle_payments,
):
    # given
    mocked_is_active.return_value = False

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        charged_value=Decimal(10),
        app=transaction_request_webhook.app,
    )
    refund_amount = Decimal(1)
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.REFUND.name,
        "amount": refund_amount,
    }
    staff_api_client.user.groups.add(permission_group_handle_payments)

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
    )

    # then
    get_graphql_content(response)

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.REFUND_REQUEST,
    ).first()

    assert request_event
    assert request_event.app is None
    assert request_event.app_identifier is None
    assert request_event.user == staff_api_client.user


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_charge_requested")
def test_transaction_request_charge_sets_app_to_request_event(
    mocked_payment_action_request,
    mocked_is_active,
    checkout,
    app_api_client,
    permission_manage_payments,
    transaction_request_webhook,
    transaction_item_generator,
):
    # given
    mocked_is_active.return_value = False

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        authorized_value=Decimal(10),
        app=transaction_request_webhook.app,
    )
    amount = Decimal(1)
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.CHARGE.name,
        "amount": amount,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    get_graphql_content(response)

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.CHARGE_REQUEST,
    ).first()

    assert request_event
    assert request_event.app.id == app_api_client.app.id
    assert request_event.app_identifier == app_api_client.app.identifier
    assert request_event.user is None


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_charge_requested")
def test_transaction_request_charge_sets_user_to_request_event(
    mocked_payment_action_request,
    mocked_is_active,
    checkout,
    staff_api_client,
    permission_manage_payments,
    transaction_request_webhook,
    transaction_item_generator,
    permission_group_handle_payments,
):
    # given
    mocked_is_active.return_value = False

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        authorized_value=Decimal(10),
        app=transaction_request_webhook.app,
    )
    amount = Decimal(1)
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.CHARGE.name,
        "amount": amount,
    }
    staff_api_client.user.groups.add(permission_group_handle_payments)

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
    )

    # then
    get_graphql_content(response)

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.CHARGE_REQUEST,
    ).first()

    assert request_event
    assert request_event.app is None
    assert request_event.app_identifier is None
    assert request_event.user == staff_api_client.user


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_cancelation_requested")
def test_transaction_request_cancel_sets_app_to_request_event(
    mocked_payment_action_request,
    mocked_is_active,
    checkout,
    app_api_client,
    permission_manage_payments,
    transaction_request_webhook,
    transaction_item_generator,
):
    # given
    mocked_is_active.return_value = False

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_CANCELATION_REQUESTED
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        authorized_value=Decimal(10),
        app=transaction_request_webhook.app,
    )
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.CANCEL.name,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    get_graphql_content(response)

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.CANCEL_REQUEST,
    ).first()

    assert request_event
    assert request_event.app.id == app_api_client.app.id
    assert request_event.app_identifier == app_api_client.app.identifier
    assert request_event.user is None


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_cancelation_requested")
def test_transaction_request_cancel_sets_user_to_request_event(
    mocked_payment_action_request,
    mocked_is_active,
    checkout,
    staff_api_client,
    permission_manage_payments,
    transaction_request_webhook,
    transaction_item_generator,
    permission_group_handle_payments,
):
    # given
    mocked_is_active.return_value = False

    transaction_request_webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_CANCELATION_REQUESTED
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk,
        authorized_value=Decimal(10),
        app=transaction_request_webhook.app,
    )
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.CANCEL.name,
    }
    staff_api_client.user.groups.add(permission_group_handle_payments)

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
    )

    # then
    get_graphql_content(response)

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.CANCEL_REQUEST,
    ).first()

    assert request_event
    assert request_event.app is None
    assert request_event.app_identifier is None
    assert request_event.user == staff_api_client.user


@pytest.mark.parametrize(
    (
        "amount",
        "expected_cancel_amount",
        "expected_authorize_status",
        "expected_available_actions",
    ),
    [
        (None, Decimal(10), CheckoutAuthorizeStatus.NONE, []),
        (
            Decimal(1),
            Decimal(1),
            CheckoutAuthorizeStatus.PARTIAL,
            [TransactionAction.CANCEL],
        ),
        (Decimal(10), Decimal(10), CheckoutAuthorizeStatus.NONE, []),
        (Decimal(11), Decimal(10), CheckoutAuthorizeStatus.NONE, []),
    ],
)
def test_transaction_request_cancelation_for_checkout_gift_card_authorization(
    amount,
    expected_cancel_amount,
    expected_authorize_status,
    expected_available_actions,
    checkout_with_prices,
    gift_card_created_by_staff,
    transaction_item_generator,
    staff_api_client,
    permission_manage_payments,
):
    # given
    assign_permissions(staff_api_client, [permission_manage_payments])

    checkout = checkout_with_prices

    transaction = transaction_item_generator(
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        checkout_id=checkout.pk,
        gift_card=gift_card_created_by_staff,
        authorized_value=Decimal(10),
        available_actions=[TransactionAction.CANCEL],
    )
    assert transaction.gift_card is not None

    update_checkout_payment_statuses(
        checkout, checkout.total.gross, checkout_has_lines=True
    )

    checkout.refresh_from_db()
    assert checkout.authorize_status == CheckoutAuthorizeStatus.PARTIAL

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.CANCEL.name,
        "amount": amount,
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["transactionRequestAction"]["errors"] == []

    transaction.refresh_from_db()
    checkout.refresh_from_db()

    assert transaction.authorized_value == Decimal(10) - expected_cancel_amount
    assert transaction.charged_value == Decimal(0)
    assert transaction.gift_card is not None
    assert transaction.available_actions == expected_available_actions
    assert checkout.authorize_status == expected_authorize_status

    TransactionEvent.objects.get(
        transaction=transaction,
        type=TransactionEventType.CANCEL_REQUEST,
        amount_value=expected_cancel_amount,
    )

    TransactionEvent.objects.get(
        transaction=transaction,
        type=TransactionEventType.CANCEL_SUCCESS,
        amount_value=expected_cancel_amount,
    )


def test_transaction_request_cancelation_fails_when_cancel_action_is_not_available(
    checkout_with_prices,
    gift_card_created_by_staff,
    transaction_item_generator,
    staff_api_client,
    permission_manage_payments,
):
    # given
    assign_permissions(staff_api_client, [permission_manage_payments])

    checkout = checkout_with_prices

    transaction = transaction_item_generator(
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        checkout_id=checkout.pk,
        gift_card=gift_card_created_by_staff,
        authorized_value=gift_card_created_by_staff.current_balance_amount,
        available_actions=[],
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.CANCEL.name,
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["transactionRequestAction"]["errors"] == []

    TransactionEvent.objects.get(
        transaction=transaction,
        type=TransactionEventType.CANCEL_REQUEST,
        amount_value=gift_card_created_by_staff.current_balance_amount,
    )

    TransactionEvent.objects.get(
        transaction=transaction,
        type=TransactionEventType.CANCEL_FAILURE,
        amount_value=gift_card_created_by_staff.current_balance_amount,
    )


def test_transaction_request_cancelation_for_type_other_than_checkout(
    order_with_lines,
    gift_card_created_by_staff,
    transaction_item_generator,
    staff_api_client,
    permission_manage_payments,
):
    # given
    assign_permissions(staff_api_client, [permission_manage_payments])

    order = order_with_lines

    transaction = transaction_item_generator(
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        order_id=order.pk,
        gift_card=gift_card_created_by_staff,
        authorized_value=gift_card_created_by_staff.current_balance_amount,
        available_actions=[TransactionAction.CANCEL],
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.CANCEL.name,
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["transactionRequestAction"]["errors"] == []

    transaction.refresh_from_db()

    assert (
        transaction.authorized_value
        == gift_card_created_by_staff.current_balance_amount
    )
    assert transaction.charged_value == Decimal(0)
    assert transaction.gift_card is not None
    assert transaction.available_actions == [TransactionAction.CANCEL]

    TransactionEvent.objects.get(
        transaction=transaction,
        type=TransactionEventType.CANCEL_REQUEST,
        amount_value=gift_card_created_by_staff.current_balance_amount,
    )

    TransactionEvent.objects.get(
        transaction=transaction,
        type=TransactionEventType.CANCEL_FAILURE,
        amount_value=gift_card_created_by_staff.current_balance_amount,
    )


@pytest.mark.parametrize(
    ("amount", "expected_refund_amount", "expected_available_actions"),
    [
        (None, Decimal(10), []),
        (Decimal(1), Decimal(1), [TransactionAction.REFUND]),
        (Decimal(10), Decimal(10), []),
        (Decimal(11), Decimal(10), []),
    ],
)
def test_transaction_request_refund_for_order_gift_card_charge(
    amount,
    expected_refund_amount,
    expected_available_actions,
    order_with_lines,
    gift_card_created_by_staff,
    transaction_item_generator,
    staff_api_client,
    permission_manage_payments,
):
    # given
    assign_permissions(staff_api_client, [permission_manage_payments])

    order = order_with_lines

    gift_card_created_by_staff.current_balance_amount = Decimal(0)
    gift_card_created_by_staff.save(update_fields=["current_balance_amount"])

    transaction = transaction_item_generator(
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        order_id=order.pk,
        gift_card=gift_card_created_by_staff,
        charged_value=Decimal(10),
        available_actions=[TransactionAction.REFUND],
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.REFUND.name,
        "amount": amount,
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["transactionRequestAction"]["errors"] == []

    transaction.refresh_from_db()
    gift_card_created_by_staff.refresh_from_db()

    assert transaction.authorized_value == Decimal(0)
    assert transaction.charged_value == Decimal(10) - expected_refund_amount
    assert transaction.refunded_value == expected_refund_amount
    assert transaction.gift_card is not None
    assert transaction.available_actions == expected_available_actions
    assert gift_card_created_by_staff.current_balance_amount == expected_refund_amount

    TransactionEvent.objects.get(
        transaction=transaction,
        type=TransactionEventType.REFUND_REQUEST,
        amount_value=expected_refund_amount,
    )

    TransactionEvent.objects.get(
        transaction=transaction,
        type=TransactionEventType.REFUND_SUCCESS,
        amount_value=expected_refund_amount,
    )

    gift_card_event = GiftCardEvent.objects.get(
        gift_card=gift_card_created_by_staff,
        type=GiftCardEvents.REFUNDED_IN_ORDER,
    )
    assert gift_card_event.order == order
    assert Decimal(gift_card_event.parameters["balance"]["current_balance"]) == (
        expected_refund_amount
    )
    assert Decimal(gift_card_event.parameters["balance"]["old_current_balance"]) == (
        Decimal(0)
    )


def test_transaction_request_refund_for_order_gift_card_charge_when_gift_card_does_not_exist_anymore(
    order_with_lines,
    transaction_item_generator,
    staff_api_client,
    permission_manage_payments,
):
    # given
    assign_permissions(staff_api_client, [permission_manage_payments])

    order = order_with_lines
    amount = Decimal(10)

    transaction = transaction_item_generator(
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        order_id=order.pk,
        gift_card=None,
        charged_value=amount,
        available_actions=[TransactionAction.REFUND],
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction.token),
        "action_type": TransactionActionEnum.REFUND.name,
        "amount": amount,
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_TRANSACTION_REQUEST_ACTION,
        variables,
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["transactionRequestAction"]["errors"] == []

    transaction.refresh_from_db()

    assert transaction.charged_value == amount
    assert transaction.refunded_value == Decimal(0)
    assert transaction.gift_card is None
    assert transaction.available_actions == [TransactionAction.REFUND]

    assert not GiftCardEvent.objects.filter(
        type=GiftCardEvents.REFUNDED_IN_ORDER
    ).exists()

    TransactionEvent.objects.get(
        transaction=transaction,
        type=TransactionEventType.REFUND_REQUEST,
        amount_value=amount,
    )

    TransactionEvent.objects.get(
        transaction=transaction,
        type=TransactionEventType.REFUND_FAILURE,
        amount_value=amount,
        message="Gift card could not be found.",
    )
