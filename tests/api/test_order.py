import json

import graphene
from django.shortcuts import reverse
from tests.utils import get_graphql_content


def test_order_query(admin_api_client, fulfilled_order):
    query = """
    query OrdersQuery {
        orders(first: 1) {
            edges {
                node {
                    orderId
                    status
                    statusDisplay
                    paymentStatus
                    paymentStatusDisplay
                    userEmail
                    isPaid
                    shippingPrice {
                        gross {
                            amount
                        }
                    }
                    lines {
                        productName
                    }
                    notes {
                        content
                    }
                    fulfillments {
                        fulfillmentOrder
                    }
                    history {
                        content
                    }
                }
            }
        }
    }
    """
    response = admin_api_client.post(
        reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    order_data = content['data']['orders']['edges'][0]['node']
    assert order_data['orderId'] == fulfilled_order.pk
    assert order_data['status'] == fulfilled_order.status.upper()
    assert order_data['statusDisplay'] == fulfilled_order.get_status_display()
    assert order_data[
               'paymentStatus'] == fulfilled_order.get_last_payment_status()
    payment_status_display = fulfilled_order.get_last_payment_status_display()
    assert order_data['paymentStatusDisplay'] == payment_status_display
    assert order_data['isPaid'] == fulfilled_order.is_fully_paid()
    assert order_data['userEmail'] == fulfilled_order.user_email
    assert order_data[
               'shippingPrice'][
               'gross'][
               'amount'] == fulfilled_order.shipping_price.gross.amount
    assert len(order_data['lines']) == fulfilled_order.lines.count()
    assert len(order_data['notes']) == fulfilled_order.notes.count()
    fulfillment_order = fulfilled_order.fulfillments.first().fulfillment_order
    assert order_data[
               'fulfillments'][0]['fulfillmentOrder'] == fulfillment_order


def test_non_staff_user_can_only_see_his_order(user_api_client, order):
    query = """
    query OrderQuery($id: ID!) {
        order(id: $id) {
            orderId
        }
    }
    """
    ID = graphene.Node.to_global_id('Order', order.id)
    variables = json.dumps({'id': ID})
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    order_data = content['data']['order']
    assert order_data['orderId'] == order.pk

    order.user = None
    order.save()
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    order_data = content['data']['order']
    assert not order_data
