from unittest.mock import patch

import graphene
import pytest
from django.test import override_settings

from .....core.models import EventDelivery
from .....discount.models import VoucherCode
from .....order import OrderStatus
from .....order.actions import call_order_event
from .....order.error_codes import OrderErrorCode
from .....webhook.event_types import WebhookEventAsyncType
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
                message
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


def test_draft_order_delete_draft_with_transactions(
    staff_api_client, permission_group_manage_orders, draft_order, transaction_item
):
    # given
    order = draft_order
    query = DRAFT_ORDER_DELETE_MUTATION
    transaction_item.order_id = order.id
    transaction_item.save()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    account_errors = content["data"]["draftOrderDelete"]["errors"]
    assert len(account_errors) == 1
    assert account_errors[0]["code"] == OrderErrorCode.INVALID.name
    assert (
        account_errors[0]["message"]
        == "Cannot delete order with payments or transactions attached to it."
    )


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


@patch(
    "saleor.graphql.order.mutations.draft_order_delete.call_order_event",
    wraps=call_order_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_draft_order_delete_do_not_trigger_sync_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_order_event,
    setup_order_webhooks,
    settings,
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        draft_order_deleted_webhook,
    ) = setup_order_webhooks(WebhookEventAsyncType.DRAFT_ORDER_DELETED)

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    query = DRAFT_ORDER_DELETE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["draftOrderDelete"]["errors"]

    # confirm that event delivery was generated for each webhook.
    draft_order_deleted_delivery = EventDelivery.objects.get(
        webhook_id=draft_order_deleted_webhook.id
    )

    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": draft_order_deleted_delivery.id},
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )
    assert not mocked_send_webhook_request_sync.called
    assert wrapped_call_order_event.called
