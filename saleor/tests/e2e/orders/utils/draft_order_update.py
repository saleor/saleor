from saleor.graphql.tests.utils import get_graphql_content

DRAFT_ORDER_UPDATE_MUTATION = """
mutation DraftOrderUpdate($input: DraftOrderInput!, $id: ID!) {
  draftOrderUpdate(input: $input, id: $id) {
    errors {
      message
      field
      code
    }
    order {
      id
      lines {
        id
        totalPrice {
          ...BaseTaxedMoney
        }
        unitPrice {
          ...BaseTaxedMoney
        }
        unitDiscountReason
      }
      subtotal {
        ...BaseTaxedMoney
      }
      totalBalance {
        amount
      }
      total {
        ...BaseTaxedMoney
      }
      voucherCode
      voucher {
        id
        code
        discountValue
      }
      discounts {
        id
        type
        name
        valueType
        value
        reason
        amount {
          amount
        }
      }
      billingAddress {
        firstName
        lastName
        companyName
        streetAddress1
        streetAddress2
        postalCode
        country {
          code
        }
        city
        countryArea
        phone
      }
      shippingAddress {
        firstName
        lastName
        companyName
        streetAddress1
        streetAddress2
        postalCode
        country {
          code
        }
        city
        countryArea
        phone
      }
      isShippingRequired
      shippingPrice {
        ...BaseTaxedMoney
      }
      undiscountedShippingPrice {
        amount
      }
      shippingMethods {
        id
      }
      channel {
        id
        name
      }
      userEmail
      deliveryMethod {
        __typename
        ... on ShippingMethod {
          id
          __typename
        }
      }
    }
  }
}

fragment BaseTaxedMoney on TaxedMoney {
  gross {
    amount
  }
  net {
    amount
  }
  tax {
    amount
  }
  currency
}
"""


def draft_order_update(
    api_client,
    id,
    input,
):
    variables = {"id": id, "input": input}

    response = api_client.post_graphql(
        DRAFT_ORDER_UPDATE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    order_id = data["order"]["id"]
    errors = data["errors"]

    assert errors == []
    assert order_id == id

    return data
