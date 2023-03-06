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

FRAGMENT_SHIPPING_METHODS = """
    fragment AvailableShippingMethods on ShippingMethod {
        id
        price {
            amount
        }
        minimumOrderPrice {
            amount
            currency
        }
    }
"""

FRAGMENT_ORDER_DETAILS = (
    FRAGMENT_ADDRESS
    + FRAGMENT_PRODUCT_VARIANT
    + FRAGMENT_DISCOUNTS
    + FRAGMENT_SHIPPING_METHODS
    + """
      fragment OrderDetail on Order {
        userEmail
        paymentStatus
        paymentStatusDisplay
        status
        statusDisplay
        canFinalize
        isShippingRequired
        id
        giftCards {
          id
        }
        invoices {
          id
        }
        payments {
          id
        }
        number
        shippingAddress {
          ...Address
        }
        billingAddress {
          ...Address
        }
        discounts {
          ...OrderDiscounts
        }
        actions
        fulfillments {
          id
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
          thumbnail {
            url
          }
        }
        availableShippingMethods {
          ...AvailableShippingMethods
        }
        subtotal {
          ...Price
        }
        total {
          ...Price
        }
        totalCaptured {
          amount
        }
        totalAuthorized {
          amount
        }
        shippingPrice {
          ...Price
        }
        displayGrossPrices
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
        "token": order_with_lines_and_events.id,
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


MULTIPLE_ORDER_DETAILS_QUERY = (
    FRAGMENT_STAFF_ORDER_DETAILS
    + """
    query orders {
      orders(first: 10) {
        edges {
          node {
            ...OrderStaffDetail
          }
        }
      }
    }
  """
)


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_staff_multiple_orders(
    staff_api_client,
    permission_manage_orders,
    permission_manage_users,
    orders_for_benchmarks,
    count_queries,
):
    staff_api_client.user.user_permissions.set(
        [permission_manage_orders, permission_manage_users]
    )
    content = get_graphql_content(
        staff_api_client.post_graphql(MULTIPLE_ORDER_DETAILS_QUERY)
    )
    assert content["data"]["orders"] is not None


MULTIPLE_DRAFT_ORDER_DETAILS_QUERY = (
    FRAGMENT_STAFF_ORDER_DETAILS
    + """
    query draftOrders {
      draftOrders(first: 10) {
        edges {
          node {
            ...OrderStaffDetail
          }
        }
      }
    }
  """
)


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_staff_multiple_draft_orders(
    staff_api_client,
    permission_manage_orders,
    permission_manage_users,
    draft_orders_for_benchmarks,
    count_queries,
):
    staff_api_client.user.user_permissions.set(
        [permission_manage_orders, permission_manage_users]
    )
    content = get_graphql_content(
        staff_api_client.post_graphql(MULTIPLE_DRAFT_ORDER_DETAILS_QUERY)
    )
    assert content["data"]["draftOrders"] is not None
