from decimal import Decimal
from unittest.mock import patch

from django.utils import timezone

from ....shipping.models import ShippingMethod
from ....webhook.event_types import WebhookEventSyncType
from ...core.utils import to_global_id_or_none
from ...tests.utils import get_graphql_content

CHECKOUTS_QUERY = """
query CheckoutsQuery {
  checkouts(first: 1) {
    edges {
      node {
        deliveryMethod {
          __typename
          ... on ShippingMethod {
            id
            name
            price {
              amount
            }
          }
        }
        shippingPrice {
          gross {
            amount
          }
        }
        totalPrice {
          gross {
            amount
          }
        }
        subtotalPrice {
          gross {
            amount
          }
        }
        lines {
          totalPrice {
            gross {
              amount
            }
          }
          unitPrice {
            gross {
              amount
            }
          }
        }
        shippingMethods {
          id
          name
          active
        }
        availableShippingMethods {
          id
          name
          active
        }
      }
    }
  }
}
"""


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_query_checkouts_do_not_trigger_external_shipping_webhook_with_flat_rates(
    mocked_request,
    staff_api_client,
    permission_manage_checkouts,
    checkout_with_delivery_method_for_external_shipping,
    settings,
    tax_configuration_flat_rates,
    shipping_app,
):
    # given
    webhook = shipping_app.webhooks.get()
    assert (
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
        in webhook.events.all().values_list("event_type", flat=True)
    )

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    checkout = checkout_with_delivery_method_for_external_shipping
    checkout.price_expiration = timezone.now()
    checkout.undiscounted_base_shipping_price_amount = Decimal("100")
    checkout.save()

    # when
    response = staff_api_client.post_graphql(
        CHECKOUTS_QUERY,
        permissions=[permission_manage_checkouts],
    )

    # then
    data = get_graphql_content(response)["data"]["checkouts"]["edges"]
    assert len(data) == 1
    checkout_data = data[0]["node"]

    shipping_method = ShippingMethod.objects.get()
    assert len(checkout_data["shippingMethods"]) == 1
    assert checkout_data["shippingMethods"][0]["id"] == to_global_id_or_none(
        shipping_method
    )

    assert len(checkout_data["availableShippingMethods"]) == 1
    assert checkout_data["availableShippingMethods"][0]["id"] == to_global_id_or_none(
        shipping_method
    )

    delivery_method = checkout_data["deliveryMethod"]
    assert delivery_method
    assert delivery_method["id"] == checkout.external_shipping_method_id
    assert delivery_method["name"] == checkout.shipping_method_name
    assert (
        delivery_method["price"]["amount"]
        == checkout.undiscounted_base_shipping_price_amount
    )
    mocked_request.assert_not_called()


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_query_checkouts_do_not_trigger_external_shipping_webhook_with_tax_app(
    mocked_request,
    staff_api_client,
    permission_manage_checkouts,
    checkout_with_delivery_method_for_external_shipping,
    settings,
    tax_configuration_tax_app,
    shipping_app,
):
    # given
    webhook = shipping_app.webhooks.get()
    assert (
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
        in webhook.events.all().values_list("event_type", flat=True)
    )

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    checkout = checkout_with_delivery_method_for_external_shipping
    checkout.price_expiration = timezone.now()
    checkout.undiscounted_base_shipping_price_amount = Decimal("100")
    checkout.save()

    # when
    response = staff_api_client.post_graphql(
        CHECKOUTS_QUERY,
        permissions=[permission_manage_checkouts],
    )

    # then
    data = get_graphql_content(response)["data"]["checkouts"]["edges"]
    assert len(data) == 1
    checkout_data = data[0]["node"]

    shipping_method = ShippingMethod.objects.get()
    assert len(checkout_data["shippingMethods"]) == 1
    assert checkout_data["shippingMethods"][0]["id"] == to_global_id_or_none(
        shipping_method
    )

    assert len(checkout_data["availableShippingMethods"]) == 1
    assert checkout_data["availableShippingMethods"][0]["id"] == to_global_id_or_none(
        shipping_method
    )

    delivery_method = checkout_data["deliveryMethod"]
    assert delivery_method
    assert delivery_method["id"] == checkout.external_shipping_method_id
    assert delivery_method["name"] == checkout.shipping_method_name
    assert (
        delivery_method["price"]["amount"]
        == checkout.undiscounted_base_shipping_price_amount
    )
    mocked_request.assert_not_called()


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_query_checkouts_do_not_trigger_exclude_shipping_webhooks_with_flat_rates(
    mocked_request,
    staff_api_client,
    permission_manage_checkouts,
    checkout_with_delivery_method_for_external_shipping,
    settings,
    tax_configuration_flat_rates,
    shipping_app,
):
    # given
    webhook = shipping_app.webhooks.get()
    webhook.events.create(
        event_type=WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    )

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    checkout = checkout_with_delivery_method_for_external_shipping
    checkout.price_expiration = timezone.now()
    checkout.undiscounted_base_shipping_price_amount = Decimal("100")
    checkout.save()

    # when
    response = staff_api_client.post_graphql(
        CHECKOUTS_QUERY,
        permissions=[permission_manage_checkouts],
    )

    # then
    data = get_graphql_content(response)["data"]["checkouts"]["edges"]
    assert len(data) == 1
    checkout_data = data[0]["node"]

    shipping_method = ShippingMethod.objects.get()
    assert len(checkout_data["shippingMethods"]) == 1
    assert checkout_data["shippingMethods"][0]["id"] == to_global_id_or_none(
        shipping_method
    )

    assert len(checkout_data["availableShippingMethods"]) == 1
    assert checkout_data["availableShippingMethods"][0]["id"] == to_global_id_or_none(
        shipping_method
    )

    delivery_method = checkout_data["deliveryMethod"]
    assert delivery_method
    assert delivery_method["id"] == checkout.external_shipping_method_id
    assert delivery_method["name"] == checkout.shipping_method_name
    assert (
        delivery_method["price"]["amount"]
        == checkout.undiscounted_base_shipping_price_amount
    )
    mocked_request.assert_not_called()


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_query_checkouts_do_not_trigger_exclude_shipping_webhooks_with_tax_app(
    mocked_request,
    staff_api_client,
    permission_manage_checkouts,
    checkout_with_delivery_method_for_external_shipping,
    settings,
    tax_configuration_tax_app,
    shipping_app,
):
    # given
    webhook = shipping_app.webhooks.get()
    webhook.events.create(
        event_type=WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    )

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    checkout = checkout_with_delivery_method_for_external_shipping
    checkout.price_expiration = timezone.now()
    checkout.undiscounted_base_shipping_price_amount = Decimal("100")
    checkout.save()

    # when
    response = staff_api_client.post_graphql(
        CHECKOUTS_QUERY,
        permissions=[permission_manage_checkouts],
    )

    # then
    data = get_graphql_content(response)["data"]["checkouts"]["edges"]
    assert len(data) == 1
    checkout_data = data[0]["node"]

    shipping_method = ShippingMethod.objects.get()
    assert len(checkout_data["shippingMethods"]) == 1
    assert checkout_data["shippingMethods"][0]["id"] == to_global_id_or_none(
        shipping_method
    )

    assert len(checkout_data["availableShippingMethods"]) == 1
    assert checkout_data["availableShippingMethods"][0]["id"] == to_global_id_or_none(
        shipping_method
    )

    delivery_method = checkout_data["deliveryMethod"]
    assert delivery_method
    assert delivery_method["id"] == checkout.external_shipping_method_id
    assert delivery_method["name"] == checkout.shipping_method_name
    assert (
        delivery_method["price"]["amount"]
        == checkout.undiscounted_base_shipping_price_amount
    )
    mocked_request.assert_not_called()
