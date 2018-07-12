import json
from unittest.mock import MagicMock, Mock

import graphene
import pytest
from django.shortcuts import reverse
from tests.utils import get_graphql_content

from saleor.account.models import Address
from saleor.graphql.order.mutations.draft_orders import (
    check_for_draft_order_errors)
from saleor.graphql.order.mutations.orders import (
    clean_refund_payment, clean_release_payment)
from saleor.order import CustomPaymentChoices
from saleor.order.models import Order, OrderStatus, Payment, PaymentStatus


def test_order_query(admin_api_client, fulfilled_order):
    order = fulfilled_order
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
                        totalCount
                    }
                    notes {
                        totalCount
                    }
                    fulfillments {
                        edges {
                            node {
                                fulfillmentOrder
                            }
                        }
                        
                    }
                    history {
                        totalCount
                    }
                    totalPrice {
                        net {
                            amount
                        }
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
    assert order_data['orderId'] == order.pk
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
    assert order_data['notes']['totalCount'] == order.notes.count()
    fulfillment = order.fulfillments.first().fulfillment_order
    fulfillment_order = order_data[
        'fulfillments']['edges'][0]['node']['fulfillmentOrder']
    assert fulfillment_order == fulfillment


def test_non_staff_user_can_only_see_his_order(user_api_client, order):
    # FIXME: Remove client.login() when JWT authentication is re-enabled.
    user_api_client.login(username=order.user.email, password='password')

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


def test_draft_order_create(
        admin_api_client, customer_user, product_without_shipping,
        shipping_price, variant, voucher):
    variant_0 = variant
    query = """
    mutation draftCreate(
        $user: ID, $discount: Decimal, $lines: [OrderLineInput],
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
    shipping_address = {
        'firstName': 'John', 'country': 'PL'}
    shipping_id = graphene.Node.to_global_id(
        'ShippingMethodCountry', shipping_price.id)
    voucher_id = graphene.Node.to_global_id('Voucher', voucher.id)
    variables = json.dumps(
        {
            'user': user_id, 'discount': discount,
            'lines': variant_list, 'shippingAddress': shipping_address,
            'shippingMethod': shipping_id, 'voucher': voucher_id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['draftOrderCreate']['order']
    assert data['status'] == OrderStatus.DRAFT.upper()
    assert data['voucher']['code'] == voucher.code

    order = Order.objects.first()
    assert order.user == customer_user
    assert order.billing_address == customer_user.default_billing_address
    assert order.shipping_method == shipping_price
    assert order.shipping_address == Address(
        **{'first_name': 'John', 'country': 'PL'})


def test_draft_order_update(admin_api_client, order_with_lines):
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
    variables = json.dumps({'id': order_id, 'email': email})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    data = content['data']['draftOrderUpdate']['order']
    assert data['userEmail'] == email


def test_draft_order_delete(admin_api_client, order_with_lines):
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
    variables = json.dumps({'id': order_id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    with pytest.raises(order._meta.model.DoesNotExist):
        order.refresh_from_db()


def test_check_for_draft_order_errors(order_with_lines):
    errors = check_for_draft_order_errors(order_with_lines)
    assert not errors

    order_with_no_lines = Mock(spec=Order)
    order_with_no_lines.get_total_quantity = MagicMock(return_value=0)
    errors = check_for_draft_order_errors(order_with_no_lines)
    assert errors[0].message == 'Could not create order without any products.'

    order_with_wrong_shipping = Mock(spec=Order)
    order_with_wrong_shipping.shipping_method = False
    errors = check_for_draft_order_errors(order_with_wrong_shipping)
    msg = 'Shipping method is not valid for chosen shipping address'
    assert errors[0].message == msg


def test_draft_order_complete(admin_api_client, draft_order):
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
    order_id = graphene.Node.to_global_id('Order', order.id)
    variables = json.dumps({'id': order_id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    data = content['data']['draftOrderComplete']['order']
    order.refresh_from_db()
    assert data['status'] == order.status.upper()


def test_order_update(admin_api_client, order_with_lines):
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
    variables = json.dumps(
        {'id': order_id, 'email': email, 'first_name': first_name,
         'last_name': last_name, 'country_code': 'PL'})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    data = content['data']['orderUpdate']['order']
    assert data['userEmail'] == email

    order.refresh_from_db()
    assert order.shipping_address.first_name == first_name
    assert order.billing_address.last_name == last_name


def test_order_add_note(admin_api_client, order_with_lines, admin_user):
    order = order_with_lines
    query = """
        mutation addNote(
        $id: ID!, $note: String, $user: ID, $is_public: Boolean) {
            orderAddNote(
            input: {order: $id, content: $note, user: $user,
            isPublic: $is_public}) {
                orderNote {
                    content
                    isPublic
                    user {
                        email
                    }
                }
            }
        }
        """
    assert not order.notes.all()
    order_id = graphene.Node.to_global_id('Order', order.id)
    note = 'nuclear note'
    user = graphene.Node.to_global_id('User', admin_user.id)
    is_public = True
    variables = json.dumps(
        {'id': order_id, 'user': user, 'is_public': is_public,
         'note': note})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    data = content['data']['orderAddNote']['orderNote']
    assert data['content'] == note
    assert data['isPublic'] == is_public
    assert data['user']['email'] == admin_user.email


def test_order_cancel(admin_api_client, order_with_lines):
    order = order_with_lines
    query = """
        mutation cancelOrder($id: ID!, $restock: Boolean!) {
            orderCancel(id: $id, restock: $restock) {
                order {
                    status
                }
            }
        }
    """
    order_id = graphene.Node.to_global_id('Order', order.id)
    restock = True
    quantity = order.get_total_quantity()
    variables = json.dumps({'id': order_id, 'restock': restock})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    data = content['data']['orderCancel']['order']
    order.refresh_from_db()
    history_entry = 'Restocked %d items' % quantity
    assert order.history.last().content == history_entry
    assert data['status'] == order.status.upper()


def test_order_capture(admin_api_client, payment_preauth):
    order = payment_preauth.order
    query = """
        mutation captureOrder($id: ID!, $amount: Decimal!) {
            orderCapture(id: $id, amount: $amount) {
                order {
                    paymentStatus
                    isPaid
                    capturedAmount {
                        amount
                    }
                }
            }
        }
    """
    order_id = graphene.Node.to_global_id('Order', order.id)
    amount = str(payment_preauth.get_total_price().gross.amount)
    variables = json.dumps({'id': order_id, 'amount': amount})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    data = content['data']['orderCapture']['order']
    order.refresh_from_db()
    assert data['paymentStatus'] == order.get_last_payment_status()
    assert data['isPaid'] == True
    assert data['capturedAmount']['amount'] == float(amount)


def test_paid_order_mark_as_paid(
        admin_api_client, payment_preauth):
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
    variables = json.dumps({'id': order_id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    errors = content['data']['orderMarkAsPaid']['errors']
    msg = 'Orders with payments can not be manually marked as paid.'
    assert errors[0]['message'] == msg
    assert errors[0]['field'] == 'payment'


def test_order_mark_as_paid(
        admin_api_client, order_with_lines):
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
    variables = json.dumps({'id': order_id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    data = content['data']['orderMarkAsPaid']['order']
    order.refresh_from_db()
    assert data['isPaid'] == True == order.is_fully_paid()


def test_order_release(admin_api_client, payment_preauth):
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
    variables = json.dumps({'id': order_id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    data = content['data']['orderRelease']['order']
    assert data['paymentStatus'] == PaymentStatus.REFUNDED
    history_entry = order.history.last().content
    assert history_entry == 'Released payment'


def test_order_refund(admin_api_client, payment_confirmed):
    order = order = payment_confirmed.order
    query = """
        mutation refundOrder($id: ID!, $amount: Decimal!) {
            orderRefund(id: $id, amount: $amount) {
                order {
                    paymentStatus
                    isPaid
                }
            }
        }
    """
    order_id = graphene.Node.to_global_id('Order', order.id)
    amount = str(payment_confirmed.get_total_price().gross.amount)
    variables = json.dumps({'id': order_id, 'amount': amount})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    data = content['data']['orderRefund']['order']
    order.refresh_from_db()
    msg = 'Refunded %(amount)s' % {'amount': amount}
    history_entry = order.history.last().content
    assert history_entry == msg
    assert data['paymentStatus'] == PaymentStatus.REFUNDED
    assert data['isPaid'] == False


def test_clean_order_release_payment():
    payment = MagicMock(spec=Payment)
    payment.status = 'not preauth'
    errors = clean_release_payment(payment)
    assert errors[0].field == 'payment'
    assert errors[0].message == 'Only pre-authorized payments can be released'

    payment.status = PaymentStatus.PREAUTH
    error_msg = 'error has happened.'
    payment.release = Mock(side_effect=ValueError(error_msg))
    errors = clean_release_payment(payment)
    assert errors[0].field == 'payment'
    assert errors[0].message == error_msg


def test_clean_order_refund_payment():
    payment = MagicMock(spec=Payment)
    payment.variant = CustomPaymentChoices.MANUAL
    amount = Mock(spec='string')
    errors = clean_refund_payment(payment, amount)
    assert errors[0].field == 'payment'
    assert errors[0].message == 'Manual payments can not be refunded.'

    payment.variant = None
    error_msg = 'error has happened.'
    payment.refund = Mock(side_effect=ValueError(error_msg))
    errors = clean_refund_payment(payment, amount)
    assert errors[0].field == 'payment'
    assert errors[0].message == error_msg
