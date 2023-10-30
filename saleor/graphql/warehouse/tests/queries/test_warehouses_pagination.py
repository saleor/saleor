import graphene
import pytest

from .....warehouse.models import Warehouse
from ....tests.utils import get_graphql_content


@pytest.fixture
def warehouses_for_pagination(db, address):
    return Warehouse.objects.bulk_create(
        [
            Warehouse(
                name="Warehouse1",
                address=address,
                slug="w1",
            ),
            Warehouse(
                name="WarehouseWarehouse1",
                address=address,
                slug="ww1",
            ),
            Warehouse(
                name="WarehouseWarehouse2",
                address=address,
                slug="ww2",
            ),
            Warehouse(
                name="Warehouse2",
                address=address,
                slug="w2",
            ),
            Warehouse(
                name="Warehouse3",
                address=address,
                slug="w3",
            ),
        ]
    )


QUERY_WAREHOUSES_PAGINATION = """
    query (
        $first: Int, $last: Int, $after: String, $before: String,
        $sortBy: WarehouseSortingInput, $filter: WarehouseFilterInput
    ){
        warehouses(
            first: $first, last: $last, after: $after, before: $before,
            sortBy: $sortBy, filter: $filter
        ) {
            edges {
                node {
                    name
                }
            }
            pageInfo{
                startCursor
                endCursor
                hasNextPage
                hasPreviousPage
            }
        }
    }
"""


@pytest.mark.parametrize(
    ("sort_by", "warehouses_order"),
    [
        (
            {"field": "NAME", "direction": "ASC"},
            ["Warehouse1", "Warehouse2", "Warehouse3"],
        ),
        (
            {"field": "NAME", "direction": "DESC"},
            ["WarehouseWarehouse2", "WarehouseWarehouse1", "Warehouse3"],
        ),
    ],
)
def test_warehouses_pagination_with_sorting(
    sort_by,
    warehouses_order,
    staff_api_client,
    permission_manage_products,
    warehouses_for_pagination,
):
    # given
    page_size = 3

    variables = {"first": page_size, "after": None, "sortBy": sort_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_PAGINATION, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    warehouses_nodes = content["data"]["warehouses"]["edges"]
    assert warehouses_order[0] == warehouses_nodes[0]["node"]["name"]
    assert warehouses_order[1] == warehouses_nodes[1]["node"]["name"]
    assert warehouses_order[2] == warehouses_nodes[2]["node"]["name"]
    assert len(warehouses_nodes) == page_size


@pytest.mark.parametrize(
    ("filter_by", "warehouses_order"),
    [
        (
            {"search": "WarehouseWarehouse"},
            ["WarehouseWarehouse2", "WarehouseWarehouse1"],
        ),
        ({"search": "Warehouse1"}, ["WarehouseWarehouse1", "Warehouse1"]),
    ],
)
def test_warehouses_pagination_with_filtering(
    filter_by,
    warehouses_order,
    staff_api_client,
    permission_manage_products,
    warehouses_for_pagination,
):
    # given
    page_size = 2

    variables = {"first": page_size, "after": None, "filter": filter_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_PAGINATION, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    warehouses_nodes = content["data"]["warehouses"]["edges"]
    assert warehouses_order[0] == warehouses_nodes[0]["node"]["name"]
    assert warehouses_order[1] == warehouses_nodes[1]["node"]["name"]
    assert len(warehouses_nodes) == page_size


def test_warehouses_pagination_with_filtering_by_id(
    staff_api_client,
    permission_manage_products,
    warehouses_for_pagination,
):
    # given
    page_size = 2
    warehouses_order = ["WarehouseWarehouse2", "WarehouseWarehouse1"]
    warehouses_ids = [
        graphene.Node.to_global_id("Warehouse", warehouse.pk)
        for warehouse in warehouses_for_pagination
    ]
    filter_by = {"ids": warehouses_ids}

    variables = {"first": page_size, "after": None, "filter": filter_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_WAREHOUSES_PAGINATION, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    warehouses_nodes = content["data"]["warehouses"]["edges"]
    assert warehouses_order[0] == warehouses_nodes[0]["node"]["name"]
    assert warehouses_order[1] == warehouses_nodes[1]["node"]["name"]
    assert len(warehouses_nodes) == page_size
