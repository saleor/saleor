from .....order.models import Order
from ....tests.utils import get_graphql_content


def test_draft_order_query(staff_api_client, permission_manage_orders, orders):
    query = """
    query DraftOrdersQuery {
        draftOrders(first: 10) {
            edges {
                node {
                    id
                }
            }
        }
    }
    """

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query)
    edges = get_graphql_content(response)["data"]["draftOrders"]["edges"]

    assert len(edges) == Order.objects.drafts().count()
