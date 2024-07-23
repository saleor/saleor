from datetime import timedelta
from unittest.mock import call, patch

import graphene
from django.test import override_settings
from django.utils import timezone

from .....checkout import base_calculations
from .....checkout.actions import call_checkout_event_for_checkout_info
from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....core.models import EventDelivery
from .....plugins.manager import get_plugins_manager
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

MUTATION_CHECKOUT_REMOVE_PROMO_CODE = """
    mutation($id: ID, $promoCode: String, $promoCodeId: ID) {
        checkoutRemovePromoCode(
            id: $id, promoCode: $promoCode, promoCodeId: $promoCodeId) {
            errors {
                field
                code
                message
            }
            checkout {
                token,
                voucherCode
                giftCards {
                    id
                    last4CodeChars
                }
                totalPrice {
                    gross {
                        amount
                    }
                }
                subtotalPrice {
                    gross {
                        amount
                    }
                }
            }
        }
    }
"""


def _mutate_checkout_remove_promo_code(client, variables):
    response = client.post_graphql(MUTATION_CHECKOUT_REMOVE_PROMO_CODE, variables)
    content = get_graphql_content(response)
    return content["data"]["checkoutRemovePromoCode"]


def test_checkout_remove_voucher_code(api_client, checkout_with_voucher):
    assert checkout_with_voucher.voucher_code is not None
    previous_checkout_last_change = checkout_with_voucher.last_change

    variables = {
        "id": to_global_id_or_none(checkout_with_voucher),
        "promoCode": checkout_with_voucher.voucher_code,
    }

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    checkout_with_voucher.refresh_from_db()
    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_voucher.token)
    assert data["checkout"]["voucherCode"] is None
    assert checkout_with_voucher.voucher_code is None
    assert checkout_with_voucher.last_change != previous_checkout_last_change


def test_checkout_remove_voucher_code_with_inactive_channel(
    api_client, checkout_with_voucher
):
    channel = checkout_with_voucher.channel
    channel.is_active = False
    channel.save()

    variables = {
        "id": to_global_id_or_none(checkout_with_voucher),
        "promoCode": checkout_with_voucher.voucher_code,
    }

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    checkout_with_voucher.refresh_from_db()
    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_voucher.token)
    assert data["checkout"]["voucherCode"] == checkout_with_voucher.voucher_code


def test_checkout_remove_gift_card_code(api_client, checkout_with_gift_card):
    assert checkout_with_gift_card.gift_cards.count() == 1
    previous_checkout_last_change = checkout_with_gift_card.last_change

    variables = {
        "id": to_global_id_or_none(checkout_with_gift_card),
        "promoCode": checkout_with_gift_card.gift_cards.first().code,
    }

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    assert data["checkout"]["token"] == str(checkout_with_gift_card.token)
    assert data["checkout"]["giftCards"] == []
    assert not checkout_with_gift_card.gift_cards.all().exists()
    checkout_with_gift_card.refresh_from_db()
    assert checkout_with_gift_card.last_change != previous_checkout_last_change


def test_checkout_remove_one_of_gift_cards(
    api_client, checkout_with_gift_card, gift_card_created_by_staff
):
    checkout_with_gift_card.gift_cards.add(gift_card_created_by_staff)
    checkout_with_gift_card.save()
    previous_checkout_last_change = checkout_with_gift_card.last_change
    gift_card_first = checkout_with_gift_card.gift_cards.first()
    gift_card_last = checkout_with_gift_card.gift_cards.last()

    variables = {
        "id": to_global_id_or_none(checkout_with_gift_card),
        "promoCode": gift_card_first.code,
    }

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    checkout_gift_cards = checkout_with_gift_card.gift_cards
    assert data["checkout"]["token"] == str(checkout_with_gift_card.token)
    assert checkout_gift_cards.filter(code=gift_card_last.code).exists()
    assert not checkout_gift_cards.filter(code=gift_card_first.code).exists()
    checkout_with_gift_card.refresh_from_db()
    assert checkout_with_gift_card.last_change != previous_checkout_last_change


def test_checkout_remove_promo_code_invalid_promo_code(api_client, checkout_with_item):
    checkout_with_item.price_expiration = timezone.now() + timedelta(days=2)
    checkout_with_item.save(update_fields=["price_expiration"])
    previous_checkout_last_change = checkout_with_item.last_change
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": "unexisting_code",
    }

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_item.token)
    checkout_with_item.refresh_from_db()
    assert checkout_with_item.last_change == previous_checkout_last_change


def test_checkout_remove_promo_code_invalid_checkout(api_client, voucher, checkout):
    variables = {"id": to_global_id_or_none(checkout), "promoCode": voucher.code}
    checkout.delete()

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["field"] == "id"


def test_checkout_remove_voucher_code_by_id(
    api_client, checkout_with_voucher, voucher, gift_card
):
    assert checkout_with_voucher.voucher_code is not None
    checkout_with_voucher.gift_cards.add(gift_card)

    variables = {
        "id": to_global_id_or_none(checkout_with_voucher),
        "promoCodeId": graphene.Node.to_global_id("Voucher", voucher.id),
    }

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    checkout_with_voucher.refresh_from_db()
    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_voucher.token)
    assert data["checkout"]["voucherCode"] is None
    assert len(data["checkout"]["giftCards"]) == 1
    assert checkout_with_voucher.voucher_code is None


def test_checkout_remove_gift_card_by_id(
    api_client, checkout_with_voucher, gift_card, gift_card_expiry_date
):
    assert checkout_with_voucher.voucher_code is not None
    checkout_with_voucher.gift_cards.add(gift_card, gift_card_expiry_date)

    variables = {
        "id": to_global_id_or_none(checkout_with_voucher),
        "promoCodeId": graphene.Node.to_global_id("GiftCard", gift_card.id),
    }

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    checkout_with_voucher.refresh_from_db()
    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_voucher.token)
    assert data["checkout"]["voucherCode"] is not None
    gift_cards = data["checkout"]["giftCards"]
    assert len(gift_cards) == 1
    assert gift_cards[0]["id"] == graphene.Node.to_global_id(
        "GiftCard", gift_card_expiry_date.pk
    )


def test_checkout_remove_promo_code_id_and_code_given(
    api_client, checkout_with_voucher, gift_card
):
    assert checkout_with_voucher.voucher_code is not None

    variables = {
        "id": to_global_id_or_none(checkout_with_voucher),
        "promoCode": checkout_with_voucher.voucher_code,
        "promoCodeId": graphene.Node.to_global_id("GiftCard", gift_card.id),
    }

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name


def test_checkout_remove_promo_code_no_id_and_code_given(
    api_client, checkout_with_voucher, gift_card
):
    assert checkout_with_voucher.voucher_code is not None

    variables = {
        "id": to_global_id_or_none(checkout_with_voucher),
    }

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name


def test_checkout_remove_promo_code_id_does_not_exist(
    api_client, checkout_with_voucher, gift_card
):
    assert checkout_with_voucher.voucher_code is not None

    variables = {
        "id": to_global_id_or_none(checkout_with_voucher),
        "promoCodeId": "Abc",
    }

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name
    assert data["errors"][0]["field"] == "promoCodeId"


def test_checkout_remove_promo_code_invalid_object_type(
    api_client, checkout_with_voucher, gift_card
):
    assert checkout_with_voucher.voucher_code is not None

    variables = {
        "id": to_global_id_or_none(checkout_with_voucher),
        "promoCodeId": graphene.Node.to_global_id("Product", gift_card.id),
    }

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.NOT_FOUND.name
    assert data["errors"][0]["field"] == "promoCodeId"


def test_checkout_remove_voucher_code_invalidates_price(
    api_client, checkout_with_item, voucher
):
    # given
    checkout_with_item.price_expiration = timezone.now() + timedelta(days=2)
    checkout_with_item.voucher_code = voucher.code
    checkout_with_item.save(update_fields=["voucher_code", "price_expiration"])
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    subtotal = base_calculations.base_checkout_subtotal(
        lines,
        checkout_info.channel,
        checkout_info.checkout.currency,
    )
    expected_total = subtotal.amount
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": voucher.code,
    }

    # when
    data = _mutate_checkout_remove_promo_code(api_client, variables)

    # then
    assert not data["errors"]
    assert data["checkout"]["subtotalPrice"]["gross"]["amount"] == subtotal.amount
    assert data["checkout"]["totalPrice"]["gross"]["amount"] == expected_total


def test_with_active_problems_flow(
    api_client,
    checkout_with_problems,
    voucher,
):
    # given
    channel = checkout_with_problems.channel
    channel.use_legacy_error_flow_for_checkout = False
    channel.save(update_fields=["use_legacy_error_flow_for_checkout"])

    checkout_with_problems.voucher_code = voucher.code
    checkout_with_problems.save(
        update_fields=[
            "voucher_code",
        ]
    )

    variables = {
        "id": to_global_id_or_none(checkout_with_problems),
        "promoCode": voucher.code,
    }

    # when
    response = api_client.post_graphql(
        MUTATION_CHECKOUT_REMOVE_PROMO_CODE,
        variables,
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["checkoutRemovePromoCode"]["errors"]


@patch(
    "saleor.graphql.checkout.mutations.checkout_remove_promo_code.call_checkout_event_for_checkout_info",
    wraps=call_checkout_event_for_checkout_info,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_remove_triggers_sync_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_checkout_event_for_checkout,
    setup_checkout_webhooks,
    settings,
    api_client,
    checkout_with_voucher,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_updated_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_UPDATED)

    variables = {
        "id": to_global_id_or_none(checkout_with_voucher),
        "promoCode": checkout_with_voucher.voucher_code,
    }

    # when
    content = _mutate_checkout_remove_promo_code(api_client, variables)

    # then
    assert not content["errors"]

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
