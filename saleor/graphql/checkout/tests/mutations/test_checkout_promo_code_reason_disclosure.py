"""Guard the information the voucher rejection reason may disclose.

Each test pins a case where reporting the true reason would let an
unprivileged caller confirm something they are not entitled to know.
"""

import datetime

import pytest
from django.utils import timezone

from .....checkout.error_codes import CheckoutErrorCode
from .....discount.models import VoucherCustomer
from .....permission.enums import DiscountPermissions
from ....core.enums import PromoCodeRejectionReason
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

MUTATION_ADD_PROMO_CODE = """
    mutation($id: ID, $promoCode: String!) {
        checkoutAddPromoCode(id: $id, promoCode: $promoCode) {
            errors {
                field
                code
                message
                promoCodeDetails {
                    reason
                }
            }
        }
    }
"""

UNKNOWN_CODE = "NO-SUCH-CODE-AT-ALL"


def _add_promo_code(client, checkout, promo_code):
    variables = {"id": to_global_id_or_none(checkout), "promoCode": promo_code}
    response = client.post_graphql(MUTATION_ADD_PROMO_CODE, variables)
    return get_graphql_content(response)["data"]["checkoutAddPromoCode"]


def _single_error(data):
    assert len(data["errors"]) == 1
    return data["errors"][0]


# --- P1: an unusable gift card must be indistinguishable from an unknown code ---


@pytest.mark.parametrize(
    ("_case", "setup"),
    [
        ("expired", lambda card: _set(card, expiry_date=_yesterday())),
        ("deactivated", lambda card: _set(card, is_active=False)),
        ("wrong_currency", lambda card: _set(card, currency="EUR")),
    ],
)
def test_unusable_gift_card_matches_unknown_code(
    _case, setup, api_client, checkout_with_item, gift_card
):
    # given
    setup(gift_card)
    baseline = _single_error(
        _add_promo_code(api_client, checkout_with_item, UNKNOWN_CODE)
    )
    assert baseline["promoCodeDetails"] == {
        "reason": PromoCodeRejectionReason.NOT_FOUND.name
    }

    # when
    error = _single_error(
        _add_promo_code(api_client, checkout_with_item, gift_card.code)
    )

    # then
    assert error == baseline
    assert checkout_with_item.gift_cards.exists() is False


def test_gift_card_assigned_to_another_customer_matches_unknown_code(
    user_api_client, checkout_with_item, gift_card, staff_user
):
    # given
    gift_card.assigned_to = staff_user
    gift_card.save(update_fields=["assigned_to"])
    assert gift_card.assigned_to_id != user_api_client.user.pk
    baseline = _single_error(
        _add_promo_code(user_api_client, checkout_with_item, UNKNOWN_CODE)
    )

    # when
    error = _single_error(
        _add_promo_code(user_api_client, checkout_with_item, gift_card.code)
    )

    # then
    assert error == baseline
    assert checkout_with_item.gift_cards.exists() is False


# --- P2: redemption history is disclosed only to the verified owner ---


def _mark_used_by(voucher, email):
    voucher.apply_once_per_customer = True
    voucher.save(update_fields=["apply_once_per_customer"])
    VoucherCustomer.objects.create(
        voucher_code=voucher.codes.get(), customer_email=email
    )


def test_already_used_hidden_from_guest_probing_another_email(
    api_client, checkout_with_item, voucher, customer_user
):
    """A guest may set any email, so the reason must not be reported."""
    # given
    _mark_used_by(voucher, customer_user.email)
    checkout_with_item.email = customer_user.email
    checkout_with_item.save(update_fields=["email"])
    assert checkout_with_item.user_id is None

    # when
    error = _single_error(_add_promo_code(api_client, checkout_with_item, voucher.code))

    # then
    assert error["code"] == CheckoutErrorCode.VOUCHER_NOT_APPLICABLE.name
    assert error["promoCodeDetails"] is None


def test_already_used_reported_to_verified_owner(
    user_api_client, checkout_with_item, voucher
):
    # given
    customer = user_api_client.user
    _mark_used_by(voucher, customer.email)
    checkout_with_item.user = customer
    checkout_with_item.email = customer.email
    checkout_with_item.save(update_fields=["user", "email"])

    # when
    error = _single_error(
        _add_promo_code(user_api_client, checkout_with_item, voucher.code)
    )

    # then
    assert error["code"] == CheckoutErrorCode.VOUCHER_NOT_APPLICABLE.name
    assert error["promoCodeDetails"] == {
        "reason": PromoCodeRejectionReason.ALREADY_USED_BY_CUSTOMER.name
    }


# --- P3: private voucher state needs MANAGE_DISCOUNTS ---


def _make_not_started(voucher):
    voucher.start_date = timezone.now() + datetime.timedelta(days=7)
    voucher.save(update_fields=["start_date"])
    return PromoCodeRejectionReason.NOT_STARTED


def _make_out_of_channel(voucher):
    voucher.channel_listings.all().delete()
    return PromoCodeRejectionReason.NOT_AVAILABLE_IN_CHANNEL


@pytest.mark.parametrize(
    ("_case", "setup"),
    [
        ("unlaunched_campaign", _make_not_started),
        ("other_channel_campaign", _make_out_of_channel),
    ],
)
def test_private_reason_hidden_without_permission(
    _case, setup, api_client, checkout_with_item, voucher
):
    # given
    setup(voucher)
    baseline = _single_error(
        _add_promo_code(api_client, checkout_with_item, UNKNOWN_CODE)
    )

    # when
    error = _single_error(_add_promo_code(api_client, checkout_with_item, voucher.code))

    # then
    assert error == baseline
    assert error["promoCodeDetails"] == {
        "reason": PromoCodeRejectionReason.NOT_FOUND.name
    }


@pytest.mark.parametrize(
    ("_case", "setup"),
    [
        ("unlaunched_campaign", _make_not_started),
        ("other_channel_campaign", _make_out_of_channel),
    ],
)
def test_private_reason_reported_with_manage_discounts(
    _case,
    setup,
    staff_api_client,
    checkout_with_item,
    voucher,
    permission_manage_discounts,
):
    # given
    expected_reason = setup(voucher)
    staff_api_client.user.user_permissions.add(permission_manage_discounts)
    assert staff_api_client.user.has_perm(DiscountPermissions.MANAGE_DISCOUNTS.value)

    # when
    error = _single_error(
        _add_promo_code(staff_api_client, checkout_with_item, voucher.code)
    )

    # then
    assert error["promoCodeDetails"] == {"reason": expected_reason.name}


def _yesterday():
    return datetime.datetime.now(tz=datetime.UTC).date() - datetime.timedelta(days=1)


def _set(gift_card, **fields):
    for name, value in fields.items():
        setattr(gift_card, name, value)
    gift_card.save(update_fields=list(fields))
