from decimal import Decimal
from unittest import mock
from unittest.mock import ANY, patch

import graphene
import pytest
from django.test import override_settings

from .....account.models import Address
from .....checkout.actions import call_checkout_info_event
from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.models import CheckoutDelivery
from .....checkout.utils import invalidate_checkout
from .....core.models import EventDelivery
from .....plugins.manager import get_plugins_manager
from .....product.models import ProductChannelListing, ProductVariantChannelListing
from .....shipping import models as shipping_models
from .....shipping.models import ShippingZone
from .....warehouse import WarehouseClickAndCollectOption
from .....warehouse.models import Stock, Warehouse
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

MUTATION_UPDATE_DELIVERY_METHOD = """
    mutation checkoutDeliveryMethodUpdate($id: ID, $deliveryMethodId: ID) {
      checkoutDeliveryMethodUpdate(id: $id, deliveryMethodId: $deliveryMethodId) {
        checkout {
          token
          id
          shippingAddress {
            id
            firstName
          }
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
          totalPrice {
            gross {
              amount
            }
            net {
              amount
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


@pytest.mark.parametrize(
    ("delivery_method", "node_name", "attribute_name"),
    [
        ("warehouse", "Warehouse", "collection_point"),
        ("shipping_method", "ShippingMethod", "shipping_method"),
    ],
    indirect=("delivery_method",),
)
@patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_delivery_method_update_not_applicable_delivery_method(
    mocked_invalidate_checkout,
    api_client,
    delivery_method,
    node_name,
    attribute_name,
    checkout_with_item_for_cc,
):
    # given
    checkout = checkout_with_item_for_cc

    Warehouse.objects.update(
        click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
    )
    ShippingZone.objects.update(countries=[])

    method_id = graphene.Node.to_global_id(node_name, delivery_method.id)

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD,
        {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id},
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    checkout.refresh_from_db()

    errors = data["errors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "deliveryMethodId"
    assert errors[0]["code"] == CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.name
    assert checkout.shipping_method is None
    assert checkout.collection_point is None
    mocked_invalidate_checkout.assert_not_called()


@pytest.mark.parametrize(
    ("delivery_method", "node_name", "attribute_name"),
    [
        ("warehouse", "Warehouse", "collection_point"),
        ("shipping_method", "ShippingMethod", "assigned_delivery"),
    ],
    indirect=("delivery_method",),
)
@patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_delivery_method_update(
    mocked_invalidate_checkout,
    api_client,
    delivery_method,
    node_name,
    attribute_name,
    checkout_with_item_for_cc,
    address,
):
    # given
    checkout = checkout_with_item_for_cc
    checkout.shipping_address = address
    checkout.save()

    method_id = graphene.Node.to_global_id(node_name, delivery_method.id)

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD,
        {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id},
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    checkout.refresh_from_db()

    errors = data["errors"]
    assert not errors
    assert getattr(checkout, attribute_name)
    mocked_invalidate_checkout.assert_called_once()


@pytest.mark.parametrize(
    ("channel_listing_model", "listing_filter_field"),
    [
        (ProductVariantChannelListing, "variant_id"),
        (ProductChannelListing, "product__variants__id"),
    ],
)
@pytest.mark.parametrize(
    ("delivery_method", "node_name", "attribute_name"),
    [
        ("warehouse", "Warehouse", "collection_point"),
        ("shipping_method", "ShippingMethod", "shipping_method"),
    ],
    indirect=("delivery_method",),
)
def test_checkout_delivery_method_update_when_line_without_channel_listing(
    api_client,
    delivery_method,
    node_name,
    attribute_name,
    channel_listing_model,
    listing_filter_field,
    checkout_with_item_for_cc,
):
    # given
    line = checkout_with_item_for_cc.lines.first()

    channel_listing_model.objects.filter(
        channel_id=checkout_with_item_for_cc.channel_id,
        **{listing_filter_field: line.variant_id},
    ).delete()

    checkout = checkout_with_item_for_cc

    query = MUTATION_UPDATE_DELIVERY_METHOD

    method_id = graphene.Node.to_global_id(node_name, delivery_method.id)

    response = api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id}
    )
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "lines"
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert checkout.shipping_method is None


@pytest.mark.parametrize(
    ("delivery_method", "node_name", "attribute_name"),
    [
        ("warehouse", "Warehouse", "collection_point"),
        ("shipping_method", "ShippingMethod", "shipping_method"),
    ],
    indirect=("delivery_method",),
)
@patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_delivery_method_update_missing_checkout_metadata_when_not_applicable_method(
    mocked_invalidate_checkout,
    api_client,
    delivery_method,
    node_name,
    attribute_name,
    checkout_with_item_for_cc,
):
    # given
    checkout = checkout_with_item_for_cc
    checkout.metadata_storage.delete()

    Warehouse.objects.update(
        click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
    )
    ShippingZone.objects.update(countries=[])

    method_id = graphene.Node.to_global_id(node_name, delivery_method.id)

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD,
        {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id},
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    checkout.refresh_from_db()

    errors = data["errors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "deliveryMethodId"
    assert errors[0]["code"] == CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.name
    assert checkout.shipping_method is None
    assert checkout.collection_point is None
    mocked_invalidate_checkout.assert_not_called()


@pytest.mark.parametrize(
    ("delivery_method", "node_name", "attribute_name"),
    [
        ("warehouse", "Warehouse", "collection_point"),
        ("shipping_method", "ShippingMethod", "assigned_delivery"),
    ],
    indirect=("delivery_method",),
)
@patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_delivery_method_update_checkout_without_metadata(
    mocked_invalidate_checkout,
    api_client,
    delivery_method,
    node_name,
    attribute_name,
    checkout_with_item_for_cc,
):
    # given
    checkout = checkout_with_item_for_cc
    checkout.metadata_storage.delete()
    method_id = graphene.Node.to_global_id(node_name, delivery_method.id)

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD,
        {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id},
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    checkout.refresh_from_db()

    errors = data["errors"]
    assert not errors
    assert getattr(checkout, attribute_name)
    mocked_invalidate_checkout.assert_called_once()


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_checkout_delivery_method_update_external_shipping(
    mock_send_request,
    api_client,
    checkout_with_item_for_cc,
    settings,
    shipping_app,
    channel_USD,
):
    checkout = checkout_with_item_for_cc
    query = MUTATION_UPDATE_DELIVERY_METHOD

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    response_method_id = "abcd"
    response_shipping_name = "Provider - Economy"
    response_shipping_price = "10"
    mock_json_response = [
        {
            "id": response_method_id,
            "name": response_shipping_name,
            "amount": response_shipping_price,
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

    assert not errors
    assert checkout.assigned_delivery
    assert checkout.shipping_method_name == response_shipping_name
    assert checkout.undiscounted_base_shipping_price_amount == Decimal(
        response_shipping_price
    )
    assert data["checkout"]["deliveryMethod"]["id"] == method_id


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_checkout_delivery_method_update_external_shipping_long_external_id(
    mock_send_request,
    api_client,
    checkout_with_item_for_cc,
    settings,
    shipping_app,
    channel_USD,
):
    checkout = checkout_with_item_for_cc
    query = MUTATION_UPDATE_DELIVERY_METHOD

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    response_method_id = "A" * 700  # External ID longer than 512 characters
    response_shipping_name = "Provider - Economy"
    response_shipping_price = "10"
    mock_json_response = [
        {
            "id": response_method_id,
            "name": response_shipping_name,
            "amount": response_shipping_price,
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

    assert not errors
    assert checkout.assigned_delivery
    assert checkout.assigned_delivery.external_shipping_method_id == method_id
    assert len(checkout.assigned_delivery.external_shipping_method_id) > 900


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_checkout_delivery_method_update_external_shipping_when_invalid(
    mock_send_request,
    api_client,
    checkout_with_item_for_cc,
    settings,
    shipping_app,
    channel_USD,
):
    # given
    checkout = checkout_with_item_for_cc
    query = MUTATION_UPDATE_DELIVERY_METHOD

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    response_method_id = "abcd"
    mock_send_request.return_value = []

    method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{response_method_id}"
    )

    # when
    response = api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id}
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    checkout.refresh_from_db()

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "deliveryMethodId"
    assert errors[0]["code"] == CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.name
    assert checkout.assigned_delivery is None
    assert checkout.shipping_method_name is None
    assert checkout.undiscounted_base_shipping_price_amount == Decimal(0)


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_checkout_delivery_method_update_keeps_shipping_when_invalid(
    mock_send_request,
    api_client,
    checkout_with_item_for_cc,
    settings,
    shipping_app,
):
    # given
    checkout = checkout_with_item_for_cc
    query = MUTATION_UPDATE_DELIVERY_METHOD

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    response_method_id = "abcd"

    mock_send_request.return_value = []

    external_shipping_method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{response_method_id}"
    )

    checkout.assigned_delivery = CheckoutDelivery.objects.create(
        checkout_id=checkout.pk,
        external_shipping_method_id=external_shipping_method_id,
        name="External",
        price_amount="10.00",
        currency="USD",
        maximum_delivery_days=7,
        is_external=True,
    )
    checkout.save()

    # when
    response = api_client.post_graphql(
        query,
        {
            "id": to_global_id_or_none(checkout),
            "deliveryMethodId": external_shipping_method_id,
        },
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    checkout.refresh_from_db()

    errors = data["errors"]

    assert errors
    assert len(errors) == 1
    assert errors[0]["field"] == "deliveryMethodId"
    assert errors[0]["code"] == CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.name

    assert checkout.assigned_delivery


def test_checkout_delivery_method_update_with_id_of_different_type_causes_and_error(
    api_client,
    checkout_with_item,
    address,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_DELIVERY_METHOD

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


def test_checkout_delivery_method_with_nonexistant_id_results_not_applicable(
    api_client,
    warehouse_for_cc,
    checkout_with_item,
    address,
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_DELIVERY_METHOD

    nonexistant_id = "YXBwOjEyMzQ6c29tZS1pZA=="

    # when
    response = api_client.post_graphql(
        query,
        {
            "id": to_global_id_or_none(checkout),
            "deliveryMethodId": nonexistant_id,
        },
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    checkout.refresh_from_db()

    assert not data["checkout"]
    assert data["errors"][0]["field"] == "deliveryMethodId"
    assert (
        data["errors"][0]["code"]
        == CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.name
    )
    assert checkout.assigned_delivery is None
    assert checkout.collection_point is None


def test_checkout_delivery_method_with_empty_fields_results_None(
    api_client, checkout_with_item, address, checkout_delivery
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.assigned_delivery = checkout_delivery(checkout)
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_DELIVERY_METHOD

    # when
    response = api_client.post_graphql(
        query,
        {
            "id": to_global_id_or_none(checkout),
        },
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    checkout.refresh_from_db()

    assert not data["errors"]
    assert data["checkout"]["deliveryMethod"] is None
    assert checkout.assigned_delivery is None
    assert checkout.collection_point is None


@patch("saleor.shipping.postal_codes.is_shipping_method_applicable_for_postal_code")
def test_checkout_delivery_method_update_excluded_postal_code(
    mock_is_shipping_method_available,
    staff_api_client,
    shipping_method,
    checkout_with_item,
    address,
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_DELIVERY_METHOD
    mock_is_shipping_method_available.return_value = False

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    # when
    response = staff_api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id}
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]

    checkout.refresh_from_db()

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "deliveryMethodId"
    assert errors[0]["code"] == CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.name
    assert checkout.assigned_delivery is None
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
    # given
    shipping_method.shipping_zone.channels.clear()
    shipping_method.channel_listings.all().delete()
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_DELIVERY_METHOD

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    # when
    response = api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id}
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]

    checkout.refresh_from_db()

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "deliveryMethodId"
    assert errors[0]["code"] == CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.name
    assert checkout.assigned_delivery is None


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

    assert checkout.assigned_delivery.shipping_method_id == str(shipping_method.id)


def test_checkout_delivery_method_update_valid_method_not_all_shipping_data(
    api_client,
    shipping_method,
    checkout_with_item_for_cc,
):
    # given

    checkout = checkout_with_item_for_cc
    checkout.shipping_address = Address.objects.create(country="US")
    checkout.save()

    query = MUTATION_UPDATE_DELIVERY_METHOD

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    # when
    response = api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id}
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]

    checkout.refresh_from_db()

    errors = data["errors"]
    assert not errors
    assert checkout.assigned_delivery.shipping_method_id == str(shipping_method.id)


def test_checkout_delivery_method_update_valid_method_not_all_shipping_data_for_cc(
    api_client,
    checkout_with_item_for_cc,
    warehouse_for_cc,
):
    # given
    checkout_address = Address.objects.create(country="US")
    checkout = checkout_with_item_for_cc
    checkout.shipping_address = checkout_address
    checkout.save()
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    checkout_info.shipping_address = warehouse_for_cc.address

    query = MUTATION_UPDATE_DELIVERY_METHOD

    method_id = graphene.Node.to_global_id("Warehouse", warehouse_for_cc.id)

    # when
    response = api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id}
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    checkout.refresh_from_db()

    errors = data["errors"]
    assert checkout.shipping_address == warehouse_for_cc.address
    assert checkout.shipping_address_id != warehouse_for_cc.address.id
    assert not errors
    assert checkout.collection_point == warehouse_for_cc


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


def test_checkout_delivery_method_update_only_with_token_cleans_shipping_address(
    api_client,
    checkout_with_item_for_cc,
    warehouse,
):
    # given
    warehouse.click_and_collect_option = WarehouseClickAndCollectOption.LOCAL_STOCK
    warehouse.save(update_fields=["click_and_collect_option"])
    checkout = checkout_with_item_for_cc
    checkout.collection_point_id = warehouse.id
    checkout.save(update_fields=["collection_point_id"])

    # when
    query = MUTATION_UPDATE_DELIVERY_METHOD
    response = api_client.post_graphql(query, {"id": to_global_id_or_none(checkout)})

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    assert not data["errors"]
    assert data["checkout"]["shippingAddress"] is None


def test_checkout_delivery_method_update_from_cc_cleans_shipping_address(
    api_client, checkout_with_item_for_cc, warehouse, shipping_method
):
    # given
    warehouse.click_and_collect_option = WarehouseClickAndCollectOption.LOCAL_STOCK
    warehouse.save(update_fields=["click_and_collect_option"])
    checkout = checkout_with_item_for_cc
    checkout.collection_point_id = warehouse.id
    checkout.save(update_fields=["collection_point_id"])

    # when
    query = MUTATION_UPDATE_DELIVERY_METHOD
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    response = api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id}
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    assert not data["errors"]
    assert data["checkout"]["shippingAddress"] is None
    assert data["checkout"]["deliveryMethod"]["id"] == method_id


def test_checkout_delivery_method_update_from_cc_to_all_warehouses_update_address(
    api_client, checkout_with_item_for_cc, warehouses_for_cc
):
    # given
    warehouse_cc_local = warehouses_for_cc[2]
    warehouse_cc_all = warehouses_for_cc[1]
    test_address_name = "Jimmy"
    warehouse_cc_all_address = warehouse_cc_all.address
    warehouse_cc_all_address.first_name = test_address_name
    warehouse_cc_all_address.save(update_fields=["first_name"])
    checkout = checkout_with_item_for_cc
    checkout.collection_point_id = warehouse_cc_local.id
    checkout.save(update_fields=["collection_point_id", "shipping_method_id"])
    Stock.objects.create(
        warehouse=warehouse_cc_all,
        product_variant=checkout.lines.first().variant,
        quantity=1,
    )

    # when
    query = MUTATION_UPDATE_DELIVERY_METHOD
    method_id = graphene.Node.to_global_id("Warehouse", warehouse_cc_all.id)
    response = api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id}
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    assert not data["errors"]
    assert data["checkout"]["shippingAddress"]["firstName"] == test_address_name


def test_checkout_delivery_method_update_from_cc_to_all_warehouses_disabled_cc(
    api_client, checkout_with_item_for_cc, warehouses_for_cc
):
    # given
    warehouse_cc_local = warehouses_for_cc[2]
    warehouse_cc_all = warehouses_for_cc[1]
    warehouse_cc_all.click_and_collect_option = WarehouseClickAndCollectOption.DISABLED
    warehouse_cc_all.save(update_fields=["click_and_collect_option"])
    checkout = checkout_with_item_for_cc
    checkout.collection_point_id = warehouse_cc_local.id
    checkout.save(update_fields=["collection_point_id", "shipping_method_id"])
    Stock.objects.create(
        warehouse=warehouse_cc_all,
        product_variant=checkout.lines.first().variant,
        quantity=1,
    )

    # when
    query = MUTATION_UPDATE_DELIVERY_METHOD
    method_id = graphene.Node.to_global_id("Warehouse", warehouse_cc_all.id)
    response = api_client.post_graphql(
        query, {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id}
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "deliveryMethodId"
    assert errors[0]["code"] == CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.name


MUTATION_UPDATE_DELIVERY_METHOD_WITH_ONLY_ID = """
    mutation checkoutDeliveryMethodUpdate($id: ID, $deliveryMethodId: ID) {
      checkoutDeliveryMethodUpdate(id: $id, deliveryMethodId: $deliveryMethodId) {
        checkout {
          id
        }
        errors {
          field
          message
          code
        }
      }
    }
"""


@patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.webhook.transport.asynchronous.transport.generate_deferred_payloads.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_delivery_method_update_triggers_webhooks(
    mocked_generate_deferred_payloads,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_checkout_info_event,
    setup_checkout_webhooks,
    settings,
    api_client,
    shipping_method,
    checkout_with_item,
    address,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_updated_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_UPDATED)

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD_WITH_ONLY_ID,
        {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id},
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["checkoutDeliveryMethodUpdate"]["errors"]

    assert wrapped_call_checkout_info_event.called

    # confirm that event delivery was generated for each async webhook.
    checkout_update_delivery = EventDelivery.objects.get(
        webhook_id=checkout_updated_webhook.id
    )

    mocked_generate_deferred_payloads.assert_called_once_with(
        kwargs={
            "event_delivery_ids": [checkout_update_delivery.id],
            "deferred_payload_data": {
                "model_name": "checkout.checkout",
                "object_id": checkout.pk,
                "requestor_model_name": None,
                "requestor_object_id": None,
                "request_time": None,
            },
            "send_webhook_queue": settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            "telemetry_context": ANY,
        },
        MessageGroupId="example.com",
    )

    # Deferred payload covers the async actions
    assert not mocked_send_webhook_request_async.called

    sync_deliveries = {
        call.args[0].event_type: call.args[0]
        for call in mocked_send_webhook_request_sync.mock_calls
    }

    assert WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT in sync_deliveries
    shipping_methods_delivery = sync_deliveries[
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
    ]
    assert shipping_methods_delivery.webhook_id == shipping_webhook.id

    assert WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS in sync_deliveries
    filter_shipping_delivery = sync_deliveries[
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    ]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id

    assert WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES not in sync_deliveries


@patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.webhook.transport.asynchronous.transport.generate_deferred_payloads.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_delivery_method_update_cc_triggers_webhooks(
    mocked_generate_deferred_payloads,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_checkout_info_event,
    setup_checkout_webhooks,
    settings,
    api_client,
    checkout_with_item_for_cc,
    warehouses_for_cc,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_updated_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_UPDATED)

    warehouse_cc_all = warehouses_for_cc[1]
    test_address_name = "Jimmy"
    warehouse_cc_all_address = warehouse_cc_all.address
    warehouse_cc_all_address.first_name = test_address_name
    warehouse_cc_all_address.save(update_fields=["first_name"])
    checkout = checkout_with_item_for_cc

    Stock.objects.create(
        warehouse=warehouse_cc_all,
        product_variant=checkout.lines.first().variant,
        quantity=1,
    )
    method_id = graphene.Node.to_global_id("Warehouse", warehouse_cc_all.id)

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD_WITH_ONLY_ID,
        {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id},
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["checkoutDeliveryMethodUpdate"]["errors"]
    assert wrapped_call_checkout_info_event.called

    # confirm that event delivery was generated for each async webhook.
    checkout_update_delivery = EventDelivery.objects.get(
        webhook_id=checkout_updated_webhook.id
    )

    mocked_generate_deferred_payloads.assert_called_once_with(
        kwargs={
            "event_delivery_ids": [checkout_update_delivery.id],
            "deferred_payload_data": {
                "model_name": "checkout.checkout",
                "object_id": checkout.pk,
                "requestor_model_name": None,
                "requestor_object_id": None,
                "request_time": None,
            },
            "send_webhook_queue": settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            "telemetry_context": ANY,
        },
        MessageGroupId="example.com",
    )

    # Deferred payload covers the sync and async actions
    assert not mocked_send_webhook_request_async.called
    assert not mocked_send_webhook_request_sync.called


@patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.webhook.transport.asynchronous.transport.generate_deferred_payloads.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_delivery_method_update_external_shipping_triggers_webhooks(
    mocked_generate_deferred_payloads,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_checkout_info_event,
    setup_checkout_webhooks,
    settings,
    api_client,
    checkout_with_item_for_cc,
):
    # given
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_updated_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_UPDATED)

    checkout = checkout_with_item_for_cc

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
    mocked_send_webhook_request_sync.side_effect = [
        mock_json_response,
        [],
        [],
    ]

    method_id = graphene.Node.to_global_id(
        "app", f"{shipping_webhook.app.identifier}:{response_method_id}"
    )

    # when

    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD_WITH_ONLY_ID,
        {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id},
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["checkoutDeliveryMethodUpdate"]["errors"]

    assert wrapped_call_checkout_info_event.called

    checkout_update_delivery = EventDelivery.objects.get(
        webhook_id=checkout_updated_webhook.id
    )

    mocked_generate_deferred_payloads.assert_called_once_with(
        kwargs={
            "event_delivery_ids": [checkout_update_delivery.id],
            "deferred_payload_data": {
                "model_name": "checkout.checkout",
                "object_id": checkout.pk,
                "requestor_model_name": None,
                "requestor_object_id": None,
                "request_time": None,
            },
            "send_webhook_queue": settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            "telemetry_context": ANY,
        },
        MessageGroupId="example.com",
    )

    # Deferred payload covers the async actions
    assert not mocked_send_webhook_request_async.called

    sync_deliveries = {
        call.args[0].event_type: call.args[0]
        for call in mocked_send_webhook_request_sync.mock_calls
    }

    assert WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT in sync_deliveries
    shipping_methods_delivery = sync_deliveries[
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
    ]
    assert shipping_methods_delivery.webhook_id == shipping_webhook.id

    assert WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS in sync_deliveries
    filter_shipping_delivery = sync_deliveries[
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    ]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id

    assert WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES not in sync_deliveries


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_checkout_delivery_method_update_from_cc_to_external_shipping(
    mocked_send_webhook_request_sync,
    mocked_invalidate_checkout,
    mocked_call_checkout_info_event,
    settings,
    checkout_with_delivery_method_for_cc,
    shipping_app,
    api_client,
):
    # given
    checkout = checkout_with_delivery_method_for_cc
    checkout.save_billing_address = True
    checkout.save_shipping_address = False
    checkout.save(update_fields=["save_billing_address", "save_shipping_address"])

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    response_method_id = "abcd"
    response_shipping_name = "Provider - Economy"
    response_shipping_price = "10"
    mock_json_response = [
        {
            "id": response_method_id,
            "name": response_shipping_name,
            "amount": response_shipping_price,
            "currency": "USD",
            "maximum_delivery_days": "7",
        }
    ]
    mocked_send_webhook_request_sync.return_value = mock_json_response

    method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{response_method_id}"
    )

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD,
        {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id},
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"]["id"] == method_id
    assert data["checkout"]["deliveryMethod"]["name"] == response_shipping_name

    checkout.refresh_from_db()
    assert checkout.collection_point_id is None
    assert checkout.shipping_address_id is None
    assert checkout.shipping_method_id is None
    assert checkout.assigned_delivery.shipping_method_id == method_id
    assert checkout.shipping_method_name == response_shipping_name
    assert checkout.save_billing_address is True
    # should be reset to the default value as the shipping address is cleared
    assert checkout.save_shipping_address is True

    mocked_invalidate_checkout.assert_called_once()
    mocked_call_checkout_info_event.assert_called_once()


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_delivery_method_update_from_cc_to_none(
    mocked_invalidate_checkout,
    mocked_call_checkout_info_event,
    checkout_with_delivery_method_for_cc,
    api_client,
):
    # given
    checkout = checkout_with_delivery_method_for_cc
    checkout.save_billing_address = True
    checkout.save_shipping_address = False
    checkout.save(update_fields=["save_billing_address", "save_shipping_address"])

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD,
        {"id": to_global_id_or_none(checkout), "deliveryMethodId": None},
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"] is None

    checkout.refresh_from_db()
    assert checkout.collection_point_id is None
    assert checkout.shipping_address_id is None
    assert checkout.assigned_delivery_id is None
    assert checkout.shipping_method_name is None
    assert checkout.save_billing_address is True
    # should be reset to the default value as the shipping address is cleared
    assert checkout.save_shipping_address is True

    mocked_invalidate_checkout.assert_called_once()
    mocked_call_checkout_info_event.assert_called_once()


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_delivery_method_update_from_cc_to_built_in_shipping(
    mocked_invalidate_checkout,
    mocked_call_checkout_info_event,
    checkout_with_delivery_method_for_cc,
    shipping_method,
    api_client,
):
    # given
    checkout = checkout_with_delivery_method_for_cc
    checkout.save_billing_address = True
    checkout.save_shipping_address = False
    checkout.save(update_fields=["save_billing_address", "save_shipping_address"])

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD,
        {
            "id": to_global_id_or_none(checkout),
            "deliveryMethodId": to_global_id_or_none(shipping_method),
        },
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"]["id"] == to_global_id_or_none(
        shipping_method
    )
    assert data["checkout"]["deliveryMethod"]["name"] == shipping_method.name

    checkout.refresh_from_db()
    assert checkout.collection_point_id is None
    assert checkout.shipping_address_id is None
    assert checkout.assigned_delivery.shipping_method_id == str(shipping_method.id)
    assert checkout.shipping_method_name == shipping_method.name
    assert checkout.save_billing_address is True
    # should be reset to the default value as the shipping address is cleared
    assert checkout.save_shipping_address is True

    mocked_invalidate_checkout.assert_called_once()
    mocked_call_checkout_info_event.assert_called_once()


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_delivery_method_update_from_cc_to_the_same_cc(
    mocked_invalidate_checkout,
    mocked_call_checkout_info_event,
    checkout_with_delivery_method_for_cc,
    api_client,
):
    # given
    checkout = checkout_with_delivery_method_for_cc
    collection_point = checkout.collection_point
    checkout.save_billing_address = True
    checkout.save_shipping_address = True
    checkout.save(update_fields=["save_billing_address", "save_shipping_address"])

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD,
        {
            "id": to_global_id_or_none(checkout),
            "deliveryMethodId": to_global_id_or_none(collection_point),
        },
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"]["id"] == to_global_id_or_none(
        collection_point
    )
    assert data["checkout"]["deliveryMethod"]["name"] == collection_point.name

    checkout.refresh_from_db()

    assert checkout.collection_point_id == collection_point.id
    assert checkout.shipping_address_id != collection_point.address.id
    assert checkout.shipping_address == collection_point.address
    assert checkout.assigned_delivery_id is None
    assert checkout.shipping_method_name is None
    assert checkout.save_billing_address is True
    # the flag remain unchanged as the address stay the same
    assert checkout.save_shipping_address is True

    mocked_invalidate_checkout.assert_not_called()
    mocked_call_checkout_info_event.assert_not_called()


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_delivery_method_update_from_cc_to_different_cc(
    mocked_invalidate_checkout,
    mocked_call_checkout_info_event,
    checkout_with_items,
    warehouses_for_cc,
    address_usa,
    api_client,
):
    # given
    warehouses_for_cc[0].address = address_usa
    warehouses_for_cc[0].save(update_fields=["address"])

    checkout = checkout_with_items
    checkout.collection_point = warehouses_for_cc[0]
    checkout.shipping_address = address_usa.get_copy()
    checkout.save_billing_address = True
    checkout.save_shipping_address = True
    checkout.save()

    collection_point = warehouses_for_cc[1]

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD,
        {
            "id": to_global_id_or_none(checkout),
            "deliveryMethodId": to_global_id_or_none(collection_point),
        },
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"]["id"] == to_global_id_or_none(
        collection_point
    )
    assert data["checkout"]["deliveryMethod"]["name"] == collection_point.name

    checkout.refresh_from_db()

    assert checkout.collection_point_id == collection_point.id
    assert checkout.shipping_address_id != collection_point.address.id
    assert checkout.shipping_address == collection_point.address
    assert checkout.assigned_delivery_id is None
    assert checkout.shipping_method_name is None
    assert checkout.save_billing_address is True
    # set the save_shipping_address setting to False for CC
    assert checkout.save_shipping_address is False

    mocked_invalidate_checkout.assert_called_once()
    mocked_call_checkout_info_event.assert_called_once()


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_delivery_method_update_from_external_shipping_to_cc(
    mocked_invalidate_checkout,
    mocked_call_checkout_info_event,
    checkout_with_delivery_method_for_external_shipping,
    warehouses_for_cc,
    address_usa,
    api_client,
):
    # given
    checkout = checkout_with_delivery_method_for_external_shipping
    checkout.save_billing_address = True
    checkout.save_shipping_address = True
    checkout.shipping_address = address_usa
    checkout.save(
        update_fields=[
            "save_billing_address",
            "save_shipping_address",
            "shipping_address",
        ]
    )

    collection_point = warehouses_for_cc[1]

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD,
        {
            "id": to_global_id_or_none(checkout),
            "deliveryMethodId": to_global_id_or_none(collection_point),
        },
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"]["id"] == to_global_id_or_none(
        collection_point
    )
    assert data["checkout"]["deliveryMethod"]["name"] == collection_point.name

    checkout.refresh_from_db()

    assert checkout.collection_point_id == collection_point.id
    assert checkout.shipping_address_id != collection_point.address.id
    assert checkout.shipping_address == collection_point.address
    assert checkout.assigned_delivery_id is None
    assert checkout.shipping_method_name is None
    assert checkout.save_billing_address is True
    # set the save_shipping_address setting to False for CC
    assert checkout.save_shipping_address is False

    mocked_invalidate_checkout.assert_called_once()
    mocked_call_checkout_info_event.assert_called_once()


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_delivery_method_update_from_external_shipping_to_built_in_shipping(
    mocked_invalidate_checkout,
    mocked_call_checkout_info_event,
    checkout_with_delivery_method_for_external_shipping,
    shipping_method,
    api_client,
):
    # given
    checkout = checkout_with_delivery_method_for_external_shipping
    checkout.save_billing_address = True
    checkout.save_shipping_address = True
    checkout.save(update_fields=["save_billing_address", "save_shipping_address"])

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD,
        {
            "id": to_global_id_or_none(checkout),
            "deliveryMethodId": to_global_id_or_none(shipping_method),
        },
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"]["id"] == to_global_id_or_none(
        shipping_method
    )
    assert data["checkout"]["deliveryMethod"]["name"] == shipping_method.name

    checkout.refresh_from_db()

    assert checkout.collection_point_id is None
    assert checkout.assigned_delivery.shipping_method_id == str(shipping_method.id)
    assert checkout.shipping_method_name == shipping_method.name
    assert checkout.save_billing_address is True
    assert checkout.save_shipping_address is True

    mocked_invalidate_checkout.assert_called_once()
    mocked_call_checkout_info_event.assert_called_once()


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_delivery_method_update_from_external_shipping_to_different_external(
    mocked_invalidate_checkout,
    mocked_send_webhook_request_sync,
    mocked_call_checkout_info_event,
    settings,
    shipping_app,
    checkout_with_delivery_method_for_external_shipping,
    api_client,
):
    # given
    checkout = checkout_with_delivery_method_for_external_shipping
    checkout.save_billing_address = True
    checkout.save_shipping_address = True
    checkout.save(update_fields=["save_billing_address", "save_shipping_address"])

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    response_method_id = "new-abcd"
    response_shipping_name = "New Provider - Economy"
    response_shipping_price = "10"
    mock_json_response = [
        {
            "id": response_method_id,
            "name": response_shipping_name,
            "amount": response_shipping_price,
            "currency": "USD",
            "maximum_delivery_days": "7",
        }
    ]
    mocked_send_webhook_request_sync.return_value = mock_json_response

    method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{response_method_id}"
    )

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD,
        {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id},
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"]["id"] == method_id
    assert data["checkout"]["deliveryMethod"]["name"] == response_shipping_name

    checkout.refresh_from_db()

    assert checkout.collection_point_id is None
    assert checkout.assigned_delivery.shipping_method_id == str(method_id)
    assert checkout.shipping_method_name == response_shipping_name
    assert checkout.save_billing_address is True
    assert checkout.save_shipping_address is True

    mocked_invalidate_checkout.assert_called_once()
    mocked_call_checkout_info_event.assert_called_once()


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_delivery_method_update_from_external_shipping_to_none(
    mocked_invalidate_checkout,
    mocked_call_checkout_info_event,
    checkout_with_delivery_method_for_external_shipping,
    api_client,
):
    # given
    checkout = checkout_with_delivery_method_for_external_shipping
    checkout.save_billing_address = True
    checkout.save_shipping_address = False
    checkout.save(update_fields=["save_billing_address", "save_shipping_address"])

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD,
        {"id": to_global_id_or_none(checkout), "deliveryMethodId": None},
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"] is None

    checkout.refresh_from_db()

    assert checkout.collection_point_id is None
    assert checkout.assigned_delivery_id is None
    assert checkout.shipping_method_name is None
    # the flags should not be changed as shipping address is not reset
    assert checkout.save_billing_address is True
    assert checkout.save_shipping_address is False

    mocked_invalidate_checkout.assert_called_once()
    mocked_call_checkout_info_event.assert_called_once()


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_delivery_method_update_from_external_shipping_to_the_same_external(
    mocked_invalidate_checkout,
    mocked_send_webhook_request_sync,
    mocked_call_checkout_info_event,
    address,
    settings,
    shipping_app,
    checkout_with_item,
    api_client,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    response_method_id = "new-abcd"
    response_shipping_name = "New Provider - Economy"
    response_shipping_price = "10"
    mock_json_response = [
        {
            "id": response_method_id,
            "name": response_shipping_name,
            "amount": response_shipping_price,
            "currency": "USD",
            "maximum_delivery_days": "7",
        }
    ]

    mocked_send_webhook_request_sync.return_value = mock_json_response

    method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{response_method_id}"
    )

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.assigned_delivery = CheckoutDelivery.objects.create(
        checkout=checkout,
        external_shipping_method_id=method_id,
        name=response_shipping_name,
        price_amount=response_shipping_price,
        currency="USD",
        maximum_delivery_days=7,
        is_external=True,
    )
    checkout.shipping_method_name = response_shipping_name
    checkout.undiscounted_base_shipping_price_amount = Decimal(response_shipping_price)
    checkout.save_billing_address = True
    checkout.save_shipping_address = True
    checkout.save()

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD,
        {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id},
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"]["id"] == method_id
    assert data["checkout"]["deliveryMethod"]["name"] == response_shipping_name

    checkout.refresh_from_db()

    assert checkout.collection_point_id is None
    assert checkout.assigned_delivery.shipping_method_id == str(method_id)
    assert checkout.shipping_method_name == response_shipping_name
    assert checkout.save_billing_address is True
    assert checkout.save_shipping_address is True

    mocked_invalidate_checkout.assert_not_called()
    mocked_call_checkout_info_event.assert_not_called()


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_delivery_method_update_from_built_in_shipping_to_cc(
    mocked_invalidate_checkout,
    mocked_call_checkout_info_event,
    checkout_with_shipping_method,
    warehouses_for_cc,
    address_usa,
    api_client,
):
    # given
    checkout = checkout_with_shipping_method
    checkout.save_billing_address = True
    checkout.save_shipping_address = True
    checkout.shipping_address = address_usa
    checkout.save(
        update_fields=[
            "save_billing_address",
            "save_shipping_address",
            "shipping_address",
        ]
    )

    collection_point = warehouses_for_cc[1]

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD,
        {
            "id": to_global_id_or_none(checkout),
            "deliveryMethodId": to_global_id_or_none(collection_point),
        },
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"]["id"] == to_global_id_or_none(
        collection_point
    )
    assert data["checkout"]["deliveryMethod"]["name"] == collection_point.name

    checkout.refresh_from_db()
    assert checkout.collection_point_id == collection_point.id
    assert checkout.shipping_address_id != collection_point.address.id
    assert checkout.shipping_address == collection_point.address
    assert checkout.assigned_delivery_id is None
    assert checkout.shipping_method_name is None
    assert checkout.save_billing_address is True
    # set the save_shipping_address setting to False for CC
    assert checkout.save_shipping_address is False

    mocked_invalidate_checkout.assert_called_once()
    mocked_call_checkout_info_event.assert_called_once()


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_delivery_method_update_from_built_in_shipping_to_external_shipping(
    mocked_invalidate_checkout,
    mocked_send_webhook_request_sync,
    mocked_call_checkout_info_event,
    settings,
    checkout_with_shipping_method,
    shipping_app,
    api_client,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    response_method_id = "new-abcd"
    response_shipping_name = "New Provider - Economy"
    response_shipping_price = "10"
    mock_json_response = [
        {
            "id": response_method_id,
            "name": response_shipping_name,
            "amount": response_shipping_price,
            "currency": "USD",
            "maximum_delivery_days": "7",
        }
    ]

    mocked_send_webhook_request_sync.return_value = mock_json_response

    method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{response_method_id}"
    )

    checkout = checkout_with_shipping_method
    checkout.save_billing_address = True
    checkout.save_shipping_address = True
    checkout.save(update_fields=["save_billing_address", "save_shipping_address"])

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD,
        {"id": to_global_id_or_none(checkout), "deliveryMethodId": method_id},
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"]["id"] == method_id
    assert data["checkout"]["deliveryMethod"]["name"] == response_shipping_name

    checkout.refresh_from_db()
    assert checkout.collection_point_id is None
    assert checkout.shipping_method_id is None
    assert checkout.assigned_delivery.shipping_method_id == str(method_id)
    assert checkout.shipping_method_name == response_shipping_name
    assert checkout.save_billing_address is True
    assert checkout.save_shipping_address is True

    mocked_invalidate_checkout.assert_called_once()
    mocked_call_checkout_info_event.assert_called_once()


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_delivery_method_update_from_built_in_shipping_to_differnt_built_in(
    mocked_invalidate_checkout,
    mocked_call_checkout_info_event,
    checkout_with_shipping_method,
    other_shipping_method,
    api_client,
):
    # given
    checkout = checkout_with_shipping_method
    checkout.save_billing_address = True
    checkout.save_shipping_address = True
    checkout.save(update_fields=["save_billing_address", "save_shipping_address"])

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD,
        {
            "id": to_global_id_or_none(checkout),
            "deliveryMethodId": to_global_id_or_none(other_shipping_method),
        },
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"]["id"] == to_global_id_or_none(
        other_shipping_method
    )
    assert data["checkout"]["deliveryMethod"]["name"] == other_shipping_method.name

    checkout.refresh_from_db()
    assert checkout.collection_point_id is None
    assert checkout.assigned_delivery.shipping_method_id == str(
        other_shipping_method.id
    )
    assert checkout.shipping_method_name == other_shipping_method.name
    assert checkout.save_billing_address is True
    assert checkout.save_shipping_address is True

    mocked_invalidate_checkout.assert_called_once()
    mocked_call_checkout_info_event.assert_called_once()


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_delivery_method_update_from_built_in_shipping_to_the_same_shipping(
    mocked_invalidate_checkout,
    mocked_call_checkout_info_event,
    checkout_with_shipping_method,
    checkout_delivery,
    shipping_method,
    api_client,
):
    # given
    checkout = checkout_with_shipping_method
    checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)
    checkout.shipping_method_name = shipping_method.name
    checkout.save_billing_address = True
    checkout.save_shipping_address = True

    price = shipping_method.channel_listings.get().price
    checkout.undiscounted_base_shipping_price_amount = price.amount
    checkout.save()

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD,
        {
            "id": to_global_id_or_none(checkout),
            "deliveryMethodId": to_global_id_or_none(shipping_method),
        },
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"]["id"] == to_global_id_or_none(
        shipping_method
    )
    assert data["checkout"]["deliveryMethod"]["name"] == shipping_method.name

    checkout.refresh_from_db()
    assert checkout.collection_point_id is None
    assert checkout.assigned_delivery.shipping_method_id == str(shipping_method.id)
    assert checkout.shipping_method_name == shipping_method.name
    assert checkout.save_billing_address is True
    assert checkout.save_shipping_address is True

    mocked_invalidate_checkout.assert_not_called()
    mocked_call_checkout_info_event.assert_not_called()


@mock.patch(
    "saleor.graphql.checkout.mutations.utils.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.utils.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_delivery_method_update_from_built_in_shipping_to_none(
    mocked_invalidate_checkout,
    mocked_call_checkout_info_event,
    checkout_with_shipping_method,
    api_client,
):
    # given
    checkout = checkout_with_shipping_method
    checkout.save_billing_address = True
    checkout.save_shipping_address = False
    checkout.save(update_fields=["save_billing_address", "save_shipping_address"])

    # when
    response = api_client.post_graphql(
        MUTATION_UPDATE_DELIVERY_METHOD,
        {"id": to_global_id_or_none(checkout), "deliveryMethodId": None},
    )

    # then
    data = get_graphql_content(response)["data"]["checkoutDeliveryMethodUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["deliveryMethod"] is None

    checkout.refresh_from_db()
    assert checkout.collection_point_id is None
    assert checkout.assigned_delivery_id is None
    assert checkout.shipping_method_name is None
    # the flags should not be changed as shipping address is not reset
    assert checkout.save_billing_address is True
    assert checkout.save_shipping_address is False

    mocked_invalidate_checkout.assert_called_once()
    mocked_call_checkout_info_event.assert_called_once()
