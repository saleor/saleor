import os

import requests

API_URL = "http://localhost:8000/graphql/"

MUTATION_CREATE_TOKEN = """
mutation {
  tokenCreate(
    email: "%s"
    password: "%s"
  ) {
    token
  }
}
"""


def create_token(email: str, password: str):
    response = requests.post(
        API_URL, json={"query": MUTATION_CREATE_TOKEN % (email, password)}
    ).json()
    return response["data"]["tokenCreate"]["token"]


jwt_token = create_token("admin@example.com", "admin")


MUTATION_ACTIVATE_PLUGIN = """
mutation {
  pluginUpdate(
    id: "mirumee.payments.np-atobarai"
    channelId: "Q2hhbm5lbDoy"
    input: {
      active: true
      configuration: [
        { name: "merchant_code", value: "%s" }
        { name: "sp_code", value: "%s" }
        { name: "terminal_id", value: "%s" }
      ]
    }
  ) {
    errors {
      field
      message
    }
  }
}
"""


def activate_np(merchant_code: str, sp_code: str, terminal_id: str):
    requests.post(
        API_URL,
        json={
            "query": MUTATION_ACTIVATE_PLUGIN % (merchant_code, sp_code, terminal_id)
        },
        headers={"Authorization": f"JWT {jwt_token}"},
    ).json()


activate_np(os.getenv("MERCHANT_CODE"), os.getenv("SP_CODE"), os.getenv("TERMINAL_ID"))


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
print(f'{product["id"] = }')

ADDRESS = """
    firstName: "John"
    lastName: "Doe"
    phone: "+81 03-1234-5678"

    country: JP
    postalCode: "108-0075"
    countryArea: "Tokyo"
    city: "Minato"
    cityArea: "Kounan"
    streetAddress1: "2-16-3"
    streetAddress2: ""
"""

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
print(f"{response.json() = }")
print(f"{checkout}")
print(f'{checkout["token"] = }')
shipping_method = checkout["availableShippingMethods"][0]
print(f"{shipping_method = }")
print()

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

response = requests.post(API_URL, json={"query": MUTATION_CREATE_PAYMENT}).json()
payment = response["data"]["checkoutPaymentCreate"]["payment"]
print(f"{response = }")
print(f"{payment = }")
print()

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

response = requests.post(API_URL, json={"query": MUTATION_CHECKOUT_COMPLETE}).json()
print(f"{response = }")
order = response["data"]["checkoutComplete"]["order"]
print(f"{order = }")
print()
