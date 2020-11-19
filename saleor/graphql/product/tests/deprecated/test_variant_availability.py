import warnings

import graphene

from .....channel.utils import DEPRECATION_WARNING_MESSAGE
from ....tests.utils import get_graphql_content

QUERY_DEPRECATED_VARIANT_AVAILABILITY = """
    query variantAvailability($id: ID!) {
        productVariant(id: $id) {
            isAvailable
            stockQuantity
            quantityAvailable
        }
    }
"""


def test_variant_availability_without_inventory_tracking(
    api_client, variant_without_inventory_tracking, settings
):
    variant = variant_without_inventory_tracking
    variables = {"id": graphene.Node.to_global_id("ProductVariant", variant.pk)}
    with warnings.catch_warnings(record=True) as warns:
        response = api_client.post_graphql(
            QUERY_DEPRECATED_VARIANT_AVAILABILITY, variables
        )
        content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["isAvailable"] is True
    assert variant_data["stockQuantity"] == settings.MAX_CHECKOUT_LINE_QUANTITY
    assert variant_data["quantityAvailable"] == settings.MAX_CHECKOUT_LINE_QUANTITY
    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )


def test_variant_availability(api_client, variant_with_many_stocks, settings):
    variant = variant_with_many_stocks
    variables = {"id": graphene.Node.to_global_id("ProductVariant", variant.pk)}
    with warnings.catch_warnings(record=True) as warns:
        response = api_client.post_graphql(
            QUERY_DEPRECATED_VARIANT_AVAILABILITY, variables
        )
        content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["isAvailable"] is True
    assert variant_data["stockQuantity"] == 7
    assert variant_data["quantityAvailable"] == 7
    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )


def test_variant_availability_without_inventory_tracking_without_stocks(
    api_client, variant_without_inventory_tracking, settings
):
    variant = variant_without_inventory_tracking
    variant.stocks.all().delete()
    variables = {"id": graphene.Node.to_global_id("ProductVariant", variant.pk)}
    with warnings.catch_warnings(record=True) as warns:
        response = api_client.post_graphql(
            QUERY_DEPRECATED_VARIANT_AVAILABILITY, variables
        )
        content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["isAvailable"] is True
    assert variant_data["stockQuantity"] == settings.MAX_CHECKOUT_LINE_QUANTITY
    assert variant_data["quantityAvailable"] == settings.MAX_CHECKOUT_LINE_QUANTITY
    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )


def test_variant_availability_without_stocks(api_client, variant, settings):
    variables = {"id": graphene.Node.to_global_id("ProductVariant", variant.pk)}
    with warnings.catch_warnings(record=True) as warns:
        response = api_client.post_graphql(
            QUERY_DEPRECATED_VARIANT_AVAILABILITY, variables
        )
        content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["isAvailable"] is False
    assert variant_data["stockQuantity"] == 0
    assert variant_data["quantityAvailable"] == 0
    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )
