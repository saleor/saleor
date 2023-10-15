import graphene
import pytest
from freezegun import freeze_time

from ....product.models import (
    Category,
    Product,
    ProductChannelListing,
    ProductVariantChannelListing,
)
from ....warehouse.models import Stock, Warehouse
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


@pytest.mark.parametrize(
    "filter_by, categories_count",
    [
        ({"updatedAt": {"gte": "2012-01-14T10:59:00+00:00"}}, 3),
        ({"updatedAt": {"lte": "2012-01-14T12:00:05+00:00"}}, 3),
        ({"updatedAt": {"gte": "2012-01-14T11:29:00+00:00"}}, 2),
        ({"updatedAt": {"lte": "2012-01-14T11:31:00+00:00"}}, 2),
        ({"updatedAt": {"gte": "2012-01-14T12:01:00+00:00"}}, 0),
        ({"updatedAt": {"lte": "2012-01-14T10:59:00+00:00"}}, 0),
        ({"updatedAt": {}}, 3),
        (
            {
                "updatedAt": {
                    "lte": "2012-01-14T12:01:00+00:00",
                    "gte": "2012-01-14T11:59:00+00:00",
                },
            },
            1,
        ),
        (
            {
                "updatedAt": {
                    "lte": "2012-01-14T12:01:00+00:00",
                    "gte": "2012-01-14T11:29:00+00:00",
                },
            },
            2,
        ),
    ],
)
def test_order_query_with_filter_updated_at(
    filter_by,
    categories_count,
    staff_api_client,
):
    # given
    with freeze_time("2012-01-14 11:00:00"):
        Category.objects.create(
            name="Category1",
            slug="category1",
            lft=0,
            rght=0,
            tree_id=2,
            level=0,
        )

    with freeze_time("2012-01-14 11:30:00"):
        Category.objects.create(
            name="Category2",
            slug="category2",
            lft=1,
            rght=2,
            tree_id=1,
            level=0,
        )

    with freeze_time("2012-01-14 12:00:00"):
        Category.objects.create(
            name="Category3",
            slug="category3",
            lft=1,
            rght=2,
            tree_id=2,
            level=0,
        )

    variables = {"filter": filter_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_CATEGORIES_WITH_FILTERING,
        variables,
    )

    content = get_graphql_content(response)
    categories_nodes = content["data"]["categories"]["edges"]
    # then
    assert len(categories_nodes) == categories_count


GET_FILTERED_PRODUCTS_CATEGORY_QUERY = """
query ($id: ID!, $channel: String, $filters: ProductFilterInput) {
  category(id: $id) {
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
"""


@pytest.mark.parametrize(
    "channel, filter_channel, count, indexes_of_products_in_result",
    [
        ("channel_USD.slug", "channel_USD.slug", 2, [1, 2]),
        ("channel_USD.slug", "channel_PLN.slug", 2, [1, 2]),
        ("channel_PLN.slug", "channel_USD.slug", 1, [0]),
        ("channel_PLN.slug", "channel_PLN.slug", 1, [0]),
    ],
)
def test_category_filter_products_by_channel(
    channel,
    filter_channel,
    count,
    indexes_of_products_in_result,
    user_api_client,
    category,
    product_list,
    channel_USD,
    channel_PLN,
):
    # given
    first_product = product_list[0]

    ProductChannelListing.objects.filter(
        product=first_product,
    ).update(channel=channel_PLN)

    ProductVariantChannelListing.objects.filter(
        variant=first_product.variants.first(),
    ).update(channel=channel_PLN)

    product_ids = [
        graphene.Node.to_global_id("Product", product_list[index].pk)
        for index in indexes_of_products_in_result
    ]

    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": eval(channel),
        "filters": {"channel": eval(filter_channel)},
    }

    # when
    response = user_api_client.post_graphql(
        GET_FILTERED_PRODUCTS_CATEGORY_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    products = content["data"]["category"]["products"]["edges"]
    assert len(products) == count
    assert [product["node"]["id"] for product in products] == product_ids


@pytest.mark.parametrize(
    "is_published, count, indexes_of_products_in_result",
    [
        (True, 2, [1, 2]),
        (False, 1, [0]),
    ],
)
def test_category_filter_products_by_is_published(
    is_published,
    count,
    indexes_of_products_in_result,
    staff_api_client,
    permission_manage_products,
    category,
    product_list_published,
    channel_USD,
):
    # given
    ProductChannelListing.objects.filter(
        product=product_list_published[0],
    ).update(is_published=False)

    product_ids = [
        graphene.Node.to_global_id("Product", product_list_published[index].pk)
        for index in indexes_of_products_in_result
    ]

    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
        "filters": {"isPublished": is_published},
    }

    # when
    response = staff_api_client.post_graphql(
        GET_FILTERED_PRODUCTS_CATEGORY_QUERY,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    products = content["data"]["category"]["products"]["edges"]
    assert len(products) == count
    assert [product["node"]["id"] for product in products] == product_ids


def test_category_filter_products_by_multiple_attributes(
    user_api_client,
    category,
    product_with_two_variants,
    product_with_multiple_values_attributes,
    channel_USD,
):
    # given
    product_with_multiple_values_attributes_id = graphene.Node.to_global_id(
        "Product", product_with_multiple_values_attributes.pk
    )

    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
        "filters": {"attributes": [{"slug": "modes", "values": ["eco"]}]},
    }

    # when
    response = user_api_client.post_graphql(
        GET_FILTERED_PRODUCTS_CATEGORY_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    products = content["data"]["category"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == product_with_multiple_values_attributes_id
    assert products[0]["node"]["attributes"] == [
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


@pytest.mark.parametrize(
    "stock_availability, count, indexes_of_products_in_result",
    [
        ("OUT_OF_STOCK", 2, [1, 2]),
        ("IN_STOCK", 1, [0]),
    ],
)
def test_category_filter_products_by_stock_availability(
    stock_availability,
    count,
    indexes_of_products_in_result,
    user_api_client,
    category,
    product_list,
    channel_USD,
):
    # given
    for index, product in enumerate(product_list):
        if index == 0:
            continue
        stock = product.variants.first().stocks.first()
        stock.quantity_allocated = stock.quantity
        stock.quantity = 0
        stock.save(update_fields=["quantity", "quantity_allocated"])

    product_ids = [
        graphene.Node.to_global_id("Product", product_list[index].pk)
        for index in indexes_of_products_in_result
    ]

    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
        "filters": {"stockAvailability": stock_availability},
    }

    # when
    response = user_api_client.post_graphql(
        GET_FILTERED_PRODUCTS_CATEGORY_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    products = content["data"]["category"]["products"]["edges"]

    assert len(products) == count
    assert [product["node"]["id"] for product in products] == product_ids


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
    category,
    product_with_single_variant,
    product_with_two_variants,
    warehouse,
    channel_USD,
):
    # given
    first_product = product_with_single_variant
    second_product = product_with_two_variants
    products = [first_product, second_product]

    first_warehouse = warehouse

    second_warehouse = Warehouse.objects.get(pk=first_warehouse.pk)
    second_warehouse.slug = "second-warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    third_warehouse = Warehouse.objects.get(pk=first_warehouse.pk)
    third_warehouse.slug = "third-warehouse"
    third_warehouse.pk = None
    third_warehouse.save()

    warehouses = [first_warehouse, second_warehouse, third_warehouse]
    warehouse_ids = [
        graphene.Node.to_global_id("Warehouse", warehouses[index].pk)
        for index in warehouse_indexes
    ]

    Stock.objects.bulk_create(
        [
            Stock(
                warehouse=third_warehouse,
                product_variant=first_product.variants.first(),
                quantity=100,
            ),
            Stock(
                warehouse=second_warehouse,
                product_variant=second_product.variants.first(),
                quantity=10,
            ),
            Stock(
                warehouse=third_warehouse,
                product_variant=second_product.variants.first(),
                quantity=25,
            ),
            Stock(
                warehouse=third_warehouse,
                product_variant=second_product.variants.last(),
                quantity=30,
            ),
        ]
    )

    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
        "filters": {
            "stocks": {"quantity": quantity_input, "warehouseIds": warehouse_ids}
        },
    }

    # when
    response = user_api_client.post_graphql(
        GET_FILTERED_PRODUCTS_CATEGORY_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    products_result = content["data"]["category"]["products"]["edges"]
    product_ids = {
        graphene.Node.to_global_id("Product", products[index].pk)
        for index in indexes_of_products_in_result
    }

    assert len(products_result) == count
    assert {node["node"]["id"] for node in products_result} == product_ids


@pytest.mark.parametrize(
    "is_published, count, indexes_of_products_in_result",
    [
        (True, 1, [1]),
        (False, 0, []),
    ],
)
def test_category_filter_products_search_by_sku(
    is_published,
    count,
    indexes_of_products_in_result,
    user_api_client,
    category,
    product_with_two_variants,
    product_with_default_variant,
    channel_USD,
):
    # given
    products = [product_with_two_variants, product_with_default_variant]

    ProductChannelListing.objects.filter(
        product=product_with_default_variant, channel=channel_USD
    ).update(is_published=is_published)

    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
        "filters": {"search": "1234"},
    }

    # when
    response = user_api_client.post_graphql(
        GET_FILTERED_PRODUCTS_CATEGORY_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    products_result = content["data"]["category"]["products"]["edges"]
    product_ids = {
        graphene.Node.to_global_id("Product", products[index].pk)
        for index in indexes_of_products_in_result
    }

    assert len(products_result) == count
    assert {node["node"]["id"] for node in products_result} == product_ids


def test_category_filter_products_by_price(
    user_api_client,
    category,
    product_list,
    permission_manage_products,
    channel_USD,
):
    # given
    product_list[0].variants.first().channel_listings.filter().update(price_amount=None)
    second_product_id = graphene.Node.to_global_id("Product", product_list[1].pk)

    # when
    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
        "filters": {"price": {"gte": 5, "lte": 25}, "channel": channel_USD.slug},
    }

    response = user_api_client.post_graphql(
        GET_FILTERED_PRODUCTS_CATEGORY_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    products = content["data"]["category"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == second_product_id


def test_category_filter_products_by_ids(
    user_api_client,
    category,
    product_list,
    channel_USD,
):
    # given
    product_ids = [
        graphene.Node.to_global_id("Product", product.pk) for product in product_list
    ][:2]

    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
        "filters": {"ids": product_ids},
    }

    # when
    response = user_api_client.post_graphql(
        GET_FILTERED_PRODUCTS_CATEGORY_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    products = content["data"]["category"]["products"]["edges"]

    assert len(products) == 2
    assert [node["node"]["id"] for node in products] == product_ids


GET_SORTED_PRODUCTS_CATEGORY_QUERY = """
query (
    $id: ID!,
    $channel: String,
    $filters: ProductFilterInput,
    $sortBy: ProductOrder,
    $where: ProductWhereInput,
){
  category(id: $id) {
    id
    products(
        first: 10, channel: $channel, sortBy: $sortBy, filter: $filters, where: $where
    ) {
      edges {
        node {
          id
          slug
        }
      }
    }
  }
}
"""


def test_category_sort_products_by_name(
    user_api_client,
    category,
    product_list,
    channel_USD,
):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
        "filters": {"channel": channel_USD.slug},
        "sortBy": {"direction": "DESC", "field": "NAME"},
    }

    # when
    response = user_api_client.post_graphql(
        GET_SORTED_PRODUCTS_CATEGORY_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    products = content["data"]["category"]["products"]["edges"]

    assert [node["node"]["id"] for node in products] == [
        graphene.Node.to_global_id("Product", product.pk)
        for product in Product.objects.order_by("-name")
    ]


def test_category_products_where_filter(
    user_api_client,
    category,
    product_list,
    channel_USD,
):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
        "where": {
            "AND": [
                {"slug": {"oneOf": ["test-product-a", "test-product-b"]}},
                {"price": {"range": {"gte": 15}}},
            ]
        },
    }

    # when
    response = user_api_client.post_graphql(
        GET_SORTED_PRODUCTS_CATEGORY_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    products = content["data"]["category"]["products"]["edges"]
    assert len(products) == 1
    assert products[0]["node"]["slug"] == "test-product-b"


CATEGORY_WHERE_QUERY = """
    query($where: CategoryWhereInput!) {
      categories(first: 10, where: $where) {
        edges {
          node {
            id
            slug
          }
        }
      }
    }
"""


def test_categories_where_by_ids(api_client, category_list):
    # given
    ids = [
        graphene.Node.to_global_id("Category", category.pk)
        for category in category_list[:2]
    ]
    variables = {"where": {"AND": [{"ids": ids}]}}

    # when
    response = api_client.post_graphql(CATEGORY_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    categories = data["data"]["categories"]["edges"]
    assert len(categories) == 2
    returned_slugs = {node["node"]["slug"] for node in categories}
    assert returned_slugs == {
        category_list[0].slug,
        category_list[1].slug,
    }


def test_categories_where_by_none_as_ids(api_client, category_list):
    # given
    variables = {"where": {"ids": None}}

    # when
    response = api_client.post_graphql(CATEGORY_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    categories = data["data"]["categories"]["edges"]
    assert len(categories) == 0


def test_categories_where_by_ids_empty_list(api_client, category_list):
    # given
    variables = {"where": {"AND": [{"ids": []}]}}

    # when
    response = api_client.post_graphql(CATEGORY_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    categories = data["data"]["categories"]["edges"]
    assert len(categories) == 0
