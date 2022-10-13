import json
from unittest.mock import patch

from .....payment import PaymentError
from .....payment.interface import InitializedPaymentResponse
from .....plugins.manager import PluginsManager
from ....tests.utils import get_graphql_content

PAYMENT_INITIALIZE_MUTATION = """
mutation PaymentInitialize(
    $gateway: String!,$channel: String!, $paymentData: JSONString){
      paymentInitialize(gateway: $gateway, channel: $channel, paymentData: $paymentData)
      {
        initializedPayment{
          gateway
          name
          data
        }
        errors{
          field
          message
        }
      }
}
"""


@patch.object(PluginsManager, "initialize_payment")
def test_payment_initialize(mocked_initialize_payment, api_client, channel_USD):
    exected_initialize_payment_response = InitializedPaymentResponse(
        gateway="gateway.id",
        name="PaymentPluginName",
        data={
            "epochTimestamp": 1604652056653,
            "expiresAt": 1604655656653,
            "merchantSessionIdentifier": "SSH5EFCB46BA25C4B14B3F37795A7F5B974_BB8E",
        },
    )
    mocked_initialize_payment.return_value = exected_initialize_payment_response

    query = PAYMENT_INITIALIZE_MUTATION
    variables = {
        "gateway": exected_initialize_payment_response.gateway,
        "channel": channel_USD.slug,
        "paymentData": json.dumps(
            {"paymentMethod": "applepay", "validationUrl": "https://127.0.0.1/valid"}
        ),
    }
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    init_payment_data = content["data"]["paymentInitialize"]["initializedPayment"]
    assert init_payment_data["gateway"] == exected_initialize_payment_response.gateway
    assert init_payment_data["name"] == exected_initialize_payment_response.name
    assert (
        json.loads(init_payment_data["data"])
        == exected_initialize_payment_response.data
    )


def test_payment_initialize_gateway_doesnt_exist(api_client, channel_USD):
    query = PAYMENT_INITIALIZE_MUTATION
    variables = {
        "gateway": "wrong.gateway",
        "channel": channel_USD.slug,
        "paymentData": json.dumps(
            {"paymentMethod": "applepay", "validationUrl": "https://127.0.0.1/valid"}
        ),
    }
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["paymentInitialize"]["initializedPayment"] is None


@patch.object(PluginsManager, "initialize_payment")
def test_payment_initialize_plugin_raises_error(
    mocked_initialize_payment, api_client, channel_USD
):
    error_msg = "Missing paymentMethod field."
    mocked_initialize_payment.side_effect = PaymentError(error_msg)

    query = PAYMENT_INITIALIZE_MUTATION
    variables = {
        "gateway": "gateway.id",
        "channel": channel_USD.slug,
        "paymentData": json.dumps({"validationUrl": "https://127.0.0.1/valid"}),
    }
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    initialized_payment_data = content["data"]["paymentInitialize"][
        "initializedPayment"
    ]
    errors = content["data"]["paymentInitialize"]["errors"]
    assert initialized_payment_data is None
    assert len(errors) == 1
    assert errors[0]["field"] == "paymentData"
    assert errors[0]["message"] == error_msg
