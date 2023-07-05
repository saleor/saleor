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


def checkout_dummy_payment_create_plain(api_client, checkout_id, total_gross_amount):
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

    checkout_data = content["data"]["checkoutPaymentCreate"]

    return checkout_data
