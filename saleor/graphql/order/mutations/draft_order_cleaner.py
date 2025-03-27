from django.core.exceptions import ValidationError

from ....channel.models import Channel
from ....core.utils.url import validate_storefront_url
from ....discount.models import Voucher, VoucherCode
from ....discount.utils.voucher import (
    get_active_voucher_code,
    get_voucher_code_instance,
)
from ....order.error_codes import OrderErrorCode


def clean_redirect_url(redirect_url: str, cleaned_input: dict):
    if not redirect_url:
        return

    try:
        validate_storefront_url(redirect_url)
    except ValidationError as e:
        e.code = OrderErrorCode.INVALID.value
        raise ValidationError({"redirect_url": e}) from e

    cleaned_input["redirect_url"] = redirect_url


def clean_voucher_and_voucher_code(channel: "Channel", cleaned_input: dict):
    voucher = cleaned_input.get("voucher", None)
    voucher_code = cleaned_input.get("voucher_code", None)
    if voucher and voucher_code:
        raise ValidationError(
            {
                "voucher": ValidationError(
                    "You cannot use both a voucher and a voucher code for the same "
                    "order. Please choose one.",
                    code=OrderErrorCode.INVALID.value,
                )
            }
        )

    if "voucher" in cleaned_input:
        clean_voucher(voucher, channel, cleaned_input)
    elif "voucher_code" in cleaned_input:
        clean_voucher_code(voucher_code, channel, cleaned_input)


def clean_voucher(voucher: Voucher | None, channel: Channel, cleaned_input: dict):
    # We need to clean voucher_code as well
    if voucher is None:
        cleaned_input["voucher_code"] = None
        return

    if isinstance(voucher, VoucherCode):
        raise ValidationError(
            {
                "voucher": ValidationError(
                    "You cannot use voucherCode in the voucher input. "
                    "Please use voucherCode input instead with a valid voucher code.",
                    code=OrderErrorCode.INVALID_VOUCHER.value,
                )
            }
        )

    code_instance = None
    if channel.include_draft_order_in_voucher_usage:
        # Validate voucher when it's included in voucher usage calculation
        try:
            code_instance = get_active_voucher_code(voucher, channel.slug)
        except ValidationError as e:
            raise ValidationError(
                {
                    "voucher": ValidationError(
                        "Voucher is invalid.",
                        code=OrderErrorCode.INVALID_VOUCHER.value,
                    )
                }
            ) from e
    else:
        clean_voucher_listing(voucher, channel, "voucher")
    if not code_instance:
        code_instance = voucher.codes.first()
    if code_instance:
        cleaned_input["voucher_code"] = code_instance.code
        cleaned_input["voucher_code_instance"] = code_instance


def clean_voucher_code(voucher_code: str | None, channel: Channel, cleaned_input: dict):
    # We need to clean voucher instance as well
    if voucher_code is None:
        cleaned_input["voucher"] = None
        return
    if channel.include_draft_order_in_voucher_usage:
        # Validate voucher when it's included in voucher usage calculation
        try:
            code_instance = get_voucher_code_instance(voucher_code, channel.slug)
        except ValidationError as e:
            raise ValidationError(
                {
                    "voucher_code": ValidationError(
                        "Voucher code is invalid.",
                        code=OrderErrorCode.INVALID_VOUCHER_CODE.value,
                    )
                }
            ) from e
        voucher = code_instance.voucher
    else:
        code_instance = VoucherCode.objects.filter(code=voucher_code).first()
        if not code_instance:
            raise ValidationError(
                {
                    "voucher": ValidationError(
                        "Invalid voucher code.",
                        code=OrderErrorCode.INVALID_VOUCHER_CODE.value,
                    )
                }
            )
        voucher = code_instance.voucher
        clean_voucher_listing(voucher, channel, "voucher_code")
    cleaned_input["voucher"] = voucher
    cleaned_input["voucher_code"] = voucher_code
    cleaned_input["voucher_code_instance"] = code_instance


def clean_voucher_listing(voucher: "Voucher", channel: "Channel", field: str):
    if not voucher.channel_listings.filter(channel=channel).exists():
        raise ValidationError(
            {
                field: ValidationError(
                    "Voucher not available for this order.",
                    code=OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.value,
                )
            }
        )
