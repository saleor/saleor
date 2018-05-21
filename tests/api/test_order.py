import json

import graphene
from django.shortcuts import reverse
from tests.utils import get_graphql_content


def test_order_query(admin_api_client, order_with_lines):
    query = """
    query OrdersQuery {
        orders(first: 1) {
            edges {
                node {
                    orderId
                    status
                    userEmail
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
    assert order_data['orderId'] == order_with_lines.pk
    assert order_data['status'] == order_with_lines.status.upper()
    assert order_data['userEmail'] == order_with_lines.user_email
    assert order_data[
               'shippingPrice'][
               'gross'][
               'amount'] == order_with_lines.shipping_price.gross.amount
    assert len(order_data['lines']) == order_with_lines.lines.count()
    assert len(order_data['notes']) == order_with_lines.notes.count()


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
    assert order_data is None
