from ...utils import get_graphql_content

TRANSACTION_CREATE_MUTATION = """
mutation TransactionCreate($id: ID!, $transactionCreateInput: TransactionCreateInput!) {
  transactionCreate(id: $id, transaction: $transactionCreateInput) {
    errors {
      field
      message
      code
    }
    transaction {
      id
      name
      order { id }
      message
      pspReference
      actions
      chargedAmount {
        currency
        amount
      }
    }
  }
}
"""


def create_transaction(
    e2e_api_client,
    id,
    transaction_name="CreditCard",
    message="",
    psp_reference="PSP-ref123",
    available_actions=None,
    currency="USD",
    amount=1,
    external_url="https://saleor.io/payment-id/123",
):
    if not available_actions:
        available_actions = []
    variables = {
        "id": id,
        "transactionCreateInput": {
            "name": transaction_name,
            "message": message,
            "pspReference": psp_reference,
            "availableActions": available_actions,
            "amountCharged": {"currency": currency, "amount": amount},
            "externalUrl": external_url,
        },
    }

    response = e2e_api_client.post_graphql(TRANSACTION_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    assert content["data"]["transactionCreate"]["errors"] == []

    data = content["data"]["transactionCreate"]["transaction"]
    assert data["id"] is not None
    assert data["name"] == transaction_name
    assert data["message"] == message
    assert data["pspReference"] == psp_reference
    assert set(data["actions"]) == set(available_actions)
    assert data["chargedAmount"]["amount"] == amount
    assert data["chargedAmount"]["currency"] == currency

    return data
