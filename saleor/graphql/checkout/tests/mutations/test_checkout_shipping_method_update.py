from unittest import mock
from unittest.mock import patch

import graphene
import pytest

from .....account.models import Address
from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import (
    fetch_checkout_info,
    fetch_checkout_lines,
    get_delivery_method_info,
)
from .....checkout.utils import PRIVATE_META_APP_SHIPPING_ID, invalidate_checkout_prices
from .....plugins.base_plugin import ExcludedShippingMethod
from .....plugins.manager import get_plugins_manager
from .....shipping import models as shipping_models
from .....shipping.utils import convert_to_shipping_method_data
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

MUTATION_UPDATE_SHIPPING_METHOD = """
    mutation checkoutShippingMethodUpdate(
            $id: ID, $shippingMethodId: ID!){
        checkoutShippingMethodUpdate(
            id: $id, shippingMethodId: $shippingMethodId) {
            errors {
                field
                message
                code
            }
            checkout {
                token
            }
        }
    }
"""


# TODO: Deprecated
@pytest.mark.parametrize("is_valid_shipping_method", (True, False))
@patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_method_update."
    "clean_delivery_method"
)
@patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_method_update."
    "invalidate_checkout_prices",
    wraps=invalidate_checkout_prices,
)
def test_checkout_shipping_method_update(
    mocked_invalidate_checkout_prices,
    mock_clean_shipping,
    staff_api_client,
    shipping_method,
    checkout_with_item_and_shipping_method,
    is_valid_shipping_method,
):
    checkout = checkout_with_item_and_shipping_method
    old_shipping_method = checkout.shipping_method
    query = MUTATION_UPDATE_SHIPPING_METHOD
    mock_clean_shipping.return_value = is_valid_shipping_method
    previous_last_change = checkout.last_change

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "shippingMethodId": method_id}
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]
    checkout.refresh_from_db()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    checkout_info.delivery_method_info = get_delivery_method_info(
        convert_to_shipping_method_data(
            old_shipping_method, old_shipping_method.channel_listings.first()
        ),
        None,
    )
    mock_clean_shipping.assert_called_once_with(
        checkout_info=checkout_info,
        lines=lines,
        method=convert_to_shipping_method_data(
            shipping_method, shipping_method.channel_listings.first()
        ),
    )
    errors = data["errors"]
    if is_valid_shipping_method:
        assert not errors
        assert data["checkout"]["token"] == str(checkout.token)
        assert checkout.shipping_method == shipping_method
        assert checkout.last_change != previous_last_change
        assert mocked_invalidate_checkout_prices.call_count == 1
    else:
        assert len(errors) == 1
        assert errors[0]["field"] == "shippingMethod"
        assert (
            errors[0]["code"] == CheckoutErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
        )
        assert checkout.shipping_method == old_shipping_method
        assert checkout.last_change == previous_last_change


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_checkout_shipping_method_update_external_shipping_method(
    mock_send_request,
    staff_api_client,
    address,
    checkout_with_item,
    shipping_app,
    channel_USD,
    settings,
):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    response_method_id = "abcd"
    mock_json_response = [
        {
            "id": response_method_id,
            "name": "Provider - Economy",
            "amount": "10",
            "currency": "USD",
            "maximum_delivery_days": "7",
        }
    ]
    mock_send_request.return_value = mock_json_response

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])

    method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{response_method_id}"
    )

    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD,
        {"id": to_global_id_or_none(checkout_with_item), "shippingMethodId": method_id},
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]
    checkout.refresh_from_db()

    errors = data["errors"]
    assert not errors
    assert data["checkout"]["token"] == str(checkout_with_item.token)
    assert PRIVATE_META_APP_SHIPPING_ID in checkout.metadata_storage.private_metadata


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_checkout_shipping_method_update_external_shipping_method_with_tax_plugin(
    mock_send_request,
    staff_api_client,
    address,
    checkout_with_item,
    shipping_app,
    channel_USD,
    settings,
):
    settings.PLUGINS = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.webhook.plugin.WebhookPlugin",
    ]
    response_method_id = "abcd"
    mock_json_response = [
        {
            "id": response_method_id,
            "name": "Provider - Economy",
            "amount": "10",
            "currency": "USD",
            "maximum_delivery_days": "7",
        }
    ]
    mock_send_request.return_value = mock_json_response

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save()

    method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{response_method_id}"
    )

    # Set external shipping method for first time
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD,
        {"id": to_global_id_or_none(checkout_with_item), "shippingMethodId": method_id},
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]
    assert not data["errors"]

    # Set external shipping for second time
    # Without a fix this request results in infinite recursion
    # between Avalara and Webhooks plugins
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD,
        {"id": to_global_id_or_none(checkout_with_item), "shippingMethodId": method_id},
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]
    assert not data["errors"]


@mock.patch(
    "saleor.plugins.manager.PluginsManager.excluded_shipping_methods_for_checkout"
)
def test_checkout_shipping_method_update_excluded_webhook(
    mocked_webhook,
    staff_api_client,
    shipping_method,
    checkout_with_item,
    address,
):
    # given
    webhook_reason = "spanish-inquisition"
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_SHIPPING_METHOD
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    mocked_webhook.return_value = [
        ExcludedShippingMethod(shipping_method.id, webhook_reason)
    ]

    # when
    response = staff_api_client.post_graphql(
        query,
        {"id": to_global_id_or_none(checkout_with_item), "shippingMethodId": method_id},
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    # then
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "shippingMethod"
    assert errors[0]["code"] == CheckoutErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
    assert checkout.shipping_method is None


# Deprecated
@patch("saleor.shipping.postal_codes.is_shipping_method_applicable_for_postal_code")
def test_checkout_shipping_method_update_excluded_postal_code(
    mock_is_shipping_method_available,
    staff_api_client,
    shipping_method,
    checkout_with_item,
    address,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_SHIPPING_METHOD
    mock_is_shipping_method_available.return_value = False

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(
        query,
        {"id": to_global_id_or_none(checkout_with_item), "shippingMethodId": method_id},
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "shippingMethod"
    assert errors[0]["code"] == CheckoutErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
    assert checkout.shipping_method is None
    assert (
        mock_is_shipping_method_available.call_count
        == shipping_models.ShippingMethod.objects.count()
    )


def test_checkout_shipping_method_update_with_not_all_required_shipping_address_data(
    staff_api_client,
    shipping_method,
    checkout_with_item,
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = Address.objects.create(country="US")
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_SHIPPING_METHOD

    shipping_method.postal_code_rules.create(start="00123", end="12345")
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    # when
    response = staff_api_client.post_graphql(
        query,
        {"id": to_global_id_or_none(checkout_with_item), "shippingMethodId": method_id},
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    assert not data["errors"]
    assert checkout.shipping_method == shipping_method


def test_checkout_shipping_method_update_with_not_valid_shipping_address_data(
    staff_api_client,
    shipping_method,
    checkout_with_item,
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = Address.objects.create(
        country="US",
        city="New York",
        city_area="ABC",
        street_address_1="New street",
        postal_code="53-601",
    )  # incorrect postalCode
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_SHIPPING_METHOD

    shipping_method.postal_code_rules.create(start="00123", end="12345")
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    # when
    response = staff_api_client.post_graphql(
        query,
        {"id": to_global_id_or_none(checkout_with_item), "shippingMethodId": method_id},
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    assert not data["errors"]
    assert checkout.shipping_method == shipping_method


def test_checkout_delivery_method_update_unavailable_variant(
    staff_api_client,
    shipping_method,
    checkout_with_item,
    address,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    checkout_with_item.lines.first().variant.channel_listings.filter(
        channel=checkout_with_item.channel
    ).delete()
    query = MUTATION_UPDATE_SHIPPING_METHOD

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(
        query,
        {"id": to_global_id_or_none(checkout_with_item), "shippingMethodId": method_id},
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "lines"
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name


# Deprecated
def test_checkout_shipping_method_update_shipping_zone_without_channel(
    staff_api_client,
    shipping_method,
    checkout_with_item,
    address,
):
    shipping_method.shipping_zone.channels.clear()
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_SHIPPING_METHOD

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(
        query,
        {"id": to_global_id_or_none(checkout_with_item), "shippingMethodId": method_id},
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "shippingMethod"
    assert errors[0]["code"] == CheckoutErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
    assert checkout.shipping_method is None


# Deprecated
def test_checkout_shipping_method_update_shipping_zone_with_channel(
    staff_api_client,
    shipping_method,
    checkout_with_item,
    address,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_SHIPPING_METHOD

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(
        query,
        {"id": to_global_id_or_none(checkout_with_item), "shippingMethodId": method_id},
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    checkout.refresh_from_db()
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["token"] == str(checkout_with_item.token)

    assert checkout.shipping_method == shipping_method


def test_checkout_update_shipping_method_with_digital(
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
