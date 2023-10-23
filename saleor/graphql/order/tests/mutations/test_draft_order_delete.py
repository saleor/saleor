import graphene
import pytest

from .....discount.models import VoucherCode
from .....order import OrderStatus
from .....order.error_codes import OrderErrorCode
from ....tests.utils import assert_no_permission, get_graphql_content

DRAFT_ORDER_DELETE_MUTATION = """
    mutation draftDelete($id: ID!) {
        draftOrderDelete(id: $id) {
            order {
                id
            }
            errors {
                code
                field
            }
        }
    }
"""


def test_draft_order_delete(
    staff_api_client, permission_group_manage_orders, draft_order
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    query = DRAFT_ORDER_DELETE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    staff_api_client.post_graphql(query, variables)
    with pytest.raises(order._meta.model.DoesNotExist):
        order.refresh_from_db()


@pytest.mark.parametrize(
    "order_status",
    [
        OrderStatus.UNFULFILLED,
        OrderStatus.UNCONFIRMED,
        OrderStatus.CANCELED,
        OrderStatus.PARTIALLY_FULFILLED,
        OrderStatus.FULFILLED,
        OrderStatus.PARTIALLY_RETURNED,
        OrderStatus.RETURNED,
        OrderStatus.EXPIRED,
    ],
)
def test_draft_order_delete_non_draft_order(
    staff_api_client, permission_group_manage_orders, order_with_lines, order_status
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.status = order_status
    order.save(update_fields=["status"])
    query = DRAFT_ORDER_DELETE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    account_errors = content["data"]["draftOrderDelete"]["errors"]
    assert len(account_errors) == 1
    assert account_errors[0]["field"] == "id"
    assert account_errors[0]["code"] == OrderErrorCode.INVALID.name


def test_draft_order_delete_by_user_no_channel_access(
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    draft_order,
    channel_PLN,
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)
    order = draft_order
    order.channel = channel_PLN
    order.save(update_fields=["channel"])

    query = DRAFT_ORDER_DELETE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


def test_draft_order_delete_by_app(
    app_api_client, permission_manage_orders, draft_order, channel_PLN
):
    # given
    order = draft_order
    order.channel = channel_PLN
    order.save(update_fields=["channel"])

    query = DRAFT_ORDER_DELETE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    app_api_client.post_graphql(
        query, variables, permissions=(permission_manage_orders,)
    )

    # then
    with pytest.raises(order._meta.model.DoesNotExist):
        order.refresh_from_db()


def test_draft_order_delete_product(
    app_api_client, permission_manage_products, draft_order
):
    query = """
        mutation DeleteProduct($id: ID!) {
          productDelete(id: $id) {
            product {
              id
            }
          }
        }
    """
    order = draft_order
    line = order.lines.first()
    product = line.variant.product
    product_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"id": product_id}
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["productDelete"]["product"]["id"] == product_id


DRAFT_ORDER_DELETE_BY_EXTERNAL_REFERENCE = """
    mutation draftDelete($id: ID, $externalReference: String) {
        draftOrderDelete(id: $id, externalReference: $externalReference) {
            order {
                id
                externalReference
            }
            errors {
                field
                message
        }
    }
}
"""


def test_draft_order_delete_by_external_reference(
    staff_api_client, permission_group_manage_orders, draft_order
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    query = DRAFT_ORDER_DELETE_BY_EXTERNAL_REFERENCE
    ext_ref = "test-ext-ref"
    order.external_reference = ext_ref
    order.save(update_fields=["external_reference"])
    variables = {"externalReference": ext_ref}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["draftOrderDelete"]
    with pytest.raises(order._meta.model.DoesNotExist):
        order.refresh_from_db()
    assert graphene.Node.to_global_id("Order", order.id) == data["order"]["id"]
    assert data["order"]["externalReference"] == order.external_reference


def test_draft_order_delete_by_both_id_and_external_reference(
    staff_api_client, permission_group_manage_orders
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_DELETE_BY_EXTERNAL_REFERENCE
    variables = {"externalReference": "whatever", "id": "whatever"}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    errors = content["data"]["draftOrderDelete"]["errors"]
    assert (
        errors[0]["message"]
        == "Argument 'id' cannot be combined with 'external_reference'"
    )


def test_draft_order_delete_by_external_reference_not_existing(
    staff_api_client, permission_group_manage_orders
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_DELETE_BY_EXTERNAL_REFERENCE
    ext_ref = "non-existing-ext-ref"
    variables = {"externalReference": ext_ref}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    errors = content["data"]["draftOrderDelete"]["errors"]
    assert errors[0]["message"] == f"Couldn't resolve to a node: {ext_ref}"


def test_draft_order_delete_release_voucher_codes_multiple_use(
    staff_api_client,
    permission_group_manage_orders,
    draft_order_list_with_multiple_use_voucher,
):
    # given
    query = DRAFT_ORDER_DELETE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order_list_with_multiple_use_voucher[0]
    voucher_code = VoucherCode.objects.get(code=order.voucher_code)
    assert voucher_code.used == 1

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    staff_api_client.post_graphql(query, variables)

    # then
    voucher_code.refresh_from_db()
    assert voucher_code.used == 0


def test_draft_order_delete_release_voucher_codes_single_use(
    staff_api_client,
    permission_group_manage_orders,
    draft_order_list_with_single_use_voucher,
):
    # given
    query = DRAFT_ORDER_DELETE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order_list_with_single_use_voucher[0]
    voucher_code = VoucherCode.objects.get(code=order.voucher_code)
    assert voucher_code.is_active is False

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    staff_api_client.post_graphql(query, variables)

    # then
    voucher_code.refresh_from_db()
    assert voucher_code.is_active is True
