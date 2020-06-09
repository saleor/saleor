import graphene
from django.test import override_settings

from ...tests.utils import get_graphql_content

COUNTRY_CODE = "US"


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
    response = api_client.post_graphql(QUERY_DEPRECATED_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["isAvailable"] is True
    assert variant_data["stockQuantity"] == settings.MAX_CHECKOUT_LINE_QUANTITY
    assert variant_data["quantityAvailable"] == settings.MAX_CHECKOUT_LINE_QUANTITY


def test_variant_availability(api_client, variant_with_many_stocks, settings):
    variant = variant_with_many_stocks
    variables = {"id": graphene.Node.to_global_id("ProductVariant", variant.pk)}
    response = api_client.post_graphql(QUERY_DEPRECATED_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["isAvailable"] is True
    assert variant_data["stockQuantity"] == 7
    assert variant_data["quantityAvailable"] == 7


def test_variant_availability_without_inventory_tracking_without_stocks(
    api_client, variant_without_inventory_tracking, settings
):
    variant = variant_without_inventory_tracking
    variant.stocks.all().delete()
    variables = {"id": graphene.Node.to_global_id("ProductVariant", variant.pk)}
    response = api_client.post_graphql(QUERY_DEPRECATED_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["isAvailable"] is True
    assert variant_data["stockQuantity"] == settings.MAX_CHECKOUT_LINE_QUANTITY
    assert variant_data["quantityAvailable"] == settings.MAX_CHECKOUT_LINE_QUANTITY


def test_variant_availability_without_stocks(api_client, variant, settings):
    variables = {"id": graphene.Node.to_global_id("ProductVariant", variant.pk)}
    response = api_client.post_graphql(QUERY_DEPRECATED_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["isAvailable"] is False
    assert variant_data["stockQuantity"] == 0
    assert variant_data["quantityAvailable"] == 0


def test_variant_quantity_available_without_country_code(
    api_client, variant_with_many_stocks
):
    query = """
    query variantAvailability($id: ID!) {
        productVariant(id: $id) {
            quantityAvailable
        }
    }
    """
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk)
    }
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["quantityAvailable"] == 7


QUERY_VARIANT_AVAILABILITY = """
    query variantAvailability($id: ID!, $country: CountryCode) {
        productVariant(id: $id) {
            quantityAvailable(countryCode: $country)
        }
    }
"""


def test_variant_quantity_available_with_country_code(
    api_client, variant_with_many_stocks,
):
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "country": COUNTRY_CODE,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["quantityAvailable"] == 7


def test_variant_quantity_available_with_null_as_country_code(
    api_client, variant_with_many_stocks
):
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "country": None,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["quantityAvailable"] == 7


@override_settings(MAX_CHECKOUT_LINE_QUANTITY=15)
def test_variant_quantity_available_with_max(
    api_client, variant_with_many_stocks, settings
):
    stock = variant_with_many_stocks.stocks.first()
    stock.quantity = 16
    stock.save(update_fields=["quantity"])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "country": COUNTRY_CODE,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["quantityAvailable"] == settings.MAX_CHECKOUT_LINE_QUANTITY


def test_variant_quantity_available_without_stocks(
    api_client, variant_with_many_stocks,
):
    variant_with_many_stocks.stocks.all().delete()
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "country": COUNTRY_CODE,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["quantityAvailable"] == 0


def test_variant_quantity_available_with_allocations(
    api_client,
    variant_with_many_stocks,
    order_line_with_allocation_in_many_stocks,
    order_line_with_one_allocation,
):
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "country": COUNTRY_CODE,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["quantityAvailable"] == 3


@override_settings(MAX_CHECKOUT_LINE_QUANTITY=15)
def test_variant_quantity_available_without_inventory_tracking(
    api_client, variant_with_many_stocks, settings
):
    variant_with_many_stocks.track_inventory = False
    variant_with_many_stocks.save(update_fields=["track_inventory"])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "country": COUNTRY_CODE,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["quantityAvailable"] == settings.MAX_CHECKOUT_LINE_QUANTITY


@override_settings(MAX_CHECKOUT_LINE_QUANTITY=15)
def test_variant_quantity_available_without_inventory_tracking_and_stocks(
    api_client, variant, settings
):
    variant.track_inventory = False
    variant.save(update_fields=["track_inventory"])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["quantityAvailable"] == settings.MAX_CHECKOUT_LINE_QUANTITY
