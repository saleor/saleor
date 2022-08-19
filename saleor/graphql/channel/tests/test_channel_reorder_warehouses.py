import uuid

import graphene

from ....channel.error_codes import ChannelErrorCode
from ....warehouse.models import ChannelWarehouse
from ...tests.utils import get_graphql_content

CHANNEL_REORDER_WAREHOUSES = """
    mutation ChannelReorderWarehouses($channelId: ID!, $moves: [ReorderInput!]!) {
        channelReorderWarehouses(channelId: $channelId, moves: $moves) {
            channel {
                id
                warehouses {
                    id
                    slug
                }
            }
            errors {
                field
                code
                message
                warehouses
            }
        }
    }
"""


def test_sort_warehouses_with_channel(
    staff_api_client,
    permission_manage_channels,
    channel_USD,
    warehouses,
    warehouse,
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)

    channel_warehouses = list(channel_USD.channelwarehouse.all())

    assert len(channel_warehouses) == 3

    channel_warehouse_1 = channel_warehouses[0]
    channel_warehouse_2 = channel_warehouses[1]
    channel_warehouse_3 = channel_warehouses[2]

    channel_warehouse_1.sort_order = 0
    channel_warehouse_2.sort_order = 1
    channel_warehouse_3.sort_order = 2

    ChannelWarehouse.objects.bulk_update(channel_warehouses, ["sort_order"])

    warehouse_1_id = graphene.Node.to_global_id(
        "Warehouse", channel_warehouse_1.warehouse_id
    )
    warehouse_2_id = graphene.Node.to_global_id(
        "Warehouse", channel_warehouse_2.warehouse_id
    )
    warehouse_3_id = graphene.Node.to_global_id(
        "Warehouse", channel_warehouse_3.warehouse_id
    )

    variables = {
        "channelId": channel_id,
        "moves": [
            {"id": warehouse_1_id, "sortOrder": +1},
            {"id": warehouse_3_id, "sortOrder": -1},
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_REORDER_WAREHOUSES, variables, permissions=[permission_manage_channels]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["channelReorderWarehouses"]
    errors = data["errors"]
    assert not errors
    warehouses = data["channel"]["warehouses"]
    assert len(warehouses) == 3
    assert warehouses[0]["id"] == warehouse_2_id
    assert warehouses[1]["id"] == warehouse_3_id
    assert warehouses[2]["id"] == warehouse_1_id


def test_sort_warehouses_with_channel_invalid_channel_id(
    staff_api_client, warehouses, channel_USD, permission_manage_channels
):
    # given
    channel_USD.warehouses.add(*warehouses)
    moves = [
        {
            "id": graphene.Node.to_global_id("Warehouse", warehouses[-1].pk),
            "sortOrder": 1,
        }
    ]

    variables = {"channelId": graphene.Node.to_global_id("Channel", -1), "moves": moves}

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_REORDER_WAREHOUSES, variables, permissions=[permission_manage_channels]
    )

    # then
    content = get_graphql_content(response)

    data = content["data"]["channelReorderWarehouses"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "channelId"
    assert errors[0]["code"] == ChannelErrorCode.NOT_FOUND.name


def test_sort_warehouses_with_channel_not_existing_warehouse_ids(
    staff_api_client, warehouses, channel_USD, permission_manage_channels
):
    # given
    channel_USD.warehouses.add(*warehouses)
    invalid_warehouse_id_1 = graphene.Node.to_global_id("Warehouse", uuid.uuid4())
    invalid_warehouse_id_2 = graphene.Node.to_global_id("Warehouse", uuid.uuid4())
    moves = [
        {"id": invalid_warehouse_id_1, "sortOrder": 1},
        {"id": invalid_warehouse_id_2, "sortOrder": 2},
    ]

    variables = {
        "channelId": graphene.Node.to_global_id("Channel", channel_USD.id),
        "moves": moves,
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_REORDER_WAREHOUSES, variables, permissions=[permission_manage_channels]
    )

    # then
    content = get_graphql_content(response)

    data = content["data"]["channelReorderWarehouses"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "moves"
    assert errors[0]["code"] == ChannelErrorCode.NOT_FOUND.name
    assert set(errors[0]["warehouses"]) == {
        invalid_warehouse_id_1,
        invalid_warehouse_id_2,
    }


def test_sort_warehouses_with_channel_not_invalid_warehouse_ids(
    staff_api_client, warehouses, channel_USD, permission_manage_channels
):
    # given
    channel_USD.warehouses.add(*warehouses)
    moves = [
        {"id": graphene.Node.to_global_id("Product", 1), "sortOrder": 1},
        {"id": graphene.Node.to_global_id("Product", 2), "sortOrder": 2},
    ]

    variables = {
        "channelId": graphene.Node.to_global_id("Channel", channel_USD.id),
        "moves": moves,
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_REORDER_WAREHOUSES, variables, permissions=[permission_manage_channels]
    )

    # then
    content = get_graphql_content(response)

    data = content["data"]["channelReorderWarehouses"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "moves"
    assert errors[0]["code"] == ChannelErrorCode.GRAPHQL_ERROR.name
