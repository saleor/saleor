import pytest

from ....tests.utils import get_graphql_content

FULFILLMENT_QUERY = """
query {
    orders(first:100) {
        edges {
            node {
                id
                fulfillments {
                    id
                    status
                    lines {
                        id
                        quantity
                        orderLine {
                            id
                        }
                    }
                    warehouse {
                        id
                    }
                }
            }
        }
    }
}
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_fulfillment_query(
    staff_api_client,
    orders_for_benchmarks,
    permission_manage_orders,
    count_queries,
):
    get_graphql_content(
        staff_api_client.post_graphql(
            FULFILLMENT_QUERY,
            permissions=[permission_manage_orders],
            check_no_permissions=False,
        )
    )
