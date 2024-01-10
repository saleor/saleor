import pytest

from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions
from .utils import (
    create_voucher,
    create_voucher_channel_listing,
    get_vouchers,
    voucher_bulk_delete,
)


def create_multiple_vouchers(e2e_staff_api_client, channel_id):
    voucher_ids = []

    for i in range(10):
        input = {
            "code": f"voucher_code_{i + 1}",
            "discountValueType": "FIXED",
            "type": "ENTIRE_ORDER",
        }
        voucher_data = create_voucher(e2e_staff_api_client, input)

        voucher_id = voucher_data["id"]
        channel_listing = [
            {
                "channelId": channel_id,
                "discountValue": i + 1,
            },
        ]
        create_voucher_channel_listing(
            e2e_staff_api_client,
            voucher_id,
            channel_listing,
        )

        voucher_ids.append(voucher_id)

    return voucher_ids


@pytest.mark.e2e
def test_staff_can_delete_vouchers_in_bulk_CORE_0924(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_discounts,
    permission_manage_checkouts,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_discounts,
        permission_manage_checkouts,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]

    voucher_ids = create_multiple_vouchers(e2e_staff_api_client, channel_id)

    # Step 1 - Delete vouchers
    voucher_id_list_to_delete = voucher_ids[:3]
    data = voucher_bulk_delete(e2e_staff_api_client, voucher_id_list_to_delete)

    # Step 2 - Verify the vouchers do not exist
    data = get_vouchers(e2e_staff_api_client)
    voucher_edges = data["vouchers"]["edges"]

    existing_voucher_ids = []
    non_existing_voucher_ids = []

    for voucher_id in voucher_id_list_to_delete:
        if voucher_id in voucher_edges:
            existing_voucher_ids.append(voucher_id)
        else:
            non_existing_voucher_ids.append(voucher_id)

    assert not existing_voucher_ids
    assert non_existing_voucher_ids == voucher_id_list_to_delete
