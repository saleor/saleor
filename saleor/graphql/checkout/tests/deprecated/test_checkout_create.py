import graphene

from .....checkout.models import Checkout
from ....tests.utils import get_graphql_content


def test_checkout_create(api_client, stock, graphql_address_data, channel_USD):
    """Create checkout object using GraphQL API."""
    query = """
        mutation createCheckout($checkoutInput: CheckoutCreateInput!) {
        checkoutCreate(input: $checkoutInput) {
            created
            checkout {
            id
            token
            email
            quantity
            lines {
                quantity
            }
            }
            errors {
            field
            message
            code
            variants
            addressType
            }
        }
        }
    """
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)["data"]["checkoutCreate"]

    assert content["created"] is True
