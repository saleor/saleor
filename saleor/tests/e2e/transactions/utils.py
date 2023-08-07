from ..utils import get_graphql_content

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
    app_auth_token,
    id,
    transaction_name="Credit card",
    message="Charged",
    psp_reference="PSP-ref123",
    available_actions="[CANCEL, REFUND]",
    amount_charged="{ currency: 'USD', amount: 1 }",
    external_url="https://saleor.io/payment-id/123",
):
    variables = {
        "input": {
            "id": id,
            "name": transaction_name,
            "message": message,
            "pspReference": psp_reference,
            "availableActions": available_actions,
            "amountCharged": amount_charged,
            "externalUrl": external_url,
        }
    }

    response = app_auth_token.post_graphql(TRANSACTION_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    assert content["data"]["transactionCreate"]["errors"] == []

    data = content["data"]["transactionCreate"]["transaction"]
    assert data["id"] is not None
    assert data["name"] == transaction_name
    assert data["message"] == message
    assert data["pspReference"] == psp_reference
    assert data["availableActions"] == available_actions
    assert data["amountCharged"]["amount"] == 1
    assert data["amountCharged"]["currency"] == "USD"

    return data
