import graphene
import pytest

from .....warehouse import WarehouseClickAndCollectOption
from .....warehouse.models import Warehouse
from ....tests.utils import get_graphql_content

QUERY_WAREHOUSES_WITH_FILTERS = """
query Warehouses($filters: WarehouseFilterInput) {
    warehouses(first:100, filter: $filters) {
        totalCount
        edges {
            node {
                id
                name
                companyName
                email
                metadata {
                    key
                    value
                }
            }
        }
    }
}
"""

QUERY_WERHOUSES_WITH_FILTERS_NO_IDS = """
query Warehouses($filters: WarehouseFilterInput) {
    warehouses(first:100, filter: $filters) {
        totalCount
        edges {
            node {
                name
                companyName
                email
            }
        }
    }
}
"""


def test_query_warehouses_with_filters_name(
    staff_api_client, permission_manage_products, warehouse
):
    # given
    variables_exists = {"filters": {"search": "warehouse"}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS,
        variables=variables_exists,
        permissions=[permission_manage_products],
    )

    # then
    content = get_graphql_content(response)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    content_warehouse = content["data"]["warehouses"]["edges"][0]["node"]
    assert content_warehouse["id"] == warehouse_id
    variables_does_not_exists = {"filters": {"search": "Absolutelywrong name"}}
    response1 = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS, variables=variables_does_not_exists
    )
    content1 = get_graphql_content(response1)
    total_count = content1["data"]["warehouses"]["totalCount"]
    assert total_count == 0


def test_query_warehouse_with_filters_email(
    staff_api_client, permission_manage_products, warehouse
):
    # given
    variables_exists = {"filters": {"search": "test"}}

    # when
    response_exists = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS,
        variables=variables_exists,
        permissions=[permission_manage_products],
    )

    # then
    content_exists = get_graphql_content(response_exists)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    content_warehouse = content_exists["data"]["warehouses"]["edges"][0]["node"]
    assert content_warehouse["id"] == warehouse_id

    variable_does_not_exists = {"filters": {"search": "Bad@email.pl"}}
    response_not_exists = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS, variables=variable_does_not_exists
    )
    content_not_exists = get_graphql_content(response_not_exists)
    total_count = content_not_exists["data"]["warehouses"]["totalCount"]
    assert total_count == 0


def test_query_warehouse_with_filters_by_ids(
    staff_api_client, permission_manage_products, warehouse, warehouse_no_shipping_zone
):
    # given
    warehouse_ids = [
        graphene.Node.to_global_id("Warehouse", warehouse.id),
        graphene.Node.to_global_id("Warehouse", warehouse_no_shipping_zone.id),
    ]
    variables_exists = {"filters": {"ids": warehouse_ids}}

    # when
    response_exists = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS,
        variables=variables_exists,
        permissions=[permission_manage_products],
    )

    # then
    content_exists = get_graphql_content(response_exists)

    content_warehouses = content_exists["data"]["warehouses"]["edges"]
    for content_warehouse in content_warehouses:
        assert content_warehouse["node"]["id"] in warehouse_ids
    assert content_exists["data"]["warehouses"]["totalCount"] == 2


def test_query_warehouse_with_filters_by_id(
    staff_api_client, permission_manage_products, warehouse, warehouse_no_shipping_zone
):
    # given
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    variables_exists = {"filters": {"ids": [warehouse_id]}}

    # when
    response_exists = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS,
        variables=variables_exists,
        permissions=[permission_manage_products],
    )

    # then
    content_exists = get_graphql_content(response_exists)

    content_warehouses = content_exists["data"]["warehouses"]["edges"]
    assert content_warehouses[0]["node"]["id"] == warehouse_id
    assert content_exists["data"]["warehouses"]["totalCount"] == 1


@pytest.mark.parametrize(
    ("graphql_filter", "db_filter"), [("true", True), ("false", False)]
)
def test_query_warehouse_with_filters_by_is_private(
    staff_api_client,
    permission_manage_products,
    warehouses_for_cc,
    graphql_filter,
    db_filter,
):
    # given
    db_count = Warehouse.objects.filter(is_private=db_filter).count()
    variables_exists = {"filters": {"isPrivate": graphql_filter}}

    # when
    response_exists = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS,
        variables=variables_exists,
        permissions=[permission_manage_products],
    )

    # then
    content_exists = get_graphql_content(response_exists)

    assert content_exists["data"]["warehouses"]["totalCount"] == db_count


@pytest.mark.parametrize(
    ("db_option", "graphql_option"),
    [
        (WarehouseClickAndCollectOption.DISABLED, "DISABLED"),
        (WarehouseClickAndCollectOption.ALL_WAREHOUSES, "ALL"),
        (WarehouseClickAndCollectOption.LOCAL_STOCK, "LOCAL"),
    ],
)
def test_query_warehouse_with_filters_by_click_and_collect_option(
    staff_api_client,
    permission_manage_products,
    warehouses_for_cc,
    db_option,
    graphql_option,
):
    # given
    db_count = Warehouse.objects.filter(click_and_collect_option=db_option).count()
    variables_exists = {"filters": {"clickAndCollectOption": graphql_option}}

    # when
    response_exists = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS,
        variables=variables_exists,
        permissions=[permission_manage_products],
    )

    # then
    content_exists = get_graphql_content(response_exists)
    assert content_exists["data"]["warehouses"]["totalCount"] == db_count


def test_query_warehouses_with_filters_and_no_id(
    staff_api_client, permission_manage_products, warehouse
):
    # given
    variables_exists = {"filters": {"search": "test"}}

    # when
    response_exists = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS,
        variables=variables_exists,
        permissions=[permission_manage_products],
    )

    # then
    content_exists = get_graphql_content(response_exists)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    content_warehouse = content_exists["data"]["warehouses"]["edges"][0]["node"]
    assert content_warehouse["id"] == warehouse_id

    variable_does_not_exists = {"filters": {"search": "Bad@email.pl"}}
    response_not_exists = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS, variables=variable_does_not_exists
    )
    content_not_exists = get_graphql_content(response_not_exists)
    total_count = content_not_exists["data"]["warehouses"]["totalCount"]
    assert total_count == 0


def test_query_warehouses_with_filters_by_channels(
    staff_api_client,
    permission_manage_products,
    warehouses,
    warehouse_JPY,
    channel_PLN,
    channel_JPY,
):
    # given
    warehouses[1].channels.add(channel_PLN)

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.id)
        for channel in [channel_PLN, channel_JPY]
    ]

    variables_exists = {"filters": {"channels": channel_ids}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS,
        variables=variables_exists,
        permissions=[permission_manage_products],
    )

    # then
    content = get_graphql_content(response)
    warehouses_data = content["data"]["warehouses"]["edges"]
    assert len(warehouses_data) == 2
    assert {warehouse_data["node"]["name"] for warehouse_data in warehouses_data} == {
        warehouses[1].name,
        warehouse_JPY.name,
    }


def test_query_warehouses_with_filters_by_channels_no_warehouse_returned(
    staff_api_client, permission_manage_products, warehouses, channel_PLN
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)

    variables_exists = {"filters": {"channels": [channel_id]}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS,
        variables=variables_exists,
        permissions=[permission_manage_products],
    )

    # then
    content = get_graphql_content(response)
    warehouses_data = content["data"]["warehouses"]["edges"]
    assert not warehouses_data


@pytest.mark.parametrize(
    ("filter_by", "pages_count"),
    [
        ({"slugs": ["warehouse1", "warehouse2"]}, 2),
        ({"slugs": []}, 2),
    ],
)
def test_query_warehouses_with_filtering(
    filter_by, pages_count, staff_api_client, permission_manage_products, warehouses
):
    # given
    variables = {"filter": filter_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS,
        variables,
        permissions=[permission_manage_products],
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["warehouses"]["edges"]
    assert len(pages_nodes) == pages_count


def test_query_warehouses_with_filters_metadata(
    staff_api_client, permission_manage_products, warehouse
):
    # given
    warehouse.metadata = {"foo": "bar"}
    warehouse.save(update_fields=["metadata"])
    metadata_filter = {"filters": {"metadata": [{"key": "foo"}]}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_WITH_FILTERS,
        variables=metadata_filter,
        permissions=[permission_manage_products],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["warehouses"]
    total_count = data["totalCount"]
    assert not total_count == 0
    assert data["edges"][0]["node"]["metadata"][0]["key"] == "foo"
    assert data["edges"][0]["node"]["metadata"][0]["value"] == "bar"
