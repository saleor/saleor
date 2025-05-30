import graphene
import pytest

from .....product.models import ProductVariant
from .....warehouse.models import Stock
from ....tests.utils import get_graphql_content

PRODUCT_VARIANTS_WHERE_QUERY = """
    query($where: ProductVariantWhereInput!, $channel: String) {
      productVariants(first: 10, where: $where, channel: $channel) {
        edges {
          node {
            id
            name
            sku
          }
        }
      }
    }
"""


def test_product_variant_filter_by_ids(api_client, product_variant_list, channel_USD):
    # given
    ids = [
        graphene.Node.to_global_id("ProductVariant", variant.pk)
        for variant in product_variant_list[:2]
    ]
    variables = {"channel": channel_USD.slug, "where": {"AND": [{"ids": ids}]}}

    # when
    response = api_client.post_graphql(PRODUCT_VARIANTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    variants = data["data"]["productVariants"]["edges"]
    assert len(variants) == 2
    returned_slugs = {node["node"]["sku"] for node in variants}
    assert returned_slugs == {
        product_variant_list[0].sku,
        product_variant_list[1].sku,
    }


def test_product_variant_filter_by_none_as_ids(
    api_client, product_variant_list, channel_USD
):
    # given
    variables = {"channel": channel_USD.slug, "where": {"AND": [{"ids": None}]}}

    # when
    response = api_client.post_graphql(PRODUCT_VARIANTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    variants = data["data"]["productVariants"]["edges"]
    assert len(variants) == 0


def test_product_variant_filter_by_ids_empty_list(
    api_client, product_variant_list, channel_USD
):
    # given
    variables = {"channel": channel_USD.slug, "where": {"AND": [{"ids": []}]}}

    # when
    response = api_client.post_graphql(PRODUCT_VARIANTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    variants = data["data"]["productVariants"]["edges"]
    assert len(variants) == 0


@pytest.mark.parametrize(
    "stocks_to_create",
    [[], [("1", 0), ("2", 1), ("4", 1)]],
)
def test_product_variant_where_in_stock(
    api_client,
    product_variant_list,
    channel_USD,
    stocks_to_create,
    shipping_zones_with_warehouses,
):
    # given
    warehouse = shipping_zones_with_warehouses[0].warehouses.first()
    channel_USD.warehouses.add(warehouse)
    channel_USD.save()
    Stock.objects.all().delete()
    Stock.objects.bulk_create(
        [
            Stock(
                product_variant=ProductVariant.objects.filter(sku=sku).first(),
                quantity=quantity,
                warehouse=warehouse,
            )
            for sku, quantity in stocks_to_create
        ]
    )
    variables = {
        "channel": channel_USD.slug,
        "where": {"stockAvailability": "IN_STOCK"},
    }

    # when
    response = api_client.post_graphql(PRODUCT_VARIANTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    variants = data["data"]["productVariants"]["edges"]

    positive_stock_variants = [
        sku for sku, quantity in stocks_to_create if quantity > 0
    ]
    assert [variant["node"]["sku"] for variant in variants] == positive_stock_variants


@pytest.mark.parametrize(
    "stocks_to_create",
    [[], [("1", 0), ("2", 1), ("4", 1)]],
)
def test_product_variant_where_out_of_stock(
    api_client,
    product_variant_list,
    channel_USD,
    stocks_to_create,
    shipping_zones_with_warehouses,
):
    # given
    warehouse = shipping_zones_with_warehouses[0].warehouses.first()
    channel_USD.warehouses.add(warehouse)
    channel_USD.save()
    Stock.objects.all().delete()
    Stock.objects.bulk_create(
        [
            Stock(
                product_variant=ProductVariant.objects.filter(sku=sku).first(),
                quantity=quantity,
                warehouse=warehouse,
            )
            for sku, quantity in stocks_to_create
        ]
    )
    variables = {
        "channel": channel_USD.slug,
        "where": {"stockAvailability": "OUT_OF_STOCK"},
    }

    # when
    response = api_client.post_graphql(PRODUCT_VARIANTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    variants = data["data"]["productVariants"]["edges"]

    positive_stock_variants = [
        sku for sku, quantity in stocks_to_create if quantity > 0
    ]
    out_of_stock_variants = (
        ProductVariant.objects.exclude(sku__in=positive_stock_variants)
        .filter(channel_listings__channel=channel_USD)
        .values_list("sku", flat=True)
    )
    assert {variant["node"]["sku"] for variant in variants} == set(
        out_of_stock_variants
    )
