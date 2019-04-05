import uuid
from unittest.mock import MagicMock, Mock, patch

import graphene
import pytest

from saleor.graphql.core.enums import ReportingPeriod
from saleor.graphql.order.enums import OrderEventsEmailsEnum
from saleor.graphql.order.mutations.orders import (
    clean_order_cancel, clean_order_capture, clean_refund_payment,
    clean_void_payment)
from saleor.graphql.order.utils import can_finalize_draft_order
from saleor.graphql.payment.enums import PaymentChargeStatusEnum
from saleor.order import OrderEvents, OrderEventsEmails, OrderStatus
from saleor.order.models import Order
from saleor.payment import CustomPaymentChoices
from saleor.payment.models import Payment
from saleor.shipping.models import ShippingMethod

from .utils import (
    assert_no_permission, assert_read_only_mode, get_graphql_content)


@pytest.fixture
def orders(customer_user):
    Order.objects.bulk_create([
        Order(
            user=customer_user,
            status=OrderStatus.CANCELED,
            token=uuid.uuid4()),
        Order(
            user=customer_user,
            status=OrderStatus.UNFULFILLED,
            token=uuid.uuid4()),
        Order(
            user=customer_user,
            status=OrderStatus.PARTIALLY_FULFILLED,
            token=uuid.uuid4()),
        Order(
            user=customer_user,
            status=OrderStatus.FULFILLED,
            token=uuid.uuid4()),
        Order(
            user=customer_user,
            status=OrderStatus.DRAFT,
            token=uuid.uuid4())])


def test_orderline_query(
        staff_api_client, permission_manage_orders, fulfilled_order):
    order = fulfilled_order
    query = """
        query OrdersQuery {
            orders(first: 1) {
                edges {
                    node {
                        lines {
                            thumbnail(size: 540) {
                                url
                            }
                            variant {
                                id
                            }
                        }
                    }
                }
            }
        }
    """
    line = order.lines.first()
    line.save()

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    order_data = content['data']['orders']['edges'][0]['node']
    assert '/static/images/placeholder540x540.png' in order_data['lines'][0]['thumbnail']['url']
    variant_id = graphene.Node.to_global_id('ProductVariant', line.variant.pk)
    assert order_data['lines'][0]['variant']['id'] == variant_id


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
                    canFinalize
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
                        id
                    }
                    fulfillments {
                        fulfillmentOrder
                    }
                    payments{
                        id
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
    assert order_data['canFinalize'] is True
    assert order_data['status'] == order.status.upper()
    assert order_data['statusDisplay'] == order.get_status_display()
    payment_status = PaymentChargeStatusEnum.get(
        order.get_payment_status()).name
    assert order_data['paymentStatus'] == payment_status
    payment_status_display = order.get_payment_status_display()
    assert order_data['paymentStatusDisplay'] == payment_status_display
    assert order_data['isPaid'] == order.is_fully_paid()
    assert order_data['userEmail'] == order.user_email
    expected_price = order_data['shippingPrice']['gross']['amount']
    assert expected_price == order.shipping_price.gross.amount
    assert len(order_data['lines']) == order.lines.count()
    fulfillment = order.fulfillments.first().fulfillment_order
    fulfillment_order = order_data['fulfillments'][0]['fulfillmentOrder']
    assert fulfillment_order == fulfillment
    assert len(order_data['payments']) == order.payments.count()

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


def test_order_query_customer(api_client):
    query = """
        query OrdersQuery {
            orders(first: 1) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """

    response = api_client.post_graphql(query)
    assert_no_permission(response)


def test_order_query_draft_excluded(
        staff_api_client, permission_manage_orders, orders):
    query = """
    query OrdersQuery {
        orders(first: 10) {
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
    edges = get_graphql_content(response)['data']['orders']['edges']

    assert len(edges) == Order.objects.confirmed().count()


def test_draft_order_query(
        staff_api_client, permission_manage_orders, orders):
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
    edges = get_graphql_content(response)['data']['draftOrders']['edges']

    assert len(edges) == Order.objects.drafts().count()


def test_nested_order_events_query(
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
                        orderNumber
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
    assert data['orderNumber'] == str(fulfilled_order.pk)


def test_non_staff_user_can_only_see_his_order(user_api_client, order):
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
        product_without_shipping, shipping_method, variant, voucher,
        graphql_address_data):
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
                            productName
                            productSku
                            quantity
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
    shipping_address = graphql_address_data
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
    assert_read_only_mode(response)


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
    assert_read_only_mode(response)


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
    assert_read_only_mode(response)


ORDER_CAN_FINALIZE_QUERY = """
    query OrderQuery($id: ID!){
        order(id: $id){
            canFinalize
        }
    }
"""

def test_can_finalize_order(
        staff_api_client, permission_manage_orders, order_with_lines):
    order_id = graphene.Node.to_global_id('Order', order_with_lines.id)
    variables = {'id': order_id}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(
        ORDER_CAN_FINALIZE_QUERY, variables)
    content = get_graphql_content(response)
    assert content['data']['order']['canFinalize'] is True


def test_can_finalize_order_no_order_lines(
        staff_api_client, permission_manage_orders, order):
    order_id = graphene.Node.to_global_id('Order', order.id)
    variables = {'id': order_id}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(
        ORDER_CAN_FINALIZE_QUERY, variables)
    content = get_graphql_content(response)
    assert content['data']['order']['canFinalize'] is False


def test_can_finalize_draft_order(order_with_lines):
    errors = can_finalize_draft_order(order_with_lines, [])
    assert not errors


def test_can_finalize_draft_order_wrong_shipping(order_with_lines):
    order = order_with_lines
    shipping_zone = order.shipping_method.shipping_zone
    shipping_zone.countries = ['DE']
    shipping_zone.save()
    assert order.shipping_address.country.code not in shipping_zone.countries
    errors = can_finalize_draft_order(order, [])
    msg = 'Shipping method is not valid for chosen shipping address'
    assert errors[0].message == msg


def test_can_finalize_draft_order_no_order_lines(order):
    errors = can_finalize_draft_order(order, [])
    assert errors[0].message == 'Could not create order without any products.'


def test_can_finalize_draft_order_non_existing_variant(order_with_lines):
    order = order_with_lines
    line = order.lines.first()
    variant = line.variant
    variant.delete()
    line.refresh_from_db()
    assert line.variant is None

    errors = can_finalize_draft_order(order, [])
    assert (
        errors[0].message ==
        'Could not create orders with non-existing products.')


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
    assert_read_only_mode(response)


def test_draft_order_complete_existing_user_email_updates_user_field(
        staff_api_client, draft_order, customer_user,
        permission_manage_orders):
    order = draft_order
    order.user_email = customer_user.email
    order.user = None
    order.save()
    query = """
        mutation draftComplete($id: ID!) {
            draftOrderComplete(id: $id) {
                order {
                    status
                }
            }
        }
        """
    order_id = graphene.Node.to_global_id('Order', order.id)
    variables = {'id': order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    assert_read_only_mode(response)


def test_draft_order_complete_anonymous_user_email_sets_user_field_null(
        staff_api_client, draft_order, permission_manage_orders):
    order = draft_order
    order.user_email = 'anonymous@example.com'
    order.user = None
    order.save()
    query = """
        mutation draftComplete($id: ID!) {
            draftOrderComplete(id: $id) {
                order {
                    status
                }
            }
        }
        """
    order_id = graphene.Node.to_global_id('Order', order.id)
    variables = {'id': order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    assert_read_only_mode(response)


def test_draft_order_complete_anonymous_user_no_email(
        staff_api_client, draft_order, permission_manage_orders):
    order = draft_order
    order.user_email = ''
    order.user = None
    order.save()
    query = """
        mutation draftComplete($id: ID!) {
            draftOrderComplete(id: $id) {
                order {
                    status
                }
                errors {
                    field
                    message
                }
            }
        }
        """
    order_id = graphene.Node.to_global_id('Order', order.id)
    variables = {'id': order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    assert_read_only_mode(response)


DRAFT_ORDER_LINES_CREATE_MUTATION = """
    mutation DraftOrderLinesCreate($orderId: ID!, $variantId: ID!, $quantity: Int!) {
        draftOrderLinesCreate(id: $orderId, input: [{variantId: $variantId, quantity: $quantity}]) {
            errors {
                field
                message
            }
            orderLines {
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


def test_draft_order_lines_create(
        draft_order, permission_manage_orders, staff_api_client):
    query = DRAFT_ORDER_LINES_CREATE_MUTATION
    order = draft_order
    line = order.lines.first()
    variant = line.variant
    old_quantity = line.quantity
    quantity = 1
    order_id = graphene.Node.to_global_id('Order', order.id)
    variant_id = graphene.Node.to_global_id('ProductVariant', variant.id)
    variables = {
        'orderId': order_id, 'variantId': variant_id, 'quantity': quantity}

    # assign permissions
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query, variables)
    assert_read_only_mode(response)


def test_require_draft_order_when_creating_lines(
        order_with_lines, staff_api_client, permission_manage_orders):
    query = DRAFT_ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    line = order.lines.first()
    variant = line.variant
    order_id = graphene.Node.to_global_id('Order', order.id)
    variant_id = graphene.Node.to_global_id('ProductVariant', variant.id)
    variables = {'orderId': order_id, 'variantId': variant_id, 'quantity': 1}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    assert_read_only_mode(response)


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

    # assign permissions
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query, variables)
    assert_read_only_mode(response)


def test_require_draft_order_when_updating_lines(
        order_with_lines, staff_api_client, permission_manage_orders):
    query = DRAFT_ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    line = order.lines.first()
    line_id = graphene.Node.to_global_id('OrderLine', line.id)
    variables = {'lineId': line_id, 'quantity': 1}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    assert_read_only_mode(response)


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
    assert_read_only_mode(response)


def test_require_draft_order_when_removing_lines(
        staff_api_client, order_with_lines, permission_manage_orders):
    query = DRAFT_ORDER_LINE_DELETE_MUTATION
    order = order_with_lines
    line = order.lines.first()
    line_id = graphene.Node.to_global_id('OrderLine', line.id)
    variables = {'id': line_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    assert_read_only_mode(response)


def test_order_update(
        staff_api_client, permission_manage_orders, order_with_lines,
        graphql_address_data):
    order = order_with_lines
    order.user = None
    order.save()
    query = """
        mutation orderUpdate(
        $id: ID!, $email: String, $address: AddressInput) {
            orderUpdate(
                id: $id, input: {
                    userEmail: $email,
                    shippingAddress: $address,
                    billingAddress: $address}) {
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
    assert not order.user_email == email
    assert not order.shipping_address.first_name == graphql_address_data['firstName']
    assert not order.billing_address.last_name == graphql_address_data['lastName']
    order_id = graphene.Node.to_global_id('Order', order.id)
    variables = {
        'id': order_id, 'email': email, 'address': graphql_address_data}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    assert_read_only_mode(response)


def test_order_update_anonymous_user_no_user_email(
        staff_api_client, order_with_lines, permission_manage_orders,
        graphql_address_data):
    order = order_with_lines
    order.user = None
    order.save()
    query = """
            mutation orderUpdate(
            $id: ID!, $address: AddressInput) {
                orderUpdate(
                    id: $id, input: {
                        shippingAddress: $address,
                        billingAddress: $address}) {
                    errors {
                        field
                        message
                    }
                    order {
                        id
                        status
                    }
                }
            }
            """
    first_name = 'Test fname'
    last_name = 'Test lname'
    order_id = graphene.Node.to_global_id('Order', order.id)
    variables = {'id': order_id, 'address': graphql_address_data}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    assert_read_only_mode(response)


def test_order_update_user_email_existing_user(
        staff_api_client, order_with_lines, customer_user,
        permission_manage_orders, graphql_address_data):
    order = order_with_lines
    order.user = None
    order.save()
    query = """
        mutation orderUpdate(
        $id: ID!, $email: String, $address: AddressInput) {
            orderUpdate(
                id: $id, input: {
                    userEmail: $email, shippingAddress: $address,
                    billingAddress: $address}) {
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
    email = customer_user.email
    order_id = graphene.Node.to_global_id('Order', order.id)
    variables = {
        'id': order_id, 'address': graphql_address_data, 'email': email}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    assert_read_only_mode(response)


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
    assert_read_only_mode(response)


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
    assert_read_only_mode(response)


def test_order_cancel(
        staff_api_client, permission_manage_orders, order_with_lines):
    order = order_with_lines
    query = CANCEL_ORDER_QUERY
    order_id = graphene.Node.to_global_id('Order', order.id)
    restock = False
    variables = {'id': order_id, 'restock': restock}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    assert_read_only_mode(response)


def test_order_capture(
        staff_api_client, permission_manage_orders,
        payment_txn_preauth, staff_user):
    order = payment_txn_preauth.order
    query = """
        mutation captureOrder($id: ID!, $amount: Decimal!) {
            orderCapture(id: $id, amount: $amount) {
                order {
                    paymentStatus
                    paymentStatusDisplay
                    isPaid
                    totalCaptured {
                        amount
                    }
                }
            }
        }
    """
    order_id = graphene.Node.to_global_id('Order', order.id)
    amount = float(payment_txn_preauth.total)
    variables = {'id': order_id, 'amount': amount}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    assert_read_only_mode(response)


def test_paid_order_mark_as_paid(
        staff_api_client, permission_manage_orders,
        payment_txn_preauth):
    order = payment_txn_preauth.order
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
    assert_read_only_mode(response)


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
    assert_read_only_mode(response)


def test_order_void(
        staff_api_client, permission_manage_orders, payment_txn_preauth,
        staff_user):
    order = payment_txn_preauth.order
    query = """
            mutation voidOrder($id: ID!) {
                orderVoid(id: $id) {
                    order {
                        paymentStatus
                        paymentStatusDisplay
                    }
                }
            }
        """
    order_id = graphene.Node.to_global_id('Order', order.id)
    variables = {'id': order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    assert_read_only_mode(response)


def test_order_refund(
        staff_api_client, permission_manage_orders,
        payment_txn_captured):
    order = order = payment_txn_captured.order
    query = """
        mutation refundOrder($id: ID!, $amount: Decimal!) {
            orderRefund(id: $id, amount: $amount) {
                order {
                    paymentStatus
                    paymentStatusDisplay
                    isPaid
                    status
                }
            }
        }
    """
    order_id = graphene.Node.to_global_id('Order', order.id)
    amount = float(payment_txn_captured.total)
    variables = {'id': order_id, 'amount': amount}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    assert_read_only_mode(response)


def test_clean_order_void_payment():
    payment = MagicMock(spec=Payment)
    payment.is_active = False
    errors = clean_void_payment(payment, [])
    assert errors[0].field == 'payment'
    assert errors[0].message == 'Only pre-authorized payments can be voided'

    payment.is_active = True
    error_msg = 'error has happened.'
    with patch('saleor.graphql.order.mutations.orders.gateway_void',
               side_effect=ValueError(error_msg)):
        errors = clean_void_payment(payment, [])
    assert errors[0].field == 'payment'
    assert errors[0].message == error_msg


def test_clean_order_refund_payment():
    payment = MagicMock(spec=Payment)
    payment.gateway = CustomPaymentChoices.MANUAL
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
    assert_read_only_mode(response)


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
    assert_read_only_mode(response)


def test_order_update_shipping_shipping_required(
        staff_api_client, permission_manage_orders, order_with_lines,
        staff_user):
    order = order_with_lines
    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id('Order', order.id)
    variables = {'order': order_id, 'shippingMethod': None}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    assert_read_only_mode(response)


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
    assert_read_only_mode(response)


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
    assert_read_only_mode(response)


def test_draft_order_clear_shipping_method(
        staff_api_client, draft_order, permission_manage_orders):
    assert draft_order.shipping_method
    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id('Order', draft_order.id)
    variables = {'order': order_id, 'shippingMethod': None}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    assert_read_only_mode(response)


def test_orders_total(
        staff_api_client, permission_manage_orders, order_with_lines):
    query = """
    query Orders($period: ReportingPeriod) {
        ordersTotal(period: $period) {
            gross {
                amount
                currency
            }
            net {
                currency
                amount
            }
        }
    }
    """
    variables = {'period': ReportingPeriod.TODAY.name}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    assert (
        content['data']['ordersTotal']['gross']['amount'] ==
        order_with_lines.total.gross.amount)


def test_order_by_token_query(api_client, order):
    query = """
    query OrderByToken($token: String!) {
        orderByToken(token: $token) {
            id
        }
    }
    """
    order_id = graphene.Node.to_global_id('Order', order.id)

    response = api_client.post_graphql(query, {'token': order.token})
    content = get_graphql_content(response)

    assert content['data']['orderByToken']['id'] == order_id
