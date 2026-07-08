from decimal import Decimal

import graphene

from .....giftcard import GiftCardEvents
from .....giftcard.error_codes import GiftCardErrorCode
from .....giftcard.models import GiftCardEvent
from ....tests.utils import assert_no_permission, get_graphql_content

MUTATION = """
    mutation GiftCardBalanceAdjust($id: ID!, $amount: Decimal!) {
        giftCardBalanceAdjust(id: $id, amount: $amount) {
            giftCard {
                id
                currentBalance { amount }
                initialBalance { amount }
            }
            errors { field code message }
        }
    }
"""


def _adjust(api_client, gift_card, amount, permissions=None):
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "amount": str(amount),
    }
    kwargs = {"permissions": permissions} if permissions is not None else {}
    response = api_client.post_graphql(MUTATION, variables, **kwargs)
    return response


def test_increase_balance(staff_api_client, gift_card, permission_manage_gift_card):
    # given
    gift_card.current_balance_amount = Decimal("50.00")
    gift_card.initial_balance_amount = Decimal("100.00")
    gift_card.save(update_fields=["current_balance_amount", "initial_balance_amount"])

    # when
    response = _adjust(
        staff_api_client, gift_card, Decimal("20.00"), [permission_manage_gift_card]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardBalanceAdjust"]
    assert data["errors"] == []
    assert data["giftCard"]["currentBalance"]["amount"] == 70.0
    assert data["giftCard"]["initialBalance"]["amount"] == 100.0
    gift_card.refresh_from_db()
    assert gift_card.current_balance_amount == Decimal("70.00")
    assert gift_card.events.filter(type=GiftCardEvents.BALANCE_ADJUSTED).count() == 1


def test_increase_above_initial_bumps_initial(
    staff_api_client, gift_card, permission_manage_gift_card
):
    # given
    gift_card.current_balance_amount = Decimal("90.00")
    gift_card.initial_balance_amount = Decimal("100.00")
    gift_card.save(update_fields=["current_balance_amount", "initial_balance_amount"])

    # when
    response = _adjust(
        staff_api_client, gift_card, Decimal("30.00"), [permission_manage_gift_card]
    )

    # then
    data = get_graphql_content(response)["data"]["giftCardBalanceAdjust"]
    assert data["giftCard"]["currentBalance"]["amount"] == 120.0
    assert data["giftCard"]["initialBalance"]["amount"] == 120.0


def test_decrease_clamps_to_zero(
    staff_api_client, gift_card, permission_manage_gift_card
):
    # given
    gift_card.current_balance_amount = Decimal("10.00")
    gift_card.initial_balance_amount = Decimal("100.00")
    gift_card.save(update_fields=["current_balance_amount", "initial_balance_amount"])

    # when
    response = _adjust(
        staff_api_client, gift_card, Decimal("-25.00"), [permission_manage_gift_card]
    )

    # then
    data = get_graphql_content(response)["data"]["giftCardBalanceAdjust"]
    assert data["giftCard"]["currentBalance"]["amount"] == 0.0
    assert data["giftCard"]["initialBalance"]["amount"] == 100.0


def test_zero_amount_is_rejected(
    staff_api_client, gift_card, permission_manage_gift_card
):
    # given
    balance_before = gift_card.current_balance_amount

    # when
    response = _adjust(
        staff_api_client, gift_card, Decimal(0), [permission_manage_gift_card]
    )

    # then
    data = get_graphql_content(response)["data"]["giftCardBalanceAdjust"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "amount"
    assert data["errors"][0]["code"] == GiftCardErrorCode.INVALID.name
    gift_card.refresh_from_db()
    assert gift_card.current_balance_amount == balance_before
    assert not GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.BALANCE_ADJUSTED
    ).exists()


def test_requires_permission(staff_api_client, gift_card):
    # given
    balance_before = gift_card.current_balance_amount

    # when
    response = _adjust(staff_api_client, gift_card, Decimal("10.00"))

    # then
    assert_no_permission(response)
    gift_card.refresh_from_db()
    assert gift_card.current_balance_amount == balance_before
