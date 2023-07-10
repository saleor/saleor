import pytest

from .....payment.models import Transaction
from ....tests.utils import get_graphql_content

PAYMENT_TRANSACTIONS_QUERY = """
query {
  orders(first:100) {
    edges {
      node {
        payments {
          id
          gateway
          isActive
          created
          modified
          token
          checkout {
            id
          }
          order {
            id
          }
          customerIpAddress
          actions
          total {
            amount
          }
          capturedAmount {
            amount
          }
          transactions {
            id
          }
          availableRefundAmount {
            amount
          }
          availableCaptureAmount {
            amount
          }
          creditCard {
            brand
          }
        }
      }
    }
  }
}
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_payment_transactions(
    staff_api_client,
    orders_for_benchmarks,
    permission_group_manage_orders,
    count_queries,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    transactions_count = 0

    # when
    content = get_graphql_content(
        staff_api_client.post_graphql(
            PAYMENT_TRANSACTIONS_QUERY,
            check_no_permissions=False,
        )
    )

    # then
    edges = content["data"]["orders"]["edges"]
    for edge in edges:
        for payment in edge["node"]["payments"]:
            transactions_count += len(payment["transactions"])

    assert transactions_count == Transaction.objects.count() > 1
