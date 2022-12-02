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
    staff_api_client, orders_for_benchmarks, permission_manage_orders, count_queries
):
    transactions_count = 0
    content = get_graphql_content(
        staff_api_client.post_graphql(
            PAYMENT_TRANSACTIONS_QUERY,
            permissions=[permission_manage_orders],
            check_no_permissions=False,
        )
    )

    edges = content["data"]["orders"]["edges"]
    for edge in edges:
        for payment in edge["node"]["payments"]:
            transactions_count += len(payment["transactions"])

    assert transactions_count == Transaction.objects.count() > 1
