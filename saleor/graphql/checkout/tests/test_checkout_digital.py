"""Test the API's checkout process over full digital orders."""

from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....plugins.manager import get_plugins_manager
from ...core.utils import to_global_id_or_none
from ...tests.utils import get_graphql_content
from ..mutations.utils import update_checkout_shipping_method_if_invalid


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


def test_remove_shipping_method_if_only_digital_in_checkout(
    checkout_with_digital_item, address, shipping_method
):
    checkout = checkout_with_digital_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.save()

    assert checkout.shipping_method
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    update_checkout_shipping_method_if_invalid(checkout_info, lines)

    checkout.refresh_from_db()
    assert not checkout.shipping_method
