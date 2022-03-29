import graphene

from ....order import OrderStatus
from ....order import models as order_models
from ...tests.utils import get_graphql_content

MUTATION_DELETE_ORDER_LINES = """
mutation draftOrderLinesBulkDelete($ids: [ID!]!) {
    draftOrderLinesBulkDelete(ids: $ids) {
        count
        errors {
            field
            message
        }
    }
}
"""


def test_delete_draft_orders(staff_api_client, order_list, permission_manage_orders):
    order_1, order_2, *orders = order_list
    order_1.status = OrderStatus.DRAFT
    order_2.status = OrderStatus.DRAFT
    order_1.save()
    order_2.save()

    query = """
    mutation draftOrderBulkDelete($ids: [ID!]!) {
        draftOrderBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [graphene.Node.to_global_id("Order", order.id) for order in order_list]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)

    assert content["data"]["draftOrderBulkDelete"]["count"] == 2
    assert not order_models.Order.objects.filter(
        id__in=[order_1.id, order_2.id]
    ).exists()
    assert order_models.Order.objects.filter(
        id__in=[order.id for order in orders]
    ).count() == len(orders)


def test_fail_to_delete_non_draft_order_lines(
    staff_api_client, order_with_lines, permission_manage_orders
):
    order = order_with_lines
    order_lines = [line for line in order.lines.all()]
    # Ensure we cannot delete a non-draft order
    order.status = OrderStatus.CANCELED
    order.save()

    variables = {
        "ids": [
            graphene.Node.to_global_id("OrderLine", order_line.id)
            for order_line in order_lines
        ]
    }
    response = staff_api_client.post_graphql(
        MUTATION_DELETE_ORDER_LINES, variables, permissions=[permission_manage_orders]
    )

    content = get_graphql_content(response)
    assert "errors" in content["data"]["draftOrderLinesBulkDelete"]
    assert content["data"]["draftOrderLinesBulkDelete"]["count"] == 0


def test_delete_draft_order_lines(
    staff_api_client, order_with_lines, permission_manage_orders
):
    order = order_with_lines
    order_lines = [line for line in order.lines.all()]
    # Only lines in draft order can be deleted
    order.status = OrderStatus.DRAFT
    order.save()

    variables = {
        "ids": [
            graphene.Node.to_global_id("OrderLine", order_line.id)
            for order_line in order_lines
        ]
    }

    response = staff_api_client.post_graphql(
        MUTATION_DELETE_ORDER_LINES, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)

    assert content["data"]["draftOrderLinesBulkDelete"]["count"] == 2
    assert not order_models.OrderLine.objects.filter(
        id__in=[order_line.pk for order_line in order_lines]
    ).exists()
