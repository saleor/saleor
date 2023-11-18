import graphene
import pytest

from ....account.tests.mutations.permission_group.test_permission_group_update import (
    PERMISSION_GROUP_UPDATE_MUTATION,
)
from ....tests.utils import assert_no_permission, get_graphql_content
from ..mutations.test_fulfillment_cancel import CANCEL_FULFILLMENT_MUTATION
from ..mutations.test_order_fulfill import ORDER_FULFILL_MUTATION


@pytest.mark.integration
def test_user_cannot_manage_order_after_losing_access_to_channel(
    staff_api_client,
    superuser_api_client,
    permission_group_manage_orders,
    permission_group_all_perms_all_channels,
    order_with_lines,
    warehouse,
    channel_PLN,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    permission_group_all_perms_all_channels.user_set.add(superuser_api_client.user)
    order = order_with_lines
    order_line_1, order_line_2 = order.lines.all()
    order_id = graphene.Node.to_global_id("Order", order.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    # when
    # fulfill order
    fulfill_order_variables = {
        "order": order_id,
        "input": {
            "lines": [
                {
                    "orderLineId": graphene.Node.to_global_id(
                        "OrderLine", order_line_1.id
                    ),
                    "stocks": [{"quantity": 3, "warehouse": warehouse_id}],
                },
                {
                    "orderLineId": graphene.Node.to_global_id(
                        "OrderLine", order_line_2.id
                    ),
                    "stocks": [{"quantity": 2, "warehouse": warehouse_id}],
                },
            ],
        },
    }

    response = staff_api_client.post_graphql(
        ORDER_FULFILL_MUTATION, fulfill_order_variables
    )
    fulfillment_id = get_graphql_content(response)["data"]["orderFulfill"][
        "fulfillments"
    ][0]["id"]

    # update permission group - remove access to order channel
    permission_group_update_variables = {
        "id": graphene.Node.to_global_id("Group", permission_group_manage_orders.id),
        "input": {
            "restrictedAccessToChannels": True,
            "addChannels": [graphene.Node.to_global_id("Channel", channel_PLN.id)],
        },
    }
    superuser_api_client.post_graphql(
        PERMISSION_GROUP_UPDATE_MUTATION, permission_group_update_variables
    )

    # try to cancel fulfillment
    cancel_fulfillment_variables = {"id": fulfillment_id, "warehouseId": warehouse_id}
    response = staff_api_client.post_graphql(
        CANCEL_FULFILLMENT_MUTATION, cancel_fulfillment_variables
    )

    # then
    assert_no_permission(response)
