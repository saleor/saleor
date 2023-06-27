import graphene
import pytest

from .....order import OrderStatus
from ....account.tests.mutations.permission_group.test_permission_group_update import (
    PERMISSION_GROUP_UPDATE_MUTATION,
)
from ....tests.utils import assert_no_permission, get_graphql_content
from ..mutations.test_draft_order_complete import DRAFT_ORDER_COMPLETE_MUTATION
from ..mutations.test_draft_order_create import DRAFT_ORDER_CREATE_MUTATION
from ..mutations.test_draft_order_update import DRAFT_ORDER_UPDATE_MUTATION
from ..mutations.test_order_lines_create import ORDER_LINES_CREATE_MUTATION
from ..mutations.test_order_mark_as_paid import MARK_ORDER_AS_PAID_MUTATION
from ..queries.test_order import QUERY_ORDER_BY_ID


@pytest.mark.integration
def test_create_order_by_staff_in_accessible_channel(
    staff_api_client,
    permission_group_manage_orders,
    channel_PLN,
    channel_USD,
    product,
    shipping_method,
    graphql_address_data,
):
    """Ensure that staff user is able to create and complete the draft order
    in the channel he has access to."""
    # given
    permission_group_manage_orders.restricted_access_to_channels = True
    permission_group_manage_orders.save(update_fields=["restricted_access_to_channels"])
    permission_group_manage_orders.channels.add(channel_USD)

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when

    # create order
    draft_order_create_variables = {
        "input": {
            "userEmail": "test@example.com",
            "billingAddress": graphql_address_data,
            "shippingAddress": graphql_address_data,
            "channelId": graphene.Node.to_global_id("Channel", channel_USD.id),
        }
    }
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_CREATE_MUTATION, draft_order_create_variables
    )

    draft_order_id = get_graphql_content(response)["data"]["draftOrderCreate"]["order"][
        "id"
    ]

    # add lines to order
    variant = product.variants.first()
    order_lines_create_variables = {
        "orderId": draft_order_id,
        "variantId": graphene.Node.to_global_id("ProductVariant", variant.id),
        "quantity": 2,
    }
    staff_api_client.post_graphql(
        ORDER_LINES_CREATE_MUTATION, order_lines_create_variables
    )

    # update order with available product and shipping method
    draft_order_update_variables = {
        "id": draft_order_id,
        "input": {
            "shippingMethod": graphene.Node.to_global_id(
                "ShippingMethod", shipping_method.id
            ),
        },
    }
    staff_api_client.post_graphql(
        DRAFT_ORDER_UPDATE_MUTATION, draft_order_update_variables
    )

    # complete order
    staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, {"id": draft_order_id})

    # then
    # query created order
    response = staff_api_client.post_graphql(QUERY_ORDER_BY_ID, {"id": draft_order_id})
    content = get_graphql_content(response)
    order_data = content["data"]["order"]
    assert order_data["status"] == OrderStatus.UNFULFILLED.upper()


@pytest.mark.integration
def test_user_cannot_manage_draft_order_after_loosing_the_channel_access(
    staff_api_client,
    permission_group_manage_orders,
    channel_USD,
    graphql_address_data,
    product,
    shipping_method,
    superuser_api_client,
):
    """Ensure that staff user cannot mark order as paid after loosing the access
    to order channel."""
    # given
    permission_group_manage_orders.restricted_access_to_channels = True
    permission_group_manage_orders.save(update_fields=["restricted_access_to_channels"])
    permission_group_manage_orders.channels.add(channel_USD)

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variant = product.variants.first()

    # when

    # create draft order
    draft_order_create_variables = {
        "input": {
            "userEmail": "test@example.com",
            "billingAddress": graphql_address_data,
            "shippingAddress": graphql_address_data,
            "channelId": graphene.Node.to_global_id("Channel", channel_USD.id),
            "lines": [
                {
                    "quantity": 1,
                    "variantId": graphene.Node.to_global_id(
                        "ProductVariant", variant.id
                    ),
                }
            ],
            "shippingMethod": graphene.Node.to_global_id(
                "ShippingMethod", shipping_method.id
            ),
        }
    }
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_CREATE_MUTATION, draft_order_create_variables
    )

    draft_order_id = get_graphql_content(response)["data"]["draftOrderCreate"]["order"][
        "id"
    ]

    # complete order
    staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, {"id": draft_order_id})

    # update permission group - remove access to order channel
    permission_group_update_variables = {
        "id": graphene.Node.to_global_id("Group", permission_group_manage_orders.id),
        "input": {
            "restrictedAccessToChannels": True,
            "removeChannels": [graphene.Node.to_global_id("Channel", channel_USD.id)],
        },
    }
    superuser_api_client.post_graphql(
        PERMISSION_GROUP_UPDATE_MUTATION, permission_group_update_variables
    )

    # try to mark order as paid
    response = staff_api_client.post_graphql(
        MARK_ORDER_AS_PAID_MUTATION, {"id": draft_order_id}
    )

    # then
    assert_no_permission(response)
