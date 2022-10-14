import graphene
import pytest

from ....product.models import Category, Product, ProductChannelListing
from ....warehouse.models import Allocation, Stock, Warehouse
from ...tests.utils import get_graphql_content


@pytest.fixture
def categories_for_filtering():
    return Category.objects.bulk_create(
        [
            Category(
                name="Category1", slug="category1", lft=0, rght=0, tree_id=0, level=0
            ),
            Category(
                name="Category2", slug="category2", lft=1, rght=2, tree_id=1, level=0
            ),
            Category(
                name="Category3", slug="category3", lft=1, rght=2, tree_id=2, level=0
            ),
        ]
    )


QUERY_CATEGORIES_WITH_FILTERING = """
    query (
        $filter: CategoryFilterInput
    ){
        categories (
            first: 10, filter: $filter
        ) {
            edges {
                node {
                    name
                    slug
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "filter_by, categories_count",
    [
        ({"slugs": ["category1"]}, 1),
        ({"slugs": ["category2", "category3"]}, 2),
        ({"slugs": []}, 3),
    ],
)
def test_categories_with_filtering(
    filter_by,
    categories_count,
    staff_api_client,
    categories_for_filtering,
):
    # given
    variables = {"filter": filter_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_CATEGORIES_WITH_FILTERING,
        variables,
    )

    # then
    content = get_graphql_content(response)
    categories_nodes = content["data"]["categories"]["edges"]
    assert len(categories_nodes) == categories_count


GET_FILTERED_PRODUCTS_CATEGORY_QUERY = """
    query ($channel: String, $filters: ProductFilterInput){
      categories(first: 5) {
        edges {
          node {
            id
            name
            products(first: 5, channel: $channel, filter: $filters) {
              edges {
                node {
                  id
                  name
                  channel
                  attributes {
                    attribute {
                      choices(first: 10) {
                        edges {
                          node {
                            slug
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """


def test_category_filter_products_by_channel(
    user_api_client,
    product_list,
    channel_USD,
    channel_PLN,
):
    ProductChannelListing.objects.filter(
        product=product_list[0],
    ).update(channel=channel_PLN)

    variables = {
        "channel": channel_USD.slug,
        "filters": {"channel": channel_PLN.slug},
    }

    response = user_api_client.post_graphql(
        GET_FILTERED_PRODUCTS_CATEGORY_QUERY, variables
    )

    content = get_graphql_content(response)
    for edge in content["data"]["categories"]["edges"]:
        for inner_edge in edge["node"]["products"]["edges"]:
            assert inner_edge["node"]["channel"] == channel_USD.slug


def test_category_filter_products_by_is_published(
    user_api_client,
    product_list_published,
    channel_USD,
):
    """
    Products created with published collections and expect to see no products after
    filter.
    """

    variables = {
        "channel": channel_USD.slug,
        "filters": {"isPublished": False},
    }

    response = user_api_client.post_graphql(
        GET_FILTERED_PRODUCTS_CATEGORY_QUERY, variables
    )

    content = get_graphql_content(response)
    for edge in content["data"]["categories"]["edges"]:
        assert edge["node"]["products"]["edges"] == []


def test_category_filter_products_by_attributes(
    user_api_client,
    product_with_two_variants,
    product_with_multiple_values_attributes,
    published_collection,
    channel_USD,
):
    published_collection.products.set(
        [product_with_two_variants, product_with_multiple_values_attributes]
    )

    variables = {
        "channel": channel_USD.slug,
        "filters": {"attributes": [{"slug": "modes", "values": ["eco"]}]},
    }

    response = user_api_client.post_graphql(
        GET_FILTERED_PRODUCTS_CATEGORY_QUERY, variables
    )

    content = get_graphql_content(response)
    products_data = content["data"]["categories"]["edges"][0]["node"]["products"][
        "edges"
    ]
    product = products_data[0]["node"]

    _, _id = graphene.Node.from_global_id(product["id"])

    assert len(products_data) == 1
    assert product["id"] == graphene.Node.to_global_id(
        "Product", product_with_multiple_values_attributes.pk
    )
    assert product["attributes"] == [
        {
            "attribute": {
                "choices": {
                    "edges": [
                        {"node": {"slug": "eco"}},
                        {"node": {"slug": "power"}},
                    ]
                }
            }
        }
    ]


def test_category_filter_products_by_stock_availability(
    user_api_client,
    product_list,
    order_line,
    channel_USD,
):
    for product in product_list:
        stock = product.variants.first().stocks.first()
        Allocation.objects.create(
            order_line=order_line, stock=stock, quantity_allocated=stock.quantity
        )
    product = product_list[0]
    product.variants.first().channel_listings.filter(channel=channel_USD).update(
        price_amount=None
    )
    variables = {
        "channel": channel_USD.slug,
        "filters": {"stockAvailability": "OUT_OF_STOCK"},
    }
    response = user_api_client.post_graphql(
        GET_FILTERED_PRODUCTS_CATEGORY_QUERY, variables
    )

    content = get_graphql_content(response)

    products_data = content["data"]["categories"]["edges"][0]["node"]["products"][
        "edges"
    ]
    product_id = graphene.Node.to_global_id("Product", product_list[1].id)
    second_product_id = graphene.Node.to_global_id("Product", product_list[2].id)

    assert len(products_data) == 2
    assert products_data[0]["node"]["id"] == product_id
    assert products_data[0]["node"]["name"] == product_list[1].name
    assert products_data[1]["node"]["id"] == second_product_id
    assert products_data[1]["node"]["name"] == product_list[2].name


@pytest.mark.parametrize(
    "quantity_input, warehouse_indexes, count, indexes_of_products_in_result",
    [
        ({"lte": "80", "gte": "20"}, [1, 2], 1, [1]),
        ({"lte": "120", "gte": "40"}, [1, 2], 1, [0]),
        ({"gte": "10"}, [1], 1, [1]),
        ({"gte": "110"}, [2], 0, []),
        (None, [1], 1, [1]),
        (None, [2], 2, [0, 1]),
        ({"lte": "210", "gte": "70"}, [], 1, [0]),
        ({"lte": "90"}, [], 1, [1]),
        ({"lte": "90", "gte": "75"}, [], 0, []),
    ],
)
def test_category_filter_products_by_stocks(
    quantity_input,
    warehouse_indexes,
    count,
    indexes_of_products_in_result,
    user_api_client,
    product_with_single_variant,
    product_with_two_variants,
    warehouse,
    channel_USD,
):
    product1 = product_with_single_variant
    product2 = product_with_two_variants
    products = [product1, product2]

    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    third_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    third_warehouse.slug = "third warehouse"
    third_warehouse.pk = None
    third_warehouse.save()

    warehouses = [warehouse, second_warehouse, third_warehouse]
    warehouse_pks = [
        graphene.Node.to_global_id("Warehouse", warehouses[index].pk)
        for index in warehouse_indexes
    ]

    Stock.objects.bulk_create(
        [
            Stock(
                warehouse=third_warehouse,
                product_variant=product1.variants.first(),
                quantity=100,
            ),
            Stock(
                warehouse=second_warehouse,
                product_variant=product2.variants.first(),
                quantity=10,
            ),
            Stock(
                warehouse=third_warehouse,
                product_variant=product2.variants.first(),
                quantity=25,
            ),
            Stock(
                warehouse=third_warehouse,
                product_variant=product2.variants.last(),
                quantity=30,
            ),
        ]
    )
    variables = {
        "filters": {
            "stocks": {"quantity": quantity_input, "warehouseIds": warehouse_pks}
        },
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(
        GET_FILTERED_PRODUCTS_CATEGORY_QUERY, variables
    )
    content = get_graphql_content(response)
    products_data = content["data"]["categories"]["edges"][0]["node"]["products"][
        "edges"
    ]
    product_ids = {
        graphene.Node.to_global_id("Product", products[index].pk)
        for index in indexes_of_products_in_result
    }

    assert len(products_data) == count
    assert {node["node"]["id"] for node in products_data} == product_ids


@pytest.mark.parametrize("is_published", [(True)])
def test_category_filter_products_search_by_sku(
    is_published,
    user_api_client,
    product_with_two_variants,
    product_with_default_variant,
    channel_USD,
):
    ProductChannelListing.objects.filter(
        product=product_with_default_variant, channel=channel_USD
    ).update(is_published=is_published)

    variables = {
        "filters": {"search": "1234"},
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(
        GET_FILTERED_PRODUCTS_CATEGORY_QUERY, variables
    )

    content = get_graphql_content(response)
    product_id = graphene.Node.to_global_id("Product", product_with_default_variant.id)
    products = content["data"]["categories"]["edges"][0]["node"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == product_id
    assert products[0]["node"]["name"] == product_with_default_variant.name


def test_category_filter_products_by_price(
    user_api_client,
    product_list,
    permission_manage_products,
    channel_USD,
):
    product = product_list[0]
    product.variants.first().channel_listings.filter().update(price_amount=None)
    second_product_id = graphene.Node.to_global_id("Product", product_list[1].id)
    third_product_id = graphene.Node.to_global_id("Product", product_list[2].id)
    variables = {
        "filters": {"price": {"gte": 9, "lte": 31}, "channel": channel_USD.slug},
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(
        GET_FILTERED_PRODUCTS_CATEGORY_QUERY, variables
    )
    content = get_graphql_content(response)
    products = content["data"]["categories"]["edges"][0]["node"]["products"]["edges"]

    assert len(products) == 2
    assert products[0]["node"]["id"] == second_product_id
    assert products[1]["node"]["id"] == third_product_id


def test_category_filter_products_by_ids(
    user_api_client,
    product_list,
    channel_USD,
):
    product_ids = [
        graphene.Node.to_global_id("Product", product.id) for product in product_list
    ][:2]
    variables = {
        "filters": {"ids": product_ids},
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(
        GET_FILTERED_PRODUCTS_CATEGORY_QUERY, variables
    )

    # then
    content = get_graphql_content(response)
    products = content["data"]["categories"]["edges"][0]["node"]["products"]["edges"]

    assert len(products) == 2
    assert [node["node"]["id"] for node in products] == product_ids


GET_SORTED_PRODUCTS_CATEGORY_QUERY = """
query ($channel: String, $sortBy: ProductOrder, $filters: ProductFilterInput) {
  categories(first:10) {
    edges {
      node {
        id
        products(first: 10, channel: $channel, sortBy: $sortBy, filter: $filters) {
          edges {
            node {
              id
            }
          }
        }
      }
    }
  }
}
"""


def test_category_sort_products_by_name(
    user_api_client, published_collection, product_list, channel_USD
):
    for product in product_list:
        published_collection.products.add(product)

    variables = {
        "sortBy": {"direction": "DESC", "field": "NAME"},
        "filters": {"channel": channel_USD.slug},
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(
        GET_SORTED_PRODUCTS_CATEGORY_QUERY, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["categories"]["edges"][0]["node"]["products"]["edges"]

    assert [node["node"]["id"] for node in data] == [
        graphene.Node.to_global_id("Product", product.pk)
        for product in Product.objects.order_by("-name")
    ]
