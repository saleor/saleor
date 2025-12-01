import datetime
from decimal import Decimal
from unittest import mock
from uuid import uuid4

import graphene
import pytest
from django.conf import settings
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time

from .....channel import TransactionFlowStrategy
from .....checkout import CheckoutAuthorizeStatus, CheckoutChargeStatus
from .....checkout.calculations import fetch_checkout_data
from .....checkout.complete_checkout import create_order_from_checkout
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.models import Checkout
from .....core.prices import Money, quantize_price
from .....giftcard.const import GIFT_CARD_PAYMENT_GATEWAY_ID
from .....order import OrderAuthorizeStatus, OrderChargeStatus, OrderStatus
from .....order.models import Order
from .....payment import (
    TransactionAction,
    TransactionEventType,
    TransactionItemIdempotencyUniqueError,
)
from .....payment.interface import (
    PaymentGatewayData,
    TransactionProcessActionData,
    TransactionSessionData,
    TransactionSessionResult,
)
from .....payment.lock_objects import (
    get_checkout_and_transaction_item_locked_for_update,
    get_order_and_transaction_item_locked_for_update,
)
from .....payment.models import Payment, TransactionItem
from .....plugins.manager import get_plugins_manager
from .....tests import race_condition
from .....webhook.event_types import WebhookEventSyncType
from .....webhook.models import Webhook
from .....webhook.transport.utils import generate_cache_key_for_webhook
from ....channel.enums import TransactionFlowStrategyEnum
from ....core.enums import TransactionInitializeErrorCode
from ....core.utils import to_global_id_or_none
from ....tests.utils import assert_no_permission, get_graphql_content

TRANSACTION_INITIALIZE = """
mutation TransactionInitialize(
  $action: TransactionFlowStrategyEnum,
  $amount: PositiveDecimal,
  $id: ID!,
  $paymentGateway: PaymentGatewayToInitialize!
  $customerIpAddress: String
  $idempotencyKey: String
) {
  transactionInitialize(
    action: $action
    amount: $amount
    id: $id
    paymentGateway: $paymentGateway
    customerIpAddress: $customerIpAddress
    idempotencyKey: $idempotencyKey
  ) {
    data
    transaction {
      id
      authorizedAmount {
        currency
        amount
      }
      chargedAmount {
        currency
        amount
      }
      chargePendingAmount {
        amount
        currency
      }
      authorizePendingAmount {
        amount
        currency
      }
    }
    transactionEvent {
      amount {
        currency
        amount
      }
      type
      createdBy {
        ... on App {
          id
        }
      }
      pspReference
      message
      externalUrl
    }
    errors{
      field
      message
      code
    }
  }
}
"""


def _assert_fields(
    content,
    source_object,
    expected_amount,
    expected_psp_reference,
    response_event_type,
    app_identifier,
    mocked_initialize=None,
    request_event_type=TransactionEventType.CHARGE_REQUEST,
    action_type=TransactionFlowStrategy.CHARGE,
    request_event_include_in_calculations=False,
    authorized_value=Decimal(0),
    charged_value=Decimal(0),
    charge_pending_value=Decimal(0),
    authorize_pending_value=Decimal(0),
    returned_data=None,
    expected_message=None,
    gift_card=None,
    available_actions=None,
):
    assert not content["data"]["transactionInitialize"]["errors"]
    response_data = content["data"]["transactionInitialize"]
    assert response_data["data"] == returned_data
    transaction_data = response_data["transaction"]
    transaction = source_object.payment_transactions.last()
    assert transaction
    assert (
        quantize_price(
            Decimal(transaction_data["authorizePendingAmount"]["amount"]),
            source_object.currency,
        )
        == authorize_pending_value
        == transaction.authorize_pending_value
    )
    assert (
        quantize_price(
            Decimal(transaction_data["authorizedAmount"]["amount"]),
            source_object.currency,
        )
        == authorized_value
        == transaction.authorized_value
    )
    assert (
        quantize_price(
            Decimal(transaction_data["chargePendingAmount"]["amount"]),
            source_object.currency,
        )
        == charge_pending_value
        == transaction.charge_pending_value
    )

    assert (
        quantize_price(
            Decimal(transaction_data["chargedAmount"]["amount"]), source_object.currency
        )
        == charged_value
    )
    assert charged_value == transaction.charged_value

    assert response_data["transactionEvent"]
    assert response_data["transactionEvent"]["type"] == response_event_type.upper()
    assert (
        quantize_price(
            Decimal(response_data["transactionEvent"]["amount"]["amount"]),
            source_object.currency,
        )
        == expected_amount
    )

    request_event = transaction.events.filter(type=request_event_type).first()
    assert request_event

    assert request_event.amount_value == expected_amount
    assert (
        request_event.include_in_calculations == request_event_include_in_calculations
    )
    assert request_event.psp_reference == expected_psp_reference
    response_event = transaction.events.filter(type=response_event_type).first()
    assert response_event
    assert response_event.amount_value == expected_amount
    assert response_event.include_in_calculations
    assert response_event.psp_reference == expected_psp_reference
    if expected_message is not None:
        assert response_event.message == expected_message

    if mocked_initialize:
        mocked_initialize.assert_called_with(
            TransactionSessionData(
                transaction=transaction,
                source_object=source_object,
                action=TransactionProcessActionData(
                    action_type=action_type,
                    amount=expected_amount,
                    currency=source_object.currency,
                ),
                customer_ip_address="127.0.0.1",
                payment_gateway_data=PaymentGatewayData(
                    app_identifier=app_identifier, data=None, error=None
                ),
                idempotency_key=request_event.idempotency_key,
            )
        )

    assert transaction.gift_card == gift_card
    assert transaction.app_identifier == app_identifier

    available_actions = available_actions if available_actions else []
    assert transaction.available_actions == available_actions


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_for_checkout_without_payment_gateway_data(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
):
    # given
    checkout = checkout_with_prices
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = "CHARGE_SUCCESS"
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=expected_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        charged_value=expected_amount,
        returned_data=expected_response["data"],
    )
    assert checkout.charge_status == CheckoutChargeStatus.PARTIAL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.PARTIAL


@override_settings(TRANSACTION_ITEMS_LIMIT=3)
def test_for_checkout_transactions_limit_on_transaction_initialize(
    user_api_client, checkout_with_prices
):
    # given
    TransactionItem.objects.bulk_create(
        [
            TransactionItem(
                checkout=checkout_with_prices, currency=checkout_with_prices.currency
            )
            for _ in range(settings.TRANSACTION_ITEMS_LIMIT)
        ]
    )

    variables = {
        "action": None,
        "amount": 99,
        "id": to_global_id_or_none(checkout_with_prices),
        "paymentGateway": {"id": "any", "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["transactionInitialize"]
    assert data["errors"]
    error = data["errors"][0]
    assert error["code"] == TransactionInitializeErrorCode.INVALID.name
    assert error["field"] == "id"
    assert error["message"] == (
        f"Checkout transactions limit of {settings.TRANSACTION_ITEMS_LIMIT} reached."
    )


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_for_checkout_with_idempotency_key(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
):
    # given
    checkout = checkout_with_prices
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = "CHARGE_SUCCESS"
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )
    idempotency_key = "ABC"

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
        "idempotencyKey": idempotency_key,
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=expected_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        charged_value=expected_amount,
        returned_data=expected_response["data"],
    )
    transaction = checkout.payment_transactions.last()
    assert transaction.idempotency_key == idempotency_key
    assert transaction.events.first().idempotency_key == idempotency_key


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_for_checkout_amount_with_lot_of_decimal_places(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
):
    # given
    checkout = checkout_with_prices
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("9.8888888889")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = "CHARGE_SUCCESS"
    expected_response["pspReference"] = expected_psp_reference
    expected_response["amount"] = round(expected_amount, 2)
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    transaction_item = checkout.payment_transactions.last()
    mocked_initialize.assert_called_once_with(
        TransactionSessionData(
            transaction=transaction_item,
            source_object=checkout,
            payment_gateway_data=mock.ANY,
            action=TransactionProcessActionData(
                action_type=TransactionFlowStrategy.CHARGE,
                currency=checkout.currency,
                amount=round(expected_amount, 2),
            ),
            idempotency_key=mock.ANY,
            customer_ip_address=mock.ANY,
        )
    )
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=round(expected_amount, 2),
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        charged_value=round(expected_amount, 2),
        returned_data=expected_response["data"],
    )


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_for_checkout_with_multiple_calls_and_idempotency_key(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
):
    # given
    checkout = checkout_with_prices
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = "CHARGE_SUCCESS"
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )
    idempotency_key = "ABC"

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
        "idempotencyKey": idempotency_key,
    }
    user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=expected_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        charged_value=expected_amount,
        returned_data=expected_response["data"],
    )
    assert checkout.payment_transactions.count() == 1
    transaction = checkout.payment_transactions.last()
    assert transaction.idempotency_key == idempotency_key
    assert transaction.events.count() == 2
    assert transaction.events.first().idempotency_key == idempotency_key


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_for_order_with_multiple_calls_and_idempotency_key(
    mocked_initialize,
    user_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
):
    # given
    order = order_with_lines
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = "CHARGE_SUCCESS"
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )
    idempotency_key = "ABC"

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(order),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
        "idempotencyKey": idempotency_key,
    }
    user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    _assert_fields(
        content=content,
        source_object=order,
        expected_amount=expected_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        charged_value=expected_amount,
        returned_data=expected_response["data"],
    )
    order.refresh_from_db()
    assert order.payment_transactions.count() == 1
    transaction = order.payment_transactions.last()
    assert transaction.idempotency_key == idempotency_key
    assert transaction.events.count() == 2
    assert transaction.events.first().idempotency_key == idempotency_key


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_for_order_with_idempotency_key(
    mocked_initialize,
    user_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
):
    # given
    order = order_with_lines
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = "CHARGE_SUCCESS"
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )
    idempotency_key = "ABC"

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(order),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
        "idempotencyKey": idempotency_key,
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    _assert_fields(
        content=content,
        source_object=order,
        expected_amount=expected_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        charged_value=expected_amount,
        returned_data=expected_response["data"],
    )
    order.refresh_from_db()
    transaction = order.payment_transactions.last()
    assert transaction.idempotency_key == idempotency_key
    assert transaction.events.first().idempotency_key == idempotency_key


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_for_order_without_payment_gateway_data(
    mocked_initialize,
    user_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
):
    # given
    order = order_with_lines
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = "CHARGE_SUCCESS"
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(order),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    _assert_fields(
        content=content,
        source_object=order,
        expected_amount=expected_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        charged_value=expected_amount,
        returned_data=expected_response["data"],
    )
    order.refresh_from_db()
    assert order.total_authorized_amount == Decimal(0)
    assert order.total_charged_amount == expected_amount


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_checkout_with_pending_amount(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
):
    # given
    checkout = checkout_with_prices
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = TransactionEventType.CHARGE_REQUEST.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=expected_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_REQUEST,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        charge_pending_value=expected_amount,
        request_event_include_in_calculations=True,
        returned_data=expected_response["data"],
    )
    assert checkout.charge_status == CheckoutChargeStatus.PARTIAL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.PARTIAL


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_order_with_pending_amount(
    mocked_initialize,
    user_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
):
    # given
    order = order_with_lines
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = TransactionEventType.CHARGE_REQUEST.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(order),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    _assert_fields(
        content=content,
        source_object=order,
        expected_amount=expected_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_REQUEST,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        charge_pending_value=expected_amount,
        request_event_include_in_calculations=True,
        returned_data=expected_response["data"],
    )

    order.refresh_from_db()
    assert order.total_authorized_amount == Decimal(0)
    assert order.total_charged_amount == Decimal(0)


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_checkout_with_action_required_response(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
):
    # given
    checkout = checkout_with_prices
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = TransactionEventType.CHARGE_ACTION_REQUIRED.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=expected_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_ACTION_REQUIRED,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        returned_data=expected_response["data"],
    )
    assert checkout.charge_status == CheckoutChargeStatus.NONE
    assert checkout.authorize_status == CheckoutAuthorizeStatus.NONE


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_order_with_action_required_response(
    mocked_initialize,
    user_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
):
    # given
    order = order_with_lines
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = TransactionEventType.CHARGE_ACTION_REQUIRED.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(order),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    _assert_fields(
        content=content,
        source_object=order,
        expected_amount=expected_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_ACTION_REQUIRED,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        returned_data=expected_response["data"],
    )

    order.refresh_from_db()
    assert order.total_authorized_amount == Decimal(0)
    assert order.total_charged_amount == Decimal(0)


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_checkout_with_action_required_response_and_missing_psp_reference(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
):
    # given
    checkout = checkout_with_prices
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("10.00")
    expected_response = transaction_session_response.copy()
    expected_response["result"] = TransactionEventType.CHARGE_ACTION_REQUIRED.upper()
    del expected_response["pspReference"]
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=expected_amount,
        expected_psp_reference=None,
        response_event_type=TransactionEventType.CHARGE_ACTION_REQUIRED,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        returned_data=expected_response["data"],
    )
    assert checkout.charge_status == CheckoutChargeStatus.NONE
    assert checkout.authorize_status == CheckoutAuthorizeStatus.NONE


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_order_with_action_required_response_and_missing_psp_reference(
    mocked_initialize,
    user_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
):
    # given
    order = order_with_lines
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("10.00")
    expected_response = transaction_session_response.copy()
    expected_response["result"] = TransactionEventType.CHARGE_ACTION_REQUIRED.upper()
    del expected_response["pspReference"]
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(order),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    _assert_fields(
        content=content,
        source_object=order,
        expected_amount=expected_amount,
        expected_psp_reference=None,
        response_event_type=TransactionEventType.CHARGE_ACTION_REQUIRED,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        returned_data=expected_response["data"],
    )

    order.refresh_from_db()
    assert order.total_authorized_amount == Decimal(0)
    assert order.total_charged_amount == Decimal(0)


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_checkout_when_amount_is_not_provided(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    plugins_manager,
):
    # given
    checkout = checkout_with_prices
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["amount"] = str(checkout_info.checkout.total_gross_amount)
    expected_response["result"] = TransactionEventType.CHARGE_SUCCESS.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": None,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=checkout.total_gross_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        charged_value=checkout.total_gross_amount,
        returned_data=expected_response["data"],
    )
    assert checkout.charge_status == CheckoutChargeStatus.FULL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_order_when_amount_is_not_provided(
    mocked_initialize,
    user_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
):
    # given
    order = order_with_lines
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = TransactionEventType.CHARGE_SUCCESS.upper()
    expected_response["amount"] = str(order.total_gross_amount)
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": None,
        "id": to_global_id_or_none(order),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    _assert_fields(
        content=content,
        source_object=order,
        expected_amount=order.total_gross_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        charged_value=order.total_gross_amount,
        returned_data=expected_response["data"],
    )

    order.refresh_from_db()
    assert order.total_authorized_amount == Decimal(0)
    assert order.total_charged_amount == order.total_gross_amount


@pytest.mark.parametrize(
    ("auto_order_confirmation", "excpected_order_status"),
    [
        (True, OrderStatus.UNFULFILLED),
        (False, OrderStatus.UNCONFIRMED),
    ],
)
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_order_status_with_order_confirmation(
    mocked_initialize,
    auto_order_confirmation,
    excpected_order_status,
    user_api_client,
    unconfirmed_order_with_lines,
    webhook_app,
    transaction_session_response,
):
    # given
    order = unconfirmed_order_with_lines
    order.channel.automatically_confirm_all_new_orders = auto_order_confirmation
    order.channel.save(update_fields=["automatically_confirm_all_new_orders"])
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = TransactionEventType.CHARGE_SUCCESS.upper()
    expected_response["amount"] = str(order.total_gross_amount)
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "amount": order.total_gross_amount,
        "id": to_global_id_or_none(order),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    _assert_fields(
        content=content,
        source_object=order,
        expected_amount=order.total_gross_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        charged_value=order.total_gross_amount,
        returned_data=expected_response["data"],
    )

    assert order.status == OrderStatus.UNCONFIRMED
    assert not order.is_fully_paid()
    order.refresh_from_db()
    assert order.is_fully_paid()
    assert order.total_authorized_amount == Decimal(0)
    assert order.total_charged_amount == order.total_gross_amount
    assert order.status == excpected_order_status
    assert order.charge_status == OrderChargeStatus.FULL


@pytest.mark.parametrize(
    "auto_order_confirmation",
    [True, False],
)
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_draft_order_status_with_order_confirmation(
    mocked_initialize,
    auto_order_confirmation,
    user_api_client,
    draft_order,
    webhook_app,
    transaction_session_response,
):
    # given
    order = draft_order
    order.channel.automatically_confirm_all_new_orders = auto_order_confirmation
    order.channel.save(update_fields=["automatically_confirm_all_new_orders"])
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = TransactionEventType.CHARGE_SUCCESS.upper()
    expected_response["amount"] = str(order.total_gross_amount)
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "amount": order.total_gross_amount,
        "id": to_global_id_or_none(order),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    _assert_fields(
        content=content,
        source_object=order,
        expected_amount=order.total_gross_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        charged_value=order.total_gross_amount,
        returned_data=expected_response["data"],
    )

    assert not order.is_fully_paid()
    order.refresh_from_db()
    assert order.is_fully_paid()
    assert order.total_authorized_amount == Decimal(0)
    assert order.total_charged_amount == order.total_gross_amount
    assert order.status == OrderStatus.DRAFT
    assert order.charge_status == OrderChargeStatus.FULL


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_order_with_transaction_when_amount_is_not_provided(
    mocked_initialize,
    user_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
    transaction_item_generator,
):
    # given
    order = order_with_lines
    expected_charged_amount = Decimal(10)
    expected_authorized_amount = Decimal(3)
    transaction_item_generator(
        order_id=order.pk,
        charged_value=expected_charged_amount,
        authorized_value=expected_authorized_amount,
    )
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = TransactionEventType.CHARGE_SUCCESS.upper()
    expected_response["amount"] = str(
        order.total_gross_amount - expected_charged_amount
    )
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": None,
        "id": to_global_id_or_none(order),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    _assert_fields(
        content=content,
        source_object=order,
        expected_amount=order.total_gross_amount - expected_charged_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        charged_value=order.total_gross_amount - expected_charged_amount,
        returned_data=expected_response["data"],
    )

    order.refresh_from_db()
    assert order.total_authorized_amount == expected_authorized_amount
    assert order.total_charged_amount == order.total_gross_amount


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_checkout_with_transaction_when_amount_is_not_provided(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    transaction_item_generator,
    plugins_manager,
):
    # given
    checkout = checkout_with_prices
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)
    checkout = checkout_info.checkout

    expected_charged_amount = Decimal(10)
    expected_authorized_amount = Decimal(3)
    transaction_item_generator(
        checkout_id=checkout.pk,
        charged_value=expected_charged_amount,
        authorized_value=expected_authorized_amount,
    )
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = TransactionEventType.CHARGE_SUCCESS.upper()
    expected_response["amount"] = str(
        checkout.total_gross_amount - expected_charged_amount
    )
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": None,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=checkout.total_gross_amount - expected_charged_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        charged_value=checkout.total_gross_amount - expected_charged_amount,
        returned_data=expected_response["data"],
    )
    assert checkout.charge_status == CheckoutChargeStatus.FULL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_app_with_action_field_and_handle_payments(
    mocked_initialize,
    app_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    permission_manage_payments,
    plugins_manager,
):
    # given
    checkout = checkout_with_prices
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)

    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()
    app_api_client.app.permissions.set([permission_manage_payments])

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = TransactionEventType.AUTHORIZATION_SUCCESS.upper()
    expected_response["amount"] = str(checkout.total_gross_amount)
    expected_response["pspReference"] = expected_psp_reference
    del expected_response["data"]
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": TransactionFlowStrategyEnum.AUTHORIZATION.name,
        "amount": None,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = app_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=checkout.total_gross_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.AUTHORIZATION_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        request_event_type=TransactionEventType.AUTHORIZATION_REQUEST,
        authorized_value=checkout.total_gross_amount,
        action_type=TransactionFlowStrategy.AUTHORIZATION,
        returned_data=None,
    )
    assert checkout.charge_status == CheckoutChargeStatus.NONE
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_uses_default_channel_action(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
):
    # given
    checkout = checkout_with_prices
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    channel = checkout.channel
    channel.default_transaction_flow_strategy = TransactionFlowStrategy.AUTHORIZATION
    channel.save()

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = "CHARGE_SUCCESS"
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=expected_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        charged_value=expected_amount,
        action_type=TransactionFlowStrategy.AUTHORIZATION,
        request_event_type=TransactionEventType.AUTHORIZATION_REQUEST,
        returned_data=expected_response["data"],
    )


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_transaction_initialize_for_already_used_idempotency_key(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_item_generator,
    transaction_session_response,
):
    # given
    checkout = checkout_with_prices
    idempotency_key = "ABC"

    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    already_existing_transaction = transaction_item_generator(app=webhook_app)
    already_existing_transaction.idempotency_key = idempotency_key
    already_existing_transaction.save()

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = "CHARGE_SUCCESS"
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
        "idempotencyKey": idempotency_key,
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["transactionInitialize"]
    assert data["errors"]
    assert data["errors"][0]["code"] == TransactionInitializeErrorCode.UNIQUE.name
    assert data["errors"][0]["field"] == "idempotencyKey"
    mocked_initialize.assert_not_called()


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_transaction_initialize_for_already_used_idempotency_key_and_different_input(
    mocked_initialize,
    user_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
):
    # given
    order = order_with_lines
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    first_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = "CHARGE_SUCCESS"
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )
    idempotency_key = "ABC"

    variables = {
        "action": None,
        "amount": first_amount,
        "id": to_global_id_or_none(order),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
        "idempotencyKey": idempotency_key,
    }
    user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    variables["amount"] = Decimal("20.00")

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["transactionInitialize"]
    assert data["errors"]
    assert data["errors"][0]["code"] == TransactionInitializeErrorCode.UNIQUE.name
    assert data["errors"][0]["field"] == "idempotencyKey"

    assert order.payment_transactions.count() == 1
    transaction = order.payment_transactions.last()
    request_event = transaction.events.first()
    mocked_initialize.assert_called_with(
        TransactionSessionData(
            transaction=transaction,
            source_object=order,
            action=TransactionProcessActionData(
                action_type=TransactionFlowStrategy.CHARGE,
                amount=first_amount,
                currency=order.currency,
            ),
            payment_gateway_data=PaymentGatewayData(
                app_identifier=expected_app_identifier, data=None, error=None
            ),
            idempotency_key=request_event.idempotency_key,
            customer_ip_address="127.0.0.1",
        )
    )


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_transaction_initialize_for_empty_string_as_idempotency_key(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_item_generator,
    transaction_session_response,
):
    # given
    checkout = checkout_with_prices
    idempotency_key = ""

    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = "CHARGE_SUCCESS"
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
        "idempotencyKey": idempotency_key,
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["transactionInitialize"]
    assert data["errors"]
    assert data["errors"][0]["code"] == TransactionInitializeErrorCode.INVALID.name
    assert data["errors"][0]["field"] == "idempotencyKey"
    mocked_initialize.assert_not_called()


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_transaction_initialize_for_removed_app(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
    removed_app,
):
    # given
    expected_amount = Decimal("10.00")
    checkout = checkout_with_prices
    expected_app_identifier = "webhook.app.identifier"
    removed_app.identifier = expected_app_identifier
    removed_app.save()

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["transactionInitialize"]
    assert data["errors"][0]["code"] == TransactionInitializeErrorCode.NOT_FOUND.name
    assert data["errors"][0]["field"] == "paymentGateway"
    mocked_initialize.assert_not_called()


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_transaction_initialize_for_disabled_app(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
    app,
):
    # given
    expected_amount = Decimal("10.00")
    checkout = checkout_with_prices
    expected_app_identifier = "webhook.app.identifier"
    app.identifier = expected_app_identifier
    app.is_active = False
    app.save()

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["transactionInitialize"]
    assert data["errors"][0]["code"] == TransactionInitializeErrorCode.NOT_FOUND.name
    assert data["errors"][0]["field"] == "paymentGateway"
    mocked_initialize.assert_not_called()


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_app_with_action_field(
    mocked_initialize,
    app_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    transaction_item_generator,
):
    # given
    checkout = checkout_with_prices
    expected_charged_amount = Decimal(10)
    expected_authorized_amount = Decimal(3)
    transaction_item_generator(
        checkout_id=checkout.pk,
        charged_value=expected_charged_amount,
        authorized_value=expected_authorized_amount,
    )
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = TransactionEventType.AUTHORIZATION_SUCCESS.upper()
    expected_response["amount"] = str(
        checkout.total_gross_amount - expected_charged_amount
    )
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": TransactionFlowStrategyEnum.AUTHORIZATION.name,
        "amount": None,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = app_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    assert_no_permission(response)


def test_customer_with_action_field(
    app_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_item_generator,
):
    # given
    checkout = checkout_with_prices
    expected_charged_amount = Decimal(10)
    expected_authorized_amount = Decimal(3)
    transaction_item_generator(
        checkout_id=checkout.pk,
        charged_value=expected_charged_amount,
        authorized_value=expected_authorized_amount,
    )
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    variables = {
        "action": TransactionFlowStrategyEnum.AUTHORIZATION.name,
        "amount": None,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = app_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    assert_no_permission(response)


def test_incorrect_source_object_id(
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_item_generator,
    product,
):
    # given
    checkout = checkout_with_prices
    expected_charged_amount = Decimal(10)
    expected_authorized_amount = Decimal(3)
    transaction_item_generator(
        checkout_id=checkout.pk,
        charged_value=expected_charged_amount,
        authorized_value=expected_authorized_amount,
    )
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    variables = {
        "action": None,
        "amount": None,
        "id": to_global_id_or_none(product),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response, ignore_errors=True)
    errors = content["data"]["transactionInitialize"]["errors"]
    assert errors
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == TransactionInitializeErrorCode.INVALID.name


def test_checkout_doesnt_exist(
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    permission_manage_payments,
):
    # given
    checkout = checkout_with_prices

    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    variables = {
        "action": None,
        "amount": None,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }
    checkout.delete()

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response, ignore_errors=True)
    errors = content["data"]["transactionInitialize"]["errors"]
    assert errors
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == TransactionInitializeErrorCode.NOT_FOUND.name


def test_order_doesnt_exists(
    user_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
    permission_manage_payments,
):
    # given
    order = order_with_lines

    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    variables = {
        "action": None,
        "amount": None,
        "id": to_global_id_or_none(order),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }
    order.delete()

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response, ignore_errors=True)
    errors = content["data"]["transactionInitialize"]["errors"]
    assert errors
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == TransactionInitializeErrorCode.NOT_FOUND.name


@pytest.mark.parametrize(
    "result", [TransactionEventType.CHARGE_REQUEST, TransactionEventType.CHARGE_SUCCESS]
)
@mock.patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
@mock.patch("saleor.plugins.manager.PluginsManager.checkout_fully_authorized")
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_checkout_fully_paid(
    mocked_initialize,
    mocked_fully_authorized,
    mocked_fully_paid,
    result,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    plugins_manager,
):
    # given
    checkout = checkout_with_prices
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["amount"] = str(checkout_info.checkout.total_gross_amount)
    expected_response["result"] = result.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": None,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["transactionInitialize"]["errors"]
    checkout.refresh_from_db()
    mocked_fully_paid.assert_called_once_with(checkout, webhooks=set())
    mocked_fully_authorized.assert_called_once_with(checkout, webhooks=set())
    assert checkout.charge_status == CheckoutChargeStatus.FULL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL


@mock.patch("saleor.plugins.manager.PluginsManager.checkout_fully_authorized")
@mock.patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_checkout_fully_paid_pending_charge(
    mocked_initialize,
    mocked_fully_paid,
    mocked_fully_authorized,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    plugins_manager,
):
    # given
    checkout = checkout_with_prices
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["amount"] = str(checkout_info.checkout.total_gross_amount)
    expected_response["result"] = TransactionEventType.CHARGE_REQUEST.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": None,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["transactionInitialize"]["errors"]
    checkout.refresh_from_db()
    mocked_fully_paid.assert_called_once_with(checkout, webhooks=set())
    mocked_fully_authorized.assert_called_once_with(checkout, webhooks=set())
    assert checkout.charge_status == CheckoutChargeStatus.FULL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.AUTHORIZATION_REQUEST,
        TransactionEventType.AUTHORIZATION_SUCCESS,
    ],
)
@mock.patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
@mock.patch("saleor.plugins.manager.PluginsManager.checkout_fully_authorized")
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_checkout_fully_authorized(
    mocked_initialize,
    mocked_fully_authorized,
    mocked_fully_paid,
    result,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    plugins_manager,
):
    # given
    checkout = checkout_with_prices
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["amount"] = str(checkout_info.checkout.total_gross_amount)
    expected_response["result"] = result.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": None,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["transactionInitialize"]["errors"]
    checkout.refresh_from_db()
    assert checkout.charge_status == CheckoutChargeStatus.NONE
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL
    mocked_fully_authorized.assert_called_once_with(checkout, webhooks=set())
    mocked_fully_paid.assert_not_called()


@mock.patch("saleor.plugins.manager.PluginsManager.checkout_fully_authorized")
@mock.patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_checkout_fully_authorized_pending_authorization(
    mocked_initialize,
    mocked_fully_paid,
    mocked_fully_authorized,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    plugins_manager,
):
    # given
    checkout = checkout_with_prices
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    channel = checkout_info.channel
    channel.automatically_complete_fully_paid_checkouts = True
    channel.save(update_fields=["automatically_complete_fully_paid_checkouts"])

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["amount"] = str(checkout_info.checkout.total_gross_amount)
    expected_response["result"] = TransactionEventType.AUTHORIZATION_REQUEST.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": None,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["transactionInitialize"]["errors"]
    checkout.refresh_from_db()
    assert checkout.charge_status == CheckoutChargeStatus.NONE
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL
    mocked_fully_authorized.assert_called_once_with(checkout, webhooks=set())
    mocked_fully_paid.assert_not_called()


def test_user_missing_permission_for_customer_ip_address(
    user_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
):
    # given
    order = order_with_lines

    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    variables = {
        "action": None,
        "amount": None,
        "id": to_global_id_or_none(order),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
        "customerIpAddress": "127.0.0.1",
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    assert_no_permission(response)


def test_app_missing_permission_for_customer_ip_address(
    app_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
):
    # given
    order = order_with_lines

    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    variables = {
        "action": None,
        "amount": None,
        "id": to_global_id_or_none(order),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
        "customerIpAddress": "127.0.0.1",
    }

    # when
    response = app_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    assert_no_permission(response)


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_with_customer_ip_address(
    mocked_initialize,
    app_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
    permission_manage_payments,
):
    # given
    order = order_with_lines
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = TransactionEventType.CHARGE_REQUEST.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )
    app_api_client.app.permissions.set([permission_manage_payments])

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(order),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
        "customerIpAddress": "127.0.0.2",
    }

    # when
    response = app_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    get_graphql_content(response)

    transaction = order.payment_transactions.last()
    mocked_initialize.assert_called_with(
        TransactionSessionData(
            transaction=transaction,
            source_object=order,
            action=TransactionProcessActionData(
                action_type=TransactionFlowStrategy.CHARGE,
                amount=expected_amount,
                currency=order.currency,
            ),
            customer_ip_address="127.0.0.2",
            payment_gateway_data=PaymentGatewayData(
                app_identifier=webhook_app.identifier, data=None, error=None
            ),
            idempotency_key=transaction.idempotency_key,
        )
    )


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_sets_customer_ip_address_when_not_provided(
    mocked_initialize,
    app_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
    permission_manage_payments,
):
    # given
    order = order_with_lines
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = TransactionEventType.CHARGE_REQUEST.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )
    app_api_client.app.permissions.set([permission_manage_payments])

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(order),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = app_api_client.post_graphql(
        TRANSACTION_INITIALIZE, variables, REMOTE_ADDR="127.0.0.2"
    )

    # then
    get_graphql_content(response)

    transaction = order.payment_transactions.last()
    mocked_initialize.assert_called_with(
        TransactionSessionData(
            transaction=transaction,
            source_object=order,
            action=TransactionProcessActionData(
                action_type=TransactionFlowStrategy.CHARGE,
                amount=expected_amount,
                currency=order.currency,
            ),
            customer_ip_address="127.0.0.2",
            payment_gateway_data=PaymentGatewayData(
                app_identifier=webhook_app.identifier, data=None, error=None
            ),
            idempotency_key=transaction.idempotency_key,
        )
    )


def test_customer_ip_address_wrong_format(
    app_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
    permission_manage_payments,
):
    # given
    order = order_with_lines
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("10.00")

    app_api_client.app.permissions.set([permission_manage_payments])

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(order),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
        "customerIpAddress": "127.0.02",
    }

    # when
    response = app_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)

    errors = content["data"]["transactionInitialize"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "customerIpAddress"
    assert errors[0]["code"] == TransactionInitializeErrorCode.INVALID.name


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_customer_ip_address_ipv6(
    mocked_initialize,
    app_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
    permission_manage_payments,
):
    # given
    order = order_with_lines
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = TransactionEventType.CHARGE_REQUEST.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )
    app_api_client.app.permissions.set([permission_manage_payments])

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(order),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
        "customerIpAddress": "::1",
    }

    # when
    response = app_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    get_graphql_content(response)

    transaction = order.payment_transactions.last()
    mocked_initialize.assert_called_with(
        TransactionSessionData(
            transaction=transaction,
            source_object=order,
            action=TransactionProcessActionData(
                action_type=TransactionFlowStrategy.CHARGE,
                amount=expected_amount,
                currency=order.currency,
            ),
            customer_ip_address="::1",
            payment_gateway_data=PaymentGatewayData(
                app_identifier=webhook_app.identifier, data=None, error=None
            ),
            idempotency_key=transaction.idempotency_key,
        )
    )


@freeze_time("2023-03-18 12:00:00")
@pytest.mark.parametrize(
    "previous_last_transaction_modified_at",
    [None, datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC)],
)
@mock.patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_updates_checkout_last_transaction_modified_at(
    mocked_initialize,
    mocked_fully_paid,
    previous_last_transaction_modified_at,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    plugins_manager,
):
    # given
    checkout = checkout_with_prices
    checkout.last_transaction_modified_at = previous_last_transaction_modified_at
    checkout.save()

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        plugins_manager,
        lines,
    )
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["amount"] = str(checkout_info.checkout.total_gross_amount)
    expected_response["result"] = TransactionEventType.CHARGE_SUCCESS.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": None,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["transactionInitialize"]["errors"]
    checkout.refresh_from_db()
    transaction = checkout.payment_transactions.first()
    assert checkout.last_transaction_modified_at == transaction.modified_at
    assert (
        checkout.last_transaction_modified_at != previous_last_transaction_modified_at
    )


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_for_locked_checkout(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
):
    # given
    checkout = checkout_with_prices
    checkout.completing_started_at = timezone.now()
    checkout.save(update_fields=["completing_started_at"])

    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = "CHARGE_SUCCESS"
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )
    idempotency_key = "ABC"

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
        "idempotencyKey": idempotency_key,
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["transactionInitialize"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert (
        error["code"]
        == TransactionInitializeErrorCode.CHECKOUT_COMPLETION_IN_PROGRESS.name
    )
    assert error["field"] == "id"


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_for_checkout_with_payments(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
):
    # given
    checkout = checkout_with_prices
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    # create payments
    payments = Payment.objects.bulk_create(
        [
            Payment(
                gateway="mirumee.payments.dummy", is_active=True, checkout=checkout
            ),
            Payment(
                gateway="mirumee.payments.dummy", is_active=False, checkout=checkout
            ),
        ]
    )

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = "CHARGE_SUCCESS"
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )
    idempotency_key = "ABC"

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
        "idempotencyKey": idempotency_key,
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=expected_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        charged_value=expected_amount,
        returned_data=expected_response["data"],
    )
    transaction = checkout.payment_transactions.last()
    assert transaction.idempotency_key == idempotency_key
    assert transaction.events.first().idempotency_key == idempotency_key
    for payment in payments:
        payment.refresh_from_db()
        assert payment.is_active is False


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_for_checkout_with_payments_error_raised(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
):
    # given
    checkout = checkout_with_prices
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    # create payments
    payments = Payment.objects.bulk_create(
        [
            Payment(
                gateway="mirumee.payments.dummy", is_active=True, checkout=checkout
            ),
            Payment(
                gateway="mirumee.payments.dummy", is_active=False, checkout=checkout
            ),
        ]
    )

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = "CHARGE_SUCCESS"
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.side_effect = TransactionItemIdempotencyUniqueError()
    idempotency_key = "ABC"

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
        "idempotencyKey": idempotency_key,
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["transactionInitialize"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["code"] == TransactionInitializeErrorCode.UNIQUE.name
    assert error["field"] == "idempotencyKey"
    for payment in payments:
        payment.refresh_from_db()
    assert payments[0].is_active is True
    assert payments[1].is_active is False


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_for_checkout_too_long_message_in_response(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    caplog,
):
    # given
    checkout = checkout_with_prices
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = "CHARGE_SUCCESS"
    expected_response["message"] = "m" * 513
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=expected_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        charged_value=expected_amount,
        returned_data=expected_response["data"],
        expected_message=expected_response["message"][:511] + "…",
    )
    assert checkout.charge_status == CheckoutChargeStatus.PARTIAL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.PARTIAL
    assert (
        "Value for field: message in response of transaction action webhook "
        "exceeds the character field limit. Message has been truncated."
    ) in [record.message for record in caplog.records]


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_for_checkout_empty_message(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    caplog,
):
    # given
    checkout = checkout_with_prices
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = "CHARGE_SUCCESS"
    expected_response["message"] = None
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=expected_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        charged_value=expected_amount,
        returned_data=expected_response["data"],
        expected_message=expected_response["message"],
    )
    assert checkout.charge_status == CheckoutChargeStatus.PARTIAL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.PARTIAL


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_for_checkout_with_shipping_app(
    mocked_send_webhook_request_sync,
    app_api_client,
    checkout_with_prices,
    permission_manage_payments,
    shipping_app_with_subscription,
    transaction_initialize_session_app,
    transaction_session_response,
    caplog,
):
    # given
    mocked_send_webhook_request_sync.return_value = transaction_session_response

    shipping_webhook = shipping_app_with_subscription.webhooks.first()
    shipping_webhook.subscription_query = """
        subscription {
            event {
                ... on ShippingListMethodsForCheckout {
                    checkout {
                        email
                        token
                    }
                }
            }
        }
    """
    shipping_webhook.save(update_fields=["subscription_query"])

    checkout = checkout_with_prices

    variables = {
        "action": TransactionFlowStrategyEnum.AUTHORIZATION.name,
        "amount": Decimal("10.00"),
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {
            "id": transaction_initialize_session_app.identifier,
            "data": None,
        },
    }

    # when
    response = app_api_client.post_graphql(
        TRANSACTION_INITIALIZE, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["transactionInitialize"]["errors"]

    assert "No payload was generated with subscription for event" not in "".join(
        caplog.messages
    )

    # gather called event types
    event_types = {
        call.args[0].event_type for call in mocked_send_webhook_request_sync.mock_calls
    }
    assert len(event_types) == 2
    assert WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT in event_types
    assert WebhookEventSyncType.TRANSACTION_INITIALIZE_SESSION in event_types

    for call in mocked_send_webhook_request_sync.mock_calls:
        delivery = call.args[0]
        assert delivery.payload.get_payload()


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@override_settings(
    PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"],
    CHECKOUT_PRICES_TTL=datetime.timedelta(0),
)
def test_for_checkout_with_tax_app(
    mocked_send_webhook_request_sync,
    app_api_client,
    checkout_with_prices,
    permission_manage_payments,
    transaction_initialize_session_app,
    tax_app,
    transaction_session_response,
    caplog,
):
    # given
    mocked_send_webhook_request_sync.return_value = transaction_session_response

    checkout = checkout_with_prices
    variables = {
        "action": TransactionFlowStrategyEnum.AUTHORIZATION.name,
        "amount": Decimal("10.00"),
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {
            "id": transaction_initialize_session_app.identifier,
            "data": None,
        },
    }

    # when
    response = app_api_client.post_graphql(
        TRANSACTION_INITIALIZE, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["transactionInitialize"]["errors"]

    assert "No payload was generated with subscription for event" not in "".join(
        caplog.messages
    )

    # gather called event types
    event_types = {
        call.args[0].event_type for call in mocked_send_webhook_request_sync.mock_calls
    }
    assert len(event_types) == 2
    assert WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES in event_types
    assert WebhookEventSyncType.TRANSACTION_INITIALIZE_SESSION in event_types

    for call in mocked_send_webhook_request_sync.mock_calls:
        delivery = call.args[0]
        assert delivery.payload.get_payload()


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_for_order_with_tax_app(
    mocked_send_webhook_request_sync,
    app_api_client,
    permission_manage_payments,
    draft_order,
    tax_app,
    transaction_initialize_session_app,
    transaction_session_response,
    caplog,
):
    # given
    mocked_send_webhook_request_sync.return_value = transaction_session_response

    order = draft_order
    order.should_refresh_prices = True
    order.save(update_fields=["should_refresh_prices"])

    variables = {
        "action": TransactionFlowStrategyEnum.AUTHORIZATION.name,
        "amount": Decimal("10.00"),
        "id": to_global_id_or_none(draft_order),
        "paymentGateway": {
            "id": transaction_initialize_session_app.identifier,
            "data": None,
        },
    }

    # when
    response = app_api_client.post_graphql(
        TRANSACTION_INITIALIZE,
        variables,
        permissions=[permission_manage_payments],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["transactionInitialize"]["errors"]

    assert "No payload was generated with subscription for event" not in "".join(
        caplog.messages
    )

    # gather called event types
    event_types = {
        call.args[0].event_type for call in mocked_send_webhook_request_sync.mock_calls
    }
    assert len(event_types) == 2
    assert WebhookEventSyncType.ORDER_CALCULATE_TAXES in event_types
    assert WebhookEventSyncType.TRANSACTION_INITIALIZE_SESSION in event_types

    for call in mocked_send_webhook_request_sync.mock_calls:
        delivery = call.args[0]
        assert delivery.payload.get_payload()


# Test wrapped by `transaction=True` to ensure that `selector_for_update` is called in a database transaction.
@pytest.mark.django_db(transaction=True)
@mock.patch(
    "saleor.payment.utils.get_order_and_transaction_item_locked_for_update",
    wraps=get_order_and_transaction_item_locked_for_update,
)
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_lock_order_during_updating_order_amounts(
    mocked_initialize,
    mocked_get_order_and_transaction_item_locked_for_update,
    user_api_client,
    unconfirmed_order_with_lines,
    webhook_app,
    transaction_session_response,
):
    # given
    order = unconfirmed_order_with_lines
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = TransactionEventType.CHARGE_SUCCESS.upper()
    expected_response["amount"] = str(order.total_gross_amount)
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "amount": order.total_gross_amount,
        "id": to_global_id_or_none(order),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    _assert_fields(
        content=content,
        source_object=order,
        expected_amount=order.total_gross_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        charged_value=order.total_gross_amount,
        returned_data=expected_response["data"],
    )

    assert not order.is_fully_paid()
    order.refresh_from_db()
    assert order.is_fully_paid()
    assert order.total_authorized_amount == Decimal(0)
    assert order.total_charged_amount == order.total_gross_amount
    assert order.charge_status == OrderChargeStatus.FULL
    assert order.authorize_status == OrderAuthorizeStatus.FULL
    transaction_pk = order.payment_transactions.get().pk
    mocked_get_order_and_transaction_item_locked_for_update.assert_called_once_with(
        order.pk, transaction_pk
    )


# Test wrapped by `transaction=True` to ensure that `selector_for_update` is called in a database transaction.
@pytest.mark.django_db(transaction=True)
@mock.patch(
    "saleor.payment.utils.get_checkout_and_transaction_item_locked_for_update",
    wraps=get_checkout_and_transaction_item_locked_for_update,
)
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_lock_checkout_during_updating_checkout_amounts(
    mocked_initialize,
    mocked_get_checkout_and_transaction_item_locked_for_update,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    plugins_manager,
):
    # given
    checkout = checkout_with_prices
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["amount"] = str(checkout_info.checkout.total_gross_amount)
    expected_response["result"] = TransactionEventType.CHARGE_SUCCESS.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": None,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=checkout.total_gross_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_initialize=mocked_initialize,
        charged_value=checkout.total_gross_amount,
        returned_data=expected_response["data"],
    )
    assert checkout.charge_status == CheckoutChargeStatus.FULL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL
    transaction_pk = checkout.payment_transactions.get().pk
    mocked_get_checkout_and_transaction_item_locked_for_update.assert_called_once_with(
        checkout.pk, transaction_pk
    )


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_transaction_initialize_checkout_completed_race_condition(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    plugins_manager,
):
    # given
    checkout = checkout_with_prices
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["amount"] = str(checkout_info.checkout.total_gross_amount)
    expected_response["result"] = TransactionEventType.CHARGE_SUCCESS.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": None,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    def complete_checkout(*args, **kwargs):
        create_order_from_checkout(
            checkout_info, plugins_manager, user=user_api_client.user, app=None
        )

    with race_condition.RunBefore(
        "saleor.payment.utils.recalculate_transaction_amounts",
        complete_checkout,
    ):
        user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    order = Order.objects.get(checkout_token=checkout.pk)
    assert order.status == OrderStatus.UNFULFILLED
    assert order.charge_status == OrderChargeStatus.FULL
    assert order.authorize_status == OrderAuthorizeStatus.FULL
    assert order.total_charged.amount == checkout.total.gross.amount


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.AUTHORIZATION_REQUEST,
        TransactionEventType.AUTHORIZATION_SUCCESS,
        TransactionEventType.CHARGE_REQUEST,
        TransactionEventType.CHARGE_SUCCESS,
    ],
)
@mock.patch("saleor.webhook.transport.list_stored_payment_methods.cache.delete")
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_invalidate_stored_payment_methods_for_order(
    mocked_initialize,
    cache_delete_mock,
    result,
    customer_user,
    user_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
    permission_manage_payments,
    list_stored_payment_methods_app,
):
    # given
    order = order_with_lines
    order.user = customer_user
    order.save(update_fields=["user_id"])

    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    webhook_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="list_stored_payment_methods",
        app=webhook_app,
        target_url="http://localhost:8000/endpoint/",
    )
    webhook.events.create(
        event_type=WebhookEventSyncType.LIST_STORED_PAYMENT_METHODS,
    )

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = result.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    channel = order.channel
    expected_payload = {
        "user_id": graphene.Node.to_global_id("User", customer_user.pk),
        "channel_slug": channel.slug,
    }
    # cache key for transaction webhook
    cache_key = generate_cache_key_for_webhook(
        expected_payload,
        webhook.target_url,
        WebhookEventSyncType.LIST_STORED_PAYMENT_METHODS,
        webhook_app.id,
    )

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(order),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["transactionInitialize"]["errors"]
    response_data = content["data"]["transactionInitialize"]
    assert response_data["transaction"]

    # ensure that only cache for result app identifier has been cleared
    cache_delete_mock.assert_called_once_with(cache_key)


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.AUTHORIZATION_REQUEST,
        TransactionEventType.AUTHORIZATION_SUCCESS,
        TransactionEventType.CHARGE_REQUEST,
        TransactionEventType.CHARGE_SUCCESS,
    ],
)
@mock.patch("saleor.webhook.transport.list_stored_payment_methods.cache.delete")
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_invalidate_stored_payment_methods_for_checkout(
    mocked_initialize,
    cache_delete_mock,
    result,
    customer_user,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    permission_manage_payments,
    list_stored_payment_methods_app,
):
    # given
    checkout = checkout_with_prices
    checkout.user = customer_user
    checkout.save(update_fields=["user_id"])

    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    webhook_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="list_stored_payment_methods",
        app=webhook_app,
        target_url="http://localhost:8000/endpoint/",
    )
    webhook.events.create(
        event_type=WebhookEventSyncType.LIST_STORED_PAYMENT_METHODS,
    )

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = result.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    channel = checkout.channel
    expected_payload = {
        "user_id": graphene.Node.to_global_id("User", customer_user.pk),
        "channel_slug": channel.slug,
    }
    # cache key for transaction webhook
    cache_key = generate_cache_key_for_webhook(
        expected_payload,
        webhook.target_url,
        WebhookEventSyncType.LIST_STORED_PAYMENT_METHODS,
        webhook_app.id,
    )

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["transactionInitialize"]["errors"]
    response_data = content["data"]["transactionInitialize"]
    assert response_data["transaction"]

    # ensure that only cache for result app identifier has been cleared
    cache_delete_mock.assert_called_once_with(cache_key)


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.AUTHORIZATION_FAILURE,
        TransactionEventType.CHARGE_ACTION_REQUIRED,
        TransactionEventType.CHARGE_FAILURE,
    ],
)
@mock.patch("saleor.webhook.transport.list_stored_payment_methods.cache.delete")
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_stored_payment_methods_not_invalidated_for_order(
    mocked_initialize,
    cache_delete_mock,
    result,
    customer_user,
    user_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
    permission_manage_payments,
):
    # given
    order = order_with_lines
    order.user = customer_user
    order.save(update_fields=["user_id"])

    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    webhook_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="list_stored_payment_methods",
        app=webhook_app,
        target_url="http://localhost:8000/endpoint/",
    )
    webhook.events.create(
        event_type=WebhookEventSyncType.LIST_STORED_PAYMENT_METHODS,
    )

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = result.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(order),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["transactionInitialize"]["errors"]
    response_data = content["data"]["transactionInitialize"]
    assert response_data["transaction"]

    # ensure that cache has not been cleared
    cache_delete_mock.assert_not_called()


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.AUTHORIZATION_FAILURE,
        TransactionEventType.CHARGE_ACTION_REQUIRED,
        TransactionEventType.CHARGE_FAILURE,
    ],
)
@mock.patch("saleor.webhook.transport.list_stored_payment_methods.cache.delete")
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_invalidate_stored_payment_methods_not_invalidated_for_checkout(
    mocked_initialize,
    cache_delete_mock,
    result,
    customer_user,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    permission_manage_payments,
):
    # given
    checkout = checkout_with_prices
    checkout.user = customer_user
    checkout.save(update_fields=["user_id"])

    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    webhook_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="list_stored_payment_methods",
        app=webhook_app,
        target_url="http://localhost:8000/endpoint/",
    )
    webhook.events.create(
        event_type=WebhookEventSyncType.LIST_STORED_PAYMENT_METHODS,
    )

    expected_amount = Decimal("10.00")
    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["result"] = result.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_initialize.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "action": None,
        "amount": expected_amount,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["transactionInitialize"]["errors"]
    response_data = content["data"]["transactionInitialize"]
    assert response_data["transaction"]

    # ensure that cache has not been cleared
    cache_delete_mock.assert_not_called()


@pytest.mark.parametrize(
    "data", [None, {}, {"some": "value"}, {"code": None}, {"code": ""}]
)
@mock.patch("saleor.giftcard.gateway.uuid4")
def test_for_checkout_with_gift_card_payment_gateway_data_and_incorrect_data_format(
    mocked_uuid4,
    user_api_client,
    checkout_with_prices,
    data,
):
    # given
    checkout = checkout_with_prices
    mocked_uuid4.return_value = uuid4()

    variables = {
        "action": None,
        "amount": 1,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {"id": GIFT_CARD_PAYMENT_GATEWAY_ID, "data": data},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=Decimal(1),
        expected_psp_reference=str(mocked_uuid4.return_value),
        request_event_type=TransactionEventType.AUTHORIZATION_REQUEST,
        response_event_type=TransactionEventType.AUTHORIZATION_FAILURE,
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        expected_message="Incorrect payment gateway data.",
    )


@pytest.mark.parametrize(
    "action",
    [
        None,
        TransactionFlowStrategyEnum.AUTHORIZATION.name,
        TransactionFlowStrategyEnum.CHARGE.name,
    ],
)
@mock.patch("saleor.giftcard.gateway.uuid4")
def test_for_checkout_with_gift_card_payment_gateway(
    mocked_uuid4,
    action,
    user_api_client,
    checkout_with_prices,
    gift_card_created_by_staff,
):
    # given
    checkout = checkout_with_prices
    mocked_uuid4.return_value = uuid4()

    variables = {
        "action": action,
        "amount": 1,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {
            "id": GIFT_CARD_PAYMENT_GATEWAY_ID,
            "data": {"code": gift_card_created_by_staff.code},
        },
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=Decimal(1),
        expected_psp_reference=str(mocked_uuid4.return_value),
        request_event_type=TransactionEventType.AUTHORIZATION_REQUEST,
        response_event_type=TransactionEventType.AUTHORIZATION_SUCCESS,
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        authorized_value=Decimal(1),
        gift_card=gift_card_created_by_staff,
        expected_message=f"Gift card (ending: {gift_card_created_by_staff.display_code}).",
        available_actions=[TransactionAction.CANCEL],
    )


@mock.patch("saleor.giftcard.gateway.uuid4")
def test_for_checkout_with_gift_card_payment_gateway_gift_card_does_not_exist(
    mocked_uuid4,
    user_api_client,
    checkout_with_prices,
):
    # given
    checkout = checkout_with_prices
    mocked_uuid4.return_value = uuid4()

    variables = {
        "action": None,
        "amount": 1,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {
            "id": GIFT_CARD_PAYMENT_GATEWAY_ID,
            "data": {"code": "not-existing"},
        },
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=Decimal(1),
        expected_psp_reference=str(mocked_uuid4.return_value),
        request_event_type=TransactionEventType.AUTHORIZATION_REQUEST,
        response_event_type=TransactionEventType.AUTHORIZATION_FAILURE,
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        expected_message="Gift card code is not valid.",
    )


@mock.patch("saleor.giftcard.gateway.uuid4")
def test_for_checkout_with_gift_card_payment_gateway_gift_card_has_different_currency(
    mocked_uuid4,
    user_api_client,
    checkout_with_prices,
    gift_card_created_by_staff,
):
    # given
    checkout = checkout_with_prices
    mocked_uuid4.return_value = uuid4()

    gift_card_created_by_staff.currency = "CHF"
    gift_card_created_by_staff.save(update_fields=["currency"])

    variables = {
        "action": None,
        "amount": 1,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {
            "id": GIFT_CARD_PAYMENT_GATEWAY_ID,
            "data": {"code": gift_card_created_by_staff.code},
        },
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=Decimal(1),
        expected_psp_reference=str(mocked_uuid4.return_value),
        request_event_type=TransactionEventType.AUTHORIZATION_REQUEST,
        response_event_type=TransactionEventType.AUTHORIZATION_FAILURE,
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        expected_message="Gift card code is not valid.",
    )


@mock.patch("saleor.giftcard.gateway.uuid4")
def test_for_checkout_with_gift_card_payment_gateway_gift_card_is_inactive(
    mocked_uuid4,
    user_api_client,
    checkout_with_prices,
    gift_card_created_by_staff,
):
    # given
    checkout = checkout_with_prices
    mocked_uuid4.return_value = uuid4()

    gift_card_created_by_staff.is_active = False
    gift_card_created_by_staff.save(update_fields=["is_active"])

    variables = {
        "action": None,
        "amount": 1,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {
            "id": GIFT_CARD_PAYMENT_GATEWAY_ID,
            "data": {"code": gift_card_created_by_staff.code},
        },
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=Decimal(1),
        expected_psp_reference=str(mocked_uuid4.return_value),
        request_event_type=TransactionEventType.AUTHORIZATION_REQUEST,
        response_event_type=TransactionEventType.AUTHORIZATION_FAILURE,
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        expected_message="Gift card code is not valid.",
    )


@mock.patch("saleor.giftcard.gateway.uuid4")
def test_for_checkout_with_gift_card_payment_gateway_gift_card_is_expired(
    mocked_uuid4,
    user_api_client,
    checkout_with_prices,
    gift_card_created_by_staff,
):
    # given
    checkout = checkout_with_prices
    mocked_uuid4.return_value = uuid4()

    gift_card_created_by_staff.expiry_date = timezone.now() - datetime.timedelta(days=3)
    gift_card_created_by_staff.save(update_fields=["expiry_date"])

    variables = {
        "action": None,
        "amount": 1,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {
            "id": GIFT_CARD_PAYMENT_GATEWAY_ID,
            "data": {"code": gift_card_created_by_staff.code},
        },
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=Decimal(1),
        expected_psp_reference=str(mocked_uuid4.return_value),
        request_event_type=TransactionEventType.AUTHORIZATION_REQUEST,
        response_event_type=TransactionEventType.AUTHORIZATION_FAILURE,
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        expected_message="Gift card code is not valid.",
    )


@mock.patch("saleor.giftcard.gateway.uuid4")
def test_for_checkout_with_gift_card_payment_gateway_gift_card_has_insufficient_funds(
    mocked_uuid4,
    user_api_client,
    checkout_with_prices,
    gift_card_created_by_staff,
):
    # given
    checkout = checkout_with_prices
    mocked_uuid4.return_value = uuid4()

    gift_card_created_by_staff.current_balance_amount = Decimal(0.1)
    gift_card_created_by_staff.save(update_fields=["current_balance_amount"])

    variables = {
        "action": None,
        "amount": 1,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {
            "id": GIFT_CARD_PAYMENT_GATEWAY_ID,
            "data": {"code": gift_card_created_by_staff.code},
        },
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=Decimal(1),
        expected_psp_reference=str(mocked_uuid4.return_value),
        request_event_type=TransactionEventType.AUTHORIZATION_REQUEST,
        response_event_type=TransactionEventType.AUTHORIZATION_FAILURE,
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        expected_message="Gift card has insufficient amount (0.10) to cover requested amount (1.00).",
    )


@mock.patch("saleor.giftcard.gateway.uuid4")
def test_for_checkout_with_gift_card_payment_gateway_invalidates_previous_authorizations(
    mocked_uuid4,
    user_api_client,
    checkout_with_prices,
    gift_card_created_by_staff,
    transaction_item_generator,
    order,
):
    # given
    checkout = checkout_with_prices
    mocked_uuid4.return_value = uuid4()

    another_checkout = Checkout.objects.create(
        currency=checkout.currency,
        user=checkout.user,
        channel=checkout.channel,
        base_total=Money("15", checkout.currency),
        base_subtotal=Money("10", checkout.currency),
    )
    another_checkout_authorize_transaction = transaction_item_generator(
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        checkout_id=another_checkout.pk,
        gift_card=gift_card_created_by_staff,
        authorized_value=Decimal(15),
    )

    manager = get_plugins_manager(allow_replica=False)
    another_checkout_info = fetch_checkout_info(another_checkout, [], manager)
    fetch_checkout_data(
        checkout_info=another_checkout_info,
        manager=manager,
        lines=[],
    )
    assert (
        another_checkout_info.checkout.authorize_status == CheckoutAuthorizeStatus.FULL
    )

    assert (
        another_checkout_authorize_transaction.events.filter(
            type=TransactionEventType.CANCEL_REQUEST
        ).count()
        == 0
    )
    assert (
        another_checkout_authorize_transaction.events.filter(
            type=TransactionEventType.CANCEL_SUCCESS
        ).count()
        == 0
    )

    order_authorize_transaction = transaction_item_generator(
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        order_id=order.pk,
        gift_card=gift_card_created_by_staff,
        authorized_value=Decimal(25),
    )
    assert (
        order_authorize_transaction.events.filter(
            type=TransactionEventType.CANCEL_REQUEST
        ).count()
        == 0
    )
    assert (
        order_authorize_transaction.events.filter(
            type=TransactionEventType.CANCEL_SUCCESS
        ).count()
        == 0
    )

    variables = {
        "action": None,
        "amount": 1,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {
            "id": GIFT_CARD_PAYMENT_GATEWAY_ID,
            "data": {"code": gift_card_created_by_staff.code},
        },
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=Decimal(1),
        expected_psp_reference=str(mocked_uuid4.return_value),
        request_event_type=TransactionEventType.AUTHORIZATION_REQUEST,
        response_event_type=TransactionEventType.AUTHORIZATION_SUCCESS,
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        authorized_value=Decimal(1),
        gift_card=gift_card_created_by_staff,
        available_actions=[TransactionAction.CANCEL],
    )

    another_checkout_authorize_transaction.refresh_from_db()
    assert another_checkout_authorize_transaction.gift_card is None
    assert (
        another_checkout_authorize_transaction.events.filter(
            type=TransactionEventType.CANCEL_REQUEST
        ).count()
        == 1
    )
    assert (
        another_checkout_authorize_transaction.events.filter(
            type=TransactionEventType.CANCEL_SUCCESS,
            message=f"Gift card (code ending with: {gift_card_created_by_staff.display_code}) has been authorized as payment method in a different checkout or has been authorized in the same checkout again.",
        ).count()
        == 1
    )
    assert another_checkout_authorize_transaction.authorized_value == Decimal(0)
    another_checkout.refresh_from_db()
    assert another_checkout.authorize_status == CheckoutAuthorizeStatus.NONE

    assert order_authorize_transaction.gift_card is not None
    assert (
        order_authorize_transaction.events.filter(
            type=TransactionEventType.CANCEL_REQUEST
        ).count()
        == 0
    )
    assert (
        order_authorize_transaction.events.filter(
            type=TransactionEventType.CANCEL_SUCCESS
        ).count()
        == 0
    )


@mock.patch("saleor.giftcard.gateway.uuid4")
def test_for_order_with_gift_card_payment_gateway(
    mocked_uuid4,
    user_api_client,
    order,
    gift_card_created_by_staff,
):
    # given
    variables = {
        "action": None,
        "amount": 1,
        "id": to_global_id_or_none(order),
        "paymentGateway": {
            "id": GIFT_CARD_PAYMENT_GATEWAY_ID,
            "data": {"code": gift_card_created_by_staff.code},
        },
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    order.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=order,
        expected_amount=Decimal(1),
        expected_psp_reference=str(mocked_uuid4.return_value),
        request_event_type=TransactionEventType.AUTHORIZATION_REQUEST,
        response_event_type=TransactionEventType.AUTHORIZATION_FAILURE,
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        expected_message=f"Cannot initialize transaction for payment gateway: {GIFT_CARD_PAYMENT_GATEWAY_ID} and object type other than Checkout.",
    )


@pytest.mark.parametrize(
    ("first_call_amount", "second_call_amount"),
    [
        (1, 1),
        (1, 2),
        (2, 1),
    ],
)
@mock.patch("saleor.giftcard.gateway.uuid4")
def test_for_checkout_with_gift_card_payment_gateway_initialize_transaction_using_the_same_gift_card(
    mocked_uuid4,
    first_call_amount,
    second_call_amount,
    user_api_client,
    checkout_with_prices,
    gift_card_created_by_staff,
):
    # given
    checkout = checkout_with_prices
    mocked_uuid4.return_value = uuid4()

    variables = {
        "action": None,
        "amount": first_call_amount,
        "id": to_global_id_or_none(checkout),
        "paymentGateway": {
            "id": GIFT_CARD_PAYMENT_GATEWAY_ID,
            "data": {"code": gift_card_created_by_staff.code},
        },
    }

    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=Decimal(first_call_amount),
        expected_psp_reference=str(mocked_uuid4.return_value),
        request_event_type=TransactionEventType.AUTHORIZATION_REQUEST,
        response_event_type=TransactionEventType.AUTHORIZATION_SUCCESS,
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        authorized_value=Decimal(first_call_amount),
        gift_card=gift_card_created_by_staff,
        expected_message=f"Gift card (ending: {gift_card_created_by_staff.display_code}).",
        available_actions=[TransactionAction.CANCEL],
    )
    assert checkout.payment_transactions.all().count() == 1
    assert checkout.payment_transactions.first().events.all().count() == 2

    variables["amount"] = second_call_amount

    # when
    response = user_api_client.post_graphql(TRANSACTION_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    checkout.refresh_from_db()
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=Decimal(second_call_amount),
        expected_psp_reference=str(mocked_uuid4.return_value),
        request_event_type=TransactionEventType.AUTHORIZATION_REQUEST,
        response_event_type=TransactionEventType.AUTHORIZATION_SUCCESS,
        app_identifier=GIFT_CARD_PAYMENT_GATEWAY_ID,
        authorized_value=Decimal(second_call_amount),
        gift_card=gift_card_created_by_staff,
        expected_message=f"Gift card (ending: {gift_card_created_by_staff.display_code}).",
        available_actions=[TransactionAction.CANCEL],
    )

    assert checkout.payment_transactions.all().count() == 2

    cancelled_transaction = checkout.payment_transactions.first()
    assert cancelled_transaction.authorized_value == Decimal(0)
    assert cancelled_transaction.charged_value == Decimal(0)
    assert cancelled_transaction.events.count() == 4
    cancelled_transaction.events.get(type=TransactionEventType.AUTHORIZATION_REQUEST)
    cancelled_transaction.events.get(type=TransactionEventType.AUTHORIZATION_SUCCESS)
    cancelled_transaction.events.get(type=TransactionEventType.CANCEL_REQUEST)
    cancelled_transaction.events.get(
        type=TransactionEventType.CANCEL_SUCCESS,
        message=f"Gift card (code ending with: {gift_card_created_by_staff.display_code}) has been authorized as payment method in a different checkout or has been authorized in the same checkout again.",
    )
    assert cancelled_transaction.available_actions == []

    latest_transaction = checkout.payment_transactions.last()
    assert latest_transaction.authorized_value == Decimal(second_call_amount)
    assert latest_transaction.charged_value == Decimal(0)
    assert latest_transaction.events.count() == 2
    latest_transaction.events.get(type=TransactionEventType.AUTHORIZATION_REQUEST)
    latest_transaction.events.get(type=TransactionEventType.AUTHORIZATION_SUCCESS)
    assert latest_transaction.available_actions == [TransactionAction.CANCEL]
