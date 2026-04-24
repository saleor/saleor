import graphene
import pytest
from .....discount.models import Voucher
from .....order import OrderStatus
from ....tests.utils import get_graphql_content

DRAFT_ORDER_UPDATE_MUTATION = """
    mutation draftUpdate(
    $id: ID!,
    $input: DraftOrderInput!,
    ) {
        draftOrderUpdate(
            id: $id,
            input: $input
        ) {
            errors {
                field
                code
                message
            }
            order {
                voucher {
                    code
                }
                voucherCode
            }
        }
    }
"""

def test_draft_order_update_with_same_voucher_does_not_increase_usage(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    voucher,
):
    # given
    order = draft_order
    code_instance = voucher.codes.first()
    order.voucher = voucher
    order.voucher_code = code_instance.code
    order.save(update_fields=["voucher", "voucher_code"])

    channel = order.channel
    channel.include_draft_order_in_voucher_usage = True
    channel.save(update_fields=["include_draft_order_in_voucher_usage"])

    code_instance.used = 1
    code_instance.save(update_fields=["used"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)

    variables = {
        "id": order_id,
        "input": {
            "voucher": voucher_id,
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]
    
    code_instance.refresh_from_db()
    # Usage should still be 1, not 2
    assert code_instance.used == 1

def test_draft_order_update_change_voucher_releases_old_increases_new(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    voucher,
    voucher_percentage,
):
    # given
    order = draft_order
    
    # Setup old voucher
    old_voucher = voucher
    old_code_instance = old_voucher.codes.first()
    order.voucher = old_voucher
    order.voucher_code = old_code_instance.code
    order.save(update_fields=["voucher", "voucher_code"])
    
    old_code_instance.used = 1
    old_code_instance.save(update_fields=["used"])

    # Setup new voucher
    new_voucher = voucher_percentage
    new_code_instance = new_voucher.codes.first()
    new_code_instance.used = 0
    new_code_instance.save(update_fields=["used"])

    channel = order.channel
    channel.include_draft_order_in_voucher_usage = True
    channel.save(update_fields=["include_draft_order_in_voucher_usage"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    new_voucher_id = graphene.Node.to_global_id("Voucher", new_voucher.id)

    variables = {
        "id": order_id,
        "input": {
            "voucher": new_voucher_id,
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]
    
    old_code_instance.refresh_from_db()
    new_code_instance.refresh_from_db()
    
    # Old usage should be released (1 -> 0)
    assert old_code_instance.used == 0
    # New usage should be increased (0 -> 1)
    assert new_code_instance.used == 1
