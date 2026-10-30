import datetime

import graphene
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from freezegun import freeze_time

from .....product.models import Product, ProductChannelListing
from ....tests.utils import get_graphql_content

QUERY_PRODUCTS_TOTAL_COUNT = """
    query (
        $channel: String
        $where: ProductWhereInput
        $filter: ProductFilterInput
    ) {
        products(first: 100, channel: $channel, where: $where, filter: $filter) {
            totalCount
            edges {
                node {
                    id
                }
            }
        }
    }
"""

QUERY_PRODUCTS_PAGE_TOTAL_COUNT = """
    query ($channel: String, $after: String) {
        products(first: 1, after: $after, channel: $channel) {
            totalCount
            pageInfo {
                endCursor
            }
        }
    }
"""


def _query_total_count(client, variables):
    content = get_graphql_content(
        client.post_graphql(QUERY_PRODUCTS_TOTAL_COUNT, variables)
    )
    return content["data"]["products"]["totalCount"]


def test_total_count_served_from_cache_within_timeout(
    api_client, product_list_published, channel_USD, total_count_cache
):
    # given
    variables = {"channel": channel_USD.slug}
    initial_count = len(product_list_published)
    content = get_graphql_content(
        api_client.post_graphql(QUERY_PRODUCTS_TOTAL_COUNT, variables)
    )
    assert content["data"]["products"]["totalCount"] == initial_count
    product_list_published[0].delete()

    # when
    response = api_client.post_graphql(QUERY_PRODUCTS_TOTAL_COUNT, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["products"]["totalCount"] == initial_count
    assert len(content["data"]["products"]["edges"]) == initial_count - 1


def test_total_count_cache_keyed_by_filters(
    api_client, product_list_published, channel_USD, total_count_cache
):
    # given
    product = product_list_published[0]
    content = get_graphql_content(
        api_client.post_graphql(
            QUERY_PRODUCTS_TOTAL_COUNT, {"channel": channel_USD.slug}
        )
    )
    assert content["data"]["products"]["totalCount"] == len(product_list_published)
    variables = {
        "channel": channel_USD.slug,
        "where": {"ids": [graphene.Node.to_global_id("Product", product.pk)]},
    }

    # when
    response = api_client.post_graphql(QUERY_PRODUCTS_TOTAL_COUNT, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["products"]["totalCount"] == 1


def test_total_count_cache_keyed_by_full_json_filter_value(
    api_client, product_list_published, channel_USD, total_count_cache
):
    # given
    metadata_key = "external_reference_id"
    shared_prefix = "A" * 40
    first_value = f"{shared_prefix}-1"
    second_value = f"{shared_prefix}-2"
    first_product, second_product, third_product = product_list_published
    first_product.store_value_in_metadata({metadata_key: first_value})
    second_product.store_value_in_metadata({metadata_key: first_value})
    third_product.store_value_in_metadata({metadata_key: second_value})
    Product.objects.bulk_update(
        [first_product, second_product, third_product], ["metadata"]
    )

    def query_total_count(value):
        variables = {
            "channel": channel_USD.slug,
            "filter": {"metadata": [{"key": metadata_key, "value": value}]},
        }
        content = get_graphql_content(
            api_client.post_graphql(QUERY_PRODUCTS_TOTAL_COUNT, variables)
        )
        return content["data"]["products"]["totalCount"]

    assert query_total_count(first_value) == 2

    # when
    total_count = query_total_count(second_value)

    # then
    assert total_count == 1


def test_total_count_not_cached_when_timeout_is_zero(
    api_client, product_list_published, channel_USD, total_count_cache, settings
):
    # given
    settings.GRAPHQL_TOTAL_COUNT_CACHE_TIMEOUT = 0
    variables = {"channel": channel_USD.slug}
    initial_count = len(product_list_published)
    content = get_graphql_content(
        api_client.post_graphql(QUERY_PRODUCTS_TOTAL_COUNT, variables)
    )
    assert content["data"]["products"]["totalCount"] == initial_count
    product_list_published[0].delete()

    # when
    response = api_client.post_graphql(QUERY_PRODUCTS_TOTAL_COUNT, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["products"]["totalCount"] == initial_count - 1


@pytest.mark.parametrize(
    ("_case", "staff_first"),
    [
        ("staff warms the cache before an anonymous user", True),
        ("anonymous user warms the cache before staff", False),
    ],
)
def test_total_count_cache_keyed_by_permission_scope(
    _case,
    staff_first,
    api_client,
    staff_api_client,
    permission_manage_products,
    product_list_published,
    channel_USD,
    total_count_cache,
):
    # given
    products = list(product_list_published)
    ProductChannelListing.objects.filter(
        product=products[0], channel=channel_USD
    ).update(is_published=False)
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variables = {"channel": channel_USD.slug}
    staff_count = len(products)
    anonymous_count = len(products) - 1

    if staff_first:
        assert _query_total_count(staff_api_client, variables) == staff_count
    else:
        assert _query_total_count(api_client, variables) == anonymous_count

    # when
    if staff_first:
        total_count = _query_total_count(api_client, variables)
    else:
        total_count = _query_total_count(staff_api_client, variables)

    # then
    expected_count = anonymous_count if staff_first else staff_count
    assert total_count == expected_count


def test_total_count_cache_keyed_by_channel(
    staff_api_client,
    permission_manage_products,
    product_list_published,
    channel_USD,
    channel_PLN,
    total_count_cache,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    assert ProductChannelListing.objects.filter(channel=channel_PLN).exists() is False
    assert _query_total_count(staff_api_client, {"channel": channel_USD.slug}) == len(
        product_list_published
    )

    # when
    total_count = _query_total_count(staff_api_client, {"channel": channel_PLN.slug})

    # then
    assert total_count == 0


def test_total_count_cache_shared_across_pages(
    api_client, product_list_published, channel_USD, total_count_cache
):
    # given
    products = list(product_list_published)
    initial_count = len(products)
    response = api_client.post_graphql(
        QUERY_PRODUCTS_PAGE_TOTAL_COUNT, {"channel": channel_USD.slug}
    )
    first_page = get_graphql_content(response)["data"]["products"]
    assert first_page["totalCount"] == initial_count
    products[-1].delete()
    variables = {
        "channel": channel_USD.slug,
        "after": first_page["pageInfo"]["endCursor"],
    }

    # when
    response = api_client.post_graphql(QUERY_PRODUCTS_PAGE_TOTAL_COUNT, variables)

    # then
    second_page = get_graphql_content(response)["data"]["products"]
    assert second_page["totalCount"] == initial_count


def test_total_count_cache_stores_zero(
    api_client, product_list_published, channel_USD, total_count_cache
):
    # given
    listings = ProductChannelListing.objects.filter(channel=channel_USD)
    listings.update(is_published=False)
    variables = {"channel": channel_USD.slug}
    assert _query_total_count(api_client, variables) == 0
    listings.update(is_published=True)

    # when
    total_count = _query_total_count(api_client, variables)

    # then
    assert total_count == 0


def test_total_count_for_inactive_channel_then_reactivated(
    api_client, product_list_published, channel_USD, total_count_cache
):
    # given
    channel_USD.is_active = False
    channel_USD.save(update_fields=["is_active"])
    variables = {"channel": channel_USD.slug}
    assert _query_total_count(api_client, variables) == 0
    channel_USD.is_active = True
    channel_USD.save(update_fields=["is_active"])

    # when
    total_count = _query_total_count(api_client, variables)

    # then
    assert total_count == len(product_list_published)


def test_total_count_refreshed_after_timeout(
    api_client, product_list_published, channel_USD, total_count_cache, settings
):
    # given
    products = list(product_list_published)
    initial_count = len(products)
    timeout = datetime.timedelta(seconds=settings.GRAPHQL_TOTAL_COUNT_CACHE_TIMEOUT)
    variables = {"channel": channel_USD.slug}

    with freeze_time(timezone.now()) as frozen_time:
        assert _query_total_count(api_client, variables) == initial_count
        products[0].delete()
        frozen_time.tick(timeout - datetime.timedelta(seconds=1))
        assert _query_total_count(api_client, variables) == initial_count

        # when
        frozen_time.tick(datetime.timedelta(seconds=2))
        total_count = _query_total_count(api_client, variables)

    # then
    assert total_count == initial_count - 1


def _count_queries(context):
    return [
        query["sql"] for query in context.captured_queries if "COUNT(" in query["sql"]
    ]


def test_total_count_cache_hit_skips_count_query(
    api_client, product_list_published, channel_USD, total_count_cache
):
    # given
    variables = {"channel": channel_USD.slug}
    with CaptureQueriesContext(connection) as context:
        assert _query_total_count(api_client, variables) == len(product_list_published)
    assert len(_count_queries(context)) == 1

    # when
    with CaptureQueriesContext(connection) as context:
        total_count = _query_total_count(api_client, variables)

    # then
    assert total_count == len(product_list_published)
    assert _count_queries(context) == []
