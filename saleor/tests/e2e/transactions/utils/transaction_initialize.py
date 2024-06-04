from unittest import mock

from .....payment.interface import TransactionSessionResult
from ...utils import get_graphql_content

TRANSACTION_INITIALIZE_MUTATION = """
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


def transaction_initialize(
    monkeypatch,
    e2e_api_client,
    id,
    amount,
    app_identifier,
    action=None,
    customer_ip_address=None,
    idempotency_key="TEST",
):
    expected_response = {
        "pspReference": "psp-123",
        "data": {"some-json": "data"},
        "result": "CHARGE_SUCCESS",
        "amount": amount,
        "time": "2022-11-18T13:25:58.169685+00:00",
        "externalUrl": "http://127.0.0.1:9090/external-reference",
        "message": "Message related to the payment",
    }

    monkeypatch.setattr(
        "saleor.plugins.manager.PluginsManager.transaction_initialize_session",
        mock.Mock(
            return_value=TransactionSessionResult(
                app_identifier=app_identifier, response=expected_response
            )
        ),
    )

    variables = {
        "action": action,
        "amount": amount,
        "id": id,
        "paymentGateway": {"id": app_identifier, "data": None},
        "customerIpAddress": customer_ip_address,
        "idempotencyKey": idempotency_key,
    }

    response = e2e_api_client.post_graphql(TRANSACTION_INITIALIZE_MUTATION, variables)
    content = get_graphql_content(response)

    assert not content["data"]["transactionInitialize"]["errors"]
    data = content["data"]["transactionInitialize"]

    return data
