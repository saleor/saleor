import requests

API_URL = "http://localhost:8000/graphql/"

PRODUCTS_QUERY = """
query {
  products(first: 1, channel: "channel-pln") {
    edges {
      node {
        id
        name
      }
    }
  }
}
"""

response = requests.post(API_URL, json={"query": PRODUCTS_QUERY})
product = response.json()["data"]["products"]["edges"][0]["node"]
print(product["id"])

MUTATION_CREATE_CHECKOUT = """
mutation {
  checkoutCreate(
    input: {
      channel: "channel-pln",
      email: "OK@example.com"
      lines: [{ quantity: 1, variantId: "UHJvZHVjdFZhcmlhbnQ6Mjk3" }]
      billingAddress: {
        firstName: "John"
        lastName: "Doe"
        streetAddress1: "4-2-8 Shiba-koen"
        city: "Tokyo"
        postalCode: "102-8900"
        countryArea: "Tokyo"
        country: JP
        phone: "+81 03-1234-5678"
      }
      shippingAddress: {
        firstName: "John"
        lastName: "Doe"
        streetAddress1: "4-2-8 Shiba-koen"
        city: "Tokyo"
        postalCode: "102-8899"
        countryArea: "Tokyo"
        country: JP
        phone: "+81 03-1234-5678"
      }
    }
  ) {
    checkout {
      id
      token
      totalPrice {
        gross {
          amount
          currency
        }
      }
      isShippingRequired
      availableShippingMethods {
        id
        name
      }
      availablePaymentGateways {
        id
        name
        config {
          field
          value
        }
      }
      billingAddress { phone }
    }
    checkoutErrors {
      field
      code
    }
  }
}"""

response = requests.post(API_URL, json={"query": MUTATION_CREATE_CHECKOUT})
checkout = response.json()["data"]["checkoutCreate"]["checkout"]
print(checkout["token"])

shipping_method = checkout["availableShippingMethods"][0]
print(shipping_method)

MUTATION_UPDATE_SHIPPING_METHOD = """
mutation {
  checkoutShippingMethodUpdate (
    token: "%TOKEN",
    shippingMethodId: "%METHOD_ID"
  ) {
    errors {
      code,
      message
    },
    checkout {
        totalPrice {
            gross {
                amount
            }
        }
    }
  }
}
""".replace(
    "%TOKEN", checkout["token"]
).replace(
    "%METHOD_ID", shipping_method["id"]
)

response = requests.post(API_URL, json={"query": MUTATION_UPDATE_SHIPPING_METHOD})
total_amount = response.json()["data"]["checkoutShippingMethodUpdate"]["checkout"][
    "totalPrice"
]["gross"]["amount"]

MUTATION_CREATE_PAYMENT = """
mutation {
  checkoutPaymentCreate (
    token: "%TOKEN",
    input: {
      gateway: "mirumee.payments.np-atobarai",
      amount: %AMOUNT
    }
  ) {
    payment {
      id,
      chargeStatus,
      gateway,
      isActive
    }
    errors {
      code,
      message
    }
  }
}
""".replace(
    "%TOKEN", checkout["token"]
).replace(
    "%AMOUNT", str(total_amount)
)

response = requests.post(API_URL, json={"query": MUTATION_CREATE_PAYMENT})
payment = response.json()["data"]["checkoutPaymentCreate"]["payment"]
print(payment)


MUTATION_CHECKOUT_COMPLETE = """
mutation {
  checkoutComplete(
    token: "%TOKEN"
  ) {
    order {
      id
      status
    }
    errors {
      field
      message
    }
  }
}""".replace(
    "%TOKEN", checkout["token"]
)

response = requests.post(API_URL, json={"query": MUTATION_CHECKOUT_COMPLETE})
print(response.json())
order = response.json()["data"]["checkoutComplete"]["order"]
print(order)
