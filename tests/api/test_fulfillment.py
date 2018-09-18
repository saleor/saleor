import json

import graphene
from django.shortcuts import reverse
from saleor.order import OrderEvents, OrderEventsEmails
from saleor.order.models import FulfillmentStatus
from tests.utils import get_graphql_content


def test_create_fulfillment(admin_api_client, order_with_lines, admin_user):
    order = order_with_lines
    query = """
    mutation fulfillOrder(
        $order: ID, $lines: [FulfillmentLineInput], $tracking: String,
        $notify: Boolean) {
            orderFulfillmentCreate(
                order: $order, input: {lines: $lines,
                trackingNumber: $tracking, notifyCustomer: $notify}) {
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
    assert not order.events.all()
    variables = json.dumps(
        {'order': order_id,
         'lines': [{'orderLineId': order_line_id, 'quantity': 1}],
         'tracking': tracking, 'notify': True})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['orderFulfillmentCreate']['fulfillment']
    assert data['fulfillmentOrder'] == 1
    assert data['status'] == FulfillmentStatus.FULFILLED.upper()
    assert data['trackingNumber'] == tracking
    assert data['lines']['totalCount'] == 1

    event_fulfillment, event_email_sent = order.events.all()
    assert event_fulfillment.type == (
        OrderEvents.FULFILLMENT_FULFILLED_ITEMS.value)
    assert event_fulfillment.parameters == {'quantity': 1}
    assert event_fulfillment.user == admin_user

    assert event_email_sent.type == OrderEvents.EMAIL_SENT.value
    assert event_email_sent.user == admin_user
    assert event_email_sent.parameters == {
        'email': order.user_email,
        'email_type': OrderEventsEmails.FULFILLMENT.value}


def test_fulfillment_update_tracking(admin_api_client, fulfillment):
    query = """
    mutation updateFulfillment($id: ID!, $tracking: String) {
            orderFulfillmentUpdateTracking(
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
    data = content['data']['orderFulfillmentUpdateTracking']['fulfillment']
    assert data['trackingNumber'] == tracking


def test_cancel_fulfillment_restock_items(
        admin_api_client, fulfillment, admin_user):
    query = """
    mutation cancelFulfillment($id: ID!, $restock: Boolean) {
            orderFulfillmentCancel(id: $id, input: {restock: $restock}) {
                    fulfillment {
                        status
                    }
                }
        }
    """
    fulfillment_id = graphene.Node.to_global_id('Fulfillment', fulfillment.id)
    variables = json.dumps({'id': fulfillment_id, 'restock': True})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['orderFulfillmentCancel']['fulfillment']
    assert data['status'] == FulfillmentStatus.CANCELED.upper()
    event_restocked_items = fulfillment.order.events.get()
    assert event_restocked_items.type == (
        OrderEvents.FULFILLMENT_RESTOCKED_ITEMS.value)
    assert event_restocked_items.parameters == {
        'quantity': fulfillment.get_total_quantity()}
    assert event_restocked_items.user == admin_user


def test_cancel_fulfillment(admin_api_client, fulfillment, admin_user):
    query = """
    mutation cancelFulfillment($id: ID!, $restock: Boolean) {
            orderFulfillmentCancel(id: $id, input: {restock: $restock}) {
                    fulfillment {
                        status
                    }
                }
        }
    """
    fulfillment_id = graphene.Node.to_global_id('Fulfillment', fulfillment.id)
    variables = json.dumps({'id': fulfillment_id, 'restock': False})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['orderFulfillmentCancel']['fulfillment']
    assert data['status'] == FulfillmentStatus.CANCELED.upper()
    event_cancel_fulfillment = fulfillment.order.events.get()
    assert event_cancel_fulfillment.type == (
        OrderEvents.FULFILLMENT_CANCELED.value)
    assert event_cancel_fulfillment.parameters == {
        'composed_id': fulfillment.composed_id}
    assert event_cancel_fulfillment.user == admin_user
