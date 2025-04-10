from unittest import mock

import pytest

from ....order.models import Order
from ....payment.interface import PaymentGatewayData
from ...tests.utils import get_graphql_content, get_graphql_content_from_response
from ..utils import to_global_id_or_none

QUERY_CHECKOUT = """
query getCheckout($token: UUID!) {
    checkout(token: $token) {
        token
    }
}
"""


def test_uuid_scalar_value_passed_as_variable(api_client, checkout):
    variables = {"token": str(checkout.token)}
    response = api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_uuid_scalar_wrong_value_passed_as_variable(api_client, checkout):
    variables = {"token": "wrong-token"}
    response = api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1


def test_uuid_scalar_value_passed_in_input(api_client, checkout):
    token = checkout.token

    query = f"""
        query{{
            checkout(token: "{token}") {{
                token
            }}
        }}
    """
    response = api_client.post_graphql(query)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_uuid_scalar_wrong_value_passed_in_input(api_client, checkout):
    token = "wrong-token"

    query = f"""
        query{{
            checkout(token: "{token}") {{
                token
            }}
        }}
    """
    response = api_client.post_graphql(query)
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1


@pytest.mark.parametrize(
    "orders_filter",
    [
        {"created": {"gte": ""}},
        {"created": {"lte": ""}},
        {"created": {"gte": "", "lte": ""}},
    ],
)
def test_order_query_with_filter_created_str_as_date_value(
    orders_filter,
    staff_api_client,
    permission_manage_orders,
    channel_USD,
):
    # given
    query = """
      query ($filter: OrderFilterInput!, ) {
        orders(first: 5, filter:$filter) {
          totalCount
          edges {
            node {
              id
            }
          }
        }
      }
    """

    Order.objects.create(channel=channel_USD)
    variables = {"filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content_from_response(response)

    assert 'Variable "$filter" got invalid value' in content["errors"][0]["message"]


PAYMENT_GATEWAY_INITIALIZE_WITH_VARIABLES = """
mutation PaymentGatewayInitialize(
    $id: ID!,
    $paymentGateways: [PaymentGatewayToInitialize!]
) {
  paymentGatewayInitialize(
    id: $id
    paymentGateways: $paymentGateways
  ) {
    gatewayConfigs {
      id
    }
  }
}
"""


@pytest.mark.parametrize(
    "data",
    [
        {"input": "json"},
        None,
        {},
        [{"input": [{"json": "a"}]}, {}],
        [
            {
                "input": [
                    {
                        "json": [
                            "a",
                        ]
                    }
                ]
            },
            {},
        ],
        [1, 2, 3],
    ],
)
@mock.patch("saleor.plugins.manager.PluginsManager.payment_gateway_initialize_session")
def test_json_scalar_as_correct_variable(
    mocked_initialize, data, user_api_client, checkout_with_prices, plugins_manager
):
    # given
    checkout = checkout_with_prices

    mocked_initialize.return_value = [
        PaymentGatewayData(app_identifier="app.id", data={"data": data})
    ]

    variables = {
        "id": to_global_id_or_none(checkout),
        "paymentGateways": [{"id": "app.id", "data": data}],
    }

    # when
    response = user_api_client.post_graphql(
        PAYMENT_GATEWAY_INITIALIZE_WITH_VARIABLES, variables
    )

    # then
    get_graphql_content(response)


@pytest.mark.parametrize("data_value", [True, "string", 1.0, 1])
@mock.patch("saleor.plugins.manager.PluginsManager.payment_gateway_initialize_session")
def test_json_scalar_as_incorrect_variable(
    mocked_initialize,
    data_value,
    user_api_client,
    checkout_with_prices,
    plugins_manager,
):
    # given
    checkout = checkout_with_prices

    mocked_initialize.return_value = [
        PaymentGatewayData(app_identifier="app.id", data={"data": {"json": "data"}})
    ]

    variables = {
        "id": to_global_id_or_none(checkout),
        "paymentGateways": [{"id": "app.id", "data": data_value}],
    }

    # when
    response = user_api_client.post_graphql(
        PAYMENT_GATEWAY_INITIALIZE_WITH_VARIABLES, variables
    )

    # then
    content = get_graphql_content_from_response(response)
    assert "errors" in content


PAYMENT_GATEWAY_INITIALIZE_WITHOUT_VARIABLES = """
mutation {
  paymentGatewayInitialize(
    id: "%s"
    paymentGateways: [{id: "app.id", data: %s}]
  ) {
    gatewayConfigs {
      id
    }
  }
}
"""


@pytest.mark.parametrize("data_value", [True, "string", 1.0, 1])
@mock.patch("saleor.plugins.manager.PluginsManager.payment_gateway_initialize_session")
def test_json_scalar_as_incorrect_value(
    mocked_initialize,
    data_value,
    user_api_client,
    checkout_with_prices,
    plugins_manager,
):
    # given
    checkout = checkout_with_prices

    mocked_initialize.return_value = [
        PaymentGatewayData(app_identifier="app.id", data={"data": {"json": "data"}})
    ]

    query = PAYMENT_GATEWAY_INITIALIZE_WITHOUT_VARIABLES % (
        to_global_id_or_none(checkout),
        data_value,
    )

    # when
    response = user_api_client.post_graphql(
        query,
    )

    # then
    content = get_graphql_content_from_response(response)
    assert "errors" in content


@pytest.mark.parametrize(
    "data",
    [
        '{input: "json"}',
        "{}",
        '[{input: "json"}]',
        '[{input: "json"}, {}]',
        '[{input: [{json: "aa"}]}, {input: {json: [{}]}}]',
        '[{input: [{json: [{json2: ["aa",]}]}]}, {}]',
        "[1,2,3]",
    ],
)
@mock.patch("saleor.plugins.manager.PluginsManager.payment_gateway_initialize_session")
def test_json_scalar_as_correct_value(
    mocked_initialize, data, user_api_client, checkout_with_prices, plugins_manager
):
    # given
    checkout = checkout_with_prices
    mocked_initialize.return_value = [
        PaymentGatewayData(app_identifier="app.id", data={"data": {"response": "data"}})
    ]
    query = PAYMENT_GATEWAY_INITIALIZE_WITHOUT_VARIABLES % (
        to_global_id_or_none(checkout),
        data,
    )

    # when
    response = user_api_client.post_graphql(query)

    # then
    get_graphql_content(response)


DATE_TIME_QUERY_WITH_VARIABLE = """
mutation vv($startDate: DateTime){
	voucherCreate(input:{
		type:SHIPPING, code:"test12", startDate: $startDate
	}){
		errors{
			code
		}
		voucher{
			id
			startDate
		}
	}
}
"""


@pytest.mark.parametrize(
    "start_date",
    [
        "0000-01-01T00:00:00+00:00",
        "0001-01-01T00:00:01+07:00",
        "0001-01-01T00:00:01+01:00",
        "0001-01-01T00:00:00+00:01",
        "0001-12-31 17:00:01+00 BC",
        "9999-12-31T23:59:59-07:00",
    ],
)
def test_incorrect_date_time_as_variable(
    start_date, staff_api_client, permission_manage_discounts
):
    # given
    variables = {"startDate": start_date}
    staff_api_client.user.user_permissions.add(permission_manage_discounts)

    # when
    response = staff_api_client.post_graphql(DATE_TIME_QUERY_WITH_VARIABLE, variables)

    # then
    content = get_graphql_content_from_response(response)
    assert "errors" in content


@pytest.mark.parametrize(
    "start_date",
    [
        "0001-01-01T00:00:01+00:00",
        "0001-01-01T01:00:02+01:00",
        "0001-01-10T00:00:01+07:00",
        "0001-01-01T07:05:01+07:00",
        "2024-06-10T11:00:00+07:00",
        "9999-12-31T23:59:59+00:00",
    ],
)
def test_correct_date_time_as_variable(
    start_date, staff_api_client, permission_manage_discounts
):
    # given
    variables = {"startDate": start_date}
    staff_api_client.user.user_permissions.add(permission_manage_discounts)

    # when
    response = staff_api_client.post_graphql(DATE_TIME_QUERY_WITH_VARIABLE, variables)

    # then
    get_graphql_content(response)


@pytest.mark.parametrize(
    "start_date",
    [
        "0000-01-01T00:00:00+00:00",
        "0001-01-01T00:00:01+07:00",
        "0001-01-01T00:00:01+01:00",
        "0001-01-01T00:00:00+00:01",
        "0001-12-31 17:00:01+00 BC",
        "9999-12-31T23:59:59-07:00",
    ],
)
def test_incorrect_date_time_as_input(
    start_date, staff_api_client, permission_manage_discounts
):
    # given
    query = f"""
    mutation{{
        voucherCreate(input:{{
            type:SHIPPING, code:"test12", startDate: "{start_date}"
        }}){{
            errors{{
                code
            }}
            voucher{{
                id
                startDate
            }}
        }}
    }}
    """
    staff_api_client.user.user_permissions.add(permission_manage_discounts)

    # when
    response = staff_api_client.post_graphql(query)

    # then
    content = get_graphql_content_from_response(response)
    assert "errors" in content


@pytest.mark.parametrize(
    "start_date",
    [
        "0001-01-01T00:00:01+00:00",
        "0001-01-01T01:00:02+01:00",
        "0001-01-10T00:00:01+07:00",
        "0001-01-01T07:05:01+07:00",
        "2024-06-10T11:00:00+07:00",
        "9999-12-31T23:59:59+00:00",
    ],
)
def test_correct_date_time_as_input(
    start_date, staff_api_client, permission_manage_discounts
):
    # given
    query = f"""
        mutation {{
            voucherCreate(input:{{
                type:SHIPPING, code:"test12", startDate: "{start_date}"
            }}){{
                errors{{
                    code
                }}
                voucher{{
                    id
                    startDate
                }}
            }}
        }}
    """
    staff_api_client.user.user_permissions.add(permission_manage_discounts)

    # when
    response = staff_api_client.post_graphql(query)

    # then
    get_graphql_content(response)
