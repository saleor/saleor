import json
from unittest.mock import MagicMock, Mock

import graphene
import pytest
from django.shortcuts import reverse
from tests.utils import get_graphql_content

from saleor.account.models import Address
from saleor.graphql.order.mutations.draft_orders import (
    check_for_draft_order_errors)
from saleor.order.models import Order, OrderStatus, PaymentStatus, FulfillmentStatus


def test_create_fulfillment(admin_api_client, order_with_lines):
    order = order_with_lines
    query = """
    mutation fulfillOrder(
        $order: ID, $lines: [FulfillmentLineInput], $tracking: String) {
            fulfillmentCreate(
                input: {lines: $lines, order: $order,
                trackingNumber: $tracking}) {
                    fulfillment {
                        fulfillmentOrder
                        status
                        trackingNumber
                        lines {
                            totalCount
                        }
                    }
                }
        }
    """
    order_id = graphene.Node.to_global_id('Order', order.id)
    order_line = order.lines.first()
    order_line_id = graphene.Node.to_global_id('OrderLine', order_line.id)
    tracking = 'Flames tracking'
    variables = json.dumps(
        {'order': order_id,
         'lines': [{'orderLineId': order_line_id, 'quantity': 1}],
         'tracking': tracking})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['fulfillmentCreate']['fulfillment']
    assert data['fulfillmentOrder'] == 1
    assert data['status'] == FulfillmentStatus.FULFILLED.upper()
    assert data['trackingNumber'] == tracking
    assert data['lines']['totalCount'] == 1


def test_update_fulfillment(admin_api_client, fulfillment):
    query = """
    mutation updateFulfillment($id: ID!, $tracking: String) {
            fulfillmentUpdate(
                id: $id, input: {trackingNumber: $tracking}) {
                    fulfillment {
                        trackingNumber
                    }
                }
        }
    """
    fulfillment_id = graphene.Node.to_global_id('Fulfillment', fulfillment.id)
    tracking = 'stationary tracking'
    variables = json.dumps(
        {'id': fulfillment_id, 'tracking': tracking})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['fulfillmentUpdate']['fulfillment']
    assert data['trackingNumber'] == tracking


def test_cancel_fulfillment(admin_api_client, fulfillment):
    query = """
    mutation cancelFulfillment($id: ID!, $restock: Boolean) {
            fulfillmentCancel(id: $id, input: {restock: $restock}) {
                    fulfillment {
                        status
                    }
                }
        }
    """
    fulfillment_id = graphene.Node.to_global_id('Fulfillment', fulfillment.id)
    restock = True
    variables = json.dumps(
        {'id': fulfillment_id, 'restock': restock})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['fulfillmentCancel']['fulfillment']
    assert data['status'] == FulfillmentStatus.CANCELED.upper()
