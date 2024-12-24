from ...vouchers.utils import create_voucher, create_voucher_channel_listing


def prepare_voucher(
    e2e_staff_api_client,
    channel_id,
    voucher_code,
    voucher_discount_type,
    voucher_discount_value,
    voucher_type,
    products_list=None,
    usage_limit=2,
    single_use=True,
    apply_once_per_order=False,
):
    input = {
        "code": voucher_code,
        "discountValueType": voucher_discount_type,
        "type": voucher_type,
        "usageLimit": usage_limit,
        "singleUse": single_use,
        "products": products_list,
        "applyOncePerOrder": apply_once_per_order,
    }
    voucher_data = create_voucher(e2e_staff_api_client, input)

    voucher_id = voucher_data["id"]
    channel_listing = [
        {
            "channelId": channel_id,
            "discountValue": voucher_discount_value,
        },
    ]
    create_voucher_channel_listing(
        e2e_staff_api_client,
        voucher_id,
        channel_listing,
    )

    return voucher_code, voucher_id, voucher_discount_value
