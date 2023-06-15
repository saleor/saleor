from ...utils import get_graphql_content

CHECKOUT_PAYMENT_CREATE_MUTATION = """
mutation createPayment($checkoutId: ID, $input: PaymentInput!) {
  checkoutPaymentCreate(id: $checkoutId, input: $input) {
    errors {
      field
      code
      message
    }
    checkout {
      id
    }
    payment {
      id
    }
  }
}
"""


def checkout_payment_create(api_client, checkout_id, total_gross_amount):
    variables = {
        "checkoutId": checkout_id,
        "input": {
            "amount": total_gross_amount,
            "gateway": "mirumee.payments.dummy",
            "token": "fully_charged",
        },
    }

    response = api_client.post_graphql(
        CHECKOUT_PAYMENT_CREATE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    assert content["data"]["checkoutPaymentCreate"]["errors"] == []

    checkout_data = content["data"]["checkoutPaymentCreate"]["checkout"]
    assert checkout_data["id"] == checkout_id
    payment_data = content["data"]["checkoutPaymentCreate"]["payment"]
    assert payment_data["id"] is not None

    return payment_data
