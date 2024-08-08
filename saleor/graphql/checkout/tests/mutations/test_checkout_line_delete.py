from unittest import mock
from unittest.mock import call, patch

import graphene
from django.test import override_settings

from .....checkout import base_calculations
from .....checkout.actions import call_checkout_event_for_checkout_info
from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.utils import (
    add_variant_to_checkout,
    add_voucher_to_checkout,
    calculate_checkout_quantity,
    invalidate_checkout,
)
from .....core.models import EventDelivery
from .....plugins.manager import get_plugins_manager
from .....warehouse.models import Reservation
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content
from ...mutations.utils import update_checkout_shipping_method_if_invalid

MUTATION_CHECKOUT_LINE_DELETE = """
    mutation checkoutLineDelete($id: ID, $lineId: ID!) {
        checkoutLineDelete(id: $id, lineId: $lineId) {
            checkout {
                token
                lines {
                    quantity
                    variant {
                        id
                    }
                }
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_line_delete."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_line_delete.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_line_delete(
    mocked_invalidate_checkout,
    mocked_update_shipping_method,
    user_api_client,
    checkout_line_with_reservation_in_many_stocks,
):
    assert Reservation.objects.count() == 2
    checkout = checkout_line_with_reservation_in_many_stocks.checkout
    previous_last_change = checkout.last_change
    lines, _ = fetch_checkout_lines(checkout)
    assert calculate_checkout_quantity(lines) == 3
    assert checkout.lines.count() == 1
    line = checkout.lines.first()
    assert line.quantity == 3

    line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)

    variables = {"id": to_global_id_or_none(checkout), "lineId": line_id}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINE_DELETE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLineDelete"]
    assert not data["errors"]
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() == 0
    assert calculate_checkout_quantity(lines) == 0
    assert Reservation.objects.count() == 0
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.last_change != previous_last_change
    assert mocked_invalidate_checkout.call_count == 1


def test_checkout_lines_delete_with_not_applicable_voucher(
    user_api_client, checkout_with_item, voucher, channel_USD
):
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    subtotal = base_calculations.base_checkout_subtotal(
        lines,
        checkout_info.channel,
        checkout_info.checkout.currency,
    )
    voucher.channel_listings.filter(channel=channel_USD).update(
        min_spent_amount=subtotal.amount
    )
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

    add_voucher_to_checkout(
        manager, checkout_info, lines, voucher, voucher.codes.first()
    )
    assert checkout_with_item.voucher_code == voucher.code

    line = checkout_with_item.lines.first()

    line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)
    variables = {"id": to_global_id_or_none(checkout_with_item), "lineId": line_id}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINE_DELETE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLineDelete"]
    assert not data["errors"]
    checkout_with_item.refresh_from_db()
    assert checkout_with_item.lines.count() == 0
    assert checkout_with_item.voucher_code is None


def test_checkout_line_delete_remove_shipping_if_removed_product_with_shipping(
    user_api_client, checkout_with_item, digital_content, address, shipping_method
):
    checkout = checkout_with_item
    digital_variant = digital_content.product_variant
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.save()
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, digital_variant, 1)
    line = checkout.lines.first()

    line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)

    variables = {"id": to_global_id_or_none(checkout), "lineId": line_id}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINE_DELETE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLineDelete"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.lines.count() == 1
    assert not checkout.shipping_method


def test_with_active_problems_flow(
    api_client, checkout_with_problems, product_with_single_variant
):
    # given
    channel = checkout_with_problems.channel
    channel.use_legacy_error_flow_for_checkout = False
    channel.save(update_fields=["use_legacy_error_flow_for_checkout"])

    variant = product_with_single_variant.variants.first()

    checkout_info = fetch_checkout_info(
        checkout_with_problems, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, variant, 1)

    line = checkout_info.checkout.lines.last()

    variables = {
        "id": to_global_id_or_none(checkout_with_problems),
        "lineId": to_global_id_or_none(line),
    }

    # when
    response = api_client.post_graphql(
        MUTATION_CHECKOUT_LINE_DELETE,
        variables,
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["checkoutLineDelete"]["errors"]


def test_checkout_line_delete_non_removable_gift(user_api_client, checkout_line):
    # given
    checkout = checkout_line.checkout
    line = checkout_line
    line.is_gift = True
    line.save(update_fields=["is_gift"])
    line_id = to_global_id_or_none(line)
    variables = {"id": to_global_id_or_none(checkout), "lineId": line_id}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINE_DELETE, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["checkoutLineDelete"]
    assert not data["checkout"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "lineId"
    assert errors[0]["code"] == CheckoutErrorCode.NON_REMOVABLE_GIFT_LINE.name


@patch(
    "saleor.graphql.checkout.mutations.checkout_line_delete.call_checkout_event_for_checkout_info",
    wraps=call_checkout_event_for_checkout_info,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_line_delete_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_checkout_event_for_checkout,
    setup_checkout_webhooks,
    settings,
    api_client,
    checkout_with_items,
    product_with_single_variant,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_updated_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_UPDATED)

    variant = product_with_single_variant.variants.first()

    checkout_info = fetch_checkout_info(
        checkout_with_items, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, variant, 1)

    line = checkout_info.checkout.lines.last()

    variables = {
        "id": to_global_id_or_none(checkout_with_items),
        "lineId": to_global_id_or_none(line),
    }

    # when
    response = api_client.post_graphql(
        MUTATION_CHECKOUT_LINE_DELETE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["checkoutLineDelete"]["errors"]

    # confirm that event delivery was generated for each webhook.
    checkout_update_delivery = EventDelivery.objects.get(
        webhook_id=checkout_updated_webhook.id
    )
    tax_delivery = EventDelivery.objects.get(webhook_id=tax_webhook.id)
    shipping_methods_delivery = EventDelivery.objects.get(
        webhook_id=shipping_webhook.id,
        event_type=WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
    )
    filter_shipping_delivery = EventDelivery.objects.get(
        webhook_id=shipping_filter_webhook.id,
        event_type=WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
    )

    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": checkout_update_delivery.id},
        queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )
    mocked_send_webhook_request_sync.assert_has_calls(
        [
            call(shipping_methods_delivery, timeout=settings.WEBHOOK_SYNC_TIMEOUT),
            call(filter_shipping_delivery, timeout=settings.WEBHOOK_SYNC_TIMEOUT),
            call(tax_delivery),
        ]
    )
    assert wrapped_call_checkout_event_for_checkout.called
