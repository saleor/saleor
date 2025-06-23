import datetime
from decimal import Decimal
from unittest import mock

import pytest
from django.conf import settings
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time

from .....channel import TransactionFlowStrategy
from .....checkout import CheckoutAuthorizeStatus, CheckoutChargeStatus
from .....checkout.calculations import fetch_checkout_data
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.models import Checkout
from .....core.prices import quantize_price
from .....order import OrderChargeStatus, OrderEvents, OrderStatus
from .....order.models import Order
from .....payment import TransactionEventType, TransactionItemIdempotencyUniqueError
from .....payment.interface import (
    PaymentGatewayData,
    TransactionProcessActionData,
    TransactionSessionData,
    TransactionSessionResult,
)
from .....payment.models import Payment, TransactionItem
from .....webhook.event_types import WebhookEventSyncType
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
    mocked_initialize,
    request_event_type=TransactionEventType.CHARGE_REQUEST,
    action_type=TransactionFlowStrategy.CHARGE,
    request_event_include_in_calculations=False,
    authorized_value=Decimal(0),
    charged_value=Decimal(0),
    charge_pending_value=Decimal(0),
    authorize_pending_value=Decimal(0),
    returned_data=None,
    expected_message=None,
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
    ("auto_order_confirmation"),
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
@mock.patch("saleor.checkout.tasks.automatic_checkout_completion_task.delay")
@mock.patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_checkout_fully_paid(
    mocked_initialize,
    mocked_fully_paid,
    mocked_automatic_checkout_completion_task,
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

    assert checkout_info.channel.automatically_complete_fully_paid_checkouts is False

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
    mocked_automatic_checkout_completion_task.assert_not_called()
    assert checkout.charge_status == CheckoutChargeStatus.FULL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL


@mock.patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_checkout_fully_paid_automatic_completion(
    mocked_initialize,
    mocked_fully_paid,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    plugins_manager,
):
    # given
    checkout = checkout_with_prices
    checkout_token = checkout.token
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
    with pytest.raises(Checkout.DoesNotExist):
        checkout.refresh_from_db()

    order = Order.objects.get(checkout_token=checkout_token)
    assert order.charge_status == CheckoutChargeStatus.FULL
    assert order.authorize_status == CheckoutAuthorizeStatus.FULL
    assert order.events.filter(
        type=OrderEvents.PLACED_AUTOMATICALLY_FROM_PAID_CHECKOUT
    ).exists()
    mocked_fully_paid.assert_called_once_with(checkout, webhooks=set())


@mock.patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_checkout_fully_paid_pending_charge_automatic_completion(
    mocked_initialize,
    mocked_fully_paid,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    plugins_manager,
):
    # given
    checkout = checkout_with_prices
    checkout_token = checkout.token
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
    with pytest.raises(Checkout.DoesNotExist):
        checkout.refresh_from_db()

    order = Order.objects.get(checkout_token=checkout_token)
    assert order.charge_status == CheckoutChargeStatus.NONE
    assert order.authorize_status == CheckoutAuthorizeStatus.NONE
    mocked_fully_paid.assert_called_once_with(checkout, webhooks=set())


@pytest.mark.parametrize(
    "result",
    [
        TransactionEventType.AUTHORIZATION_REQUEST,
        TransactionEventType.AUTHORIZATION_SUCCESS,
    ],
)
@mock.patch("saleor.checkout.tasks.automatic_checkout_completion_task.delay")
@mock.patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_checkout_fully_authorized(
    mocked_initialize,
    mocked_fully_paid,
    mocked_automatic_checkout_completion_task,
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

    assert checkout_info.channel.automatically_complete_fully_paid_checkouts is False

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
    mocked_automatic_checkout_completion_task.assert_not_called()
    mocked_fully_paid.assert_not_called()


@mock.patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_checkout_fully_authorized_automatic_completion(
    mocked_initialize,
    mocked_fully_paid,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    plugins_manager,
):
    # given
    checkout = checkout_with_prices
    checkout_token = checkout.token
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
    expected_response["result"] = TransactionEventType.AUTHORIZATION_SUCCESS.upper()
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
    with pytest.raises(Checkout.DoesNotExist):
        checkout.refresh_from_db()

    order = Order.objects.get(checkout_token=checkout_token)
    assert order.charge_status == CheckoutChargeStatus.NONE
    assert order.authorize_status == CheckoutAuthorizeStatus.FULL
    assert order.events.filter(
        type=OrderEvents.PLACED_AUTOMATICALLY_FROM_PAID_CHECKOUT
    ).exists()
    mocked_fully_paid.assert_not_called()


@mock.patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_initialize_session")
def test_checkout_fully_authorizaed_pending_authorization_automatic_completion(
    mocked_initialize,
    mocked_fully_paid,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    plugins_manager,
):
    # given
    checkout = checkout_with_prices
    checkout_token = checkout.token
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
    with pytest.raises(Checkout.DoesNotExist):
        checkout.refresh_from_db()

    order = Order.objects.get(checkout_token=checkout_token)
    assert order.charge_status == CheckoutChargeStatus.NONE
    assert order.authorize_status == CheckoutAuthorizeStatus.NONE
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
