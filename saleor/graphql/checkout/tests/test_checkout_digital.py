"""Test the API's checkout process over full digital orders."""
import graphene
import pytest

from ....account.models import Address
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.models import Checkout
from ....checkout.utils import add_variant_to_checkout
from ....plugins.manager import get_plugins_manager
from ...core.utils import to_global_id_or_none
from ...tests.utils import get_graphql_content
from ..mutations.utils import update_checkout_shipping_method_if_invalid
from .test_checkout import (
    MUTATION_CHECKOUT_CREATE,
    MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE,
    MUTATION_UPDATE_SHIPPING_METHOD,
)
from .test_checkout_lines import (
    MUTATION_CHECKOUT_LINE_DELETE,
    MUTATION_CHECKOUT_LINES_UPDATE,
)


@pytest.mark.parametrize("with_shipping_address", (True, False))
def test_create_checkout(
    api_client,
    digital_content,
    graphql_address_data,
    with_shipping_address,
    channel_USD,
):
    """Test creating a checkout with a shipping address gets the address ignored."""

    address_count = Address.objects.count()

    variant = digital_content.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    checkout_input = {
        "channel": channel_USD.slug,
        "lines": [{"quantity": 1, "variantId": variant_id}],
        "email": "customer@example.com",
    }

    if with_shipping_address:
        checkout_input["shippingAddress"] = graphql_address_data

    get_graphql_content(
        api_client.post_graphql(
            MUTATION_CHECKOUT_CREATE, {"checkoutInput": checkout_input}
        )
    )["data"]["checkoutCreate"]

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
        query getCheckout($id: ID!) {
            checkout(id: $id) {
                availableShippingMethods {
                    name
                    price {
                        amount
                    }
                }
            }
        }
    """

    checkout = checkout_with_digital_item

    # Put a shipping address, to ensure it is still handled properly
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])

    variables = {"id": to_global_id_or_none(checkout)}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    assert len(data["availableShippingMethods"]) == 0


def test_checkout_update_shipping_address(
    api_client, checkout_with_digital_item, graphql_address_data
):
    """Test updating the shipping address of a digital order throws an error."""

    checkout = checkout_with_digital_item
    variables = {
        "id": to_global_id_or_none(checkout),
        "shippingAddress": graphql_address_data,
    }

    response = api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]

    assert data["errors"] == [
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
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.pk)
    variables = {"id": to_global_id_or_none(checkout), "shippingMethodId": method_id}

    # Put a shipping address, to ensure it is still handled properly
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])

    response = api_client.post_graphql(MUTATION_UPDATE_SHIPPING_METHOD, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingMethodUpdate"]

    assert data["errors"] == [
        {
            "field": "shippingMethod",
            "message": "This checkout doesn't need shipping",
            "code": CheckoutErrorCode.SHIPPING_NOT_REQUIRED.name,
        }
    ]

    # Ensure the shipping method was unchanged
    checkout.refresh_from_db(fields=["shipping_method"])
    assert checkout.shipping_method is None


def test_remove_shipping_method_if_only_digital_in_checkout(
    checkout_with_digital_item, address, shipping_method
):
    checkout = checkout_with_digital_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.save()

    assert checkout.shipping_method
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    update_checkout_shipping_method_if_invalid(checkout_info, lines)

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
    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, digital_variant, 1)
    line = checkout.lines.first()
    variant = line.variant

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "id": to_global_id_or_none(checkout),
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
    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, digital_variant, 1)
    line = checkout.lines.first()

    line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)

    variables = {"id": to_global_id_or_none(checkout), "lineId": line_id}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINE_DELETE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLineDelete"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.lines.count() == 1
    assert not checkout.shipping_method
