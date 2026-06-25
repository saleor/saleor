import datetime

import graphene
import pytest
from django.utils import timezone

from ......warehouse.models import Allocation, Reservation, Stock, Warehouse
from .....tests.utils import get_graphql_content
from .shared import PRODUCT_VARIANTS_WHERE_QUERY


@pytest.mark.parametrize(
    ("where", "indexes"),
    [
        ({"stockAvailability": "OUT_OF_STOCK"}, [0, 1]),
        ({"stockAvailability": "IN_STOCK"}, [2]),
        ({"stockAvailability": None}, []),
    ],
)
def test_variants_filter_by_stock_availability(
    where, indexes, api_client, product_list, channel_USD
):
    # given
    # ``product_list`` yields 3 products with a single, in-stock variant each.
    variants = [prod.variants.first() for prod in product_list]
    # make the first two variants out of stock by zeroing their stock quantity
    Stock.objects.filter(product_variant__in=variants[:2]).update(quantity=0)

    variables = {"channel": channel_USD.slug, "where": where}

    # when
    response = api_client.post_graphql(PRODUCT_VARIANTS_WHERE_QUERY, variables)
    content = get_graphql_content(response)

    # then
    nodes = content["data"]["productVariants"]["edges"]
    returned_ids = {node["node"]["id"] for node in nodes}
    expected_ids = {
        graphene.Node.to_global_id("ProductVariant", variants[index].id)
        for index in indexes
    }
    assert returned_ids == expected_ids


def test_variants_filter_by_stock_availability_respects_allocations(
    api_client, product_list, order_line, channel_USD
):
    # given
    variants = [prod.variants.first() for prod in product_list]
    # fully allocate the stock of the first variant -> out of stock
    allocated_variant = variants[0]
    stock = allocated_variant.stocks.first()
    Allocation.objects.create(
        order_line=order_line, stock=stock, quantity_allocated=stock.quantity
    )

    variables = {
        "channel": channel_USD.slug,
        "where": {"stockAvailability": "IN_STOCK"},
    }

    # when
    response = api_client.post_graphql(PRODUCT_VARIANTS_WHERE_QUERY, variables)
    content = get_graphql_content(response)

    # then
    returned_ids = {
        node["node"]["id"] for node in content["data"]["productVariants"]["edges"]
    }
    allocated_id = graphene.Node.to_global_id("ProductVariant", allocated_variant.id)
    in_stock_id = graphene.Node.to_global_id("ProductVariant", variants[1].id)
    assert allocated_id not in returned_ids
    assert in_stock_id in returned_ids


@pytest.mark.parametrize(
    ("reserved_delta", "expected_in_stock"),
    [
        # active reservation consumes the available quantity
        (datetime.timedelta(minutes=5), False),
        # expired reservation is ignored
        (datetime.timedelta(minutes=-5), True),
    ],
)
def test_variants_filter_by_stock_availability_respects_reservations(
    reserved_delta,
    expected_in_stock,
    api_client,
    product_with_two_variants,
    checkout_line,
    channel_USD,
):
    # given
    variants = list(product_with_two_variants.variants.all().order_by("pk"))
    reserved_variant = variants[0]
    stock = reserved_variant.stocks.first()
    Reservation.objects.create(
        checkout_line=checkout_line,
        stock=stock,
        quantity_reserved=stock.quantity,
        reserved_until=timezone.now() + reserved_delta,
    )

    variables = {
        "where": {"stockAvailability": "IN_STOCK"},
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(PRODUCT_VARIANTS_WHERE_QUERY, variables)
    content = get_graphql_content(response)

    # then
    returned_ids = {
        node["node"]["id"] for node in content["data"]["productVariants"]["edges"]
    }
    reserved_variant_id = graphene.Node.to_global_id(
        "ProductVariant", reserved_variant.id
    )
    assert (reserved_variant_id in returned_ids) is expected_in_stock


@pytest.mark.parametrize(
    ("quantity_input", "warehouse_indexes", "variant_indexes"),
    [
        # aggregated over all warehouses: v1=100, v2=35, v3=30
        ({"lte": 40}, [], [1, 2]),
        ({"gte": 50}, [], [0]),
        ({"gte": 10, "lte": 30}, [], [2]),
        ({"gte": 1000}, [], []),
        ({"lte": None, "gte": None}, [], []),
        # scoped to a single warehouse, any quantity
        (None, [1], [1]),
        (None, [2], [0, 1, 2]),
    ],
)
def test_variants_filter_by_stocks(
    quantity_input,
    warehouse_indexes,
    variant_indexes,
    api_client,
    product_with_single_variant,
    product_with_two_variants,
    warehouse,
    channel_USD,
):
    # given
    v1 = product_with_single_variant.variants.first()
    v2, v3 = product_with_two_variants.variants.all().order_by("pk")
    variants = [v1, v2, v3]

    # reset fixture-provided stocks for a deterministic setup
    Stock.objects.filter(product_variant__in=variants).delete()

    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second-warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    third_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    third_warehouse.slug = "third-warehouse"
    third_warehouse.pk = None
    third_warehouse.save()

    warehouses = [warehouse, second_warehouse, third_warehouse]
    warehouse_ids = [
        graphene.Node.to_global_id("Warehouse", warehouses[index].pk)
        for index in warehouse_indexes
    ]

    Stock.objects.bulk_create(
        [
            Stock(warehouse=third_warehouse, product_variant=v1, quantity=100),
            Stock(warehouse=second_warehouse, product_variant=v2, quantity=10),
            Stock(warehouse=third_warehouse, product_variant=v2, quantity=25),
            Stock(warehouse=third_warehouse, product_variant=v3, quantity=30),
        ]
    )

    variables = {
        "where": {
            "stocks": {"quantity": quantity_input, "warehouseIds": warehouse_ids}
        },
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(PRODUCT_VARIANTS_WHERE_QUERY, variables)
    content = get_graphql_content(response)

    # then
    returned_ids = {
        node["node"]["id"] for node in content["data"]["productVariants"]["edges"]
    }
    expected_ids = {
        graphene.Node.to_global_id("ProductVariant", variants[index].id)
        for index in variant_indexes
    }
    assert returned_ids == expected_ids


def test_variants_filter_by_none_as_stocks(
    api_client, product_with_single_variant, channel_USD
):
    # given
    variables = {
        "where": {"stocks": None},
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(PRODUCT_VARIANTS_WHERE_QUERY, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["productVariants"]["edges"] == []
