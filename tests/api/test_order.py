from unittest.mock import MagicMock, Mock

import pytest

import graphene
from payments import PaymentStatus
from saleor.account.models import Address
from saleor.core.utils.taxes import ZERO_TAXED_MONEY
from saleor.graphql.order.mutations.draft_orders import (
    check_for_draft_order_errors)
from saleor.graphql.order.mutations.orders import (
    clean_order_cancel, clean_order_capture, clean_order_mark_as_paid,
    clean_refund_payment, clean_release_payment)
from saleor.graphql.order.types import OrderEventsEmailsEnum, PaymentStatusEnum
from saleor.order import (
    CustomPaymentChoices, OrderEvents, OrderEventsEmails, OrderStatus)
from saleor.order.models import Order, OrderEvent, Payment
from saleor.shipping.models import ShippingMethod
from tests.api.utils import get_graphql_content

from .utils import assert_no_permission


def test_orderline_query(
        staff_api_client, permission_manage_orders, fulfilled_order):
    order = fulfilled_order
    query = """
        query OrdersQuery {
            orders(first: 1) {
                edges {
                    node {
                        lines {
                            edges {
                                node {
                                    thumbnailUrl(size: 540)
                                }
                            }
                        }
                    }
                }
            }
        }
    """
    line = order.lines.first()
    line.variant = None
    line.save()
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    order_data = content['data']['orders']['edges'][0]['node']
    lines_data = order_data['lines']['edges']
    thumbnails = [l['node']['thumbnailUrl'] for l in lines_data]
    assert len(thumbnails) == 2
    assert None in thumbnails
    assert '/static/images/placeholder540x540.png' in thumbnails


def test_order_query(
        staff_api_client, permission_manage_orders, fulfilled_order,
        shipping_zone):
    order = fulfilled_order
    query = """
    query OrdersQuery {
        orders(first: 1) {
            edges {
                node {
                    number
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
                        totalCount
                    }
                    fulfillments {
                        fulfillmentOrder
                    }
                    subtotal {
                        net {
                            amount
                        }
                    }
                    total {
                        net {
                            amount
                        }
                    }
                    availableShippingMethods {
                        id
                        price {
                            amount
                        }
                        minimumOrderPrice {
                            amount
                            currency
                        }
                        type
                    }
                }
            }
        }
    }
    """
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    order_data = content['data']['orders']['edges'][0]['node']
    assert order_data['number'] == str(order.pk)
    assert order_data['status'] == order.status.upper()
    assert order_data['statusDisplay'] == order.get_status_display()
    assert order_data['paymentStatus'] == order.get_last_payment_status()
    payment_status_display = order.get_last_payment_status_display()
    assert order_data['paymentStatusDisplay'] == payment_status_display
    assert order_data['isPaid'] == order.is_fully_paid()
    assert order_data['userEmail'] == order.user_email
    expected_price = order_data['shippingPrice']['gross']['amount']
    assert expected_price == order.shipping_price.gross.amount
    assert order_data['lines']['totalCount'] == order.lines.count()
    fulfillment = order.fulfillments.first().fulfillment_order
    fulfillment_order = order_data['fulfillments'][0]['fulfillmentOrder']
    assert fulfillment_order == fulfillment

    expected_methods = ShippingMethod.objects.applicable_shipping_methods(
        price=order.get_subtotal().gross.amount,
        weight=order.get_total_weight(),
        country_code=order.shipping_address.country.code)
    assert len(order_data['availableShippingMethods']) == (
        expected_methods.count())

    method = order_data['availableShippingMethods'][0]
    expected_method = expected_methods.first()
    assert float(expected_method.price.amount) == method['price']['amount']
    assert float(expected_method.minimum_order_price.amount) == (
        method['minimumOrderPrice']['amount'])
    assert expected_method.type.upper() == method['type']


def test_order_events_query(
        staff_api_client, permission_manage_orders, fulfilled_order,
        staff_user):
    query = """
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
                        message
                        email
                        emailType
                        amount
                        quantity
                        composedId
                        }
                    }
                }
            }
        }
    """
    event = fulfilled_order.events.create(
        type=OrderEvents.OTHER.value,
        user=staff_user,
        parameters={
            'message': 'Example note',
            'email_type': OrderEventsEmails.PAYMENT.value,
            'amount': '80.00',
            'quantity': '10',
            'composed_id': '10-10'})
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content['data']['orders']['edges'][0]['node']['events'][0]
    assert data['message'] == event.parameters['message']
    assert data['amount'] == float(event.parameters['amount'])
    assert data['emailType'] == OrderEventsEmailsEnum.PAYMENT.name
    assert data['quantity'] == int(event.parameters['quantity'])
    assert data['composedId'] == event.parameters['composed_id']
    assert data['user']['email'] == staff_user.email
    assert data['type'] == OrderEvents.OTHER.value.upper()
    assert data['date'] == event.date.isoformat()


def test_non_staff_user_can_only_see_his_order(user_api_client, order):
    # FIXME: Remove client.login() when JWT authentication is re-enabled.
    user_api_client.login(username=order.user.email, password='password')

    query = """
    query OrderQuery($id: ID!) {
        order(id: $id) {
            number
        }
    }
    """
    ID = graphene.Node.to_global_id('Order', order.id)
    variables = {'id': ID}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    order_data = content['data']['order']
    assert order_data['number'] == str(order.pk)

    order.user = None
    order.save()
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    order_data = content['data']['order']
    assert not order_data


def test_draft_order_create(
        staff_api_client, permission_manage_orders, customer_user,
        product_without_shipping, shipping_method, variant, voucher):
    variant_0 = variant
    query = """
    mutation draftCreate(
        $user: ID, $discount: Decimal, $lines: [OrderLineCreateInput],
        $shippingAddress: AddressInput, $shippingMethod: ID, $voucher: ID) {
            draftOrderCreate(
                input: {user: $user, discount: $discount,
                lines: $lines, shippingAddress: $shippingAddress,
                shippingMethod: $shippingMethod, voucher: $voucher}) {
                    errors {
                        field
                        message
                    }
                    order {
                        discountAmount {
                            amount
                        }
                        discountName
                        lines {
                            edges {
                                node {
                                    productName
                                    productSku
                                    quantity
                                }
                            }
                        }
                        status
                        voucher {
                            code
                        }

                    }
                }
        }
    """
    user_id = graphene.Node.to_global_id('User', customer_user.id)
    variant_0_id = graphene.Node.to_global_id('ProductVariant', variant_0.id)
    variant_1 = product_without_shipping.variants.first()
    variant_1.quantity = 2
    variant_1.save()
    variant_1_id = graphene.Node.to_global_id('ProductVariant', variant_1.id)
    discount = '10'
    variant_list = [
        {'variantId': variant_0_id, 'quantity': 2},
        {'variantId': variant_1_id, 'quantity': 1}]
    shipping_address = {'firstName': 'John', 'country': 'PL'}
    shipping_id = graphene.Node.to_global_id(
        'ShippingMethod', shipping_method.id)
    voucher_id = graphene.Node.to_global_id('Voucher', voucher.id)
    variables = {
        'user': user_id,
        'discount': discount,
        'lines': variant_list,
        'shippingAddress': shipping_address,
        'shippingMethod': shipping_id,
        'voucher': voucher_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['draftOrderCreate']['order']
    assert data['status'] == OrderStatus.DRAFT.upper()
    assert data['voucher']['code'] == voucher.code

    order = Order.objects.first()
    assert order.user == customer_user
    assert order.billing_address == customer_user.default_billing_address
    assert order.shipping_method == shipping_method
    assert order.shipping_address == Address(
        **{'first_name': 'John', 'country': 'PL'})


def test_draft_order_update(
        staff_api_client, permission_manage_orders, order_with_lines):
    order = order_with_lines
    query = """
        mutation draftUpdate($id: ID!, $email: String) {
            draftOrderUpdate(id: $id, input: {userEmail: $email}) {
                errors {
                    field
                    message
                }
                order {
                    userEmail
                }
            }
        }
        """
    email = 'not_default@example.com'
    order_id = graphene.Node.to_global_id('Order', order.id)
    variables = {'id': order_id, 'email': email}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['draftOrderUpdate']['order']
    assert data['userEmail'] == email


def test_draft_order_delete(
        staff_api_client, permission_manage_orders, order_with_lines):
    order = order_with_lines
    query = """
        mutation draftDelete($id: ID!) {
            draftOrderDelete(id: $id) {
                order {
                    id
                }
            }
        }
        """
    order_id = graphene.Node.to_global_id('Order', order.id)
    variables = {'id': order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    with pytest.raises(order._meta.model.DoesNotExist):
        order.refresh_from_db()


def test_check_for_draft_order_errors(order_with_lines):
    errors = check_for_draft_order_errors(order_with_lines, [])
    assert not errors


def test_check_for_draft_order_errors_wrong_shipping(order_with_lines):
    order = order_with_lines
    shipping_zone = order.shipping_method.shipping_zone
    shipping_zone.countries = ['DE']
    shipping_zone.save()
    assert order.shipping_address.country.code not in shipping_zone.countries
    errors = check_for_draft_order_errors(order, [])
    msg = 'Shipping method is not valid for chosen shipping address'
    assert errors[0].message == msg


def test_check_for_draft_order_errors_no_order_lines(order):
    errors = check_for_draft_order_errors(order, [])
    assert errors[0].message == 'Could not create order without any products.'


def test_draft_order_complete(
        staff_api_client, permission_manage_orders, staff_user, draft_order):
    order = draft_order
    query = """
        mutation draftComplete($id: ID!) {
            draftOrderComplete(id: $id) {
                order {
                    status
                }
            }
        }
        """
    line_1, line_2 = order.lines.order_by('-quantity').all()
    line_1.quantity = 1
    line_1.save(update_fields=['quantity'])
    assert line_1.variant.quantity_available >= line_1.quantity
    assert line_2.variant.quantity_available < line_2.quantity

    order_id = graphene.Node.to_global_id('Order', order.id)
    variables = {'id': order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['draftOrderComplete']['order']
    order.refresh_from_db()
    assert data['status'] == order.status.upper()
    missing_stock_event, draft_placed_event = OrderEvent.objects.all()

    assert missing_stock_event.user == staff_user
    assert missing_stock_event.type == OrderEvents.OVERSOLD_ITEMS.value
    assert missing_stock_event.parameters == {'oversold_items': [str(line_2)]}

    assert draft_placed_event.user == staff_user
    assert draft_placed_event.type == OrderEvents.PLACED_FROM_DRAFT.value
    assert draft_placed_event.parameters == {}


DRAFT_ORDER_LINE_CREATE_MUTATION = """
    mutation DraftOrderLineCreate($orderId: ID!, $variantId: ID!, $quantity: Int!) {
        draftOrderLineCreate(id: $orderId, input: {variantId: $variantId, quantity: $quantity}) {
            errors {
                field
                message
            }
            orderLine {
                id
                quantity
                productSku
            }
            order {
                total {
                    gross {
                        amount
                    }
                }
            }
        }
    }
"""


def test_draft_order_line_create(
        draft_order, permission_manage_orders, staff_api_client):
    query = DRAFT_ORDER_LINE_CREATE_MUTATION
    order = draft_order
    line = order.lines.first()
    variant = line.variant
    old_quantity = line.quantity
    quantity = 1
    order_id = graphene.Node.to_global_id('Order', order.id)
    variant_id = graphene.Node.to_global_id('ProductVariant', variant.id)
    variables = {
        'orderId': order_id, 'variantId': variant_id, 'quantity': quantity}

    # mutation should fail without proper permissions
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)

    # assign permissions
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['draftOrderLineCreate']
    assert data['orderLine']['productSku'] == variant.sku
    assert data['orderLine']['quantity'] == old_quantity + quantity

    # mutation should fail when quantity is lower than 1
    variables = {'orderId': order_id, 'variantId': variant_id, 'quantity': 0}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['draftOrderLineCreate']
    assert data['errors']
    assert data['errors'][0]['field'] == 'quantity'


def test_require_draft_order_when_creating_lines(
        order_with_lines, staff_api_client, permission_manage_orders):
    query = DRAFT_ORDER_LINE_CREATE_MUTATION
    order = order_with_lines
    line = order.lines.first()
    variant = line.variant
    order_id = graphene.Node.to_global_id('Order', order.id)
    variant_id = graphene.Node.to_global_id('ProductVariant', variant.id)
    variables = {'orderId': order_id, 'variantId': variant_id, 'quantity': 1}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['draftOrderLineCreate']
    assert data['errors']


DRAFT_ORDER_LINE_UPDATE_MUTATION = """
    mutation DraftOrderLineUpdate($lineId: ID!, $quantity: Int!) {
        draftOrderLineUpdate(id: $lineId, input: {quantity: $quantity}) {
            errors {
                field
                message
            }
            orderLine {
                id
                quantity
            }
            order {
                total {
                    gross {
                        amount
                    }
                }
            }
        }
    }
"""


def test_draft_order_line_update(
        draft_order, permission_manage_orders, staff_api_client):
    query = DRAFT_ORDER_LINE_UPDATE_MUTATION
    order = draft_order
    line = order.lines.first()
    new_quantity = 1
    line_id = graphene.Node.to_global_id('OrderLine', line.id)
    variables = {'lineId': line_id, 'quantity': new_quantity}

    # mutation should fail without proper permissions
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)

    # assign permissions
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['draftOrderLineUpdate']
    assert data['orderLine']['quantity'] == new_quantity

    # mutation should fail when quantity is lower than 1
    variables = {'lineId': line_id, 'quantity': 0}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['draftOrderLineUpdate']
    assert data['errors']
    assert data['errors'][0]['field'] == 'quantity'


def test_require_draft_order_when_updating_lines(
        order_with_lines, staff_api_client, permission_manage_orders):
    query = DRAFT_ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    line = order.lines.first()
    line_id = graphene.Node.to_global_id('OrderLine', line.id)
    variables = {'lineId': line_id, 'quantity': 1}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['draftOrderLineUpdate']
    assert data['errors']


DRAFT_ORDER_LINE_DELETE_MUTATION = """
    mutation DraftOrderLineDelete($id: ID!) {
        draftOrderLineDelete(id: $id) {
            errors {
                field
                message
            }
            orderLine {
                id
            }
            order {
                id
            }
        }
    }
"""


def test_draft_order_line_remove(
        draft_order, permission_manage_orders, staff_api_client):
    query = DRAFT_ORDER_LINE_DELETE_MUTATION
    order = draft_order
    line = order.lines.first()
    line_id = graphene.Node.to_global_id('OrderLine', line.id)
    variables = {'id': line_id}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['draftOrderLineDelete']
    assert data['orderLine']['id'] == line_id
    assert line not in order.lines.all()


def test_require_draft_order_when_removing_lines(
        staff_api_client, order_with_lines, permission_manage_orders):
    query = DRAFT_ORDER_LINE_DELETE_MUTATION
    order = order_with_lines
    line = order.lines.first()
    line_id = graphene.Node.to_global_id('OrderLine', line.id)
    variables = {'id': line_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['draftOrderLineDelete']
    assert data['errors']


def test_order_update(
        staff_api_client, permission_manage_orders, order_with_lines):
    order = order_with_lines
    query = """
        mutation orderUpdate(
        $id: ID!, $email: String, $first_name: String, $last_name: String,
        $country_code: String) {
            orderUpdate(
                id: $id, input: {
                    userEmail: $email, shippingAddress:
                    {firstName: $first_name, country: $country_code},
                    billingAddress:
                    {lastName: $last_name, country: $country_code}}) {
                errors {
                    field
                    message
                }
                order {
                    userEmail
                }
            }
        }
        """
    email = 'not_default@example.com'
    first_name = 'Test fname'
    last_name = 'Test lname'
    assert not order.user_email == email
    assert not order.shipping_address.first_name == first_name
    assert not order.billing_address.last_name == last_name
    order_id = graphene.Node.to_global_id('Order', order.id)
    variables = {
        'id': order_id,
        'email': email,
        'first_name': first_name,
        'last_name': last_name,
        'country_code': 'PL'}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['orderUpdate']['order']
    assert data['userEmail'] == email

    order.refresh_from_db()
    assert order.shipping_address.first_name == first_name
    assert order.billing_address.last_name == last_name


def test_order_add_note(
        staff_api_client, permission_manage_orders, order_with_lines,
        staff_user):
    order = order_with_lines
    query = """
        mutation addNote($id: ID!, $message: String) {
            orderAddNote(order: $id, input: {message: $message}) {
                errors {
                field
                message
                }
                order {
                    id
                }
                event {
                    user {
                        email
                    }
                    message
                }
            }
        }
    """
    assert not order.events.all()
    order_id = graphene.Node.to_global_id('Order', order.id)
    message = 'nuclear note'
    variables = {'id': order_id, 'message': message}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['orderAddNote']

    assert data['order']['id'] == order_id
    assert data['event']['user']['email'] == staff_user.email
    assert data['event']['message'] == message

    event = order.events.get()
    assert event.type == OrderEvents.NOTE_ADDED.value
    assert event.user == staff_user
    assert event.parameters == {'message': message}


CANCEL_ORDER_QUERY = """
    mutation cancelOrder($id: ID!, $restock: Boolean!) {
        orderCancel(id: $id, restock: $restock) {
            order {
                status
            }
        }
    }
"""


def test_order_cancel_and_restock(
        staff_api_client, permission_manage_orders, order_with_lines):
    order = order_with_lines
    query = CANCEL_ORDER_QUERY
    order_id = graphene.Node.to_global_id('Order', order.id)
    restock = True
    quantity = order.get_total_quantity()
    variables = {'id': order_id, 'restock': restock}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['orderCancel']['order']
    order.refresh_from_db()
    order_event = order.events.last()
    assert order_event.parameters['quantity'] == quantity
    assert order_event.type == OrderEvents.FULFILLMENT_RESTOCKED_ITEMS.value
    assert data['status'] == order.status.upper()


def test_order_cancel(
        staff_api_client, permission_manage_orders, order_with_lines):
    order = order_with_lines
    query = CANCEL_ORDER_QUERY
    order_id = graphene.Node.to_global_id('Order', order.id)
    restock = False
    variables = {'id': order_id, 'restock': restock}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['orderCancel']['order']
    order.refresh_from_db()
    order_event = order.events.last()
    assert order_event.type == OrderEvents.CANCELED.value
    assert data['status'] == order.status.upper()


def test_order_capture(
        staff_api_client, permission_manage_orders, payment_preauth, staff_user):
    order = payment_preauth.order
    query = """
        mutation captureOrder($id: ID!, $amount: Decimal!) {
            orderCapture(id: $id, amount: $amount) {
                order {
                    paymentStatus
                    isPaid
                    totalCaptured {
                        amount
                    }
                }
            }
        }
    """
    order_id = graphene.Node.to_global_id('Order', order.id)
    amount = float(payment_preauth.get_total().gross.amount)
    variables = {'id': order_id, 'amount': amount}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['orderCapture']['order']
    order.refresh_from_db()
    assert data['paymentStatus'] == PaymentStatusEnum.CONFIRMED.name
    assert data['isPaid']
    assert data['totalCaptured']['amount'] == float(amount)

    event_order_paid = order.events.first()
    assert event_order_paid.type == OrderEvents.ORDER_FULLY_PAID.value
    assert event_order_paid.user is None

    event_email_sent, event_captured = list(order.events.all())[-2:]
    assert event_email_sent.user is None
    assert event_email_sent.parameters == {
        'email': order.user_email,
        'email_type': OrderEventsEmails.PAYMENT.value}
    assert event_captured.type == OrderEvents.PAYMENT_CAPTURED.value
    assert event_captured.user == staff_user
    assert event_captured.parameters == {'amount': str(amount)}


def test_paid_order_mark_as_paid(
        staff_api_client, permission_manage_orders, payment_preauth):
    order = payment_preauth.order
    query = """
            mutation markPaid($id: ID!) {
                orderMarkAsPaid(id: $id) {
                    errors {
                        field
                        message
                    }
                    order {
                        isPaid
                    }
                }
            }
        """
    order_id = graphene.Node.to_global_id('Order', order.id)
    variables = {'id': order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    errors = content['data']['orderMarkAsPaid']['errors']
    msg = 'Orders with payments can not be manually marked as paid.'
    assert errors[0]['message'] == msg
    assert errors[0]['field'] == 'payment'


def test_order_mark_as_paid(
        staff_api_client, permission_manage_orders, order_with_lines,
        staff_user):
    order = order_with_lines
    query = """
            mutation markPaid($id: ID!) {
                orderMarkAsPaid(id: $id) {
                    errors {
                        field
                        message
                    }
                    order {
                        isPaid
                    }
                }
            }
        """
    assert not order.is_fully_paid()
    order_id = graphene.Node.to_global_id('Order', order.id)
    variables = {'id': order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['orderMarkAsPaid']['order']
    order.refresh_from_db()
    assert data['isPaid'] == True == order.is_fully_paid()

    event_order_paid = order.events.first()
    assert event_order_paid.type == OrderEvents.ORDER_MARKED_AS_PAID.value
    assert event_order_paid.user == staff_user


def test_order_release(
        staff_api_client, permission_manage_orders, payment_preauth, staff_user):
    order = payment_preauth.order
    query = """
            mutation releaseOrder($id: ID!) {
                orderRelease(id: $id) {
                    order {
                        paymentStatus
                    }
                }
            }
        """
    order_id = graphene.Node.to_global_id('Order', order.id)
    variables = {'id': order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['orderRelease']['order']
    assert data['paymentStatus'] == PaymentStatusEnum.REFUNDED.name
    event_payment_released = order.events.last()
    assert event_payment_released.type == OrderEvents.PAYMENT_RELEASED.value
    assert event_payment_released.user == staff_user


def test_order_refund(
        staff_api_client, permission_manage_orders, payment_confirmed):
    order = order = payment_confirmed.order
    query = """
        mutation refundOrder($id: ID!, $amount: Decimal!) {
            orderRefund(id: $id, amount: $amount) {
                order {
                    paymentStatus
                    isPaid
                    status
                }
            }
        }
    """
    order_id = graphene.Node.to_global_id('Order', order.id)
    amount = float(payment_confirmed.get_total().gross.amount)
    variables = {'id': order_id, 'amount': amount}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['orderRefund']['order']
    order.refresh_from_db()
    assert data['status'] == order.status.upper()
    assert data['paymentStatus'] == PaymentStatusEnum.REFUNDED.name
    assert data['isPaid'] == False

    order_event = order.events.last()
    assert order_event.parameters['amount'] == str(amount)
    assert order_event.type == OrderEvents.PAYMENT_REFUNDED.value


def test_clean_order_release_payment():
    payment = MagicMock(spec=Payment)
    payment.status = 'not preauth'
    errors = clean_release_payment(payment, [])
    assert errors[0].field == 'payment'
    assert errors[0].message == 'Only pre-authorized payments can be released'

    payment.status = PaymentStatus.PREAUTH
    error_msg = 'error has happened.'
    payment.release = Mock(side_effect=ValueError(error_msg))
    errors = clean_release_payment(payment, [])
    assert errors[0].field == 'payment'
    assert errors[0].message == error_msg


def test_clean_order_refund_payment():
    payment = MagicMock(spec=Payment)
    payment.variant = CustomPaymentChoices.MANUAL
    amount = Mock(spec='string')
    errors = clean_refund_payment(payment, amount, [])
    assert errors[0].field == 'payment'
    assert errors[0].message == 'Manual payments can not be refunded.'


def test_clean_order_capture():
    amount = Mock(spec='string')
    errors = clean_order_capture(None, amount, [])
    assert errors[0].field == 'payment'
    assert errors[0].message == (
        'There\'s no payment associated with the order.')


def test_clean_order_mark_as_paid(payment_preauth):
    order = payment_preauth.order
    errors = clean_order_mark_as_paid(order, [])
    assert errors[0].field == 'payment'
    assert errors[0].message == (
        'Orders with payments can not be manually marked as paid.')

    order.payments.all().delete()
    assert clean_order_mark_as_paid(order, []) == []


def test_clean_order_cancel(order):
    assert clean_order_cancel(order, []) == []

    order.status = OrderStatus.DRAFT
    order.save()

    errors = clean_order_cancel(order, [])
    assert errors[0].field == 'order'
    assert errors[0].message == 'This order can\'t be canceled.'


ORDER_UPDATE_SHIPPING_QUERY = """
    mutation orderUpdateShipping($order: ID!, $shippingMethod: ID) {
        orderUpdateShipping(
                order: $order, input: {shippingMethod: $shippingMethod}) {
            errors {
                field
                message
            }
            order {
                id
            }
        }
    }
"""


def test_order_update_shipping(
        staff_api_client, permission_manage_orders, order_with_lines,
        shipping_method, staff_user):
    order = order_with_lines
    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id('Order', order.id)
    method_id = graphene.Node.to_global_id(
        'ShippingMethod', shipping_method.id)
    variables = {'order': order_id, 'shippingMethod': method_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['orderUpdateShipping']
    assert data['order']['id'] == order_id

    order.refresh_from_db()
    shipping_price = shipping_method.get_total()
    assert order.shipping_method == shipping_method
    assert order.shipping_price_net == shipping_price.net
    assert order.shipping_price_gross == shipping_price.gross
    assert order.shipping_method_name == shipping_method.name


def test_order_update_shipping_clear_shipping_method(
        staff_api_client, permission_manage_orders, order, staff_user,
        shipping_method):
    order.shipping_method = shipping_method
    order.shipping_price = shipping_method.get_total()
    order.shipping_method_name = 'Example shipping'
    order.save()

    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id('Order', order.id)
    variables = {'order': order_id, 'shippingMethod': None}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['orderUpdateShipping']
    assert data['order']['id'] == order_id

    order.refresh_from_db()
    assert order.shipping_method is None
    assert order.shipping_price == ZERO_TAXED_MONEY
    assert order.shipping_method_name is None


def test_order_update_shipping_shipping_required(
        staff_api_client, permission_manage_orders, order_with_lines,
        staff_user):
    order = order_with_lines
    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id('Order', order.id)
    variables = {'order': order_id, 'shippingMethod': None}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['orderUpdateShipping']
    assert data['errors'][0]['field'] == 'shippingMethod'
    assert data['errors'][0]['message'] == (
        'Shipping method is required for this order.')


def test_order_update_shipping_no_shipping_address(
        staff_api_client, permission_manage_orders, order_with_lines,
        shipping_method, staff_user):
    order = order_with_lines
    order.shipping_address = None
    order.save()
    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id('Order', order.id)
    method_id = graphene.Node.to_global_id(
        'ShippingMethod', shipping_method.id)
    variables = {'order': order_id, 'shippingMethod': method_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['orderUpdateShipping']
    assert data['errors'][0]['field'] == 'order'
    assert data['errors'][0]['message'] == (
        'Cannot choose a shipping method for an order without'
        ' the shipping address.')


def test_order_update_shipping_incorrect_shipping_method(
        staff_api_client, permission_manage_orders, order_with_lines,
        shipping_method, staff_user):
    order = order_with_lines
    zone = shipping_method.shipping_zone
    zone.countries = ['DE']
    zone.save()
    assert order.shipping_address.country.code not in zone.countries
    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id('Order', order.id)
    method_id = graphene.Node.to_global_id(
        'ShippingMethod', shipping_method.id)
    variables = {'order': order_id, 'shippingMethod': method_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['orderUpdateShipping']
    assert data['errors'][0]['field'] == 'shippingMethod'
    assert data['errors'][0]['message'] == (
        'Shipping method cannot be used with this order.')
