import datetime
from decimal import Decimal
from unittest import mock

import graphene
import pytest
import pytz
from django.utils import timezone
from freezegun import freeze_time

from .....channel import TransactionFlowStrategy
from .....checkout import CheckoutAuthorizeStatus, CheckoutChargeStatus
from .....checkout.calculations import fetch_checkout_data
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....core.prices import quantize_price
from .....order import OrderChargeStatus, OrderStatus
from .....payment import TransactionEventType
from .....payment.interface import (
    PaymentGatewayData,
    TransactionProcessActionData,
    TransactionSessionData,
    TransactionSessionResult,
)
from .....payment.models import Payment, TransactionEvent
from ....core.enums import TransactionProcessErrorCode
from ....core.utils import to_global_id_or_none
from ....tests.utils import assert_no_permission, get_graphql_content

TRANSACTION_PROCESS = """
mutation TransactionProcess(
  $id: ID
  $data: JSON
  $customerIpAddress: String

) {
  transactionProcess(
    id: $id
    data: $data
    customerIpAddress: $customerIpAddress
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
      id
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

TRANSACTION_PROCESS_BY_TOKEN = """
mutation TransactionProcess(
  $token: UUID
  $data: JSON
) {
  transactionProcess(
    token: $token
    data: $data
  ) {
    data
    transaction {
      id
      token
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
      id
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
    mocked_process,
    request_event_type=TransactionEventType.CHARGE_REQUEST,
    action_type=TransactionFlowStrategy.CHARGE,
    request_event_include_in_calculations=False,
    data=None,
    authorized_value=Decimal(0),
    charged_value=Decimal(0),
    charge_pending_value=Decimal(0),
    authorize_pending_value=Decimal(0),
    returned_data=None,
):
    assert not content["data"]["transactionProcess"]["errors"]
    response_data = content["data"]["transactionProcess"]
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
        == transaction.charged_value
    )

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

    mocked_process.assert_called_with(
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
                app_identifier=app_identifier, data=data, error=None
            ),
        )
    )


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_process_session")
def test_for_checkout_without_data(
    mocked_process,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    transaction_item_generator,
):
    # given
    expected_amount = Decimal("10.00")

    checkout = checkout_with_prices
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    transaction_item = transaction_item_generator(
        checkout_id=checkout_with_prices.pk, app=webhook_app
    )
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=expected_amount,
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["amount"] = expected_amount
    expected_response["result"] = TransactionEventType.CHARGE_SUCCESS.upper()
    expected_response["pspReference"] = expected_psp_reference
    del expected_response["data"]
    mocked_process.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token),
        "data": None,
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS, variables)

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
        mocked_process=mocked_process,
        charged_value=expected_amount,
        returned_data=None,
    )
    assert checkout.charge_status == CheckoutChargeStatus.PARTIAL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.PARTIAL


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_process_session")
def test_for_order_without_data(
    mocked_process,
    user_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
    transaction_item_generator,
):
    # given
    expected_amount = Decimal("10.00")

    order = order_with_lines
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    transaction_item = transaction_item_generator(order_id=order.pk, app=webhook_app)
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=expected_amount,
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["amount"] = expected_amount
    expected_response["result"] = TransactionEventType.CHARGE_SUCCESS.upper()
    expected_response["pspReference"] = expected_psp_reference
    del expected_response["data"]
    mocked_process.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token),
        "data": None,
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    content = get_graphql_content(response)
    _assert_fields(
        content=content,
        source_object=order,
        expected_amount=expected_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_process=mocked_process,
        charged_value=expected_amount,
        returned_data=None,
    )


@pytest.mark.parametrize(
    ("auto_order_confirmation", "excpected_order_status"),
    [
        (True, OrderStatus.UNFULFILLED),
        (False, OrderStatus.UNCONFIRMED),
    ],
)
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_process_session")
def test_order_status_with_order_confirmation(
    mocked_process,
    auto_order_confirmation,
    excpected_order_status,
    user_api_client,
    unconfirmed_order_with_lines,
    webhook_app,
    transaction_session_response,
    transaction_item_generator,
):
    # given
    order = unconfirmed_order_with_lines
    order.channel.automatically_confirm_all_new_orders = auto_order_confirmation
    order.channel.save(update_fields=["automatically_confirm_all_new_orders"])
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    transaction_item = transaction_item_generator(order_id=order.pk, app=webhook_app)
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=order.total.gross.amount,
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["amount"] = order.total.gross.amount
    expected_response["result"] = TransactionEventType.CHARGE_SUCCESS.upper()
    expected_response["pspReference"] = expected_psp_reference
    del expected_response["data"]
    mocked_process.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token),
        "data": None,
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    content = get_graphql_content(response)
    _assert_fields(
        content=content,
        source_object=order,
        expected_amount=order.total.gross.amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_process=mocked_process,
        charged_value=order.total.gross.amount,
        returned_data=None,
    )

    order.refresh_from_db()
    assert order.status == excpected_order_status
    assert order.charge_status == OrderChargeStatus.FULL


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_process_session")
def test_for_checkout_with_data(
    mocked_process,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    transaction_item_generator,
):
    # given
    expected_amount = Decimal("10.00")

    checkout = checkout_with_prices
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    transaction_item = transaction_item_generator(
        checkout_id=checkout_with_prices.pk, app=webhook_app
    )
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=expected_amount,
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["amount"] = expected_amount
    expected_response["result"] = TransactionEventType.CHARGE_SUCCESS.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_process.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )
    expected_data = {"some": "json-data"}
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token),
        "data": expected_data,
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS, variables)

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
        mocked_process=mocked_process,
        charged_value=expected_amount,
        data=expected_data,
        returned_data=expected_response["data"],
    )
    assert checkout.charge_status == CheckoutChargeStatus.PARTIAL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.PARTIAL


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_process_session")
def test_for_checkout_with_data_via_token(
    mocked_process,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    transaction_item_generator,
):
    # given
    expected_amount = Decimal("10.00")

    checkout = checkout_with_prices
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    transaction_item = transaction_item_generator(
        checkout_id=checkout_with_prices.pk, app=webhook_app
    )
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=expected_amount,
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["amount"] = expected_amount
    expected_response["result"] = TransactionEventType.CHARGE_SUCCESS.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_process.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )
    expected_data = {"some": "json-data"}
    variables = {
        "token": transaction_item.token,
        "data": expected_data,
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS_BY_TOKEN, variables)

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
        mocked_process=mocked_process,
        charged_value=expected_amount,
        data=expected_data,
        returned_data=expected_response["data"],
    )
    assert content["data"]["transactionProcess"]["transaction"]["token"] == str(
        transaction_item.token
    )
    assert checkout.charge_status == CheckoutChargeStatus.PARTIAL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.PARTIAL


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_process_session")
def test_for_order_with_data(
    mocked_process,
    user_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
    transaction_item_generator,
):
    # given
    expected_amount = Decimal("10.00")

    order = order_with_lines
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    transaction_item = transaction_item_generator(order_id=order.pk, app=webhook_app)
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=expected_amount,
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["amount"] = expected_amount
    expected_response["result"] = TransactionEventType.CHARGE_SUCCESS.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_process.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    expected_data = {"some": "json-data"}
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token),
        "data": expected_data,
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    content = get_graphql_content(response)
    _assert_fields(
        content=content,
        source_object=order,
        expected_amount=expected_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_SUCCESS,
        app_identifier=webhook_app.identifier,
        mocked_process=mocked_process,
        charged_value=expected_amount,
        data=expected_data,
        returned_data=expected_response["data"],
    )


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_process_session")
def test_checkout_with_pending_amount(
    mocked_process,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    transaction_item_generator,
):
    # given
    expected_amount = Decimal("10.00")

    checkout = checkout_with_prices
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    transaction_item = transaction_item_generator(
        checkout_id=checkout.pk, app=webhook_app
    )
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=expected_amount,
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["amount"] = expected_amount
    expected_response["result"] = TransactionEventType.CHARGE_REQUEST.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_process.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token)
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    checkout.refresh_from_db()
    content = get_graphql_content(response)
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=expected_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_REQUEST,
        app_identifier=webhook_app.identifier,
        mocked_process=mocked_process,
        charge_pending_value=expected_amount,
        request_event_include_in_calculations=True,
        returned_data=expected_response["data"],
    )
    assert checkout.charge_status == CheckoutChargeStatus.PARTIAL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.PARTIAL


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_process_session")
def test_order_with_pending_amount(
    mocked_process,
    user_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
    transaction_item_generator,
):
    # given
    expected_amount = Decimal("10.00")

    order = order_with_lines
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    transaction_item = transaction_item_generator(order_id=order.pk, app=webhook_app)
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=expected_amount,
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["amount"] = expected_amount
    expected_response["result"] = TransactionEventType.CHARGE_REQUEST.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_process.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token)
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    content = get_graphql_content(response)
    _assert_fields(
        content=content,
        source_object=order,
        expected_amount=expected_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_REQUEST,
        app_identifier=webhook_app.identifier,
        mocked_process=mocked_process,
        charge_pending_value=expected_amount,
        request_event_include_in_calculations=True,
        returned_data=expected_response["data"],
    )


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_process_session")
def test_checkout_with_action_required_response(
    mocked_process,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    transaction_item_generator,
):
    # given
    expected_amount = Decimal("10.00")

    checkout = checkout_with_prices
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    transaction_item = transaction_item_generator(
        checkout_id=checkout.pk, app=webhook_app
    )
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=expected_amount,
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["amount"] = expected_amount
    expected_response["result"] = TransactionEventType.CHARGE_ACTION_REQUIRED.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_process.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token)
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    checkout.refresh_from_db()
    content = get_graphql_content(response)
    _assert_fields(
        content=content,
        source_object=checkout,
        expected_amount=expected_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_ACTION_REQUIRED,
        app_identifier=webhook_app.identifier,
        mocked_process=mocked_process,
        returned_data=expected_response["data"],
    )
    assert checkout.charge_status == CheckoutChargeStatus.NONE
    assert checkout.authorize_status == CheckoutAuthorizeStatus.NONE


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_process_session")
def test_order_with_action_required_response(
    mocked_process,
    user_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
    transaction_item_generator,
):
    # given
    expected_amount = Decimal("10.00")

    order = order_with_lines
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    transaction_item = transaction_item_generator(order_id=order.pk, app=webhook_app)
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=expected_amount,
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["amount"] = expected_amount
    expected_response["result"] = TransactionEventType.CHARGE_ACTION_REQUIRED.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_process.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token)
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    content = get_graphql_content(response)
    _assert_fields(
        content=content,
        source_object=order,
        expected_amount=expected_amount,
        expected_psp_reference=expected_psp_reference,
        response_event_type=TransactionEventType.CHARGE_ACTION_REQUIRED,
        app_identifier=webhook_app.identifier,
        mocked_process=mocked_process,
        returned_data=expected_response["data"],
    )


def test_transaction_already_processed(
    user_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
    transaction_item_generator,
):
    # given
    order = order_with_lines
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    transaction_item = transaction_item_generator(
        order_id=order.pk, app=webhook_app, charged_value=Decimal("10")
    )
    transaction_event = transaction_item.events.get()

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token)
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    assert transaction_item.events.count() == 1
    content = get_graphql_content(response)
    response_data = content["data"]["transactionProcess"]
    transaction_data = response_data["transaction"]
    assert transaction_data["id"] == graphene.Node.to_global_id(
        "TransactionItem", transaction_item.token
    )
    assert response_data["transactionEvent"]["type"] == transaction_event.type.upper()
    assert response_data["transactionEvent"]["id"] == to_global_id_or_none(
        transaction_event
    )


def test_request_event_is_missing(
    user_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
    transaction_item_generator,
):
    # given
    order = order_with_lines
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    transaction_item = transaction_item_generator(
        order_id=order.pk,
        app=webhook_app,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token)
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    content = get_graphql_content(response)
    response_data = content["data"]["transactionProcess"]
    assert len(response_data["errors"]) == 1
    assert response_data["errors"][0]["field"] == "id"
    assert (
        response_data["errors"][0]["code"] == TransactionProcessErrorCode.INVALID.name
    )


def test_transaction_doesnt_have_source_object(
    user_api_client,
    webhook_app,
    transaction_session_response,
    transaction_item_generator,
):
    # given
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    transaction_item = transaction_item_generator(
        app=webhook_app,
    )
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=Decimal("10"),
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token)
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    content = get_graphql_content(response)
    response_data = content["data"]["transactionProcess"]
    assert len(response_data["errors"]) == 1
    assert response_data["errors"][0]["field"] == "id"
    assert (
        response_data["errors"][0]["code"] == TransactionProcessErrorCode.INVALID.name
    )


def test_transaction_doesnt_have_app_identifier(
    order_with_lines,
    user_api_client,
    transaction_session_response,
    transaction_item_generator,
):
    # given
    transaction_item = transaction_item_generator(order_id=order_with_lines.pk)
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=Decimal("10"),
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token)
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    content = get_graphql_content(response)
    response_data = content["data"]["transactionProcess"]
    assert len(response_data["errors"]) == 1
    assert response_data["errors"][0]["field"] == "id"
    assert (
        response_data["errors"][0]["code"]
        == TransactionProcessErrorCode.MISSING_PAYMENT_APP_RELATION.name
    )


def test_app_attached_to_transaction_doesnt_exist(
    order_with_lines,
    user_api_client,
    webhook_app,
    transaction_session_response,
    transaction_item_generator,
):
    # given
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    transaction_item = transaction_item_generator(
        order_id=order_with_lines.pk,
        app=webhook_app,
    )
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=Decimal("10"),
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )
    webhook_app.delete()

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token)
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    content = get_graphql_content(response)
    response_data = content["data"]["transactionProcess"]
    assert len(response_data["errors"]) == 1
    assert response_data["errors"][0]["field"] == "id"
    assert (
        response_data["errors"][0]["code"]
        == TransactionProcessErrorCode.MISSING_PAYMENT_APP.name
    )


@pytest.mark.parametrize(
    "result", [TransactionEventType.CHARGE_REQUEST, TransactionEventType.CHARGE_SUCCESS]
)
@mock.patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_process_session")
def test_checkout_fully_paid(
    mocked_process,
    mocked_fully_paid,
    result,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    plugins_manager,
    transaction_item_generator,
):
    # given
    checkout = checkout_with_prices
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    transaction_item = transaction_item_generator(
        checkout_id=checkout.pk,
        app=webhook_app,
    )
    TransactionEvent.objects.create(
        include_in_calculations=False,
        transaction=transaction_item,
        amount_value=checkout_info.checkout.total_gross_amount,
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["amount"] = str(checkout_info.checkout.total_gross_amount)
    expected_response["result"] = result.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_process.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["transactionProcess"]["errors"]

    checkout.refresh_from_db()
    mocked_fully_paid.assert_called_once_with(checkout)
    assert checkout.charge_status == CheckoutChargeStatus.FULL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL


def test_transaction_process_doesnt_accept_old_id(
    user_api_client,
    order_with_lines,
    webhook_app,
    transaction_session_response,
    transaction_item_generator,
):
    # given
    order = order_with_lines
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    transaction_item = transaction_item_generator(
        order_id=order.pk, app=webhook_app, use_old_id=True
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.pk)
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    content = get_graphql_content(response)
    response_data = content["data"]["transactionProcess"]
    assert len(response_data["errors"]) == 1
    assert response_data["errors"][0]["field"] == "id"
    assert (
        response_data["errors"][0]["code"] == TransactionProcessErrorCode.INVALID.name
    )


def test_transaction_process_for_removed_app(
    user_api_client,
    checkout_with_prices,
    removed_app,
    transaction_item_generator,
):
    # given
    expected_amount = Decimal("10.00")
    expected_app_identifier = "webhook.app.identifier"
    removed_app.identifier = expected_app_identifier
    removed_app.save()

    transaction_item = transaction_item_generator(
        checkout_id=checkout_with_prices.pk, app=removed_app
    )
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=expected_amount,
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token)
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["transactionProcess"]
    assert (
        data["errors"][0]["code"]
        == TransactionProcessErrorCode.MISSING_PAYMENT_APP.name
    )
    assert data["errors"][0]["field"] == "id"


def test_user_missing_permission_for_customer_ip_address(
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    transaction_item_generator,
):
    # given
    checkout = checkout_with_prices

    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("10.00")

    transaction_item = transaction_item_generator(
        checkout_id=checkout.pk, app=webhook_app
    )
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=expected_amount,
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token),
        "data": None,
        "customerIpAddress": "127.0.0.1",
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    assert_no_permission(response)


def test_app_missing_permission_for_customer_ip_address(
    app_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_item_generator,
    transaction_session_response,
):
    # given
    checkout = checkout_with_prices

    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    expected_amount = Decimal("10.00")

    transaction_item = transaction_item_generator(
        checkout_id=checkout.pk, app=webhook_app
    )
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=expected_amount,
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token),
        "data": None,
        "customerIpAddress": "127.0.0.1",
    }

    # when
    response = app_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    assert_no_permission(response)


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_process_session")
def test_with_customer_ip_address(
    mocked_process,
    app_api_client,
    checkout_with_prices,
    transaction_item_generator,
    webhook_app,
    transaction_session_response,
    permission_manage_payments,
):
    # given
    expected_amount = Decimal("10.00")

    checkout = checkout_with_prices
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    transaction_item = transaction_item_generator(
        checkout_id=checkout_with_prices.pk, app=webhook_app
    )
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=expected_amount,
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    mocked_process.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=transaction_session_response
    )

    app_api_client.app.permissions.set([permission_manage_payments])

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token),
        "data": None,
        "customerIpAddress": "127.0.0.2",
    }

    # when
    response = app_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    get_graphql_content(response)

    mocked_process.assert_called_with(
        TransactionSessionData(
            transaction=transaction_item,
            source_object=checkout,
            action=TransactionProcessActionData(
                action_type=TransactionFlowStrategy.CHARGE,
                amount=expected_amount,
                currency=checkout.currency,
            ),
            customer_ip_address="127.0.0.2",
            payment_gateway_data=PaymentGatewayData(
                app_identifier=webhook_app.identifier, data=None, error=None
            ),
        )
    )


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_process_session")
def test_sets_customer_ip_address_when_not_provided(
    mocked_process,
    app_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    transaction_item_generator,
    permission_manage_payments,
):
    # given
    expected_amount = Decimal("10.00")

    checkout = checkout_with_prices
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    transaction_item = transaction_item_generator(
        checkout_id=checkout_with_prices.pk, app=webhook_app
    )
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=expected_amount,
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    mocked_process.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=transaction_session_response
    )

    app_api_client.app.permissions.set([permission_manage_payments])

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token),
        "data": None,
    }

    # when
    response = app_api_client.post_graphql(
        TRANSACTION_PROCESS, variables, REMOTE_ADDR="127.0.0.2"
    )

    # then
    get_graphql_content(response)

    mocked_process.assert_called_with(
        TransactionSessionData(
            transaction=transaction_item,
            source_object=checkout,
            action=TransactionProcessActionData(
                action_type=TransactionFlowStrategy.CHARGE,
                amount=expected_amount,
                currency=checkout.currency,
            ),
            customer_ip_address="127.0.0.2",
            payment_gateway_data=PaymentGatewayData(
                app_identifier=webhook_app.identifier, data=None, error=None
            ),
        )
    )


def test_customer_ip_address_wrong_format(
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    permission_manage_payments,
    transaction_item_generator,
    app_api_client,
):
    # given
    expected_amount = Decimal("10.00")

    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    transaction_item = transaction_item_generator(
        checkout_id=checkout_with_prices.pk, app=webhook_app
    )
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=expected_amount,
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    app_api_client.app.permissions.set([permission_manage_payments])

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token),
        "data": None,
        "customerIpAddress": "127.0.02",
    }
    # when
    response = app_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    content = get_graphql_content(response)

    errors = content["data"]["transactionProcess"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "customerIpAddress"
    assert errors[0]["code"] == TransactionProcessErrorCode.INVALID.name


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_process_session")
def test_customer_ip_address_ipv6(
    mocked_process,
    app_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    permission_manage_payments,
    transaction_item_generator,
):
    # given
    expected_amount = Decimal("10.00")

    checkout = checkout_with_prices
    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    transaction_item = transaction_item_generator(
        checkout_id=checkout_with_prices.pk, app=webhook_app
    )
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=expected_amount,
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    mocked_process.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=transaction_session_response
    )

    app_api_client.app.permissions.set([permission_manage_payments])

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token),
        "data": None,
        "customerIpAddress": "::1",
    }

    # when
    response = app_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    get_graphql_content(response)

    mocked_process.assert_called_with(
        TransactionSessionData(
            transaction=transaction_item,
            source_object=checkout,
            action=TransactionProcessActionData(
                action_type=TransactionFlowStrategy.CHARGE,
                amount=expected_amount,
                currency=checkout.currency,
            ),
            customer_ip_address="::1",
            payment_gateway_data=PaymentGatewayData(
                app_identifier=webhook_app.identifier, data=None, error=None
            ),
        )
    )


def test_transaction_process_for_disabled_app(
    user_api_client,
    checkout_with_prices,
    app,
    transaction_item_generator,
):
    # given
    expected_amount = Decimal("10.00")
    expected_app_identifier = "webhook.app.identifier"
    app.identifier = expected_app_identifier
    app.is_active = False
    app.save()

    transaction_item = transaction_item_generator(
        checkout_id=checkout_with_prices.pk, app=app
    )
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=expected_amount,
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token)
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["transactionProcess"]
    assert (
        data["errors"][0]["code"]
        == TransactionProcessErrorCode.MISSING_PAYMENT_APP.name
    )
    assert data["errors"][0]["field"] == "id"


@freeze_time("2023-03-18 12:00:00")
@pytest.mark.parametrize(
    "previous_last_transaction_modified_at",
    [None, datetime.datetime(2020, 1, 1, tzinfo=pytz.UTC)],
)
@mock.patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
@mock.patch("saleor.plugins.manager.PluginsManager.transaction_process_session")
def test_updates_checkout_last_transaction_modified_at(
    mocked_process,
    mocked_fully_paid,
    previous_last_transaction_modified_at,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    plugins_manager,
    transaction_item_generator,
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

    transaction_item = transaction_item_generator(
        checkout_id=checkout.pk,
        app=webhook_app,
    )
    TransactionEvent.objects.create(
        include_in_calculations=False,
        transaction=transaction_item,
        amount_value=checkout_info.checkout.total_gross_amount,
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["amount"] = str(checkout_info.checkout.total_gross_amount)
    expected_response["result"] = TransactionEventType.CHARGE_SUCCESS.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_process.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token),
        "paymentGateway": {"id": expected_app_identifier, "data": None},
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["transactionProcess"]["errors"]

    checkout.refresh_from_db()
    transaction = checkout.payment_transactions.first()
    assert checkout.last_transaction_modified_at == transaction.modified_at
    assert (
        checkout.last_transaction_modified_at != previous_last_transaction_modified_at
    )


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_process_session")
def test_for_locked_checkout(
    mocked_process,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    transaction_item_generator,
):
    # given
    expected_amount = Decimal("10.00")

    checkout = checkout_with_prices
    checkout.completing_started_at = timezone.now()
    checkout.save(update_fields=["completing_started_at"])

    expected_app_identifier = "webhook.app.identifier"
    webhook_app.identifier = expected_app_identifier
    webhook_app.save()

    transaction_item = transaction_item_generator(
        checkout_id=checkout_with_prices.pk, app=webhook_app
    )
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=expected_amount,
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["amount"] = expected_amount
    expected_response["result"] = TransactionEventType.CHARGE_SUCCESS.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_process.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )
    expected_data = {"some": "json-data"}
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token),
        "data": expected_data,
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["transactionProcess"]
    assert len(data["errors"]) == 1
    assert (
        data["errors"][0]["code"]
        == TransactionProcessErrorCode.CHECKOUT_COMPLETION_IN_PROGRESS.name
    )
    assert data["errors"][0]["field"] == "id"
    mocked_process.assert_not_called()


@mock.patch("saleor.plugins.manager.PluginsManager.transaction_process_session")
def test_for_checkout_with_payments(
    mocked_process,
    user_api_client,
    checkout_with_prices,
    webhook_app,
    transaction_session_response,
    transaction_item_generator,
):
    # given
    expected_amount = Decimal("10.00")

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

    transaction_item = transaction_item_generator(
        checkout_id=checkout_with_prices.pk, app=webhook_app
    )
    TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=expected_amount,
        currency=transaction_item.currency,
        type=TransactionEventType.CHARGE_REQUEST,
    )

    expected_psp_reference = "ppp-123"
    expected_response = transaction_session_response.copy()
    expected_response["amount"] = expected_amount
    expected_response["result"] = TransactionEventType.CHARGE_SUCCESS.upper()
    expected_response["pspReference"] = expected_psp_reference
    mocked_process.return_value = TransactionSessionResult(
        app_identifier=expected_app_identifier, response=expected_response
    )
    expected_data = {"some": "json-data"}
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token),
        "data": expected_data,
    }

    # when
    response = user_api_client.post_graphql(TRANSACTION_PROCESS, variables)

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
        mocked_process=mocked_process,
        charged_value=expected_amount,
        data=expected_data,
        returned_data=expected_response["data"],
    )
    assert checkout.charge_status == CheckoutChargeStatus.PARTIAL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.PARTIAL
    for payment in payments:
        payment.refresh_from_db()
        assert payment.is_active is False
