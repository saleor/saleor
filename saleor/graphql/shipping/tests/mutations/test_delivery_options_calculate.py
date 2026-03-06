import datetime
from decimal import Decimal
from unittest import mock

import graphene
from django.utils import timezone
from prices import Money
from promise import Promise

from .....checkout.delivery_context import fetch_shipping_methods_for_checkout
from .....checkout.models import Checkout, CheckoutDelivery
from .....checkout.webhooks.exclude_shipping import (
    excluded_shipping_methods_for_checkout,
)
from .....checkout.webhooks.list_shipping_methods import (
    list_shipping_methods_for_checkout,
)
from .....shipping.error_codes import DeliveryOptionsCalculateErrorCode
from .....shipping.interface import ShippingMethodData
from .....shipping.models import ShippingMethod
from .....webhook.transport.shipping_helpers import to_shipping_app_id
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

DELIVERY_OPTIONS_CALCULATE = """
mutation DeliveryOptionsCalculate($id: ID!) {
  deliveryOptionsCalculate(id: $id) {
    deliveries {
      id
      shippingMethod {
        name
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


def test_used_with_different_type_than_checkout(api_client, address):
    # given
    invalid_id = graphene.Node.to_global_id("Address", address.id)
    variables = {"id": invalid_id}

    # when
    response = api_client.post_graphql(DELIVERY_OPTIONS_CALCULATE, variables)
    content = get_graphql_content(response, ignore_errors=True)
    errors = content["data"]["deliveryOptionsCalculate"]["errors"]

    # then
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == DeliveryOptionsCalculateErrorCode.GRAPHQL_ERROR.name


def test_checkout_not_found(api_client):
    # given
    assert Checkout.objects.count() == 0
    variables = {
        "id": graphene.Node.to_global_id(
            "Checkout", "00000000-0000-0000-0000-000000000000"
        )
    }

    # when
    response = api_client.post_graphql(DELIVERY_OPTIONS_CALCULATE, variables)
    content = get_graphql_content(response, ignore_errors=True)
    errors = content["data"]["deliveryOptionsCalculate"]["errors"]

    # then
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == DeliveryOptionsCalculateErrorCode.NOT_FOUND.name


@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping.excluded_shipping_methods_for_checkout",
    wraps=excluded_shipping_methods_for_checkout,
)
@mock.patch(
    "saleor.checkout.webhooks.list_shipping_methods.list_shipping_methods_for_checkout"
)
def test_fetches_external_shipping_methods(
    mocked_list_shipping_methods,
    mocked_exclude_shipping_methods,
    api_client,
    checkout_with_item,
    address,
    app,
):
    # given
    checkout = checkout_with_item
    ShippingMethod.objects.all().delete()
    expected_name = "External Shipping"
    available_shipping_method = ShippingMethodData(
        id=to_shipping_app_id(app, "external-id"),
        price=Money(Decimal(10), checkout.currency),
        name=expected_name,
        description="External Shipping Description",
        active=True,
        maximum_delivery_days=10,
        minimum_delivery_days=5,
        metadata={},
    )
    mocked_list_shipping_methods.return_value = Promise.resolve(
        [available_shipping_method]
    )

    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])

    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = api_client.post_graphql(DELIVERY_OPTIONS_CALCULATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["deliveryOptionsCalculate"]

    # then
    delivery = CheckoutDelivery.objects.get()
    assert not data["errors"]
    assert len(data["deliveries"]) == 1
    assert data["deliveries"][0]["shippingMethod"]["name"] == expected_name
    assert data["deliveries"][0]["id"] == graphene.Node.to_global_id(
        "CheckoutDelivery", delivery.pk
    )


@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping.excluded_shipping_methods_for_checkout",
    wraps=excluded_shipping_methods_for_checkout,
)
@mock.patch(
    "saleor.checkout.webhooks.list_shipping_methods.list_shipping_methods_for_checkout"
)
def test_excluded_shipping_methods_called_for_checkout(
    mocked_list_shipping_methods,
    mocked_excluded_shipping_methods_for_checkout,
    api_client,
    checkout_with_item,
    address,
    app,
):
    # given
    checkout = checkout_with_item
    available_shipping_method = ShippingMethodData(
        id=to_shipping_app_id(app, "external-id"),
        price=Money(Decimal(10), checkout.currency),
        name="External Shipping",
        description="External Shipping Description",
        active=True,
        maximum_delivery_days=10,
        minimum_delivery_days=5,
        metadata={},
    )
    mocked_list_shipping_methods.return_value = Promise.resolve(
        [available_shipping_method]
    )

    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])

    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = api_client.post_graphql(DELIVERY_OPTIONS_CALCULATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["deliveryOptionsCalculate"]

    # then
    assert not data["errors"]
    mocked_excluded_shipping_methods_for_checkout.assert_called_once()


@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping.excluded_shipping_methods_for_checkout",
    wraps=excluded_shipping_methods_for_checkout,
)
@mock.patch(
    "saleor.checkout.webhooks.list_shipping_methods.list_shipping_methods_for_checkout",
    wraps=list_shipping_methods_for_checkout,
)
def test_when_checkout_has_stale_deliveries(
    mocked_list_shipping_methods,
    mocked_exclude_shipping_methods,
    api_client,
    checkout_with_item,
    address,
    checkout_delivery,
):
    # given
    checkout = checkout_with_item
    existing_delivery = checkout_delivery(checkout)

    checkout.shipping_address = address
    checkout.delivery_methods_stale_at = timezone.now() - datetime.timedelta(minutes=5)
    checkout.save(update_fields=["shipping_address", "delivery_methods_stale_at"])

    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = api_client.post_graphql(DELIVERY_OPTIONS_CALCULATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["deliveryOptionsCalculate"]

    # then
    assert not data["errors"]
    assert len(data["deliveries"]) == 1

    existing_delivery.refresh_from_db()
    assert existing_delivery.is_valid
    assert data["deliveries"][0]["shippingMethod"]["name"] == existing_delivery.name
    assert CheckoutDelivery.objects.filter(checkout=checkout).count() == 1
    assert mocked_exclude_shipping_methods.called
    assert mocked_list_shipping_methods.called


@mock.patch(
    "saleor.graphql.shipping.mutations.delivery_options_calculate.fetch_shipping_methods_for_checkout",
    wraps=fetch_shipping_methods_for_checkout,
)
@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping.excluded_shipping_methods_for_checkout",
    wraps=excluded_shipping_methods_for_checkout,
)
@mock.patch(
    "saleor.checkout.webhooks.list_shipping_methods.list_shipping_methods_for_checkout",
    wraps=list_shipping_methods_for_checkout,
)
def test_refresh_deliveries_when_delivery_methods_stale_at_has_future_date(
    mocked_list_shipping_methods,
    mocked_exclude_shipping_methods,
    mocked_fetch_shipping_methods,
    api_client,
    checkout_with_item,
    address,
    checkout_delivery,
):
    # given
    checkout = checkout_with_item
    existing_delivery = checkout_delivery(checkout)

    checkout.shipping_address = address
    checkout.assigned_delivery = existing_delivery
    checkout.delivery_methods_stale_at = timezone.now() + datetime.timedelta(minutes=5)
    checkout.save()

    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = api_client.post_graphql(DELIVERY_OPTIONS_CALCULATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["deliveryOptionsCalculate"]

    # then
    assert not data["errors"]
    assert len(data["deliveries"]) == 1

    existing_delivery.refresh_from_db()
    assert existing_delivery.is_valid
    assert data["deliveries"][0]["shippingMethod"]["name"] == existing_delivery.name
    assert CheckoutDelivery.objects.filter(checkout=checkout).count() == 1
    assert mocked_fetch_shipping_methods.called
    assert mocked_list_shipping_methods.called
    assert mocked_exclude_shipping_methods.called


@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping.excluded_shipping_methods_for_checkout",
    wraps=excluded_shipping_methods_for_checkout,
)
@mock.patch(
    "saleor.checkout.webhooks.list_shipping_methods.list_shipping_methods_for_checkout",
    wraps=list_shipping_methods_for_checkout,
)
def test_when_refreshed_delivery_has_different_details(
    mocked_list_shipping_methods,
    mocked_exclude_shipping_methods,
    api_client,
    checkout_with_item,
    address,
    checkout_delivery,
):
    # given
    checkout = checkout_with_item
    assigned_delivery = checkout_delivery(checkout)
    checkout.assigned_delivery = assigned_delivery
    checkout.shipping_address = address
    checkout.save()

    expected_name = assigned_delivery.name
    assigned_delivery.name = "PreviousName"
    assigned_delivery.save()

    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = api_client.post_graphql(DELIVERY_OPTIONS_CALCULATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["deliveryOptionsCalculate"]

    # then
    refreshed_delivery = CheckoutDelivery.objects.exclude(id=assigned_delivery.id).get()
    assigned_delivery.refresh_from_db()
    assert not assigned_delivery.is_valid
    assert (
        assigned_delivery.built_in_shipping_method_id
        == refreshed_delivery.built_in_shipping_method_id
    )
    assert refreshed_delivery.is_valid

    assert not data["errors"]
    assert len(data["deliveries"]) == 1
    assert data["deliveries"][0]["id"] == graphene.Node.to_global_id(
        "CheckoutDelivery", refreshed_delivery.pk
    )
    assert data["deliveries"][0]["shippingMethod"]["name"] == expected_name

    checkout.refresh_from_db()
    assert checkout.assigned_delivery_id == assigned_delivery.id
    assert mocked_list_shipping_methods.called
    assert mocked_exclude_shipping_methods.called


@mock.patch(
    "saleor.graphql.shipping.mutations.delivery_options_calculate.fetch_shipping_methods_for_checkout",
    wraps=fetch_shipping_methods_for_checkout,
)
@mock.patch(
    "saleor.checkout.webhooks.exclude_shipping.excluded_shipping_methods_for_checkout",
    wraps=excluded_shipping_methods_for_checkout,
)
@mock.patch(
    "saleor.checkout.webhooks.list_shipping_methods.list_shipping_methods_for_checkout",
    wraps=list_shipping_methods_for_checkout,
)
def test_refresh_deliveries_when_assigned_delivery_is_none(
    mocked_list_shipping_methods,
    mocked_exclude_shipping_methods,
    mocked_fetch_shipping_methods,
    api_client,
    checkout_with_item,
    address,
    checkout_delivery,
):
    # given
    checkout = checkout_with_item
    existing_delivery = checkout_delivery(checkout)

    checkout.shipping_address = address
    checkout.delivery_methods_stale_at = timezone.now() + datetime.timedelta(minutes=5)
    checkout.save(update_fields=["shipping_address", "delivery_methods_stale_at"])

    assert not checkout.assigned_delivery

    variables = {"id": to_global_id_or_none(checkout)}

    # when
    response = api_client.post_graphql(DELIVERY_OPTIONS_CALCULATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["deliveryOptionsCalculate"]

    # then
    assert not data["errors"]
    assert len(data["deliveries"]) == 1

    checkout.refresh_from_db()
    assert not checkout.assigned_delivery

    existing_delivery.refresh_from_db()
    assert existing_delivery.is_valid
    assert data["deliveries"][0]["shippingMethod"]["name"] == existing_delivery.name
    assert CheckoutDelivery.objects.filter(checkout=checkout).count() == 1
    assert mocked_fetch_shipping_methods.called
    assert mocked_list_shipping_methods.called
    assert mocked_exclude_shipping_methods.called
