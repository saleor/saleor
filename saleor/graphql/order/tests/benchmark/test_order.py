import graphene
import pytest

from ....checkout.tests.benchmark.test_checkout_mutations import (
    FRAGMENT_ADDRESS,
    FRAGMENT_PRODUCT_VARIANT,
)
from ....tests.utils import get_graphql_content

FRAGMENT_DISCOUNTS = """
    fragment OrderDiscounts on OrderDiscount {
            id
            type
            valueType
            value
            name
            translatedName
    }
"""

FRAGMENT_ORDER_DETAILS = (
    FRAGMENT_ADDRESS
    + FRAGMENT_PRODUCT_VARIANT
    + FRAGMENT_DISCOUNTS
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
          discounts {
            ...OrderDiscounts
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
def test_user_order_details(
    user_api_client, order_with_lines_and_events, count_queries
):
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
        "token": order_with_lines_and_events.token,
    }
    get_graphql_content(user_api_client.post_graphql(query, variables))


FRAGMENT_STAFF_ORDER_DETAILS = (
    FRAGMENT_ORDER_DETAILS
    + """
    fragment OrderStaffDetail on Order {
      ...OrderDetail
      events {
        id
        date
        type
        user {
          email
        }
        message
        email
        emailType
        amount
        paymentId
        paymentGateway
        quantity
        composedId
        orderNumber
        invoiceNumber
        oversoldItems
        lines {
          itemName
        }
        fulfilledItems {
          orderLine {
            id
          }
        }
        warehouse {
          id
        }
        transactionReference
        shippingCostsIncluded
        relatedOrder {
          id
        }
      }
    }

    """
)


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_staff_order_details(
    staff_api_client,
    permission_manage_orders,
    order_with_lines_and_events,
    count_queries,
):
    query = (
        FRAGMENT_STAFF_ORDER_DETAILS
        + """
                query Order($id: ID!) {
                  order(id: $id) {
                    ...OrderStaffDetail
                  }
                }
            """
    )
    variables = {
        "id": graphene.Node.to_global_id("Order", order_with_lines_and_events.id),
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    get_graphql_content(staff_api_client.post_graphql(query, variables))
