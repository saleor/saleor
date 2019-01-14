import uuid
from unittest.mock import ANY, patch

import graphene
import pytest

from saleor.checkout.models import Cart
from saleor.order.models import Order
from tests.api.utils import get_graphql_content


MUTATION_CHECKOUT_CREATE = """
    mutation createCheckout($checkoutInput: CheckoutCreateInput!) {
        checkoutCreate(input: $checkoutInput) {
            checkout {
                token,
                id
            }
            errors {
                field
                message
            }
        }
    }
    """


def test_checkout_create(api_client, variant, graphql_address_data):
    """Create checkout object using GraphQL API."""
    variant_id = graphene.Node.to_global_id('ProductVariant', variant.id)
    test_email = 'test@example.com'
    shipping_address = graphql_address_data
    variables = {
        'checkoutInput': {
            'lines': [{
                'quantity': 1,
                'variantId': variant_id}],
            'email': test_email,
            'shippingAddress': shipping_address}}
    assert not Cart.objects.exists()
    response = api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)

    new_cart = Cart.objects.first()
    assert new_cart is not None
    checkout_data = content['data']['checkoutCreate']['checkout']
    assert checkout_data['token'] == str(new_cart.token)
    assert new_cart.lines.count() == 1
    cart_line = new_cart.lines.first()
    assert cart_line.variant == variant
    assert cart_line.quantity == 1
    assert new_cart.shipping_address is not None
    assert new_cart.shipping_address.first_name == shipping_address[
        'firstName']
    assert new_cart.shipping_address.last_name == shipping_address['lastName']
    assert new_cart.shipping_address.street_address_1 == shipping_address[
        'streetAddress1']
    assert new_cart.shipping_address.street_address_2 == shipping_address[
        'streetAddress2']
    assert new_cart.shipping_address.postal_code == shipping_address[
        'postalCode']
    assert new_cart.shipping_address.country == shipping_address['country']
    assert new_cart.shipping_address.city == shipping_address['city']


def test_checkout_create_logged_in_customer(
        user_api_client, variant):
    variant_id = graphene.Node.to_global_id('ProductVariant', variant.id)
    variables = {
        'checkoutInput': {
            'lines': [{
                'quantity': 1,
                'variantId': variant_id}]}}
    assert not Cart.objects.exists()
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    new_cart = Cart.objects.first()
    assert new_cart is not None
    checkout_data = content['data']['checkoutCreate']['checkout']
    assert checkout_data['token'] == str(new_cart.token)
    cart_user = new_cart.user
    customer = user_api_client.user
    assert customer.id == cart_user.id
    assert customer.default_shipping_address_id == new_cart.shipping_address_id
    assert customer.default_billing_address_id == new_cart.billing_address_id


def test_checkout_create_logged_in_customer_custom_email(
        user_api_client, variant):
    variant_id = graphene.Node.to_global_id('ProductVariant', variant.id)
    customer = user_api_client.user
    custom_email = 'custom@example.com'
    variables = {
        'checkoutInput': {
            'lines': [{
                'quantity': 1,
                'variantId': variant_id}],
            'email': custom_email}}
    assert not Cart.objects.exists()
    assert not custom_email == customer.email
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    new_cart = Cart.objects.first()
    assert new_cart is not None
    checkout_data = content['data']['checkoutCreate']['checkout']
    assert checkout_data['token'] == str(new_cart.token)
    cart_user = new_cart.user
    assert customer.id == cart_user.id
    assert new_cart.email == custom_email


def test_checkout_create_logged_in_customer_custom_addresses(
        user_api_client, variant, graphql_address_data):
    variant_id = graphene.Node.to_global_id('ProductVariant', variant.id)
    shipping_address = graphql_address_data
    billing_address = graphql_address_data
    variables = {
        'checkoutInput': {
            'lines': [{
                'quantity': 1,
                'variantId': variant_id}],
            'shippingAddress': shipping_address,
            'billingAddress': billing_address}}
    assert not Cart.objects.exists()
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    new_cart = Cart.objects.first()
    assert new_cart is not None
    checkout_data = content['data']['checkoutCreate']['checkout']
    assert checkout_data['token'] == str(new_cart.token)
    cart_user = new_cart.user
    customer = user_api_client.user
    assert customer.id == cart_user.id
    assert not customer.default_shipping_address_id == new_cart.shipping_address_id
    assert not customer.default_billing_address_id == new_cart.billing_address_id
    assert new_cart.shipping_address.first_name == shipping_address['firstName']
    assert new_cart.billing_address.first_name == billing_address['firstName']


def test_checkout_create_check_lines_quantity(
        user_api_client, variant, graphql_address_data):
    variant_id = graphene.Node.to_global_id('ProductVariant', variant.id)
    test_email = 'test@example.com'
    shipping_address = graphql_address_data
    variables = {
        'checkoutInput': {
            'lines': [{
                'quantity': 3,
                'variantId': variant_id}],
            'email': test_email,
            'shippingAddress': shipping_address}}
    assert not Cart.objects.exists()
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    data = content['data']['checkoutCreate']
    assert data['errors'][0]['message'] == 'Could not add item Test product (SKU_A). Only 2 remaining in stock.'
    assert data['errors'][0]['field'] == 'quantity'


MUTATION_CHECKOUT_LINES_ADD = """
    mutation checkoutLinesAdd($checkoutId: ID!, $lines: [CheckoutLineInput!]!) {
        checkoutLinesAdd(checkoutId: $checkoutId, lines: $lines) {
            checkout {
                token
                lines {
                    quantity
                    variant {
                        id
                    }
                }
            }
            errors {
                field
                message
            }
        }
    }"""


def test_checkout_lines_add(user_api_client, cart_with_item, variant):
    cart = cart_with_item
    line = cart.lines.first()
    assert line.quantity == 3
    variant_id = graphene.Node.to_global_id('ProductVariant', variant.pk)
    checkout_id = graphene.Node.to_global_id('Checkout', cart.pk)

    variables = {
        'checkoutId': checkout_id,
        'lines': [{'variantId': variant_id, 'quantity': 1}]}
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)
    data = content['data']['checkoutLinesAdd']
    assert not data['errors']
    cart.refresh_from_db()
    line = cart.lines.latest('pk')
    assert line.variant == variant
    assert line.quantity == 1


def test_checkout_lines_add_empty_checkout(
        user_api_client, cart, variant):
    variant_id = graphene.Node.to_global_id('ProductVariant', variant.pk)
    checkout_id = graphene.Node.to_global_id('Checkout', cart.pk)

    variables = {
        'checkoutId': checkout_id,
        'lines': [{'variantId': variant_id, 'quantity': 1}]}
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)
    data = content['data']['checkoutLinesAdd']
    assert not data['errors']
    cart.refresh_from_db()
    line = cart.lines.first()
    assert line.variant == variant
    assert line.quantity == 1


def test_checkout_lines_add_check_lines_quantity(
        user_api_client, cart, variant):
    variant_id = graphene.Node.to_global_id('ProductVariant', variant.pk)
    checkout_id = graphene.Node.to_global_id('Checkout', cart.pk)

    variables = {
        'checkoutId': checkout_id,
        'lines': [{'variantId': variant_id, 'quantity': 3}]}
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_ADD, variables)
    content = get_graphql_content(response)
    data = content['data']['checkoutLinesAdd']
    assert data['errors'][0]['message'] == 'Could not add item Test product (SKU_A). Only 2 remaining in stock.'
    assert data['errors'][0]['field'] == 'quantity'


MUTATION_CHECKOUT_LINES_UPDATE = """
    mutation checkoutLinesUpdate($checkoutId: ID!, $lines: [CheckoutLineInput!]!) {
        checkoutLinesUpdate(checkoutId: $checkoutId, lines: $lines) {
            checkout {
                token
                lines {
                    quantity
                    variant {
                        id
                    }
                }
            }
            errors {
                field
                message
            }
        }
    }
    """


def test_checkout_lines_update(user_api_client, cart_with_item):
    cart = cart_with_item
    assert cart.lines.count() == 1
    line = cart.lines.first()
    variant = line.variant
    assert line.quantity == 3

    variant_id = graphene.Node.to_global_id('ProductVariant', variant.pk)
    checkout_id = graphene.Node.to_global_id('Checkout', cart.pk)

    variables = {
        'checkoutId': checkout_id,
        'lines': [{
            'variantId': variant_id,
            'quantity': 1}]}
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content['data']['checkoutLinesUpdate']
    assert not data['errors']
    cart.refresh_from_db()
    assert cart.lines.count() == 1
    line = cart.lines.first()
    assert line.variant == variant
    assert line.quantity == 1


def test_checkout_lines_update_invalid_checkout_id(
        user_api_client):
    variables = {'checkoutId': 'test', 'lines': []}
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)
    data = content['data']['checkoutLinesUpdate']
    assert data['errors'][0]['field'] == 'checkoutId'


def test_checkout_lines_update_check_lines_quantity(
        user_api_client, cart_with_item):
    cart = cart_with_item
    line = cart.lines.first()
    variant = line.variant

    variant_id = graphene.Node.to_global_id('ProductVariant', variant.pk)
    checkout_id = graphene.Node.to_global_id('Checkout', cart.pk)

    variables = {
        'checkoutId': checkout_id,
        'lines': [{
            'variantId': variant_id,
            'quantity': 10}]}
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content['data']['checkoutLinesUpdate']
    assert data['errors'][0]['message'] == 'Could not add item Test product (123). Only 9 remaining in stock.'
    assert data['errors'][0]['field'] == 'quantity'


def test_checkout_line_delete(user_api_client, cart_with_item):
    cart = cart_with_item
    assert cart.lines.count() == 1
    line = cart.lines.first()
    assert line.quantity == 3
    query = """
        mutation checkoutLineDelete($checkoutId: ID!, $lineId: ID!) {
            checkoutLineDelete(checkoutId: $checkoutId, lineId: $lineId) {
                checkout {
                    token
                    lines {
                        quantity
                        variant {
                            id
                        }
                    }
                }
                errors {
                    field
                    message
                }
            }
        }
    """
    checkout_id = graphene.Node.to_global_id('Checkout', cart.pk)
    line_id = graphene.Node.to_global_id('CheckoutLine', line.pk)

    variables = {'checkoutId': checkout_id, 'lineId': line_id}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    data = content['data']['checkoutLineDelete']
    assert not data['errors']
    cart.refresh_from_db()
    assert cart.lines.count() == 0


def test_checkout_customer_attach(
        user_api_client, cart_with_item, customer_user):
    cart = cart_with_item
    assert cart.user is None

    query = """
        mutation checkoutCustomerAttach($checkoutId: ID!, $customerId: ID!) {
            checkoutCustomerAttach(checkoutId: $checkoutId, customerId: $customerId) {
                checkout {
                    token
                }
                errors {
                    field
                    message
                }
            }
        }
    """
    checkout_id = graphene.Node.to_global_id('Checkout', cart.pk)
    customer_id = graphene.Node.to_global_id('User', customer_user.pk)

    variables = {'checkoutId': checkout_id, 'customerId': customer_id}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    data = content['data']['checkoutCustomerAttach']
    assert not data['errors']
    cart.refresh_from_db()
    assert cart.user == customer_user


MUTATION_CHECKOUT_CUSTOMER_DETACH = """
    mutation checkoutCustomerDetach($checkoutId: ID!) {
        checkoutCustomerDetach(checkoutId: $checkoutId) {
            checkout {
                token
            }
            errors {
                field
                message
            }
        }
    }
    """


def test_checkout_customer_detach(
        user_api_client, cart_with_item, customer_user):
    cart = cart_with_item
    cart.user = customer_user
    cart.save(update_fields=['user'])

    checkout_id = graphene.Node.to_global_id('Checkout', cart.pk)
    variables = {
        'checkoutId': checkout_id, }
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CUSTOMER_DETACH, variables)
    content = get_graphql_content(response)

    data = content['data']['checkoutCustomerDetach']
    assert not data['errors']
    cart.refresh_from_db()
    assert cart.user is None


def test_checkout_customer_detach_without_customer(
        user_api_client, cart_with_item, customer_user):
    cart = cart_with_item

    checkout_id = graphene.Node.to_global_id('Checkout', cart.pk)
    variables = {
        'checkoutId': checkout_id, }
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CUSTOMER_DETACH, variables)
    content = get_graphql_content(response)
    data = content['data']['checkoutCustomerDetach']
    assert data['errors'][0]['message'] == 'There\'s no customer assigned to this Checkout.'


def test_checkout_shipping_address_update(
        user_api_client, cart_with_item, graphql_address_data):
    cart = cart_with_item
    assert cart.shipping_address is None
    checkout_id = graphene.Node.to_global_id('Checkout', cart.pk)

    query = """
    mutation checkoutShippingAddressUpdate($checkoutId: ID!, $shippingAddress: AddressInput!) {
        checkoutShippingAddressUpdate(checkoutId: $checkoutId, shippingAddress: $shippingAddress) {
            checkout {
                token,
                id
            },
            errors {
                field,
                message
            }
        }
    }
    """
    shipping_address = graphql_address_data
    variables = {
        'checkoutId': checkout_id, 'shippingAddress': shipping_address}

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['checkoutShippingAddressUpdate']
    assert not data['errors']
    cart.refresh_from_db()
    assert cart.shipping_address is not None
    assert cart.shipping_address.first_name == shipping_address['firstName']
    assert cart.shipping_address.last_name == shipping_address['lastName']
    assert cart.shipping_address.street_address_1 == shipping_address[
        'streetAddress1']
    assert cart.shipping_address.street_address_2 == shipping_address[
        'streetAddress2']
    assert cart.shipping_address.postal_code == shipping_address['postalCode']
    assert cart.shipping_address.country == shipping_address['country']
    assert cart.shipping_address.city == shipping_address['city']


def test_checkout_billing_address_update(
        user_api_client, cart_with_item, graphql_address_data):
    cart = cart_with_item
    assert cart.shipping_address is None
    checkout_id = graphene.Node.to_global_id('Checkout', cart.pk)

    query = """
    mutation checkoutBillingAddressUpdate($checkoutId: ID!, $billingAddress: AddressInput!) {
        checkoutBillingAddressUpdate(checkoutId: $checkoutId, billingAddress: $billingAddress) {
            checkout {
                token,
                id
            },
            errors {
                field,
                message
            }
        }
    }
    """
    billing_address = graphql_address_data

    variables = {'checkoutId': checkout_id, 'billingAddress': billing_address}

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['checkoutBillingAddressUpdate']
    assert not data['errors']
    cart.refresh_from_db()
    assert cart.billing_address is not None
    assert cart.billing_address.first_name == billing_address['firstName']
    assert cart.billing_address.last_name == billing_address['lastName']
    assert cart.billing_address.street_address_1 == billing_address[
        'streetAddress1']
    assert cart.billing_address.street_address_2 == billing_address[
        'streetAddress2']
    assert cart.billing_address.postal_code == billing_address['postalCode']
    assert cart.billing_address.country == billing_address['country']
    assert cart.billing_address.city == billing_address['city']

def test_checkout_email_update(user_api_client, cart_with_item):
    cart = cart_with_item
    assert not cart.email
    checkout_id = graphene.Node.to_global_id('Checkout', cart.pk)

    query = """
    mutation checkoutEmailUpdate($checkoutId: ID!, $email: String!) {
        checkoutEmailUpdate(checkoutId: $checkoutId, email: $email) {
            checkout {
                id,
                email
            },
            errors {
                field,
                message
            }
        }
    }
    """
    email = 'test@example.com'
    variables = {'checkoutId': checkout_id, 'email': email}

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['checkoutEmailUpdate']
    assert not data['errors']
    cart.refresh_from_db()
    assert cart.email == email


@pytest.mark.integration
def test_checkout_complete(
        user_api_client, cart_with_item, payment_dummy, address,
        shipping_method):
    checkout = cart_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.save()
    total = checkout.get_total()
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    checkout_id = graphene.Node.to_global_id('Checkout', checkout.pk)
    assert not payment.transactions.exists()
    query = """
    mutation checkoutComplete($checkoutId: ID!) {
        checkoutComplete(checkoutId: $checkoutId) {
            order {
                id,
                token
            },
            errors {
                field,
                message
            }
        }
    }
    """
    variables = {'checkoutId': checkout_id}
    orders_count = Order.objects.count()
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['checkoutComplete']
    assert not data['errors']
    order_token = data['order']['token']
    assert Order.objects.count() == orders_count + 1
    order = Order.objects.first()
    assert order.token == order_token
    assert order.total.gross == total.gross
    checkout_line = checkout.lines.first()
    order_line = order.lines.first()
    assert checkout_line.quantity == order_line.quantity
    assert checkout_line.variant == order_line.variant
    assert order.shipping_address == address
    assert order.shipping_method == checkout.shipping_method
    assert order.payments.exists()
    order_payment = order.payments.first()
    assert order_payment == payment
    assert payment.transactions.count() == 2


def test_fetch_checkout_by_token(user_api_client, cart_with_item):
    query = """
    query getCheckout($token: UUID!) {
        checkout(token: $token) {
           token,
           lines {
                variant {
                    product {
                        name
                    }
                }
           }
        }
    }
    """
    variables = {'token': str(cart_with_item.token)}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['checkout']
    assert data['token'] == str(cart_with_item.token)
    assert len(data['lines']) == cart_with_item.lines.count()


def test_fetch_checkout_invalid_token(user_api_client):
    query = """
        query getCheckout($token: UUID!) {
            checkout(token: $token) {
                token
            }
        }
    """
    variables = {'token': str(uuid.uuid4())}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['checkout']
    assert data is None


def test_checkout_prices(user_api_client, cart_with_item):
    query = """
    query getCheckout($token: UUID!) {
        checkout(token: $token) {
           token,
           totalPrice {
                currency
                gross {
                    amount
                }
            }
            subtotalPrice {
                currency
                gross {
                    amount
                }
            }
           lines {
                totalPrice {
                    currency
                    gross {
                        amount
                    }
                }
           }
        }
    }
    """
    variables = {'token': str(cart_with_item.token)}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['checkout']
    assert data['token'] == str(cart_with_item.token)
    assert len(data['lines']) == cart_with_item.lines.count()
    assert data['totalPrice']['gross']['amount'] == (
        cart_with_item.get_total().gross.amount)
    assert data['subtotalPrice']['gross']['amount'] == (
        cart_with_item.get_subtotal().gross.amount)


@patch('saleor.graphql.checkout.mutations.clean_shipping_method')
def test_checkout_shipping_method_update(
        mock_clean_shipping, staff_api_client, shipping_method,
        cart_with_item, sale, vatlayer):
    query = """
    mutation checkoutShippingMethodUpdate($checkoutId:ID!, $shippingMethodId:ID!){
        checkoutShippingMethodUpdate(
            checkoutId:$checkoutId, shippingMethodId:$shippingMethodId) {
            errors {
                field
                message
            }
            checkout {
                id
            }
        }
    }
    """
    checkout = cart_with_item
    checkout_id = graphene.Node.to_global_id('Checkout', checkout.pk)
    method_id = graphene.Node.to_global_id(
        'ShippingMethod', shipping_method.id)
    variables = {'checkoutId': checkout_id, 'shippingMethodId': method_id}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['checkoutShippingMethodUpdate']
    assert not data['errors']
    assert data['checkout']['id'] == checkout_id

    checkout.refresh_from_db()
    assert checkout.shipping_method == shipping_method
    mock_clean_shipping.assert_called_once_with(
        checkout, shipping_method, [], ANY, ANY, remove=False)


def test_query_checkout_line(cart_with_item, user_api_client):
    query = """
    query checkoutLine($id: ID) {
        checkoutLine(id: $id) {
            id
        }
    }
    """
    checkout = cart_with_item
    line = checkout.lines.first()
    line_id = graphene.Node.to_global_id('CheckoutLine', line.pk)
    variables = {'id': line_id}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    received_id = content['data']['checkoutLine']['id']
    assert received_id == line_id


def test_query_checkouts(
        cart_with_item, staff_api_client, permission_manage_orders):
    query = """
    {
        checkouts(first: 20) {
            edges {
                node {
                    token
                }
            }
        }
    }
    """
    checkout = cart_with_item
    response = staff_api_client.post_graphql(
        query, {}, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    received_checkout = content['data']['checkouts']['edges'][0]['node']
    assert str(checkout.token) == received_checkout['token']


def test_query_checkout_lines(
        cart_with_item, staff_api_client, permission_manage_orders):
    query = """
    {
        checkoutLines(first: 20) {
            edges {
                node {
                    id
                }
            }
        }
    }
    """
    checkout = cart_with_item
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    lines = content['data']['checkoutLines']['edges']
    checkout_lines_ids = [line['node']['id'] for line in lines]
    expected_lines_ids = [
        graphene.Node.to_global_id('CheckoutLine', item.pk)
        for item in checkout]
    assert expected_lines_ids == checkout_lines_ids
