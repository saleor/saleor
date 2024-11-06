from unittest import mock
from unittest.mock import patch

import graphene
from django.test import override_settings

from .....checkout.actions import call_checkout_info_event
from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.models import CheckoutLine
from .....checkout.utils import invalidate_checkout
from .....core.models import EventDelivery
from .....plugins.manager import get_plugins_manager
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content
from ...mutations.utils import update_checkout_shipping_method_if_invalid

MUTATION_CHECKOUT_LINES_DELETE = """
    mutation checkoutLinesDelete($id: ID, $linesIds: [ID!]!) {
        checkoutLinesDelete(id: $id, linesIds: $linesIds) {
            checkout {
                token
                lines {
                    id
                    quantity
                    variant {
                        id
                    }
                }
            }
            errors {
                  message
                  code
                  field
                  lines
            }
        }
    }
"""


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_lines_delete."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_lines_delete.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_lines_delete(
    mocked_invalidate_checkout,
    mocked_update_shipping_method,
    user_api_client,
    checkout_with_items,
):
    checkout = checkout_with_items
    checkout_lines_count = checkout.lines.count()
    previous_last_change = checkout.last_change
    line = checkout.lines.first()
    second_line = checkout.lines.last()

    first_line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)
    second_line_id = graphene.Node.to_global_id("CheckoutLine", second_line.pk)
    lines_list = [first_line_id, second_line_id]

    variables = {"id": to_global_id_or_none(checkout), "linesIds": lines_list}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_DELETE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesDelete"]
    assert not data["errors"]
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() + len(lines_list) == checkout_lines_count
    remaining_lines = data["checkout"]["lines"]
    lines_ids = [line["id"] for line in remaining_lines]
    assert lines_list not in lines_ids
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.last_change != previous_last_change
    assert mocked_invalidate_checkout.call_count == 1


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_lines_delete."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_lines_delete.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_lines_delete_when_variant_without_channel_listing(
    mocked_invalidate_checkout,
    mocked_update_shipping_method,
    user_api_client,
    checkout_with_items,
):
    # given
    checkout = checkout_with_items
    checkout_lines_count = checkout.lines.count()
    previous_last_change = checkout.last_change
    line = checkout.lines.first()
    line.variant.channel_listings.all().delete()
    second_line = checkout.lines.last()

    first_line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)
    second_line_id = graphene.Node.to_global_id("CheckoutLine", second_line.pk)
    lines_list = [first_line_id, second_line_id]

    variables = {"id": to_global_id_or_none(checkout), "linesIds": lines_list}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_DELETE, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesDelete"]
    assert not data["errors"]
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() + len(lines_list) == checkout_lines_count
    remaining_lines = data["checkout"]["lines"]
    lines_ids = [line["id"] for line in remaining_lines]
    assert lines_list not in lines_ids
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.last_change != previous_last_change
    assert mocked_invalidate_checkout.call_count == 1


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_lines_delete."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_lines_delete.invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_lines_delete_when_checkout_has_variant_without_channel_listing(
    mocked_invalidate_checkout,
    mocked_update_shipping_method,
    user_api_client,
    checkout_with_items,
):
    # given
    checkout = checkout_with_items
    checkout_lines_count = checkout.lines.count()
    previous_last_change = checkout.last_change

    line = checkout.lines.first()

    line_without_listing = checkout.lines.last()
    line_without_listing.variant.channel_listings.all().delete()

    first_line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)
    lines_list = [
        first_line_id,
    ]

    variables = {"id": to_global_id_or_none(checkout), "linesIds": lines_list}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_DELETE, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["checkoutLinesDelete"]
    assert not data["errors"]
    checkout.refresh_from_db()
    lines, _ = fetch_checkout_lines(checkout)
    assert checkout.lines.count() + len(lines_list) == checkout_lines_count
    remaining_lines = data["checkout"]["lines"]
    lines_ids = [line["id"] for line in remaining_lines]
    assert lines_list not in lines_ids
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.last_change != previous_last_change
    assert mocked_invalidate_checkout.call_count == 1


def test_checkout_lines_delete_invalid_checkout_id(
    user_api_client, checkout_with_items
):
    checkout = checkout_with_items
    line = checkout.lines.first()
    second_line = checkout.lines.last()

    first_line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)
    second_line_id = graphene.Node.to_global_id("CheckoutLine", second_line.pk)
    lines_list = [first_line_id, second_line_id]

    variables = {
        "id": graphene.Node.to_global_id("Checkout", checkout.pk),
        "linesIds": lines_list,
    }
    checkout.delete()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_DELETE, variables)
    content = get_graphql_content(response)
    errors = content["data"]["checkoutLinesDelete"]["errors"][0]
    assert errors["code"] == CheckoutErrorCode.NOT_FOUND.name


def tests_checkout_lines_delete_invalid_lines_ids(user_api_client, checkout_with_items):
    checkout = checkout_with_items
    previous_last_change = checkout.last_change
    line = checkout.lines.first()

    first_line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)
    lines_list = [first_line_id, "Q2hlY2tvdXRMaW5lOjE8"]

    variables = {"id": to_global_id_or_none(checkout), "linesIds": lines_list}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_DELETE, variables)
    content = get_graphql_content(response, ignore_errors=True)
    errors = content["errors"][0]
    assert errors["extensions"]["exception"]["code"] == "GraphQLError"
    assert checkout.last_change == previous_last_change


def test_with_active_problems_flow(api_client, checkout_with_problems):
    # given
    channel = checkout_with_problems.channel
    channel.use_legacy_error_flow_for_checkout = False
    channel.save(update_fields=["use_legacy_error_flow_for_checkout"])

    line = checkout_with_problems.lines.first()
    first_line_id = to_global_id_or_none(line)

    variables = {
        "id": to_global_id_or_none(checkout_with_problems),
        "linesIds": [first_line_id],
    }

    # when
    response = api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_DELETE,
        variables,
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["checkoutLinesDelete"]["errors"]


def test_checkout_lines_delete_non_removable_gift(user_api_client, checkout_with_items):
    # given
    checkout = checkout_with_items
    gift_line = checkout.lines.first()
    gift_line.is_gift = True
    gift_line.save(update_fields=["is_gift"])
    non_gift_line = checkout.lines.last()
    gift_line_id = to_global_id_or_none(gift_line)
    non_gift_line_id = to_global_id_or_none(non_gift_line)
    lines_list = [gift_line_id, non_gift_line_id]

    variables = {"id": to_global_id_or_none(checkout), "linesIds": lines_list}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_DELETE, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["checkoutLinesDelete"]
    assert not data["checkout"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "lineIds"
    assert errors[0]["code"] == CheckoutErrorCode.NON_REMOVABLE_GIFT_LINE.name
    assert errors[0]["lines"] == [gift_line_id]


def test_checkout_lines_delete_not_associated_with_checkout(
    user_api_client, checkout_with_items, checkouts_list, variant
):
    # given
    checkout = checkout_with_items
    wrong_checkout = checkouts_list[0]
    line = CheckoutLine.objects.create(
        checkout=wrong_checkout,
        variant=variant,
        quantity=1,
        undiscounted_unit_price_amount=variant.channel_listings.get(
            channel_id=checkout.channel_id
        ).price_amount,
    )
    line_id = to_global_id_or_none(line)
    variables = {"id": to_global_id_or_none(checkout), "linesIds": [line_id]}

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINES_DELETE, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["checkoutLinesDelete"]
    assert not data["checkout"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "lineId"
    assert errors[0]["code"] == CheckoutErrorCode.INVALID.name
    assert errors[0]["lines"] == [line_id]


@patch(
    "saleor.graphql.checkout.mutations.checkout_lines_delete.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_lines_delete_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_checkout_info_event,
    setup_checkout_webhooks,
    settings,
    api_client,
    checkout_with_items,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_updated_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_UPDATED)

    line = checkout_with_items.lines.first()
    first_line_id = to_global_id_or_none(line)

    variables = {
        "id": to_global_id_or_none(checkout_with_items),
        "linesIds": [first_line_id],
    }

    # when
    response = api_client.post_graphql(
        MUTATION_CHECKOUT_LINES_DELETE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["checkoutLinesDelete"]["errors"]

    assert wrapped_call_checkout_info_event.called

    # confirm that event delivery was generated for each async webhook.
    checkout_update_delivery = EventDelivery.objects.get(
        webhook_id=checkout_updated_webhook.id
    )
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": checkout_update_delivery.id},
        queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 3
    assert not EventDelivery.objects.exclude(
        webhook_id=checkout_updated_webhook.id
    ).exists()

    shipping_methods_call, filter_shipping_call, tax_delivery_call = (
        mocked_send_webhook_request_sync.mock_calls
    )
    shipping_methods_delivery = shipping_methods_call.args[0]
    assert shipping_methods_delivery.webhook_id == shipping_webhook.id
    assert (
        shipping_methods_delivery.event_type
        == WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
    )
    assert shipping_methods_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    )
    assert filter_shipping_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    tax_delivery = tax_delivery_call.args[0]
    assert tax_delivery.webhook_id == tax_webhook.id
