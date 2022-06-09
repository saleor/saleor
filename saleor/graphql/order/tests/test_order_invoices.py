from ....core import JobStatus
from ...tests.utils import assert_no_permission, get_graphql_content

ORDERS_WITH_INVOICES_QUERY = """
    query OrdersQuery {
        orders(first: 5) {
            edges {
                node {
                    invoices {
                        status
                        externalUrl
                        number
                    }
                }
            }
        }
    }
"""


def test_order_query_invoices(
    user_api_client, permission_manage_orders, fulfilled_order
):
    user_api_client.user.user_permissions.add(permission_manage_orders)
    response = user_api_client.post_graphql(ORDERS_WITH_INVOICES_QUERY)
    content = get_graphql_content(response)
    edges = content["data"]["orders"]["edges"]
    assert len(edges) == 1
    assert edges[0]["node"]["invoices"] == [
        {
            "status": JobStatus.SUCCESS.upper(),
            "externalUrl": "http://www.example.com/invoice.pdf",
            "number": "01/12/2020/TEST",
        }
    ]


def test_order_query_invoices_staff_no_permission(staff_api_client):
    response = staff_api_client.post_graphql(ORDERS_WITH_INVOICES_QUERY)
    assert_no_permission(response)


def test_order_query_invoices_customer_user(user_api_client):
    response = user_api_client.post_graphql(ORDERS_WITH_INVOICES_QUERY)
    assert_no_permission(response)


def test_order_query_invoices_anonymous_user(api_client):
    response = api_client.post_graphql(ORDERS_WITH_INVOICES_QUERY)
    assert_no_permission(response)


def test_order_query_invoices_app(
    app_api_client, permission_manage_orders, fulfilled_order
):
    app_api_client.app.permissions.add(permission_manage_orders)
    response = app_api_client.post_graphql(ORDERS_WITH_INVOICES_QUERY)
    content = get_graphql_content(response)
    edges = content["data"]["orders"]["edges"]
    assert len(edges) == 1
    assert edges[0]["node"]["invoices"] == [
        {
            "status": JobStatus.SUCCESS.upper(),
            "externalUrl": "http://www.example.com/invoice.pdf",
            "number": "01/12/2020/TEST",
        }
    ]


def test_order_query_invoices_customer_user_by_token(api_client, fulfilled_order):
    query = """
    query OrderByToken($token: UUID!) {
        orderByToken(token: $token) {
            invoices {
                status
                number
                externalUrl
            }
        }
    }
    """
    response = api_client.post_graphql(query, {"token": fulfilled_order.id})
    content = get_graphql_content(response)
    data = content["data"]["orderByToken"]
    assert data["invoices"] == [
        {
            "status": JobStatus.SUCCESS.upper(),
            "externalUrl": "http://www.example.com/invoice.pdf",
            "number": "01/12/2020/TEST",
        }
    ]
