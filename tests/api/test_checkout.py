import json

import graphene
from django.shortcuts import reverse
from tests.utils import get_graphql_content
from saleor.checkout.models import Cart


def test_checkout_create(user_api_client, variant):
    """
    Create checkout object using GraphQL API
    """
    query = """
    mutation createCheckout($checkoutInput: CheckoutCreateInput!) {
        checkoutCreate(input: $checkoutInput) {
            checkout {
                token,
                id
            }
        }
    }
    """
    variant_id = graphene.Node.to_global_id('ProductVariant', variant.id)
    test_email = 'test@example.com'
    shipping_address = {
        'firstName': "John",
        'lastName': 'Doe',
        'streetAddress1': 'Wall st.',
        'streetAddress2': '',
        'postalCode': '902010',
        'country': 'US',
        'city': 'New York'
    }

    variables = json.dumps({
        'checkoutInput': {
            'lines': [
                {'quantity': 1, 'variantId': variant_id}
            ],
            'email': test_email,
            'shippingAddress': shipping_address
        }
    })
    assert not Cart.objects.exists()
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    new_cart = Cart.objects.first()
    assert new_cart is not None
    checkout_data = content['data']['checkoutCreate']['checkout']
    assert 'id' in checkout_data
    assert 'token' in checkout_data
    assert checkout_data['token'] == str(new_cart.token)
    assert new_cart.lines.count() == 1
    cart_line = new_cart.lines.first()
    assert cart_line.variant == variant
    assert cart_line.quantity == 1
    assert new_cart.shipping_address is not None
    assert new_cart.shipping_address.first_name == shipping_address['firstName']
    assert new_cart.shipping_address.last_name == shipping_address['lastName']
    assert new_cart.shipping_address.street_address_1 == shipping_address['streetAddress1']
    assert new_cart.shipping_address.street_address_2 == shipping_address['streetAddress2']
    assert new_cart.shipping_address.postal_code == shipping_address['postalCode']
    assert new_cart.shipping_address.country == shipping_address['country']
    assert new_cart.shipping_address.city == shipping_address['city']


def test_checkout_lines_add(user_api_client, cart_with_item, variant):
    """
    Create checkout object using GraphQL API
    """
    cart = cart_with_item
    line = cart.lines.first()
    assert line.quantity == 3
    query = """
        mutation checkoutLinesAdd($checkoutId: ID!, $lines: [CheckoutLineInput!]!) {
            checkoutLinesAdd(checkoutId: $checkoutId, lines: $lines) {
                checkout {
                    token
                    lines {
                        edges {
                            node {
                                quantity
                                variant {
                                    id
                                }
                            }
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
    variant_id = graphene.Node.to_global_id('ProductVariant', variant.pk)
    checkout_id = graphene.Node.to_global_id('Checkout', cart.pk)

    variables = json.dumps({
        'checkoutId': checkout_id,
        'lines': [{
            'variantId': variant_id,
            'quantity': 1
        }]
    })
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['checkoutLinesAdd']
    assert not data['errors']
    cart.refresh_from_db()
    line = cart.lines.latest('pk')
    assert line.variant == variant
    assert line.quantity == 1
