from decimal import Decimal
from unittest import mock

from django.conf import settings
from django.test import override_settings

from .....checkout.calculations import fetch_checkout_data
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....payment.interface import PaymentGatewayData
from .....payment.models import TransactionItem
from ....core.enums import PaymentGatewayConfigErrorCode, TransactionInitializeErrorCode
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

PAYMENT_GATEWAY_INITIALIZE = """
mutation PaymentGatewayInitialize(
    $id: ID!,
    $amount: PositiveDecimal,
    $paymentGateways: [PaymentGatewayToInitialize!]
) {
  paymentGatewayInitialize(
    id: $id
    amount: $amount
    paymentGateways: $paymentGateways
  ) {
    gatewayConfigs {
      id
      data
      errors {
        field
        message
        code
      }
    }
    errors {
      field
      message
      code
    }
  }
}
"""


@mock.patch("saleor.plugins.manager.PluginsManager.payment_gateway_initialize_session")
def test_for_checkout_without_payment_gateways(
    mocked_initialize, user_api_client, checkout_with_prices, plugins_manager
):
    # given
    checkout = checkout_with_prices
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)
    checkout = checkout_info.checkout
    expected_app_identifier = "app.id"
    expected_data = {"json": "data"}
    expected_response = {"data": expected_data}

    mocked_initialize.return_value = [
        PaymentGatewayData(
            app_identifier=expected_app_identifier, data=expected_response
        )
    ]

    variables = {"id": to_global_id_or_none(checkout), "paymentGateways": None}

    # when
    response = user_api_client.post_graphql(PAYMENT_GATEWAY_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["paymentGatewayInitialize"]["errors"]
    assert content["data"]
    assert len(content["data"]["paymentGatewayInitialize"]["gatewayConfigs"]) == 1
    gateway_config = content["data"]["paymentGatewayInitialize"]["gatewayConfigs"][0]
    assert gateway_config == {
        "id": expected_app_identifier,
        "data": expected_data,
        "errors": [],
    }
    mocked_initialize.assert_called_once_with(checkout.total.gross.amount, [], checkout)


@override_settings(TRANSACTION_ITEMS_LIMIT=3)
def test_for_checkout_transactions_limit_on_gateway_initialize(
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
        "id": to_global_id_or_none(checkout_with_prices),
        "paymentGateways": None,
    }

    # when
    response = user_api_client.post_graphql(PAYMENT_GATEWAY_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentGatewayInitialize"]
    assert data["errors"]
    error = data["errors"][0]
    assert error["code"] == TransactionInitializeErrorCode.INVALID.name
    assert error["field"] == "id"
    assert error["message"] == (
        "Checkout transactions limit of " f"{settings.TRANSACTION_ITEMS_LIMIT} reached."
    )


@mock.patch("saleor.plugins.manager.PluginsManager.payment_gateway_initialize_session")
def test_for_order_without_payment_gateways(
    mocked_initialize,
    user_api_client,
    order_with_lines,
):
    # given
    order = order_with_lines
    expected_app_identifier = "app.id"
    expected_data = {"json": "data"}
    expected_response = {"data": expected_data}

    mocked_initialize.return_value = [
        PaymentGatewayData(
            app_identifier=expected_app_identifier, data=expected_response
        )
    ]

    variables = {"id": to_global_id_or_none(order), "paymentGateways": None}

    # when
    response = user_api_client.post_graphql(PAYMENT_GATEWAY_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["paymentGatewayInitialize"]["errors"]
    assert content["data"]
    assert len(content["data"]["paymentGatewayInitialize"]["gatewayConfigs"]) == 1
    gateway_config = content["data"]["paymentGatewayInitialize"]["gatewayConfigs"][0]
    assert gateway_config == {
        "id": expected_app_identifier,
        "data": expected_data,
        "errors": [],
    }

    mocked_initialize.assert_called_once_with(order.total.gross.amount, [], order)


@mock.patch("saleor.plugins.manager.PluginsManager.payment_gateway_initialize_session")
def test_for_checkout_with_payment_gateways(
    mocked_initialize, user_api_client, checkout_with_prices, plugins_manager
):
    # given
    checkout = checkout_with_prices
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)
    checkout = checkout_info.checkout

    expected_app_identifier = "app.id"
    expected_data = {"json": "data"}
    expected_input_data = {"input": "json"}
    expected_response = {"data": expected_data}

    mocked_initialize.return_value = [
        PaymentGatewayData(
            app_identifier=expected_app_identifier, data=expected_response
        )
    ]

    variables = {
        "id": to_global_id_or_none(checkout),
        "paymentGateways": [
            {"id": expected_app_identifier, "data": expected_input_data}
        ],
    }

    # when
    response = user_api_client.post_graphql(PAYMENT_GATEWAY_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["paymentGatewayInitialize"]["errors"]
    assert content["data"]
    assert len(content["data"]["paymentGatewayInitialize"]["gatewayConfigs"]) == 1
    gateway_config = content["data"]["paymentGatewayInitialize"]["gatewayConfigs"][0]
    assert gateway_config == {
        "id": expected_app_identifier,
        "data": expected_data,
        "errors": [],
    }

    mocked_initialize.assert_called_once_with(
        checkout.total.gross.amount,
        [
            PaymentGatewayData(
                app_identifier=expected_app_identifier, data=expected_input_data
            )
        ],
        checkout,
    )


@mock.patch("saleor.plugins.manager.PluginsManager.payment_gateway_initialize_session")
def test_for_order_with_payment_gateways(
    mocked_initialize,
    user_api_client,
    order_with_lines,
):
    # given
    order = order_with_lines
    expected_app_identifier = "app.id"
    expected_data = {"json": "data"}
    expected_input_data = {"input": "json"}
    expected_response = {"data": expected_data}

    mocked_initialize.return_value = [
        PaymentGatewayData(
            app_identifier=expected_app_identifier, data=expected_response
        )
    ]

    variables = {
        "id": to_global_id_or_none(order),
        "paymentGateways": [
            {"id": expected_app_identifier, "data": expected_input_data}
        ],
    }

    # when
    response = user_api_client.post_graphql(PAYMENT_GATEWAY_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["paymentGatewayInitialize"]["errors"]
    assert content["data"]
    assert len(content["data"]["paymentGatewayInitialize"]["gatewayConfigs"]) == 1
    gateway_config = content["data"]["paymentGatewayInitialize"]["gatewayConfigs"][0]
    assert gateway_config == {
        "id": expected_app_identifier,
        "data": expected_data,
        "errors": [],
    }

    mocked_initialize.assert_called_once_with(
        order.total.gross.amount,
        [
            PaymentGatewayData(
                app_identifier=expected_app_identifier, data=expected_input_data
            )
        ],
        order,
    )


@mock.patch("saleor.plugins.manager.PluginsManager.payment_gateway_initialize_session")
def test_for_checkout_with_payment_gateways_and_amount(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
):
    # given
    checkout = checkout_with_prices
    expected_app_identifier = "app.id"
    expected_data = {"json": "data"}
    expected_response = {"data": expected_data}
    expected_input_data = {"input": "json"}
    excpected_amount = Decimal(30)

    mocked_initialize.return_value = [
        PaymentGatewayData(
            app_identifier=expected_app_identifier, data=expected_response
        )
    ]

    variables = {
        "id": to_global_id_or_none(checkout),
        "amount": excpected_amount,
        "paymentGateways": [
            {"id": expected_app_identifier, "data": expected_input_data}
        ],
    }

    # when
    response = user_api_client.post_graphql(PAYMENT_GATEWAY_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["paymentGatewayInitialize"]["errors"]
    assert content["data"]
    assert len(content["data"]["paymentGatewayInitialize"]["gatewayConfigs"]) == 1
    gateway_config = content["data"]["paymentGatewayInitialize"]["gatewayConfigs"][0]
    assert gateway_config == {
        "id": expected_app_identifier,
        "data": expected_data,
        "errors": [],
    }

    mocked_initialize.assert_called_once_with(
        excpected_amount,
        [
            PaymentGatewayData(
                app_identifier=expected_app_identifier, data=expected_input_data
            )
        ],
        checkout,
    )


@mock.patch("saleor.plugins.manager.PluginsManager.payment_gateway_initialize_session")
def test_for_order_with_payment_gateways_and_amount(
    mocked_initialize,
    user_api_client,
    order_with_lines,
):
    # given
    order = order_with_lines
    expected_app_identifier = "app.id"
    expected_data = {"json": "data"}
    expected_response = {"data": expected_data}
    expected_input_data = {"input": "json"}
    excpected_amount = Decimal(30)
    mocked_initialize.return_value = [
        PaymentGatewayData(
            app_identifier=expected_app_identifier, data=expected_response
        )
    ]
    variables = {
        "id": to_global_id_or_none(order),
        "amount": excpected_amount,
        "paymentGateways": [
            {"id": expected_app_identifier, "data": expected_input_data}
        ],
    }

    # when
    response = user_api_client.post_graphql(PAYMENT_GATEWAY_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["paymentGatewayInitialize"]["errors"]
    assert content["data"]
    assert len(content["data"]["paymentGatewayInitialize"]["gatewayConfigs"]) == 1
    gateway_config = content["data"]["paymentGatewayInitialize"]["gatewayConfigs"][0]
    assert gateway_config == {
        "id": expected_app_identifier,
        "data": expected_data,
        "errors": [],
    }

    mocked_initialize.assert_called_once_with(
        excpected_amount,
        [
            PaymentGatewayData(
                app_identifier=expected_app_identifier, data=expected_input_data
            )
        ],
        order,
    )


@mock.patch("saleor.plugins.manager.PluginsManager.payment_gateway_initialize_session")
def test_for_checkout_with_payment_gateways_returns_error(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
):
    # given
    checkout = checkout_with_prices
    expected_app_identifier = "app.id"
    expected_error_msg = "Cannot fetch."
    expected_input_data = {"input": "json"}
    excpected_amount = Decimal(30)

    mocked_initialize.return_value = [
        PaymentGatewayData(
            app_identifier=expected_app_identifier, data=None, error=expected_error_msg
        )
    ]

    variables = {
        "id": to_global_id_or_none(checkout),
        "amount": excpected_amount,
        "paymentGateways": [
            {"id": expected_app_identifier, "data": expected_input_data}
        ],
    }

    # when
    response = user_api_client.post_graphql(PAYMENT_GATEWAY_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["paymentGatewayInitialize"]["errors"]
    assert content["data"]
    assert len(content["data"]["paymentGatewayInitialize"]["gatewayConfigs"]) == 1
    gateway_config = content["data"]["paymentGatewayInitialize"]["gatewayConfigs"][0]
    assert gateway_config == {
        "id": expected_app_identifier,
        "data": None,
        "errors": [
            {
                "field": "id",
                "message": expected_error_msg,
                "code": PaymentGatewayConfigErrorCode.INVALID.name,
            }
        ],
    }

    mocked_initialize.assert_called_once_with(
        excpected_amount,
        [
            PaymentGatewayData(
                app_identifier=expected_app_identifier, data=expected_input_data
            )
        ],
        checkout,
    )


@mock.patch("saleor.plugins.manager.PluginsManager.payment_gateway_initialize_session")
def test_for_order_with_payment_gateways_returns_error(
    mocked_initialize,
    user_api_client,
    order_with_lines,
):
    # given
    order = order_with_lines
    expected_app_identifier = "app.id"

    expected_input_data = {"input": "json"}
    excpected_amount = Decimal(30)
    expected_error_msg = "Cannot fetch."
    mocked_initialize.return_value = [
        PaymentGatewayData(
            app_identifier=expected_app_identifier, data=None, error=expected_error_msg
        )
    ]
    variables = {
        "id": to_global_id_or_none(order),
        "amount": excpected_amount,
        "paymentGateways": [
            {"id": expected_app_identifier, "data": expected_input_data}
        ],
    }

    # when
    response = user_api_client.post_graphql(PAYMENT_GATEWAY_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["paymentGatewayInitialize"]["errors"]
    assert content["data"]
    assert len(content["data"]["paymentGatewayInitialize"]["gatewayConfigs"]) == 1
    gateway_config = content["data"]["paymentGatewayInitialize"]["gatewayConfigs"][0]
    assert gateway_config == {
        "id": expected_app_identifier,
        "data": None,
        "errors": [
            {
                "field": "id",
                "message": expected_error_msg,
                "code": PaymentGatewayConfigErrorCode.INVALID.name,
            }
        ],
    }

    mocked_initialize.assert_called_once_with(
        excpected_amount,
        [
            PaymentGatewayData(
                app_identifier=expected_app_identifier, data=expected_input_data
            )
        ],
        order,
    )


@mock.patch("saleor.plugins.manager.PluginsManager.payment_gateway_initialize_session")
def test_for_checkout_with_missing_payment_gateway(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
):
    # given
    checkout = checkout_with_prices
    expected_app_identifier = "app.id"
    expected_error_msg = (
        "Active app with `HANDLE_PAYMENT` permissions or app webhook not found."
    )
    expected_input_data = {"input": "json"}
    excpected_amount = Decimal(30)

    mocked_initialize.return_value = []

    variables = {
        "id": to_global_id_or_none(checkout),
        "amount": excpected_amount,
        "paymentGateways": [
            {"id": expected_app_identifier, "data": expected_input_data}
        ],
    }

    # when
    response = user_api_client.post_graphql(PAYMENT_GATEWAY_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["paymentGatewayInitialize"]["errors"]
    assert content["data"]
    assert len(content["data"]["paymentGatewayInitialize"]["gatewayConfigs"]) == 1
    gateway_config = content["data"]["paymentGatewayInitialize"]["gatewayConfigs"][0]
    assert gateway_config == {
        "id": expected_app_identifier,
        "data": None,
        "errors": [
            {
                "field": "id",
                "message": expected_error_msg,
                "code": PaymentGatewayConfigErrorCode.NOT_FOUND.name,
            }
        ],
    }

    mocked_initialize.assert_called_once_with(
        excpected_amount,
        [
            PaymentGatewayData(
                app_identifier=expected_app_identifier, data=expected_input_data
            )
        ],
        checkout,
    )


@mock.patch("saleor.plugins.manager.PluginsManager.payment_gateway_initialize_session")
def test_for_order_with_missing_payment_gateway(
    mocked_initialize,
    user_api_client,
    order_with_lines,
):
    # given
    order = order_with_lines
    expected_app_identifier = "app.id"

    expected_input_data = {"input": "json"}
    excpected_amount = Decimal(30)
    expected_error_msg = (
        "Active app with `HANDLE_PAYMENT` permissions or app webhook not found."
    )
    mocked_initialize.return_value = []
    variables = {
        "id": to_global_id_or_none(order),
        "amount": excpected_amount,
        "paymentGateways": [
            {"id": expected_app_identifier, "data": expected_input_data}
        ],
    }

    # when
    response = user_api_client.post_graphql(PAYMENT_GATEWAY_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["paymentGatewayInitialize"]["errors"]
    assert content["data"]
    assert len(content["data"]["paymentGatewayInitialize"]["gatewayConfigs"]) == 1
    gateway_config = content["data"]["paymentGatewayInitialize"]["gatewayConfigs"][0]
    assert gateway_config == {
        "id": expected_app_identifier,
        "data": None,
        "errors": [
            {
                "field": "id",
                "message": expected_error_msg,
                "code": PaymentGatewayConfigErrorCode.NOT_FOUND.name,
            }
        ],
    }

    mocked_initialize.assert_called_once_with(
        excpected_amount,
        [
            PaymentGatewayData(
                app_identifier=expected_app_identifier, data=expected_input_data
            )
        ],
        order,
    )


@mock.patch("saleor.plugins.manager.PluginsManager.payment_gateway_initialize_session")
def test_for_checkout_with_multiple_payment_gateways(
    mocked_initialize,
    user_api_client,
    checkout_with_prices,
):
    # given
    checkout = checkout_with_prices
    excpected_amount = Decimal(30)
    first_expected_app_identifier = "app.id"
    first_expected_data = {"json": "data"}
    first_expected_response = {"data": first_expected_data}
    first_expected_input_data = {"input": "json"}

    second_expected_input_data = {"input": "json2"}
    second_error_msg = "Cannot fetch"
    second_expected_app_identifier = "app.id2"

    third_expected_app_identifier = "app.id3"
    third_expected_input_data = {"input": "json3"}

    expected_error_msg = (
        "Active app with `HANDLE_PAYMENT` permissions or app webhook not found."
    )

    mocked_initialize.return_value = [
        PaymentGatewayData(
            app_identifier=first_expected_app_identifier, data=first_expected_response
        ),
        PaymentGatewayData(
            app_identifier=second_expected_app_identifier, error=second_error_msg
        ),
    ]

    variables = {
        "id": to_global_id_or_none(checkout),
        "amount": excpected_amount,
        "paymentGateways": [
            {"id": first_expected_app_identifier, "data": first_expected_input_data},
            {"id": second_expected_app_identifier, "data": second_expected_input_data},
            {"id": third_expected_app_identifier, "data": third_expected_input_data},
        ],
    }

    # when
    response = user_api_client.post_graphql(PAYMENT_GATEWAY_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["paymentGatewayInitialize"]["errors"]
    assert content["data"]
    assert len(content["data"]["paymentGatewayInitialize"]["gatewayConfigs"]) == 3
    configs = content["data"]["paymentGatewayInitialize"]["gatewayConfigs"]
    first_gateway = [c for c in configs if c["id"] == first_expected_app_identifier][0]
    second_gateway = [c for c in configs if c["id"] == second_expected_app_identifier][
        0
    ]
    third_gateway = [c for c in configs if c["id"] == third_expected_app_identifier][0]

    assert first_gateway == {
        "id": first_expected_app_identifier,
        "data": first_expected_data,
        "errors": [],
    }

    assert second_gateway == {
        "id": second_expected_app_identifier,
        "data": None,
        "errors": [
            {
                "field": "id",
                "message": second_error_msg,
                "code": PaymentGatewayConfigErrorCode.INVALID.name,
            }
        ],
    }
    assert third_gateway == {
        "id": third_expected_app_identifier,
        "data": None,
        "errors": [
            {
                "field": "id",
                "message": expected_error_msg,
                "code": PaymentGatewayConfigErrorCode.NOT_FOUND.name,
            }
        ],
    }
    mocked_initialize.assert_called_once_with(
        excpected_amount,
        [
            PaymentGatewayData(
                app_identifier=first_expected_app_identifier,
                data=first_expected_input_data,
            ),
            PaymentGatewayData(
                app_identifier=second_expected_app_identifier,
                data=second_expected_input_data,
            ),
            PaymentGatewayData(
                app_identifier=third_expected_app_identifier,
                data=third_expected_input_data,
            ),
        ],
        checkout,
    )


@mock.patch("saleor.plugins.manager.PluginsManager.payment_gateway_initialize_session")
def test_for_order_with_multiple_payment_gateways(
    mocked_initialize,
    user_api_client,
    order_with_lines,
):
    # given
    order = order_with_lines
    excpected_amount = Decimal(30)
    first_expected_app_identifier = "app.id"
    first_expected_data = {"json": "data"}
    first_expected_response = {"data": first_expected_data}
    first_expected_input_data = {"input": "json"}

    second_expected_input_data = {"input": "json2"}
    second_error_msg = "Cannot fetch"
    second_expected_app_identifier = "app.id2"

    third_expected_app_identifier = "app.id3"
    third_expected_input_data = {"input": "json3"}

    expected_error_msg = (
        "Active app with `HANDLE_PAYMENT` permissions or app webhook not found."
    )

    mocked_initialize.return_value = [
        PaymentGatewayData(
            app_identifier=first_expected_app_identifier, data=first_expected_response
        ),
        PaymentGatewayData(
            app_identifier=second_expected_app_identifier, error=second_error_msg
        ),
    ]

    variables = {
        "id": to_global_id_or_none(order),
        "amount": excpected_amount,
        "paymentGateways": [
            {"id": first_expected_app_identifier, "data": first_expected_input_data},
            {"id": second_expected_app_identifier, "data": second_expected_input_data},
            {"id": third_expected_app_identifier, "data": third_expected_input_data},
        ],
    }

    # when
    response = user_api_client.post_graphql(PAYMENT_GATEWAY_INITIALIZE, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["paymentGatewayInitialize"]["errors"]
    assert content["data"]
    assert len(content["data"]["paymentGatewayInitialize"]["gatewayConfigs"]) == 3
    configs = content["data"]["paymentGatewayInitialize"]["gatewayConfigs"]
    first_gateway = [c for c in configs if c["id"] == first_expected_app_identifier][0]
    second_gateway = [c for c in configs if c["id"] == second_expected_app_identifier][
        0
    ]
    third_gateway = [c for c in configs if c["id"] == third_expected_app_identifier][0]

    assert first_gateway == {
        "id": first_expected_app_identifier,
        "data": first_expected_data,
        "errors": [],
    }

    assert second_gateway == {
        "id": second_expected_app_identifier,
        "data": None,
        "errors": [
            {
                "field": "id",
                "message": second_error_msg,
                "code": PaymentGatewayConfigErrorCode.INVALID.name,
            }
        ],
    }
    assert third_gateway == {
        "id": third_expected_app_identifier,
        "data": None,
        "errors": [
            {
                "field": "id",
                "message": expected_error_msg,
                "code": PaymentGatewayConfigErrorCode.NOT_FOUND.name,
            }
        ],
    }
    mocked_initialize.assert_called_once_with(
        excpected_amount,
        [
            PaymentGatewayData(
                app_identifier=first_expected_app_identifier,
                data=first_expected_input_data,
            ),
            PaymentGatewayData(
                app_identifier=second_expected_app_identifier,
                data=second_expected_input_data,
            ),
            PaymentGatewayData(
                app_identifier=third_expected_app_identifier,
                data=third_expected_input_data,
            ),
        ],
        order,
    )
