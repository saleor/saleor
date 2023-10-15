from prices import Money

from .....order import events as order_events
from ....tests.utils import get_graphql_content

ORDERS_PAYMENTS_EVENTS_QUERY = """
    query OrdersQuery {
        orders(first: 1) {
            edges {
                node {
                    events {
                        type
                        user {
                            email
                        }
                        app {
                            name
                        }
                        message
                        email
                        emailType
                        amount
                        quantity
                        composedId
                        orderNumber
                        lines {
                            quantity
                        }
                        paymentId
                        paymentGateway
                    }
                }
            }
        }
    }
"""


def test_payment_information_order_events_query(
    staff_api_client,
    permission_group_manage_orders,
    permission_manage_apps,
    order,
    payment_dummy,
    staff_user,
):
    query = ORDERS_PAYMENTS_EVENTS_QUERY

    amount = order.total.gross.amount

    order_events.payment_captured_event(
        order=order, user=staff_user, app=None, amount=amount, payment=payment_dummy
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["orders"]["edges"][0]["node"]["events"][0]

    assert data["message"] is None
    assert Money(str(data["amount"]), "USD") == order.total.gross
    assert data["emailType"] is None
    assert data["quantity"] is None
    assert data["composedId"] is None
    assert data["lines"] is None
    assert data["user"]["email"] == staff_user.email
    assert data["app"] is None
    assert data["type"] == "PAYMENT_CAPTURED"
    assert data["orderNumber"] == str(order.number)
    assert data["paymentId"] == payment_dummy.token
    assert data["paymentGateway"] == payment_dummy.gateway


def test_payment_information_order_events_query_for_app(
    staff_api_client,
    permission_group_manage_orders,
    permission_manage_apps,
    order,
    payment_dummy,
    app,
):
    query = ORDERS_PAYMENTS_EVENTS_QUERY

    amount = order.total.gross.amount

    order_events.payment_captured_event(
        order=order, user=None, app=app, amount=amount, payment=payment_dummy
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["orders"]["edges"][0]["node"]["events"][0]

    assert data["message"] is None
    assert Money(str(data["amount"]), "USD") == order.total.gross
    assert data["emailType"] is None
    assert data["quantity"] is None
    assert data["composedId"] is None
    assert data["lines"] is None
    assert data["app"]["name"] == app.name
    assert data["type"] == "PAYMENT_CAPTURED"
    assert data["orderNumber"] == str(order.number)
    assert data["paymentId"] == payment_dummy.token
    assert data["paymentGateway"] == payment_dummy.gateway
