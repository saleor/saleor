from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import graphene
from django.utils import timezone
from prices import Money

from .....checkout import base_calculations
from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....discount import RewardValueType
from .....discount.models import Voucher, VoucherChannelListing, VoucherCode
from .....plugins.manager import get_plugins_manager
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
                token
                voucherCode
                lines {
                    id
                }
                discount {
                    amount
                }
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


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_checkout_remove_voucher_code(
    checkout_updated_webhook_mock, api_client, checkout_with_voucher
):
    # given
    assert checkout_with_voucher.voucher_code is not None
    previous_checkout_last_change = checkout_with_voucher.last_change

    variables = {
        "id": to_global_id_or_none(checkout_with_voucher),
        "promoCode": checkout_with_voucher.voucher_code,
    }

    # when
    data = _mutate_checkout_remove_promo_code(api_client, variables)

    # then
    checkout_with_voucher.refresh_from_db()
    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_voucher.token)
    assert data["checkout"]["voucherCode"] is None
    assert checkout_with_voucher.voucher_code is None
    assert checkout_with_voucher.last_change != previous_checkout_last_change
    checkout_updated_webhook_mock.assert_called_once_with(checkout_with_voucher)


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_checkout_remove_voucher_code_from_voucher_with_multiple_codes(
    checkout_updated_webhook_mock,
    api_client,
    checkout_with_voucher,
    voucher_with_many_codes,
):
    # given
    assert checkout_with_voucher.voucher_code is not None
    previous_checkout_last_change = checkout_with_voucher.last_change

    variables = {
        "id": to_global_id_or_none(checkout_with_voucher),
        "promoCodeId": graphene.Node.to_global_id(
            "Voucher", voucher_with_many_codes.id
        ),
    }

    # when
    data = _mutate_checkout_remove_promo_code(api_client, variables)

    # then
    checkout_with_voucher.refresh_from_db()
    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_voucher.token)
    assert data["checkout"]["voucherCode"] is None
    assert checkout_with_voucher.voucher_code is None
    assert checkout_with_voucher.last_change != previous_checkout_last_change
    checkout_updated_webhook_mock.assert_called_once_with(checkout_with_voucher)


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_checkout_remove_voucher_code_voucher_not_exists_anymore(
    checkout_updated_webhook_mock, api_client, checkout_with_voucher
):
    # given
    assert checkout_with_voucher.voucher_code is not None
    previous_checkout_last_change = checkout_with_voucher.last_change
    Voucher.objects.all().delete()

    variables = {
        "id": to_global_id_or_none(checkout_with_voucher),
        "promoCode": checkout_with_voucher.voucher_code,
    }

    # when
    data = _mutate_checkout_remove_promo_code(api_client, variables)

    # then
    assert data["errors"][0]["field"] == "promoCode"
    assert data["errors"][0]["code"] == CheckoutErrorCode.NOT_FOUND.name
    assert data["errors"][0]["message"] == "Promo code does not exists."

    checkout_with_voucher.refresh_from_db()
    assert checkout_with_voucher.last_change == previous_checkout_last_change
    checkout_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_checkout_remove_promo_code_id_voucher_not_exists_anymore(
    checkout_updated_webhook_mock, api_client, checkout_with_voucher, voucher
):
    # given
    assert checkout_with_voucher.voucher_code is not None
    previous_checkout_last_change = checkout_with_voucher.last_change
    Voucher.objects.all().delete()

    variables = {
        "id": to_global_id_or_none(checkout_with_voucher),
        "promoCodeId": graphene.Node.to_global_id("Voucher", voucher.id),
    }

    # when
    data = _mutate_checkout_remove_promo_code(api_client, variables)

    # then
    assert data["errors"][0]["field"] == "promoCodeId"
    assert data["errors"][0]["code"] == CheckoutErrorCode.NOT_FOUND.name

    checkout_with_voucher.refresh_from_db()
    assert checkout_with_voucher.last_change == previous_checkout_last_change
    checkout_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_checkout_remove_voucher_code_with_inactive_channel(
    checkout_updated_webhook_mock, api_client, checkout_with_voucher
):
    # given
    checkout_with_voucher.price_expiration = timezone.now() + timedelta(days=2)
    checkout_with_voucher.save(update_fields=["price_expiration"])
    previous_checkout_last_change = checkout_with_voucher.last_change

    channel = checkout_with_voucher.channel
    channel.is_active = False
    channel.save()

    variables = {
        "id": to_global_id_or_none(checkout_with_voucher),
        "promoCode": checkout_with_voucher.voucher_code,
    }

    # when
    data = _mutate_checkout_remove_promo_code(api_client, variables)

    # then
    assert data["errors"][0]["field"] == "promoCode"
    assert data["errors"][0]["code"] == CheckoutErrorCode.INVALID.name
    assert data["errors"][0]["message"] == (
        "Cannot remove a voucher not attached to this checkout."
    )

    checkout_with_voucher.refresh_from_db()
    assert checkout_with_voucher.last_change == previous_checkout_last_change
    checkout_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_checkout_remove_gift_card_code(
    checkout_updated_webhook_mock, api_client, checkout_with_gift_card
):
    # given
    assert checkout_with_gift_card.gift_cards.count() == 1
    previous_checkout_last_change = checkout_with_gift_card.last_change

    variables = {
        "id": to_global_id_or_none(checkout_with_gift_card),
        "promoCode": checkout_with_gift_card.gift_cards.first().code,
    }

    # when
    data = _mutate_checkout_remove_promo_code(api_client, variables)

    # then
    assert data["checkout"]["token"] == str(checkout_with_gift_card.token)
    assert data["checkout"]["giftCards"] == []
    assert not checkout_with_gift_card.gift_cards.all().exists()
    checkout_with_gift_card.refresh_from_db()
    assert checkout_with_gift_card.last_change != previous_checkout_last_change
    checkout_updated_webhook_mock.assert_called_once_with(checkout_with_gift_card)


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_checkout_remove_gift_card_code_from_wrong_checkout(
    checkout_updated_webhook_mock,
    api_client,
    checkout_with_gift_card,
    gift_card_with_metadata,
):
    # given
    assert checkout_with_gift_card.gift_cards.count() == 1
    previous_checkout_last_change = checkout_with_gift_card.last_change

    variables = {
        "id": to_global_id_or_none(checkout_with_gift_card),
        "promoCode": gift_card_with_metadata.code,
    }

    # when
    data = _mutate_checkout_remove_promo_code(api_client, variables)

    # then
    assert data["errors"][0]["field"] == "promoCode"
    assert data["errors"][0]["code"] == CheckoutErrorCode.INVALID.name
    assert data["errors"][0]["message"] == (
        "Cannot remove a gift card not attached to this checkout."
    )

    assert checkout_with_gift_card.gift_cards.count() == 1

    checkout_with_gift_card.refresh_from_db()
    assert checkout_with_gift_card.last_change == previous_checkout_last_change
    checkout_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_checkout_remove_one_of_gift_cards(
    checkout_updated_webhook_mock,
    api_client,
    checkout_with_gift_card,
    gift_card_created_by_staff,
):
    # given
    checkout_with_gift_card.gift_cards.add(gift_card_created_by_staff)
    checkout_with_gift_card.save()
    previous_checkout_last_change = checkout_with_gift_card.last_change
    gift_card_first = checkout_with_gift_card.gift_cards.first()
    gift_card_last = checkout_with_gift_card.gift_cards.last()

    variables = {
        "id": to_global_id_or_none(checkout_with_gift_card),
        "promoCode": gift_card_first.code,
    }

    # when
    data = _mutate_checkout_remove_promo_code(api_client, variables)

    # then
    checkout_gift_cards = checkout_with_gift_card.gift_cards
    assert data["checkout"]["token"] == str(checkout_with_gift_card.token)
    assert checkout_gift_cards.filter(code=gift_card_last.code).exists()
    assert not checkout_gift_cards.filter(code=gift_card_first.code).exists()
    checkout_with_gift_card.refresh_from_db()
    assert checkout_with_gift_card.last_change != previous_checkout_last_change
    checkout_updated_webhook_mock.assert_called_once_with(checkout_with_gift_card)


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_checkout_remove_promo_code_invalid_promo_code(
    checkout_updated_webhook_mock, api_client, checkout_with_item
):
    # given
    checkout_with_item.price_expiration = timezone.now() + timedelta(days=2)
    checkout_with_item.save(update_fields=["price_expiration"])
    previous_checkout_last_change = checkout_with_item.last_change
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "promoCode": "unexisting_code",
    }

    # when
    data = _mutate_checkout_remove_promo_code(api_client, variables)

    # then
    assert data["errors"][0]["field"] == "promoCode"
    assert data["errors"][0]["code"] == CheckoutErrorCode.NOT_FOUND.name
    assert data["errors"][0]["message"] == "Promo code does not exists."

    checkout_with_item.refresh_from_db()
    assert checkout_with_item.last_change == previous_checkout_last_change
    checkout_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_checkout_remove_promo_code_invalid_checkout(
    checkout_updated_webhook_mock, api_client, voucher, checkout
):
    # given
    variables = {"id": to_global_id_or_none(checkout), "promoCode": voucher.code}
    checkout.delete()

    # when
    data = _mutate_checkout_remove_promo_code(api_client, variables)

    # then
    assert data["errors"]
    assert data["errors"][0]["field"] == "id"
    checkout_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_checkout_remove_voucher_code_by_id(
    checkout_updated_webhook_mock, api_client, checkout_with_voucher, voucher, gift_card
):
    # given
    assert checkout_with_voucher.voucher_code is not None
    checkout_with_voucher.gift_cards.add(gift_card)

    variables = {
        "id": to_global_id_or_none(checkout_with_voucher),
        "promoCodeId": graphene.Node.to_global_id("Voucher", voucher.id),
    }

    # when
    data = _mutate_checkout_remove_promo_code(api_client, variables)

    # then
    checkout_with_voucher.refresh_from_db()
    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_voucher.token)
    assert data["checkout"]["voucherCode"] is None
    assert len(data["checkout"]["giftCards"]) == 1
    assert checkout_with_voucher.voucher_code is None
    checkout_updated_webhook_mock.assert_called_once_with(checkout_with_voucher)


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_checkout_remove_voucher_code_by_id_wrong_voucher(
    checkout_updated_webhook_mock,
    api_client,
    checkout_with_voucher,
    voucher,
    gift_card,
    channel_USD,
):
    # given
    assert checkout_with_voucher.voucher_code is not None
    checkout_with_voucher.gift_cards.add(gift_card)
    checkout_with_voucher.price_expiration = timezone.now() + timedelta(days=2)
    checkout_with_voucher.save(update_fields=["price_expiration"])
    previous_checkout_last_change = checkout_with_voucher.last_change

    wrong_voucher = Voucher.objects.create()
    VoucherCode.objects.create(code="voucher", voucher=wrong_voucher)
    VoucherChannelListing.objects.create(
        voucher=wrong_voucher,
        channel=channel_USD,
        discount=Money(20, channel_USD.currency_code),
    )

    variables = {
        "id": to_global_id_or_none(checkout_with_voucher),
        "promoCodeId": graphene.Node.to_global_id("Voucher", wrong_voucher.id),
    }

    # when
    data = _mutate_checkout_remove_promo_code(api_client, variables)

    # then
    checkout_with_voucher.refresh_from_db()

    # then
    assert data["errors"][0]["field"] == "promoCodeId"
    assert data["errors"][0]["code"] == CheckoutErrorCode.NOT_FOUND.name
    assert data["errors"][0]["message"] == (
        "Couldn't remove a promo code from a checkout."
    )

    assert checkout_with_voucher.last_change == previous_checkout_last_change
    checkout_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_checkout_remove_voucher_with_multiple_codes_by_id(
    checkout_updated_webhook_mock,
    api_client,
    checkout_with_voucher,
    voucher_with_many_codes,
    gift_card,
):
    # given
    assert checkout_with_voucher.voucher_code is not None
    checkout_with_voucher.gift_cards.add(gift_card)

    variables = {
        "id": to_global_id_or_none(checkout_with_voucher),
        "promoCodeId": graphene.Node.to_global_id(
            "Voucher", voucher_with_many_codes.id
        ),
    }

    # when
    data = _mutate_checkout_remove_promo_code(api_client, variables)

    # then
    checkout_with_voucher.refresh_from_db()
    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_voucher.token)
    assert data["checkout"]["voucherCode"] is None
    assert len(data["checkout"]["giftCards"]) == 1
    assert checkout_with_voucher.voucher_code is None
    checkout_updated_webhook_mock.assert_called_once_with(checkout_with_voucher)


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_checkout_remove_gift_card_by_id(
    checkout_updated_webhook_mock,
    api_client,
    checkout_with_voucher,
    gift_card,
    gift_card_expiry_date,
):
    # given
    assert checkout_with_voucher.voucher_code is not None
    checkout_with_voucher.gift_cards.add(gift_card, gift_card_expiry_date)

    variables = {
        "id": to_global_id_or_none(checkout_with_voucher),
        "promoCodeId": graphene.Node.to_global_id("GiftCard", gift_card.id),
    }

    # when
    data = _mutate_checkout_remove_promo_code(api_client, variables)

    # then
    checkout_with_voucher.refresh_from_db()
    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_voucher.token)
    assert data["checkout"]["voucherCode"] is not None
    gift_cards = data["checkout"]["giftCards"]
    assert len(gift_cards) == 1
    assert gift_cards[0]["id"] == graphene.Node.to_global_id(
        "GiftCard", gift_card_expiry_date.pk
    )
    checkout_updated_webhook_mock.assert_called_once_with(checkout_with_voucher)


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_checkout_remove_promo_code_id_and_code_given(
    checkout_updated_webhook_mock, api_client, checkout_with_voucher, gift_card
):
    # given
    assert checkout_with_voucher.voucher_code is not None

    variables = {
        "id": to_global_id_or_none(checkout_with_voucher),
        "promoCode": checkout_with_voucher.voucher_code,
        "promoCodeId": graphene.Node.to_global_id("GiftCard", gift_card.id),
    }

    # when
    data = _mutate_checkout_remove_promo_code(api_client, variables)

    # then
    assert data["errors"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name
    checkout_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_checkout_remove_promo_code_no_id_and_code_given(
    checkout_updated_webhook_mock, api_client, checkout_with_voucher, gift_card
):
    # given
    assert checkout_with_voucher.voucher_code is not None

    variables = {
        "id": to_global_id_or_none(checkout_with_voucher),
    }

    # when
    data = _mutate_checkout_remove_promo_code(api_client, variables)

    # then
    assert data["errors"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name
    checkout_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_checkout_remove_promo_code_id_does_not_exist(
    checkout_updated_webhook_mock, api_client, checkout_with_voucher, gift_card
):
    # given
    assert checkout_with_voucher.voucher_code is not None

    variables = {
        "id": to_global_id_or_none(checkout_with_voucher),
        "promoCodeId": "Abc",
    }

    # when
    data = _mutate_checkout_remove_promo_code(api_client, variables)

    # then
    assert data["errors"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name
    assert data["errors"][0]["field"] == "promoCodeId"
    checkout_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_checkout_remove_promo_code_invalid_object_type(
    checkout_updated_webhook_mock, api_client, checkout_with_voucher, gift_card
):
    # given
    assert checkout_with_voucher.voucher_code is not None

    variables = {
        "id": to_global_id_or_none(checkout_with_voucher),
        "promoCodeId": graphene.Node.to_global_id("Product", gift_card.id),
    }

    # when
    data = _mutate_checkout_remove_promo_code(api_client, variables)

    # then
    assert data["errors"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.NOT_FOUND.name
    assert data["errors"][0]["field"] == "promoCodeId"
    checkout_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_checkout_remove_voucher_code_invalidates_price(
    checkout_updated_webhook_mock, api_client, checkout_with_item, voucher
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
    checkout_updated_webhook_mock.assert_called_once_with(checkout_with_item)


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_checkout_remove_voucher_code_order_promotion_discount_applied(
    checkout_updated_webhook_mock,
    api_client,
    checkout_with_voucher,
    order_promotion_rule,
):
    # given
    checkout = checkout_with_voucher
    reward_value = Decimal("5")
    order_promotion_rule.reward_value = reward_value
    order_promotion_rule.reward_value_type = RewardValueType.FIXED
    order_promotion_rule.save(update_fields=["reward_value", "reward_value_type"])

    assert checkout.voucher_code is not None
    previous_checkout_last_change = checkout.last_change

    variables = {
        "id": to_global_id_or_none(checkout),
        "promoCode": checkout.voucher_code,
    }

    # when
    data = _mutate_checkout_remove_promo_code(api_client, variables)

    # then
    checkout.refresh_from_db()
    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout.token)
    assert data["checkout"]["voucherCode"] is None
    assert data["checkout"]["discount"]["amount"] == reward_value
    assert checkout.voucher_code is None
    assert checkout.discount_amount == reward_value
    assert checkout.last_change != previous_checkout_last_change
    assert checkout.discounts.count() == 1
    checkout_updated_webhook_mock.assert_called_once_with(checkout_with_voucher)


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_checkout_remove_voucher_code_gift_reward_applied(
    checkout_updated_webhook_mock,
    api_client,
    checkout_with_voucher,
    gift_promotion_rule,
):
    # given
    checkout = checkout_with_voucher

    assert checkout.voucher_code is not None
    previous_checkout_last_change = checkout.last_change

    lines_count = checkout.lines.count()

    variables = {
        "id": to_global_id_or_none(checkout),
        "promoCode": checkout.voucher_code,
    }

    # when
    data = _mutate_checkout_remove_promo_code(api_client, variables)

    # then
    checkout.refresh_from_db()
    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout.token)
    assert data["checkout"]["voucherCode"] is None
    assert data["checkout"]["discount"]["amount"] == 0
    assert checkout.voucher_code is None
    assert not checkout.discount_amount
    assert checkout.last_change != previous_checkout_last_change
    assert not checkout.discounts.all()
    assert checkout.lines.count() == lines_count + 1 == len(data["checkout"]["lines"])
    gift_line = checkout.lines.get(is_gift=True)
    assert gift_line.discounts.count() == 1
    checkout_updated_webhook_mock.assert_called_once_with(checkout_with_voucher)


@patch("saleor.plugins.manager.PluginsManager.checkout_updated")
def test_with_active_problems_flow(
    checkout_updated_webhook_mock,
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
    checkout_updated_webhook_mock.assert_called_once_with(checkout_with_problems)
