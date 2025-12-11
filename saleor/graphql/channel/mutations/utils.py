import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from ....channel.models import Channel
from ...core.enums import ChannelErrorCode

CHANNEL_UPDATE_FIELDS = [
    "name",
    "slug",
    "default_country",
    "is_active",
    "allocation_strategy",
    "automatically_confirm_all_new_orders",
    "automatically_fulfill_non_shippable_gift_card",
    "expire_orders_after",
    "delete_expired_orders_after",
    "order_mark_as_paid_strategy",
    "allow_unpaid_orders",
    "include_draft_order_in_voucher_usage",
    "draft_order_line_price_freeze_period",
    "use_legacy_line_discount_propagation_for_order",
    "use_legacy_error_flow_for_checkout",
    "automatically_complete_fully_paid_checkouts",
    "automatic_completion_delay",
    "automatic_completion_cut_off_date",
    "default_transaction_flow_strategy",
    "release_funds_for_expired_checkouts",
    "checkout_ttl_before_releasing_funds",
    "checkout_release_funds_cut_off_date",
    "allow_legacy_gift_card_use",
    "metadata",
    "private_metadata",
]

DELETE_EXPIRED_ORDERS_MAX_DAYS = 120


def clean_expire_orders_after(expire_orders_after: int) -> int | None:
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


def clean_delete_expired_orders_after(
    delete_expired_orders_after: int,
) -> datetime.timedelta:
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
    return datetime.timedelta(days=delete_expired_orders_after)


def clean_checkout_ttl_before_releasing_funds(
    checkout_ttl_before_releasing_funds: int,
) -> datetime.timedelta:
    if checkout_ttl_before_releasing_funds <= 0:
        raise ValidationError(
            {
                "checkout_ttl_before_releasing_funds": ValidationError(
                    "The time in hours after which funds for expired checkouts will be released must be greater than 0.",
                    code=ChannelErrorCode.INVALID.value,
                )
            }
        )
    return datetime.timedelta(hours=checkout_ttl_before_releasing_funds)


def clean_input_order_settings(
    order_settings: dict, cleaned_input: dict, instance: Channel
):
    channel_settings = [
        "automatically_confirm_all_new_orders",
        "automatically_fulfill_non_shippable_gift_card",
        "allow_unpaid_orders",
        "include_draft_order_in_voucher_usage",
    ]

    for field in channel_settings:
        if (value := order_settings.get(field)) is not None:
            cleaned_input[field] = value

    if (
        mark_as_paid_strategy := order_settings.get("mark_as_paid_strategy")
    ) is not None:
        cleaned_input["order_mark_as_paid_strategy"] = mark_as_paid_strategy

    if "expire_orders_after" in order_settings:
        expire_orders_after = order_settings["expire_orders_after"]
        cleaned_input["expire_orders_after"] = clean_expire_orders_after(
            expire_orders_after
        )

    if "delete_expired_orders_after" in order_settings:
        delete_expired_orders_after = order_settings["delete_expired_orders_after"]
        cleaned_input["delete_expired_orders_after"] = (
            clean_delete_expired_orders_after(delete_expired_orders_after)
        )

    cleaned_input["prev_include_draft_order_in_voucher_usage"] = (
        instance.include_draft_order_in_voucher_usage
    )

    if "draft_order_line_price_freeze_period" in order_settings:
        cleaned_input["draft_order_line_price_freeze_period"] = order_settings[
            "draft_order_line_price_freeze_period"
        ]

    # For newly created channels, by default use new discount propagation flow
    if instance.pk is None:
        cleaned_input["use_legacy_line_discount_propagation_for_order"] = False

    if order_settings.get("use_legacy_line_discount_propagation") is not None:
        cleaned_input["use_legacy_line_discount_propagation_for_order"] = (
            order_settings["use_legacy_line_discount_propagation"]
        )


def clean_input_checkout_settings(
    checkout_settings: dict, cleaned_input: dict, instance: Channel | None = None
):
    clean_automatic_completion(checkout_settings, cleaned_input)

    if "allow_legacy_gift_card_use" in checkout_settings:
        cleaned_input["allow_legacy_gift_card_use"] = checkout_settings[
            "allow_legacy_gift_card_use"
        ]

    # Handle legacy fields
    if "use_legacy_error_flow" in checkout_settings:
        cleaned_input["use_legacy_error_flow_for_checkout"] = checkout_settings[
            "use_legacy_error_flow"
        ]


def clean_automatic_completion(checkout_settings: dict, cleaned_input: dict):
    # Validate that both old and new fields aren't provided together
    if (
        "automatically_complete_fully_paid_checkouts" in checkout_settings
        and "automatic_completion" in checkout_settings
    ):
        raise ValidationError(
            {
                "automatically_complete_fully_paid_checkouts": ValidationError(
                    "Cannot provide both 'automaticallyCompleteFullyPaidCheckouts' "
                    "and 'automaticCompletion'. Use 'automaticCompletion' instead.",
                    code=ChannelErrorCode.INVALID.value,
                )
            }
        )

    # Handle the automatic_completion nested input
    if automatic_completion := checkout_settings.get("automatic_completion"):
        enabled = automatic_completion.get("enabled")
        delay = automatic_completion.get("delay")
        cut_off_date = automatic_completion.get("cut_off_date")

        cleaned_input["automatically_complete_fully_paid_checkouts"] = enabled
        clean_automatic_completion_delay(delay, enabled, cleaned_input)
        clean_automatic_completion_cut_off_date(cut_off_date, enabled, cleaned_input)
    # Handle deprecated field for backward compatibility
    elif "automatically_complete_fully_paid_checkouts" in checkout_settings:
        automatically_complete = checkout_settings[
            "automatically_complete_fully_paid_checkouts"
        ]
        cleaned_input["automatically_complete_fully_paid_checkouts"] = (
            automatically_complete
        )
        cleaned_input["automatic_completion_delay"] = (
            settings.DEFAULT_AUTOMATIC_CHECKOUT_COMPLETION_DELAY
            if automatically_complete is True
            else None
        )
        cleaned_input["automatic_completion_cut_off_date"] = (
            timezone.now() if automatically_complete else None
        )


def clean_automatic_completion_delay(
    delay: int, automatic_completion_enabled: bool, cleaned_input: dict
):
    if automatic_completion_enabled is False:
        if delay is not None:
            raise ValidationError(
                {
                    "delay": ValidationError(
                        "The delay cannot be set when automatic completion is disabled.",
                        code=ChannelErrorCode.INVALID.value,
                    )
                }
            )
        # When disabled, clear the delay
        cleaned_input["automatic_completion_delay"] = None
    else:
        oldest_allowed_checkout = (
            settings.AUTOMATIC_CHECKOUT_COMPLETION_OLDEST_MODIFIED.total_seconds() // 60
        )
        if delay is not None:
            if delay < 0:
                raise ValidationError(
                    {
                        "delay": ValidationError(
                            "The automatic completion delay must be greater than or equal to 0.",
                            code=ChannelErrorCode.INVALID.value,
                        )
                    }
                )
            if delay >= oldest_allowed_checkout:
                raise ValidationError(
                    {
                        "delay": ValidationError(
                            f"The automatic completion delay must be less than "
                            f"{oldest_allowed_checkout}, that is the threshold for the "
                            "oldest modified checkout eligible for automatic "
                            "completion.",
                            code=ChannelErrorCode.INVALID.value,
                        )
                    }
                )
            cleaned_input["automatic_completion_delay"] = delay
        else:
            # If enabled and delay is missing, set default
            cleaned_input["automatic_completion_delay"] = (
                settings.DEFAULT_AUTOMATIC_CHECKOUT_COMPLETION_DELAY
            )


def clean_automatic_completion_cut_off_date(
    cut_off_date: datetime.datetime,
    automatic_completion_enabled: bool,
    cleaned_input: dict,
):
    if automatic_completion_enabled is False:
        if cut_off_date is not None:
            raise ValidationError(
                {
                    "cut_off_date": ValidationError(
                        "The cut-off date cannot be set when automatic completion is disabled.",
                        code=ChannelErrorCode.INVALID.value,
                    )
                }
            )
        # When disabled, clear the delay
        cleaned_input["automatic_completion_cut_off_date"] = None
    else:
        if cut_off_date is not None:
            if (
                cut_off_date
                < timezone.now()
                - settings.AUTOMATIC_CHECKOUT_COMPLETION_OLDEST_MODIFIED
            ):
                raise ValidationError(
                    {
                        "cut_off_date": ValidationError(
                            "The cut-off date must be more recent than "
                            "the threshold for the oldest modified checkout "
                            "eligible for automatic completion.",
                            code=ChannelErrorCode.INVALID.value,
                        )
                    }
                )
            cleaned_input["automatic_completion_cut_off_date"] = cut_off_date
        else:
            cleaned_input["automatic_completion_cut_off_date"] = timezone.now()


def clean_input_payment_settings(payment_settings: dict, cleaned_input: dict):
    if default_transaction_strategy := payment_settings.get(
        "default_transaction_flow_strategy"
    ):
        cleaned_input["default_transaction_flow_strategy"] = (
            default_transaction_strategy
        )
    if (
        release_funds_for_expired_checkouts := payment_settings.get(
            "release_funds_for_expired_checkouts"
        )
    ) is not None:
        cleaned_input["release_funds_for_expired_checkouts"] = (
            release_funds_for_expired_checkouts
        )

    if (
        checkout_ttl_before_releasing_funds := payment_settings.get(
            "checkout_ttl_before_releasing_funds"
        )
    ) is not None:
        cleaned_input["checkout_ttl_before_releasing_funds"] = (
            clean_checkout_ttl_before_releasing_funds(
                checkout_ttl_before_releasing_funds
            )
        )

    if "checkout_release_funds_cut_off_date" in payment_settings:
        checkout_release_funds_cut_off_date = payment_settings[
            "checkout_release_funds_cut_off_date"
        ]
        cleaned_input["checkout_release_funds_cut_off_date"] = (
            checkout_release_funds_cut_off_date
        )
