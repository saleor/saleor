import datetime

import graphene
import pytest
from django.utils import timezone

from .....order.error_codes import OrderErrorCode
from ....core.enums import PromoCodeRejectionReason
from ....tests.utils import get_graphql_content

DRAFT_ORDER_UPDATE_MUTATION = """
    mutation draftUpdate($id: ID!, $input: DraftOrderInput!) {
        draftOrderUpdate(id: $id, input: $input) {
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
                    countries
                }
            }
        }
    }
"""

DRAFT_ORDER_COMPLETE_MUTATION = """
    mutation draftComplete($id: ID!) {
        draftOrderComplete(id: $id) {
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
                    countries
                }
            }
        }
    }
"""

NO_PARAMS = {"minSpent": None, "minCheckoutItemsQuantity": None, "countries": None}


def _expire(voucher):
    voucher.end_date = timezone.now() - datetime.timedelta(days=1)
    voucher.save(update_fields=["end_date"])


def _deactivate_code(voucher):
    code = voucher.codes.get()
    code.is_active = False
    code.save(update_fields=["is_active"])


def _assert_single_error(data, expected_code, expected_field, expected_reason):
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == expected_field
    assert error["code"] == expected_code.name
    assert error["promoCodeDetails"] == NO_PARAMS | {"reason": expected_reason.name}


@pytest.mark.parametrize(
    ("_case", "setup", "expected_reason"),
    [
        ("expired_voucher", _expire, PromoCodeRejectionReason.EXPIRED),
        (
            "deactivated_code",
            _deactivate_code,
            PromoCodeRejectionReason.CODE_DEACTIVATED,
        ),
    ],
)
def test_draft_order_update_voucher_code(
    _case,
    setup,
    expected_reason,
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    voucher,
):
    """Report the rejection reason for the `voucherCode` input."""
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    code = voucher.codes.get().code
    setup(voucher)
    variables = {
        "id": graphene.Node.to_global_id("Order", draft_order.pk),
        "input": {"voucherCode": code},
    }

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_UPDATE_MUTATION, variables)

    # then
    data = get_graphql_content(response)["data"]["draftOrderUpdate"]
    _assert_single_error(
        data, OrderErrorCode.INVALID_VOUCHER_CODE, "voucherCode", expected_reason
    )
    draft_order.refresh_from_db(fields=("voucher_code",))
    assert draft_order.voucher_code is None


def test_draft_order_update_unknown_voucher_code(
    staff_api_client, permission_group_manage_orders, draft_order
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "id": graphene.Node.to_global_id("Order", draft_order.pk),
        "input": {"voucherCode": "THIS-CODE-DOES-NOT-EXIST"},
    }

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_UPDATE_MUTATION, variables)

    # then
    data = get_graphql_content(response)["data"]["draftOrderUpdate"]
    _assert_single_error(
        data,
        OrderErrorCode.INVALID_VOUCHER_CODE,
        "voucherCode",
        PromoCodeRejectionReason.NOT_FOUND,
    )


@pytest.mark.parametrize(
    ("_case", "setup", "expected_reason"),
    [
        ("expired_voucher", _expire, PromoCodeRejectionReason.EXPIRED),
        (
            "deactivated_code",
            _deactivate_code,
            PromoCodeRejectionReason.CODE_DEACTIVATED,
        ),
    ],
)
def test_draft_order_update_voucher(
    _case,
    setup,
    expected_reason,
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    voucher,
):
    """Report the rejection reason for the deprecated `voucher` ID input."""
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    setup(voucher)
    variables = {
        "id": graphene.Node.to_global_id("Order", draft_order.pk),
        "input": {"voucher": graphene.Node.to_global_id("Voucher", voucher.pk)},
    }

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_UPDATE_MUTATION, variables)

    # then
    data = get_graphql_content(response)["data"]["draftOrderUpdate"]
    _assert_single_error(
        data, OrderErrorCode.INVALID_VOUCHER, "voucher", expected_reason
    )
    draft_order.refresh_from_db(fields=("voucher_id",))
    assert draft_order.voucher_id is None


def test_draft_order_complete_voucher_not_in_channel(
    staff_api_client, permission_group_manage_orders, draft_order_with_voucher
):
    """Report the rejection reason raised while validating the draft order."""
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order_with_voucher
    order.voucher.channel_listings.all().delete()
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)

    # then
    data = get_graphql_content(response)["data"]["draftOrderComplete"]
    _assert_single_error(
        data,
        OrderErrorCode.INVALID_VOUCHER,
        "voucher",
        PromoCodeRejectionReason.NOT_AVAILABLE_IN_CHANNEL,
    )
    assert data["order"] is None
