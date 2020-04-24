"""Test the API's checkout process over full digital orders."""
import graphene
import pytest

from saleor.account.models import Address
from saleor.checkout import calculations
from saleor.checkout.error_codes import CheckoutErrorCode
from saleor.checkout.models import Checkout
from saleor.checkout.utils import add_variant_to_checkout
from saleor.graphql.checkout.mutations import update_checkout_shipping_method_if_invalid
from saleor.order.models import Order
from tests.api.utils import get_graphql_content

from .test_checkout import (
    MUTATION_CHECKOUT_COMPLETE,
    MUTATION_CHECKOUT_CREATE,
    MUTATION_CHECKOUT_LINES_DELETE,
    MUTATION_CHECKOUT_LINES_UPDATE,
    MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE,
    MUTATION_UPDATE_SHIPPING_METHOD,
)


@pytest.fixture
def checkout_with_digital_item(checkout, digital_content):
    """Create a checkout with a digital line."""
    variant = digital_content.product_variant
    add_variant_to_checkout(checkout, variant, 1)
    checkout.email = "customer@example.com"
    checkout.save()
    return checkout


@pytest.fixture(autouse=True)
def enable_dummy_gateway(settings):
    settings.PLUGINS = ["saleor.payment.gateways.dummy.plugin.DummyGatewayPlugin"]
    return settings


@pytest.mark.parametrize("with_shipping_address", (True, False))
def test_create_checkout(
    api_client, digital_content, graphql_address_data, with_shipping_address
):
    """Test creating a checkout with a shipping address gets the address ignored."""

    address_count = Address.objects.count()

    variant = digital_content.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    checkout_input = {
        "lines": [{"quantity": 1, "variantId": variant_id}],
        "email": "customer@example.com",
    }

    if with_shipping_address:
        checkout_input["shippingAddress"] = graphql_address_data

    content = get_graphql_content(
        api_client.post_graphql(
            MUTATION_CHECKOUT_CREATE, {"checkoutInput": checkout_input}
        )
    )["data"]["checkoutCreate"]

    # Ensure checkout was created
    assert content["created"] is True, "The checkout should have been created"

    # Retrieve the created checkout
    checkout = Checkout.objects.get()

    # Check that the shipping address was ignored, thus not created
    assert (
        checkout.shipping_address is None
    ), "The address shouldn't have been associated"
    assert (
        Address.objects.count() == address_count
    ), "No address should have been created"


def test_checkout_has_no_available_shipping_methods(
    api_client, checkout_with_digital_item, address, shipping_zone
):
    """Test no shipping method are available on digital orders."""

    query = """
        query getCheckout($token: UUID!) {
            checkout(token: $token) {
                availableShippingMethods {
                    name
                }
            }
        }
    """

    checkout = checkout_with_digital_item

    # Put a shipping address, to ensure it is still handled properly
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])

    response = api_client.post_graphql(query, {"token": checkout.token})
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    assert len(data["availableShippingMethods"]) == 0


def test_checkout_update_shipping_address(
    api_client, checkout_with_digital_item, graphql_address_data
):
    """Test updating the shipping address of a digital order throws an error."""

    checkout = checkout_with_digital_item
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "shippingAddress": graphql_address_data}

    response = api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]

    assert data["errors"] == [
        {"field": "shippingAddress", "message": "This checkout doesn't need shipping"}
    ]

    assert data["checkoutErrors"] == [
        {
            "field": "shippingAddress",
            "message": "This checkout doesn't need shipping",
            "code": CheckoutErrorCode.SHIPPING_NOT_REQUIRED.name,
        }
    ]

    # Ensure the address was unchanged
    checkout.refresh_from_db(fields=["shipping_address"])
    assert checkout.shipping_address is None


def test_checkout_update_shipping_method(
    api_client, checkout_with_digital_item, address, shipping_method
):
    """Test updating the shipping method of a digital order throws an error."""

    checkout = checkout_with_digital_item
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.pk)
    variables = {"checkoutId": checkout_id, "shippingMethodId": method_id}

    # Put a shipping address, to ensure it is still handled properly
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])

    response = api_client.post_graphql(MUTATION_UPDATE_SHIPPING_METHOD, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingMethodUpdate"]

    assert data["errors"] == [
        {"field": "shippingMethod", "message": "This checkout doesn't need shipping"}
    ]

    # Ensure the shipping method was unchanged
    checkout.refresh_from_db(fields=["shipping_method"])
    assert checkout.shipping_method is None


def test_checkout_complete(
    api_client, checkout_with_digital_item, address, payment_dummy
):
    """Ensure it is possible to complete a digital checkout without shipping."""

    order_count = Order.objects.count()
    checkout = checkout_with_digital_item
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {"checkoutId": checkout_id, "redirectUrl": "https://www.example.com"}

    # Set a billing address
    checkout.billing_address = address
    checkout.save(update_fields=["billing_address"])

    # Create a dummy payment to charge
    total = calculations.checkout_total(checkout=checkout, lines=list(checkout))
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    assert not payment.transactions.exists()

    # Send the creation request
    response = api_client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    content = get_graphql_content(response)["data"]["checkoutComplete"]
    assert not content["errors"]

    # Ensure the order was actually created
    assert (
        Order.objects.count() == order_count + 1
    ), "The order should have been created"


def test_remove_shipping_method_if_only_digital_in_checkout(
    checkout_with_digital_item, address, shipping_method
):
    checkout = checkout_with_digital_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.save()

    assert checkout.shipping_method
    update_checkout_shipping_method_if_invalid(checkout, list(checkout), None)

    checkout.refresh_from_db()
    assert not checkout.shipping_method


def test_checkout_lines_update_remove_shipping_if_removed_product_with_shipping(
    user_api_client, checkout_with_item, digital_content, address, shipping_method
):
    checkout = checkout_with_item
    digital_variant = digital_content.product_variant
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.save()
    add_variant_to_checkout(checkout, digital_variant, 1)
    line = checkout.lines.first()
    variant = line.variant

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    variables = {
        "checkoutId": checkout_id,
        "lines": [{"variantId": variant_id, "quantity": 0}],
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_UPDATE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.lines.count() == 1
    assert not checkout.shipping_method


def test_checkout_line_delete_remove_shipping_if_removed_product_with_shipping(
    user_api_client, checkout_with_item, digital_content, address, shipping_method
):
    checkout = checkout_with_item
    digital_variant = digital_content.product_variant
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.save()
    add_variant_to_checkout(checkout, digital_variant, 1)
    line = checkout.lines.first()

    line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    variables = {"checkoutId": checkout_id, "lineId": line_id}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_DELETE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLineDelete"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.lines.count() == 1
    assert not checkout.shipping_method
