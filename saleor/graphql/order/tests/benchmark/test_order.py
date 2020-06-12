import pytest

from ....checkout.tests.benchmark.test_checkout_mutations import (
    FRAGMENT_ADDRESS,
    FRAGMENT_PRODUCT_VARIANT,
)
from ....tests.utils import get_graphql_content

FRAGMENT_ORDER_DETAILS = (
    FRAGMENT_ADDRESS
    + FRAGMENT_PRODUCT_VARIANT
    + """
        fragment OrderDetail on Order {
          userEmail
          paymentStatus
          paymentStatusDisplay
          status
          statusDisplay
          id
          number
          shippingAddress {
            ...Address
          }
          lines {
            productName
            quantity
            variant {
              ...ProductVariant
            }
            unitPrice {
              currency
              ...Price
            }
          }
          subtotal {
            ...Price
          }
          total {
            ...Price
          }
          shippingPrice {
            ...Price
          }
        }
    """
)


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_user_order_details(user_api_client, order_with_lines, count_queries):
    query = (
        FRAGMENT_ORDER_DETAILS
        + """
            query OrderByToken($token: UUID!) {
              orderByToken(token: $token) {
                ...OrderDetail
              }
            }
        """
    )
    variables = {
        "token": order_with_lines.token,
    }
    get_graphql_content(user_api_client.post_graphql(query, variables))
