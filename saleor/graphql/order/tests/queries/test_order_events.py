from copy import deepcopy

import graphene

from .....order import OrderEvents
from .....order import events as order_events
from .....order.events import order_replacement_created
from .....order.models import OrderEvent, get_order_number
from ....tests.utils import get_graphql_content

ORDERS_FULFILLED_EVENTS = """
    query OrdersQuery {
        orders(first: 1) {
            edges {
                node {
                    events {
                        date
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
                        fulfilledItems {
                            quantity
                            orderLine {
                                productName
                                variantName
                            }
                        }
                        paymentId
                        paymentGateway
                        warehouse {
                            name
                        }
                    }
                }
            }
        }
    }
"""


def test_nested_order_events_query(
    staff_api_client,
    permission_group_manage_orders,
    permission_manage_apps,
    fulfilled_order,
    fulfillment,
    staff_user,
    warehouse,
):
    query = ORDERS_FULFILLED_EVENTS

    event = order_events.fulfillment_fulfilled_items_event(
        order=fulfilled_order,
        user=staff_user,
        app=None,
        fulfillment_lines=fulfillment.lines.all(),
    )
    event.parameters.update(
        {
            "message": "Example note",
            "email_type": order_events.OrderEventsEmails.PAYMENT,
            "amount": "80.00",
            "quantity": "10",
            "composed_id": "10-10",
            "warehouse": warehouse.pk,
        }
    )
    event.save()

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["orders"]["edges"][0]["node"]["events"][0]
    assert data["message"] == event.parameters["message"]
    assert data["amount"] == float(event.parameters["amount"])
    assert data["emailType"] == "PAYMENT_CONFIRMATION"
    assert data["quantity"] == int(event.parameters["quantity"])
    assert data["composedId"] == event.parameters["composed_id"]
    assert data["user"]["email"] == staff_user.email
    assert data["type"] == "FULFILLMENT_FULFILLED_ITEMS"
    assert data["date"] == event.date.isoformat()
    assert data["orderNumber"] == str(fulfilled_order.number)
    assert data["fulfilledItems"] == [
        {
            "quantity": line.quantity,
            "orderLine": {
                "productName": line.order_line.product_name,
                "variantName": line.order_line.variant_name,
            },
        }
        for line in fulfillment.lines.all()
    ]
    assert data["paymentId"] is None
    assert data["paymentGateway"] is None
    assert data["warehouse"]["name"] == warehouse.name


def test_nested_order_events_query_for_app(
    staff_api_client,
    permission_group_manage_orders,
    permission_manage_apps,
    fulfilled_order,
    fulfillment,
    app,
    warehouse,
):
    query = ORDERS_FULFILLED_EVENTS

    event = order_events.fulfillment_fulfilled_items_event(
        order=fulfilled_order,
        user=None,
        app=app,
        fulfillment_lines=fulfillment.lines.all(),
    )
    event.parameters.update(
        {
            "message": "Example note",
            "email_type": order_events.OrderEventsEmails.PAYMENT,
            "amount": "80.00",
            "quantity": "10",
            "composed_id": "10-10",
            "warehouse": warehouse.pk,
        }
    )
    event.save()

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["orders"]["edges"][0]["node"]["events"][0]
    assert data["message"] == event.parameters["message"]
    assert data["amount"] == float(event.parameters["amount"])
    assert data["emailType"] == "PAYMENT_CONFIRMATION"
    assert data["quantity"] == int(event.parameters["quantity"])
    assert data["composedId"] == event.parameters["composed_id"]
    assert data["user"] is None
    assert data["app"]["name"] == app.name
    assert data["type"] == "FULFILLMENT_FULFILLED_ITEMS"
    assert data["date"] == event.date.isoformat()
    assert data["orderNumber"] == str(fulfilled_order.number)
    assert data["fulfilledItems"] == [
        {
            "quantity": line.quantity,
            "orderLine": {
                "productName": line.order_line.product_name,
                "variantName": line.order_line.variant_name,
            },
        }
        for line in fulfillment.lines.all()
    ]
    assert data["paymentId"] is None
    assert data["paymentGateway"] is None
    assert data["warehouse"]["name"] == warehouse.name


ORDERS_WITH_EVENTS = """
    query OrdersQuery {
        orders(first: 2) {
            edges {
                node {
                    id
                    events {
                        relatedOrder{
                            id
                        }
                        user {
                            id
                        }
                    }
                }
            }
        }
    }
    """


def test_related_order_events_query(
    staff_api_client, permission_group_manage_orders, order, payment_dummy, staff_user
):
    new_order = deepcopy(order)
    new_order.id = None
    new_order.number = get_order_number()
    new_order.save()

    related_order_id = graphene.Node.to_global_id("Order", new_order.id)

    order_replacement_created(
        original_order=order, replace_order=new_order, user=staff_user, app=None
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(ORDERS_WITH_EVENTS)
    content = get_graphql_content(response)

    data = content["data"]["orders"]["edges"]
    for order_data in data:
        events_data = order_data["node"]["events"]
        if order_data["node"]["id"] != related_order_id:
            assert events_data[0]["relatedOrder"]["id"] == related_order_id


def test_related_order_events_query_for_app(
    staff_api_client, permission_group_manage_orders, order, payment_dummy, app
):
    new_order = deepcopy(order)
    new_order.id = None
    new_order.number = get_order_number()
    new_order.save()

    related_order_id = graphene.Node.to_global_id("Order", new_order.id)

    order_replacement_created(
        original_order=order, replace_order=new_order, user=None, app=app
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(ORDERS_WITH_EVENTS)
    content = get_graphql_content(response)

    data = content["data"]["orders"]["edges"]
    for order_data in data:
        events_data = order_data["node"]["events"]
        if order_data["node"]["id"] != related_order_id:
            assert events_data[0]["relatedOrder"]["id"] == related_order_id


def test_related_order_eventes_old_order_id(
    staff_api_client, permission_group_manage_orders, order, payment_dummy, app
):
    # given
    new_order = deepcopy(order)
    new_order.id = None
    new_order.number = get_order_number()
    new_order.save()

    related_order_id = graphene.Node.to_global_id("Order", new_order.id)

    parameters = {"related_order_pk": new_order.number}
    OrderEvent.objects.create(
        order=order,
        type=OrderEvents.ORDER_REPLACEMENT_CREATED,
        user=None,
        app=app,
        parameters=parameters,
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_WITH_EVENTS)

    # then
    content = get_graphql_content(response)

    data = content["data"]["orders"]["edges"]
    for order_data in data:
        events_data = order_data["node"]["events"]
        if order_data["node"]["id"] != related_order_id:
            assert events_data[0]["relatedOrder"]["id"] == related_order_id


def test_order_events_without_permission(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines_and_events,
    customer_user,
):
    last_event = order_with_lines_and_events.events.last()
    last_event.user = customer_user
    last_event.save()

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(ORDERS_WITH_EVENTS)
    content = get_graphql_content(response)

    response_events = content["data"]["orders"]["edges"][0]["node"]["events"]
    assert response_events[-1]["user"] is None


QUERY_GET_FIRST_EVENT = """
        query OrdersQuery {
            orders(first: 1) {
                edges {
                    node {
                        events {
                            lines {
                                quantity
                                orderLine {
                                    id
                                }
                            }
                            fulfilledItems {
                                id
                            }
                            app {
                                name
                            }
                        }
                    }
                }
            }
        }
    """


def test_retrieving_event_lines_with_deleted_line(
    staff_api_client, order_with_lines, staff_user, permission_group_manage_orders
):
    order = order_with_lines
    lines = order_with_lines.lines.all()

    # Create the test event
    order_events.order_added_products_event(
        order=order, user=staff_user, app=None, order_lines=lines
    )

    # Delete a line
    deleted_line = lines.first()
    deleted_line.delete()

    # Prepare the query
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # Send the query and retrieve the data
    content = get_graphql_content(staff_api_client.post_graphql(QUERY_GET_FIRST_EVENT))
    data = content["data"]["orders"]["edges"][0]["node"]["events"][0]

    # Check every line is returned and the one deleted is None
    assert len(data["lines"]) == len(lines)
    for expected_data, received_line in zip(lines, data["lines"]):
        quantity = expected_data.quantity
        line = expected_data

        if line is deleted_line:
            assert received_line["orderLine"] is None
        else:
            assert received_line["orderLine"] is not None
            assert received_line["orderLine"]["id"] == graphene.Node.to_global_id(
                "OrderLine", line.pk
            )

        assert received_line["quantity"] == quantity


def test_retrieving_event_lines_with_missing_line_pk_in_data(
    staff_api_client, order_with_lines, staff_user, permission_group_manage_orders
):
    order = order_with_lines
    line = order_with_lines.lines.first()

    # Create the test event
    event = order_events.order_added_products_event(
        order=order, user=staff_user, app=None, order_lines=[line]
    )
    del event.parameters["lines"][0]["line_pk"]
    event.save(update_fields=["parameters"])

    # Prepare the query
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # Send the query and retrieve the data
    content = get_graphql_content(staff_api_client.post_graphql(QUERY_GET_FIRST_EVENT))
    data = content["data"]["orders"]["edges"][0]["node"]["events"][0]

    # Check every line is returned and the one deleted is None
    received_line = data["lines"][0]
    assert len(data["lines"]) == 1
    assert received_line["quantity"] == line.quantity
    assert received_line["orderLine"] is None


def test_related_order_events_query_with_removed_app(
    staff_api_client, permission_group_manage_orders, order, payment_dummy, removed_app
):
    event = order_events.fulfillment_fulfilled_items_event(
        order=order,
        user=None,
        app=removed_app,
        fulfillment_lines=[],
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(QUERY_GET_FIRST_EVENT)
    content = get_graphql_content(response)

    event = content["data"]["orders"]["edges"][0]["node"]["events"][0]
    assert event["app"] is None
