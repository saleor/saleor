"""Report why a gift card already on the checkout can no longer be used.

The card was accepted onto the checkout earlier, so the caller demonstrably
holds it and the reason discloses nothing a code guesser could use. Add-time
rejections stay redacted -- see `test_checkout_promo_code_reason_disclosure`.
"""

import datetime

from .....checkout.error_codes import CheckoutErrorCode
from .....order.models import Order
from ....core.enums import PromoCodeRejectionReason
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content
from .test_checkout_complete_with_transactions import prepare_checkout_for_test

MUTATION_CHECKOUT_COMPLETE = """
    mutation checkoutComplete($id: ID, $redirectUrl: String) {
        checkoutComplete(id: $id, redirectUrl: $redirectUrl) {
            order {
                id
            }
            errors {
                field
                code
                promoCodeDetails {
                    reason
                    minSpent {
                        amount
                        currency
                    }
                    minCheckoutItemsQuantity
                }
            }
        }
    }
"""

NO_PARAMS = {"minSpent": None, "minCheckoutItemsQuantity": None}


def _complete(client, checkout):
    variables = {
        "id": to_global_id_or_none(checkout),
        "redirectUrl": "https://www.example.com",
    }
    response = client.post_graphql(MUTATION_CHECKOUT_COMPLETE, variables)
    return get_graphql_content(response)["data"]["checkoutComplete"]


def _assert_rejected(data, expected_reason):
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "giftCards"
    assert error["code"] == CheckoutErrorCode.INVALID.name
    assert error["promoCodeDetails"] == NO_PARAMS | {"reason": expected_reason.name}
    assert data["order"] is None
    assert Order.objects.exists() is False


def test_expired_gift_card_reports_expired(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    address,
    checkout_delivery,
    transaction_item_generator,
    transaction_events_generator,
):
    # given
    assert checkout_with_gift_card.gift_cards.get() == gift_card
    gift_card.expiry_date = datetime.datetime.now(
        tz=datetime.UTC
    ).date() - datetime.timedelta(days=1)
    gift_card.save(update_fields=["expiry_date"])
    checkout = prepare_checkout_for_test(
        checkout_with_gift_card,
        address,
        address,
        checkout_delivery(checkout_with_gift_card),
        transaction_item_generator,
        transaction_events_generator,
    )

    # when
    data = _complete(user_api_client, checkout)

    # then
    _assert_rejected(data, PromoCodeRejectionReason.EXPIRED)


def test_gift_card_restricted_to_another_customer_reports_not_applicable(
    user_api_client,
    checkout_with_gift_card,
    gift_card,
    staff_user,
    address,
    checkout_delivery,
    transaction_item_generator,
    transaction_events_generator,
):
    """A card may be assigned to someone else after it was added."""
    # given
    assert checkout_with_gift_card.gift_cards.get() == gift_card
    gift_card.assigned_to = staff_user
    gift_card.assigned_to_email = staff_user.email
    gift_card.save(update_fields=["assigned_to", "assigned_to_email"])
    checkout = prepare_checkout_for_test(
        checkout_with_gift_card,
        address,
        address,
        checkout_delivery(checkout_with_gift_card),
        transaction_item_generator,
        transaction_events_generator,
        user=user_api_client.user,
    )
    assert gift_card.assigned_to_id != checkout.user_id

    # when
    data = _complete(user_api_client, checkout)

    # then
    _assert_rejected(data, PromoCodeRejectionReason.NOT_APPLICABLE)
