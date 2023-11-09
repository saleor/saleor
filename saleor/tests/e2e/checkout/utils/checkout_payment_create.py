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


def raw_checkout_dummy_payment_create(
    api_client, checkout_id, total_gross_amount, token
):
    variables = {
        "checkoutId": checkout_id,
        "input": {
            "amount": total_gross_amount,
            "gateway": "mirumee.payments.dummy",
            "token": token,
        },
    }

    response = api_client.post_graphql(
        CHECKOUT_PAYMENT_CREATE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    checkout_data = content["data"]["checkoutPaymentCreate"]

    return checkout_data


def checkout_dummy_payment_create(api_client, checkout_id, total_gross_amount):
    checkout_payment_create_response = raw_checkout_dummy_payment_create(
        api_client,
        checkout_id,
        total_gross_amount,
        token="fully_charged",
    )

    assert checkout_payment_create_response["errors"] == []

    checkout_data = checkout_payment_create_response["checkout"]
    assert checkout_data["id"] == checkout_id
    payment_data = checkout_payment_create_response["payment"]
    assert payment_data["id"] is not None

    return payment_data
