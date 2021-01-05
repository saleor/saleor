import datetime

import pytest

from ....product.models import Collection, CollectionChannelListing
from ...channel.filters import LACK_OF_CHANNEL_IN_FILTERING_MSG
from ...channel.sorters import LACK_OF_CHANNEL_IN_SORTING_MSG
from ...tests.utils import assert_graphql_error_with_message, get_graphql_content


@pytest.fixture
def collections_for_sorting_with_channels(channel_USD, channel_PLN):
    collections = Collection.objects.bulk_create(
        [
            Collection(name="Collection1", slug="collection1"),
            Collection(name="Collection2", slug="collection2"),
            Collection(name="Collection3", slug="collection3"),
            Collection(name="Collection4", slug="collection4"),
            Collection(name="Collection5", slug="collection5"),
        ]
    )
    CollectionChannelListing.objects.bulk_create(
        [
            CollectionChannelListing(
                collection=collections[0],
                publication_date=None,
                is_published=True,
                channel=channel_USD,
            ),
            CollectionChannelListing(
                collection=collections[1],
                publication_date=None,
                is_published=False,
                channel=channel_USD,
            ),
            CollectionChannelListing(
                collection=collections[2],
                publication_date=datetime.date(2004, 1, 1),
                is_published=False,
                channel=channel_USD,
            ),
            CollectionChannelListing(
                collection=collections[3],
                publication_date=datetime.date(2003, 1, 1),
                is_published=False,
                channel=channel_USD,
            ),
            # second channel
            CollectionChannelListing(
                collection=collections[0],
                publication_date=None,
                is_published=False,
                channel=channel_PLN,
            ),
            CollectionChannelListing(
                collection=collections[1],
                publication_date=None,
                is_published=True,
                channel=channel_PLN,
            ),
            CollectionChannelListing(
                collection=collections[2],
                publication_date=datetime.date(2002, 1, 1),
                is_published=False,
                channel=channel_PLN,
            ),
            CollectionChannelListing(
                collection=collections[4],
                publication_date=datetime.date(2001, 1, 1),
                is_published=False,
                channel=channel_PLN,
            ),
        ]
    )


QUERY_COLLECTIONS_WITH_SORTING_AND_FILTERING = """
    query ($sortBy: CollectionSortingInput, $filter: CollectionFilterInput){
        collections (
            first: 10, sortBy: $sortBy, filter: $filter
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
    "sort_by",
    [
        {"field": "AVAILABILITY", "direction": "ASC"},
        {"field": "PUBLICATION_DATE", "direction": "DESC"},
    ],
)
def test_collections_with_sorting_and_without_channel(
    sort_by,
    staff_api_client,
    permission_manage_products,
):
    # given
    variables = {"sortBy": sort_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_COLLECTIONS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    assert_graphql_error_with_message(response, LACK_OF_CHANNEL_IN_SORTING_MSG)


@pytest.mark.parametrize(
    "sort_by, collections_order",
    [
        (
            {"field": "AVAILABILITY", "direction": "ASC"},
            ["Collection2", "Collection3", "Collection4", "Collection1", "Collection5"],
        ),
        (
            {"field": "AVAILABILITY", "direction": "DESC"},
            ["Collection5", "Collection1", "Collection4", "Collection3", "Collection2"],
        ),
        (
            {"field": "PUBLICATION_DATE", "direction": "ASC"},
            ["Collection4", "Collection3", "Collection1", "Collection2", "Collection5"],
        ),
        (
            {"field": "PUBLICATION_DATE", "direction": "DESC"},
            ["Collection5", "Collection2", "Collection1", "Collection3", "Collection4"],
        ),
    ],
)
def test_collections_with_sorting_and_channel_USD(
    sort_by,
    collections_order,
    staff_api_client,
    permission_manage_products,
    collections_for_sorting_with_channels,
    channel_USD,
):
    # given
    sort_by["channel"] = channel_USD.slug
    variables = {"sortBy": sort_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_COLLECTIONS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    collections_nodes = content["data"]["collections"]["edges"]
    for index, collection_name in enumerate(collections_order):
        assert collection_name == collections_nodes[index]["node"]["name"]


@pytest.mark.parametrize(
    "sort_by, collections_order",
    [
        (
            {"field": "AVAILABILITY", "direction": "ASC"},
            ["Collection1", "Collection3", "Collection5", "Collection2", "Collection4"],
        ),
        (
            {"field": "AVAILABILITY", "direction": "DESC"},
            ["Collection4", "Collection2", "Collection5", "Collection3", "Collection1"],
        ),
        (
            {"field": "PUBLICATION_DATE", "direction": "ASC"},
            ["Collection5", "Collection3", "Collection1", "Collection2", "Collection4"],
        ),
        (
            {"field": "PUBLICATION_DATE", "direction": "DESC"},
            ["Collection4", "Collection2", "Collection1", "Collection3", "Collection5"],
        ),
    ],
)
def test_collections_with_sorting_and_channel_PLN(
    sort_by,
    collections_order,
    staff_api_client,
    permission_manage_products,
    collections_for_sorting_with_channels,
    channel_PLN,
):
    # given
    sort_by["channel"] = channel_PLN.slug
    variables = {"sortBy": sort_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_COLLECTIONS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    collections_nodes = content["data"]["collections"]["edges"]

    for index, collection_name in enumerate(collections_order):
        assert collection_name == collections_nodes[index]["node"]["name"]


@pytest.mark.parametrize(
    "sort_by",
    [
        {"field": "AVAILABILITY", "direction": "ASC"},
        {"field": "PUBLICATION_DATE", "direction": "ASC"},
    ],
)
def test_collections_with_sorting_and_not_existing_channel_asc(
    sort_by,
    staff_api_client,
    permission_manage_products,
    collections_for_sorting_with_channels,
    channel_USD,
):
    # given
    collections_order = [
        "Collection1",
        "Collection2",
        "Collection3",
        "Collection4",
        "Collection5",
    ]
    sort_by["channel"] = "Not-existing"
    variables = {"sortBy": sort_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_COLLECTIONS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    collections_nodes = content["data"]["collections"]["edges"]
    for index, collection_name in enumerate(collections_order):
        assert collection_name == collections_nodes[index]["node"]["name"]


@pytest.mark.parametrize(
    "sort_by",
    [
        {"field": "AVAILABILITY", "direction": "DESC"},
        {"field": "PUBLICATION_DATE", "direction": "DESC"},
    ],
)
def test_collections_with_sorting_and_not_existing_channel_desc(
    sort_by,
    staff_api_client,
    permission_manage_products,
    collections_for_sorting_with_channels,
    channel_USD,
):
    collections_order = [
        "Collection5",
        "Collection4",
        "Collection3",
        "Collection2",
        "Collection1",
    ]
    # given
    sort_by["channel"] = "Not-existing"
    variables = {"sortBy": sort_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_COLLECTIONS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    collections_nodes = content["data"]["collections"]["edges"]
    for index, collection_name in enumerate(collections_order):
        assert collection_name == collections_nodes[index]["node"]["name"]


def test_collections_with_filtering_without_channel(
    staff_api_client, permission_manage_products
):
    # given
    variables = {"filter": {"published": "PUBLISHED"}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_COLLECTIONS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    assert_graphql_error_with_message(response, LACK_OF_CHANNEL_IN_FILTERING_MSG)


@pytest.mark.parametrize(
    "filter_by, collections_count",
    [({"published": "PUBLISHED"}, 1), ({"published": "HIDDEN"}, 3)],
)
def test_collections_with_filtering_with_channel_USD(
    filter_by,
    collections_count,
    staff_api_client,
    permission_manage_products,
    collections_for_sorting_with_channels,
    channel_USD,
):
    # given
    filter_by["channel"] = channel_USD.slug
    variables = {"filter": filter_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_COLLECTIONS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    collections_nodes = content["data"]["collections"]["edges"]
    assert len(collections_nodes) == collections_count


@pytest.mark.parametrize(
    "filter_by, collections_count",
    [({"published": "PUBLISHED"}, 1), ({"published": "HIDDEN"}, 3)],
)
def test_collections_with_filtering_with_channel_PLN(
    filter_by,
    collections_count,
    staff_api_client,
    permission_manage_products,
    collections_for_sorting_with_channels,
    channel_PLN,
):
    # given
    filter_by["channel"] = channel_PLN.slug
    variables = {"filter": filter_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_COLLECTIONS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    collections_nodes = content["data"]["collections"]["edges"]
    assert len(collections_nodes) == collections_count


@pytest.mark.parametrize(
    "filter_by",
    [{"published": "PUBLISHED"}, {"published": "HIDDEN"}],
)
def test_collections_with_filtering_and_not_existing_channel(
    filter_by,
    staff_api_client,
    permission_manage_products,
    collections_for_sorting_with_channels,
    channel_USD,
):
    # given
    filter_by["channel"] = "Not-existing"
    variables = {"filter": filter_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_COLLECTIONS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    collections_nodes = content["data"]["collections"]["edges"]
    assert len(collections_nodes) == 0
