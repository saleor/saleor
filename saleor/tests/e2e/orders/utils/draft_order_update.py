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
        totalPrice {
          gross {
            amount
          }
        }
        unitPrice {
          gross {
            amount
          }
        }
        unitDiscountReason
      }
      subtotal {
        gross {
          amount
        }
      }
      totalBalance {
        amount
      }
      total {
        gross {
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
        country{ code }
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
        country{ code }
        city
        countryArea
        phone
      }
      isShippingRequired
      shippingPrice {
        gross {
          amount
        }
      }
      shippingMethod {
        id
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
