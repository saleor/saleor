from unittest import mock
from unittest.mock import patch

import graphene
import pytest

from .....account.models import Address
from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.utils import PRIVATE_META_APP_SHIPPING_ID, invalidate_checkout_prices
from .....plugins.manager import get_plugins_manager
from .....shipping import models as shipping_models
from .....shipping.utils import convert_to_shipping_method_data
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

MUTATION_UPDATE_DELIVERY_METHOD = """
    mutation checkoutDeliveryMethodUpdate(
            $id: ID, $deliveryMethodId: ID) {
        checkoutDeliveryMethodUpdate(
            id: $id,
            deliveryMethodId: $deliveryMethodId) {
            checkout {
            id
            deliveryMethod {
                __typename
                ... on ShippingMethod {
                    name
                    id
                    translation(languageCode: EN_US) {
                        name
                    }
                }
                ... on Warehouse {
                   name
                   id
                }
            }
        }
        errors {
            field
            message
            code
        }
    }
}
"""


@pytest.mark.parametrize("is_valid_delivery_method", (True, False))
@pytest.mark.parametrize(
    "delivery_method, node_name, attribute_name",
    [
        ("warehouse", "Warehouse", "collection_point"),
        ("shipping_method", "ShippingMethod", "shipping_method"),
    ],
    indirect=("delivery_method",),
)
@patch(
    "saleor.graphql.checkout.mutations.checkout_delivery_method_update."
    "clean_delivery_method"
)
@patch(
    "saleor.graphql.checkout.mutations.checkout_delivery_method_update."
    "invalidate_checkout_prices",
    wraps=invalidate_checkout_prices,
)
def test_checkout_delivery_method_update(
    mock_invalidate_checkout_prices,
    mock_clean_delivery,
    api_client,
    delivery_method,
    node_name,
    attribute_name,
    checkout_with_item_for_cc,
    is_valid_delivery_method,
):
    # given
    mock_clean_delivery.return_value = is_valid_delivery_method

    checkout = checkout_with_item_for_cc
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    shipping_method_data = delivery_method
    if attribute_name == "shipping_method":
        shipping_method_data = convert_to_shipping_method_data(
            delivery_method,
            delivery_method.channel_listings.get(),
        )
    query = MUTATION_UPDATE_DELIVERY_METHOD
    mock_clean_delivery.return_value = is_valid_delivery_method

    method_id = graphene.Node.to_global_id(node_name, delivery_method.id)

    response = api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id}
    )
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    checkout.refresh_from_db()

    mock_clean_delivery.assert_called_once_with(
        checkout_info=checkout_info, lines=lines, method=shipping_method_data
    )
    errors = data["errors"]
    if is_valid_delivery_method:
        assert not errors
        assert getattr(checkout, attribute_name) == delivery_method
        assert mock_invalidate_checkout_prices.call_count == 1
    else:
        assert len(errors) == 1
        assert errors[0]["field"] == "deliveryMethodId"
        assert (
            errors[0]["code"] == CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.name
        )
        assert checkout.shipping_method is None
        assert checkout.collection_point is None


@pytest.mark.parametrize("is_valid_delivery_method", (True, False))
@pytest.mark.parametrize(
    "delivery_method, node_name, attribute_name",
    [
        ("warehouse", "Warehouse", "collection_point"),
        ("shipping_method", "ShippingMethod", "shipping_method"),
    ],
    indirect=("delivery_method",),
)
@patch(
    "saleor.graphql.checkout.mutations.checkout_delivery_method_update."
    "clean_delivery_method"
)
@patch(
    "saleor.graphql.checkout.mutations.checkout_delivery_method_update."
    "invalidate_checkout_prices",
    wraps=invalidate_checkout_prices,
)
def test_checkout_delivery_method_update_no_checkout_metadata(
    mock_invalidate_checkout_prices,
    mock_clean_delivery,
    api_client,
    delivery_method,
    node_name,
    attribute_name,
    checkout_with_item_for_cc,
    is_valid_delivery_method,
):
    # given
    mock_clean_delivery.return_value = is_valid_delivery_method

    checkout = checkout_with_item_for_cc
    checkout.metadata_storage.delete()
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    shipping_method_data = delivery_method
    if attribute_name == "shipping_method":
        shipping_method_data = convert_to_shipping_method_data(
            delivery_method,
            delivery_method.channel_listings.get(),
        )
    query = MUTATION_UPDATE_DELIVERY_METHOD
    mock_clean_delivery.return_value = is_valid_delivery_method

    method_id = graphene.Node.to_global_id(node_name, delivery_method.id)

    # when
    response = api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id}
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    checkout.refresh_from_db()

    mock_clean_delivery.assert_called_once_with(
        checkout_info=checkout_info, lines=lines, method=shipping_method_data
    )
    errors = data["errors"]
    if is_valid_delivery_method:
        assert not errors
        assert getattr(checkout, attribute_name) == delivery_method
        assert mock_invalidate_checkout_prices.call_count == 1
    else:
        assert len(errors) == 1
        assert errors[0]["field"] == "deliveryMethodId"
        assert (
            errors[0]["code"] == CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.name
        )
        assert checkout.shipping_method is None
        assert checkout.collection_point is None


@pytest.mark.parametrize("is_valid_delivery_method", (True, False))
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.graphql.checkout.mutations.checkout_delivery_method_update."
    "clean_delivery_method"
)
def test_checkout_delivery_method_update_external_shipping(
    mock_clean_delivery,
    mock_send_request,
    api_client,
    checkout_with_item_for_cc,
    is_valid_delivery_method,
    settings,
    shipping_app,
    channel_USD,
):
    checkout = checkout_with_item_for_cc
    query = MUTATION_UPDATE_DELIVERY_METHOD
    mock_clean_delivery.return_value = is_valid_delivery_method

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

    method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{response_method_id}"
    )

    response = api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id}
    )
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    checkout.refresh_from_db()

    errors = data["errors"]
    if is_valid_delivery_method:
        assert not errors
        assert (
            PRIVATE_META_APP_SHIPPING_ID in checkout.metadata_storage.private_metadata
        )
        assert data["checkout"]["deliveryMethod"]["id"] == method_id
    else:
        assert len(errors) == 1
        assert errors[0]["field"] == "deliveryMethodId"
        assert (
            errors[0]["code"] == CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.name
        )
        assert (
            PRIVATE_META_APP_SHIPPING_ID
            not in checkout.metadata_storage.private_metadata
        )


@patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_method_update."
    "clean_delivery_method"
)
def test_checkout_delivery_method_update_with_id_of_different_type_causes_and_error(
    mock_clean_delivery,
    api_client,
    checkout_with_item,
    address,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_DELIVERY_METHOD
    mock_clean_delivery.return_value = True
    invalid_method_id = graphene.Node.to_global_id("Address", address.id)

    response = api_client.post_graphql(
        query,
        {
            "id": to_global_id_or_none(checkout),
            "deliveryMethodId": invalid_method_id,
        },
    )
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    checkout.refresh_from_db()

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "deliveryMethodId"
    assert errors[0]["code"] == CheckoutErrorCode.INVALID.name
    assert checkout.shipping_method is None
    assert checkout.collection_point is None


@patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_method_update."
    "clean_delivery_method"
)
def test_checkout_delivery_method_with_nonexistant_id_results_not_found(
    mock_clean_delivery,
    api_client,
    warehouse_for_cc,
    checkout_with_item,
    address,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_DELIVERY_METHOD
    mock_clean_delivery.return_value = True

    nonexistant_id = "YXBwOjEyMzQ6c29tZS1pZA=="
    response = api_client.post_graphql(
        query,
        {
            "id": to_global_id_or_none(checkout),
            "deliveryMethodId": nonexistant_id,
        },
    )
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    checkout.refresh_from_db()

    assert not data["checkout"]
    assert data["errors"][0]["field"] == "deliveryMethodId"
    assert data["errors"][0]["code"] == CheckoutErrorCode.NOT_FOUND.name
    assert checkout.shipping_method is None
    assert checkout.collection_point is None


@patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_method_update."
    "clean_delivery_method"
)
def test_checkout_delivery_method_with_empty_fields_results_None(
    mock_clean_delivery,
    api_client,
    warehouse_for_cc,
    checkout_with_item,
    address,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_DELIVERY_METHOD
    mock_clean_delivery.return_value = True

    response = api_client.post_graphql(
        query,
        {
            "id": to_global_id_or_none(checkout),
        },
    )
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    checkout.refresh_from_db()

    assert not data["errors"]
    assert data["checkout"]["deliveryMethod"] is None
    assert checkout.shipping_method is None
    assert checkout.collection_point is None


@patch("saleor.shipping.postal_codes.is_shipping_method_applicable_for_postal_code")
def test_checkout_delivery_method_update_excluded_postal_code(
    mock_is_shipping_method_available,
    staff_api_client,
    shipping_method,
    checkout_with_item,
    address,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_DELIVERY_METHOD
    mock_is_shipping_method_available.return_value = False

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id}
    )
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]

    checkout.refresh_from_db()

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "deliveryMethodId"
    assert errors[0]["code"] == CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.name
    assert checkout.shipping_method is None
    assert (
        mock_is_shipping_method_available.call_count
        == shipping_models.ShippingMethod.objects.count()
    )


def test_checkout_delivery_method_update_shipping_zone_without_channel(
    api_client,
    shipping_method,
    checkout_with_item,
    address,
):
    shipping_method.shipping_zone.channels.clear()
    shipping_method.channel_listings.all().delete()
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_DELIVERY_METHOD

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id}
    )
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]

    checkout.refresh_from_db()

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "deliveryMethodId"
    assert errors[0]["code"] == CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.name
    assert checkout.shipping_method is None


def test_checkout_delivery_method_update_shipping_zone_with_channel(
    staff_api_client,
    shipping_method,
    checkout_with_item,
    address,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_DELIVERY_METHOD

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id}
    )
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]

    checkout.refresh_from_db()

    checkout.refresh_from_db()
    errors = data["errors"]
    assert not errors

    assert checkout.shipping_method == shipping_method


@pytest.mark.parametrize("is_valid_delivery_method", (True, False))
@pytest.mark.parametrize(
    "delivery_method, node_name, attribute_name",
    [
        ("warehouse", "Warehouse", "collection_point"),
        ("shipping_method", "ShippingMethod", "shipping_method"),
    ],
    indirect=("delivery_method",),
)
@patch(
    "saleor.graphql.checkout.mutations.checkout_delivery_method_update."
    "clean_delivery_method"
)
def test_checkout_delivery_method_update_with_not_all_required_shipping_address_data(
    mock_clean_delivery,
    api_client,
    delivery_method,
    node_name,
    attribute_name,
    checkout_with_item_for_cc,
    is_valid_delivery_method,
):
    # given
    mock_clean_delivery.return_value = is_valid_delivery_method

    checkout = checkout_with_item_for_cc
    checkout.shipping_address = Address.objects.create(country="US")
    checkout.save()
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    shipping_method_data = delivery_method
    if attribute_name == "shipping_method":
        shipping_method_data = convert_to_shipping_method_data(
            delivery_method,
            delivery_method.channel_listings.get(),
        )
    query = MUTATION_UPDATE_DELIVERY_METHOD
    mock_clean_delivery.return_value = is_valid_delivery_method

    method_id = graphene.Node.to_global_id(node_name, delivery_method.id)

    # when
    response = api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id}
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    checkout.refresh_from_db()

    mock_clean_delivery.assert_called_once_with(
        checkout_info=checkout_info, lines=lines, method=shipping_method_data
    )
    errors = data["errors"]
    if is_valid_delivery_method:
        assert not errors
        assert getattr(checkout, attribute_name) == delivery_method
    else:
        assert len(errors) == 1
        assert errors[0]["field"] == "deliveryMethodId"
        assert (
            errors[0]["code"] == CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.name
        )
        assert checkout.shipping_method is None
        assert checkout.collection_point is None


@pytest.mark.parametrize("is_valid_delivery_method", (True, False))
@pytest.mark.parametrize(
    "delivery_method, node_name, attribute_name",
    [
        ("warehouse", "Warehouse", "collection_point"),
        ("shipping_method", "ShippingMethod", "shipping_method"),
    ],
    indirect=("delivery_method",),
)
@patch(
    "saleor.graphql.checkout.mutations.checkout_delivery_method_update."
    "clean_delivery_method"
)
def test_checkout_delivery_method_update_with_not_valid_address_data(
    mock_clean_delivery,
    api_client,
    delivery_method,
    node_name,
    attribute_name,
    checkout_with_item_for_cc,
    is_valid_delivery_method,
):
    # given
    mock_clean_delivery.return_value = is_valid_delivery_method

    checkout = checkout_with_item_for_cc
    checkout.shipping_address = Address.objects.create(
        country="US",
        city="New York",
        city_area="ABC",
        street_address_1="New street",
        postal_code="53-601",
    )
    checkout.save()
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    shipping_method_data = delivery_method
    if attribute_name == "shipping_method":
        shipping_method_data = convert_to_shipping_method_data(
            delivery_method,
            delivery_method.channel_listings.get(),
        )
    query = MUTATION_UPDATE_DELIVERY_METHOD
    mock_clean_delivery.return_value = is_valid_delivery_method

    method_id = graphene.Node.to_global_id(node_name, delivery_method.id)

    # when
    response = api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id}
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    checkout.refresh_from_db()

    mock_clean_delivery.assert_called_once_with(
        checkout_info=checkout_info, lines=lines, method=shipping_method_data
    )
    errors = data["errors"]
    if is_valid_delivery_method:
        assert not errors
        assert getattr(checkout, attribute_name) == delivery_method
    else:
        assert len(errors) == 1
        assert errors[0]["field"] == "deliveryMethodId"
        assert (
            errors[0]["code"] == CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.name
        )
        assert checkout.shipping_method is None
        assert checkout.collection_point is None


def test_with_active_problems_flow(
    api_client,
    checkout_with_problems,
    shipping_method,
):
    # given
    channel = checkout_with_problems.channel
    channel.use_legacy_error_flow_for_checkout = False
    channel.save(update_fields=["use_legacy_error_flow_for_checkout"])

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD,
        {
            "id": to_global_id_or_none(checkout_with_problems),
            "deliveryMethodId": method_id,
        },
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["checkoutDeliveryMethodUpdate"]["errors"]
