"""Regression tests for the SQL shape of channel-dependent and category filters.

Resolving the channel through a `channel_channel.slug` subquery inside every filter,
and the category subtree through an MPTT range subquery, hides the real row counts
from the Postgres planner. It then picks a plan that reads the whole catalogue on every
page of a paginated `products` query. These tests pin the SQL shape that avoids that:
a literal `channel_id = <id>` and a literal `category_id IN (...)`.
"""

import datetime

import graphene
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from .....product.models import Product, ProductChannelListing
from ....core.connection import where_filter_qs
from ....tests.utils import get_graphql_content
from ...filters.product import ProductFilter, ProductWhere
from ...filters.product_helpers import filter_products_by_categories

PRODUCTS_FILTER_QUERY = """
    query ($filter: ProductFilterInput!, $channel: String) {
      products(first: 10, filter: $filter, channel: $channel) {
        edges {
          node {
            id
          }
        }
      }
    }
"""

PRODUCTS_WHERE_QUERY = """
    query ($where: ProductWhereInput!, $channel: String) {
      products(first: 10, where: $where, channel: $channel) {
        edges {
          node {
            id
          }
        }
      }
    }
"""

CATEGORY_PRODUCTS_QUERY = """
    query ($id: ID!, $channel: String) {
      category(id: $id) {
        products(first: 10, channel: $channel) {
          edges {
            node {
              id
            }
          }
        }
      }
    }
"""

PUBLISHED_AT = datetime.datetime(1999, 1, 1, tzinfo=datetime.UTC)
PUBLISHED_FROM = "2000-01-01T00:00:00+00:00"

CHANNEL_FILTER_INPUTS = [
    {"isPublished": True},
    {"isAvailable": True},
    {"isVisibleInListing": True},
    {"publishedFrom": PUBLISHED_FROM},
    {"availableFrom": PUBLISHED_FROM},
    {"price": {"gte": 1}},
]

CHANNEL_WHERE_INPUTS = [
    {"isPublished": True},
    {"isAvailable": True},
    {"isVisibleInListing": True},
    {"publishedFrom": PUBLISHED_FROM},
    {"availableFrom": PUBLISHED_FROM},
    {"price": {"range": {"gte": 1}}},
]


@pytest.fixture
def published_product_list(product_list, channel_USD):
    """Products with a publication date, so `publishedFrom` has something to match."""
    ProductChannelListing.objects.filter(
        product__in=product_list, channel=channel_USD
    ).update(published_at=PUBLISHED_AT)
    return product_list


def get_products_select(captured_queries: list[dict]) -> str:
    """Return the single paginated SELECT over `product_product`."""
    selects = [
        query["sql"]
        for query in captured_queries
        if query["sql"].startswith("SELECT")
        and 'FROM "product_product"' in query["sql"]
        and "LIMIT" in query["sql"]
    ]
    assert len(selects) == 1
    return selects[0]


def count_category_queries(captured_queries: list[dict]) -> int:
    return sum(
        1 for query in captured_queries if 'FROM "product_category"' in query["sql"]
    )


def get_product_ids(content: dict, *path: str) -> set[str]:
    data = content["data"]
    for key in path:
        data = data[key]
    return {edge["node"]["id"] for edge in data["edges"]}


def to_product_ids(products) -> set[str]:
    return {graphene.Node.to_global_id("Product", product.pk) for product in products}


@pytest.mark.parametrize("filter_input", CHANNEL_FILTER_INPUTS)
def test_filter_compares_channel_id_literal(
    filter_input, api_client, published_product_list, channel_USD
):
    # given
    variables = {"channel": channel_USD.slug, "filter": filter_input}

    # when
    with CaptureQueriesContext(connection) as queries:
        response = api_client.post_graphql(PRODUCTS_FILTER_QUERY, variables)

    # then
    content = get_graphql_content(response)
    assert get_product_ids(content, "products") == to_product_ids(
        published_product_list
    )
    products_select = get_products_select(queries.captured_queries)
    assert "channel_channel" not in products_select
    assert f'"channel_id" = {channel_USD.pk}' in products_select


@pytest.mark.parametrize("where_input", CHANNEL_WHERE_INPUTS)
def test_where_compares_channel_id_literal(
    where_input, api_client, published_product_list, channel_USD
):
    # given
    variables = {"channel": channel_USD.slug, "where": where_input}

    # when
    with CaptureQueriesContext(connection) as queries:
        response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    assert get_product_ids(content, "products") == to_product_ids(
        published_product_list
    )
    products_select = get_products_select(queries.captured_queries)
    assert "channel_channel" not in products_select
    assert f'"channel_id" = {channel_USD.pk}' in products_select


def test_filter_resolves_channel_once_per_filterset(
    published_product_list, channel_USD, django_assert_num_queries
):
    # given
    filterset = ProductFilter(
        {
            "channel": channel_USD.slug,
            "is_published": True,
            "is_available": True,
            "is_visible_in_listing": True,
            "published_from": PUBLISHED_FROM,
            "available_from": PUBLISHED_FROM,
            "price": {"gte": 1},
        },
        queryset=Product.objects.all(),
    )

    # when
    with django_assert_num_queries(1):
        queryset = filterset.qs

    # then
    assert filterset.channel_id == channel_USD.pk
    assert "channel_channel" not in str(queryset.query)
    assert set(queryset) == set(published_product_list)


def test_where_resolves_channel_once_per_filterset(
    published_product_list, channel_USD, django_assert_num_queries
):
    # given
    filterset = ProductWhere(
        {
            "channel": channel_USD.slug,
            "is_published": True,
            "is_available": True,
            "is_visible_in_listing": True,
            "published_from": PUBLISHED_FROM,
            "available_from": PUBLISHED_FROM,
            "price": {"range": {"gte": 1}},
        },
        queryset=Product.objects.all(),
    )

    # when
    with django_assert_num_queries(1):
        queryset = filterset.qs

    # then
    assert filterset.channel_id == channel_USD.pk
    assert "channel_channel" not in str(queryset.query)
    assert set(queryset) == set(published_product_list)


@pytest.mark.parametrize(
    ("filter_input", "expects_all_products"),
    [
        ({"isPublished": True}, False),
        ({"isPublished": False}, False),
        ({"isAvailable": True}, False),
        ({"isAvailable": False}, False),
        ({"isVisibleInListing": True}, False),
        ({"publishedFrom": PUBLISHED_FROM}, False),
        ({"availableFrom": PUBLISHED_FROM}, False),
        ({"price": {"gte": 1}}, False),
        # minimal price is the one channel filter that ignores an unknown channel
        ({"minimalPrice": {"gte": 1}}, True),
    ],
)
def test_filter_with_nonexistent_channel(
    filter_input,
    expects_all_products,
    staff_api_client,
    permission_manage_products,
    published_product_list,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variables = {"filter": {"channel": "non-existent-channel", **filter_input}}

    # when
    response = staff_api_client.post_graphql(PRODUCTS_FILTER_QUERY, variables)

    # then
    content = get_graphql_content(response)
    expected_products = published_product_list if expects_all_products else []
    assert get_product_ids(content, "products") == to_product_ids(expected_products)


@pytest.mark.parametrize(
    "filter_input",
    [
        {"isPublished": True},
        {"isVisibleInListing": True},
        {"price": {"gte": 1}},
    ],
)
def test_filter_excludes_products_listed_only_in_another_channel(
    filter_input,
    staff_api_client,
    permission_manage_products,
    product_list_with_variants_many_channel,
    channel_USD,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    product_in_channel = product_list_with_variants_many_channel[0]
    assert product_in_channel.channel_listings.get().channel_id == channel_USD.pk
    variables = {"filter": {"channel": channel_USD.slug, **filter_input}}

    # when
    response = staff_api_client.post_graphql(PRODUCTS_FILTER_QUERY, variables)

    # then
    content = get_graphql_content(response)
    assert get_product_ids(content, "products") == to_product_ids([product_in_channel])


@pytest.mark.parametrize(
    ("where_input", "expects_all_products"),
    [
        ({"is_published": True}, False),
        ({"is_available": True}, False),
        ({"is_visible_in_listing": True}, False),
        ({"published_from": PUBLISHED_FROM}, False),
        ({"available_from": PUBLISHED_FROM}, False),
        ({"price": {"range": {"gte": 1}}}, False),
        # minimal price is the one channel filter that ignores an unknown channel
        ({"minimal_price": {"range": {"gte": 1}}}, True),
    ],
)
def test_where_with_nonexistent_channel(
    where_input, expects_all_products, published_product_list
):
    # given
    filterset = ProductWhere(
        {"channel": "non-existent-channel", **where_input},
        queryset=Product.objects.all(),
    )

    # when
    queryset = filterset.qs

    # then
    assert filterset.channel_id is None
    expected_products = published_product_list if expects_all_products else []
    assert set(queryset) == set(expected_products)


@pytest.mark.parametrize(
    ("is_published", "expected_count"),
    [(True, 1), (False, 0)],
)
def test_where_without_channel_in_input_uses_default_channel(
    is_published, expected_count, product, channel_USD
):
    # given
    # Promotion rule predicates evaluate `ProductWhere` outside a GraphQL request,
    # with no channel in the filter input. `filter_qs` then injects the default
    # channel slug, which is the only channel here.
    assert product.channel_listings.get().channel_id == channel_USD.pk

    # when
    queryset = where_filter_qs(
        Product.objects.all(), {}, ProductWhere, {"is_published": is_published}, None
    )

    # then
    sql = str(queryset.query)
    assert "channel_channel" not in sql
    assert f'"channel_id" = {channel_USD.pk}' in sql
    assert list(queryset) == [product] * expected_count


def test_filter_by_categories_uses_literal_descendant_ids(
    staff_api_client, permission_manage_products, categories_tree, channel_USD
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    parent = categories_tree
    child = parent.children.get()
    product_in_child = child.products.get()
    parent_id = graphene.Node.to_global_id("Category", parent.pk)
    variables = {"channel": channel_USD.slug, "filter": {"categories": [parent_id]}}

    # when
    with CaptureQueriesContext(connection) as queries:
        response = staff_api_client.post_graphql(PRODUCTS_FILTER_QUERY, variables)

    # then
    content = get_graphql_content(response)
    assert get_product_ids(content, "products") == to_product_ids([product_in_child])
    products_select = get_products_select(queries.captured_queries)
    assert "product_category" not in products_select
    assert f'"product_product"."category_id" IN ({parent.pk}, {child.pk})' in (
        products_select
    )


def test_where_by_category_uses_literal_descendant_ids(
    staff_api_client, permission_manage_products, categories_tree, channel_USD
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    parent = categories_tree
    child = parent.children.get()
    product_in_child = child.products.get()
    parent_id = graphene.Node.to_global_id("Category", parent.pk)
    variables = {"channel": channel_USD.slug, "where": {"category": {"eq": parent_id}}}

    # when
    with CaptureQueriesContext(connection) as queries:
        response = staff_api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    assert get_product_ids(content, "products") == to_product_ids([product_in_child])
    products_select = get_products_select(queries.captured_queries)
    assert "product_category" not in products_select
    assert f'"product_product"."category_id" IN ({parent.pk}, {child.pk})' in (
        products_select
    )


def test_category_products_uses_literal_descendant_ids(
    staff_api_client, permission_manage_products, categories_tree, channel_USD
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    parent = categories_tree
    child = parent.children.get()
    product_in_child = child.products.get()
    variables = {
        "id": graphene.Node.to_global_id("Category", parent.pk),
        "channel": channel_USD.slug,
    }

    # when
    with CaptureQueriesContext(connection) as queries:
        response = staff_api_client.post_graphql(CATEGORY_PRODUCTS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    assert get_product_ids(content, "category", "products") == to_product_ids(
        [product_in_child]
    )
    products_select = get_products_select(queries.captured_queries)
    assert "product_category" not in products_select
    assert f'"product_product"."category_id" IN ({parent.pk}, {child.pk})' in (
        products_select
    )
    # The category itself and its descendants.
    assert count_category_queries(queries.captured_queries) == 2


def test_category_products_of_leaf_category_skips_descendants_query(
    staff_api_client, permission_manage_products, categories_tree, channel_USD
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    leaf = categories_tree.children.get()
    assert leaf.is_leaf_node() is True
    product_in_leaf = leaf.products.get()
    variables = {
        "id": graphene.Node.to_global_id("Category", leaf.pk),
        "channel": channel_USD.slug,
    }

    # when
    with CaptureQueriesContext(connection) as queries:
        response = staff_api_client.post_graphql(CATEGORY_PRODUCTS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    assert get_product_ids(content, "category", "products") == to_product_ids(
        [product_in_leaf]
    )
    products_select = get_products_select(queries.captured_queries)
    assert "product_category" not in products_select
    assert f'"product_product"."category_id" IN ({leaf.pk})' in products_select
    # Only the category itself is loaded.
    assert count_category_queries(queries.captured_queries) == 1


def test_filter_products_by_categories_fetches_descendants_in_one_query(
    categories_tree, django_assert_num_queries
):
    # given
    parent = categories_tree
    child = parent.children.get()
    product_in_child = child.products.get()

    # when
    with django_assert_num_queries(1):
        queryset = filter_products_by_categories(Product.objects.all(), [parent.pk])

    # then
    assert f'"product_product"."category_id" IN ({parent.pk}, {child.pk})' in str(
        queryset.query
    )
    assert list(queryset) == [product_in_child]


@pytest.mark.parametrize("category_ids", [[], [-1]])
def test_filter_products_by_categories_without_matching_category(
    category_ids, product_list, django_assert_num_queries
):
    # when
    with django_assert_num_queries(1):
        queryset = filter_products_by_categories(Product.objects.all(), category_ids)

    # then
    assert queryset.exists() is False
