from datetime import timedelta
from typing import Optional

from django.core.exceptions import ValidationError

from saleor.graphql.core.enums import ChannelErrorCode

DELETE_EXPIRED_ORDERS_MAX_DAYS = 120


def clean_expire_orders_after(expire_orders_after: int) -> Optional[int]:
    if expire_orders_after is None or expire_orders_after == 0:
        return None
    if expire_orders_after < 0:
        raise ValidationError(
            {
                "expire_orders_after": ValidationError(
                    "Expiration time for orders cannot be lower than 0.",
                    code=ChannelErrorCode.INVALID.value,
                )
            }
        )
    return expire_orders_after


def clean_delete_expired_orders_after(delete_expired_orders_after: int) -> timedelta:
    if (
        delete_expired_orders_after < 1
        or delete_expired_orders_after > DELETE_EXPIRED_ORDERS_MAX_DAYS
    ):
        raise ValidationError(
            {
                "delete_expired_orders_after": ValidationError(
                    "Delete time for expired orders needs to be in range from 1 to "
                    f"{DELETE_EXPIRED_ORDERS_MAX_DAYS}.",
                    code=ChannelErrorCode.INVALID.value,
                )
            }
        )
    return timedelta(days=delete_expired_orders_after)


def clean_input_order_settings(order_settings: dict, cleaned_input: dict):
    automatically_confirm_all_new_orders = order_settings.get(
        "automatically_confirm_all_new_orders"
    )
    if automatically_confirm_all_new_orders is not None:
        cleaned_input[
            "automatically_confirm_all_new_orders"
        ] = automatically_confirm_all_new_orders

    automatically_fulfill_non_shippable_gift_card = order_settings.get(
        "automatically_fulfill_non_shippable_gift_card"
    )
    if automatically_fulfill_non_shippable_gift_card is not None:
        cleaned_input[
            "automatically_fulfill_non_shippable_gift_card"
        ] = automatically_fulfill_non_shippable_gift_card
    if mark_as_paid_strategy := order_settings.get("mark_as_paid_strategy"):
        cleaned_input["order_mark_as_paid_strategy"] = mark_as_paid_strategy

    if "expire_orders_after" in order_settings:
        expire_orders_after = order_settings["expire_orders_after"]
        cleaned_input["expire_orders_after"] = clean_expire_orders_after(
            expire_orders_after
        )

    if "delete_expired_orders_after" in order_settings:
        delete_expired_orders_after = order_settings["delete_expired_orders_after"]
        cleaned_input[
            "delete_expired_orders_after"
        ] = clean_delete_expired_orders_after(delete_expired_orders_after)

    if default_transaction_strategy := order_settings.get(
        "default_transaction_flow_strategy"
    ):
        cleaned_input[
            "default_transaction_flow_strategy"
        ] = default_transaction_strategy

    allow_unpaid_orders = order_settings.get("allow_unpaid_orders")
    if allow_unpaid_orders is not None:
        cleaned_input["allow_unpaid_orders"] = allow_unpaid_orders


def clean_input_checkout_settings(checkout_settings: dict, cleaned_input: dict):
    if "use_legacy_error_flow" in checkout_settings:
        cleaned_input["use_legacy_error_flow_for_checkout"] = checkout_settings[
            "use_legacy_error_flow"
        ]


def clean_input_payment_settings(payment_settings: dict, cleaned_input: dict):
    if default_transaction_strategy := payment_settings.get(
        "default_transaction_flow_strategy"
    ):
        cleaned_input[
            "default_transaction_flow_strategy"
        ] = default_transaction_strategy
