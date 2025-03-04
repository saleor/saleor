from typing import TYPE_CHECKING

from django.conf import settings
from django.db import transaction

from ...checkout.base_calculations import (
    base_checkout_delivery_price,
    base_checkout_subtotal,
)
from ...checkout.models import Checkout
from ...core.db.connection import allow_writer
from .. import DiscountType
from ..models import (
    CheckoutDiscount,
    CheckoutLineDiscount,
)
from .promotion import (
    _get_rule_discount_amount,
    create_discount_objects_for_order_promotions,
    delete_gift_line,
    get_discount_name,
    get_discount_translated_name,
    is_discounted_line_by_catalogue_promotion,
    prepare_promotion_discount_reason,
    update_promotion_discount,
)
from .shared import update_line_info_cached_discounts

if TYPE_CHECKING:
    from ...checkout.fetch import CheckoutInfo, CheckoutLineInfo


def create_or_update_discount_objects_from_promotion_for_checkout(
    checkout_info: "CheckoutInfo",
    lines_info: list["CheckoutLineInfo"],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    create_checkout_line_discount_objects_for_catalogue_promotions(lines_info)
    create_checkout_discount_objects_for_order_promotions(
        checkout_info, lines_info, database_connection_name=database_connection_name
    )


def create_checkout_line_discount_objects_for_catalogue_promotions(
    lines_info: list["CheckoutLineInfo"],
):
    discount_data = prepare_checkout_line_discount_objects_for_catalogue_promotions(
        lines_info
    )
    if not discount_data or not lines_info:
        return

    (
        discounts_to_create_inputs,
        discounts_to_update,
        discount_to_remove,
        updated_fields,
    ) = discount_data

    new_line_discounts = []
    with allow_writer():
        with transaction.atomic():
            # Protect against potential thread race. CheckoutLine object can have only
            # single catalogue discount applied.
            checkout_id = lines_info[0].line.checkout_id
            _checkout_lock = list(
                Checkout.objects.filter(pk=checkout_id).select_for_update(of=(["self"]))
            )

            if discount_ids_to_remove := [
                discount.id for discount in discount_to_remove
            ]:
                CheckoutLineDiscount.objects.filter(
                    id__in=discount_ids_to_remove
                ).delete()

            if discounts_to_create_inputs:
                new_line_discounts = [
                    CheckoutLineDiscount(**input)
                    for input in discounts_to_create_inputs
                ]
                CheckoutLineDiscount.objects.bulk_create(
                    new_line_discounts, ignore_conflicts=True
                )

            if discounts_to_update and updated_fields:
                CheckoutLineDiscount.objects.bulk_update(
                    discounts_to_update, updated_fields
                )

    update_line_info_cached_discounts(
        lines_info, new_line_discounts, discounts_to_update, discount_ids_to_remove
    )


def prepare_checkout_line_discount_objects_for_catalogue_promotions(
    lines_info: list["CheckoutLineInfo"],
) -> (
    tuple[list[dict], list[CheckoutLineDiscount], list[CheckoutLineDiscount], list[str]]
    | None
):
    line_discounts_to_create_inputs: list[dict] = []
    line_discounts_to_update: list[CheckoutLineDiscount] = []
    line_discounts_to_remove: list[CheckoutLineDiscount] = []
    updated_fields: list[str] = []

    if not lines_info:
        return None

    for line_info in lines_info:
        line = line_info.line

        # if channel_listing is not present, we can't close the checkout. User needs to
        # remove the line for the checkout first. Until that moment, we return the same
        # price as we did when listing was present - including line discount.
        if not line_info.channel_listing:
            continue

        # get the existing catalogue discount for the line
        discount_to_update = None
        if discounts_to_update := line_info.get_catalogue_discounts():
            discount_to_update = discounts_to_update[0]
            # Line should never have multiple catalogue discounts associated. Before
            # introducing unique_type on discount models, there was such a possibility.
            line_discounts_to_remove.extend(discounts_to_update[1:])

        # manual line discount do not stack with other line discounts
        if [
            discount
            for discount in line_info.discounts
            if discount.type == DiscountType.MANUAL
        ]:
            line_discounts_to_remove.extend(discounts_to_update)
            continue

        # check if the line price is discounted by catalogue promotion
        discounted_line = is_discounted_line_by_catalogue_promotion(
            line_info.channel_listing
        )

        # delete all existing discounts if the line is not discounted or it is a gift
        if not discounted_line or line.is_gift:
            line_discounts_to_remove.extend(discounts_to_update)
            continue

        if line_info.rules_info:
            rule_info = line_info.rules_info[0]
            rule = rule_info.rule
            rule_discount_amount = _get_rule_discount_amount(
                line, rule_info, line_info.channel
            )
            discount_name = get_discount_name(rule, rule_info.promotion)
            translated_name = get_discount_translated_name(rule_info)
            reason = prepare_promotion_discount_reason(rule_info.promotion)
            if not discount_to_update:
                line_discount_input = {
                    "line": line,
                    "type": DiscountType.PROMOTION,
                    "value_type": rule.reward_value_type,
                    "value": rule.reward_value,
                    "amount_value": rule_discount_amount,
                    "currency": line.currency,
                    "name": discount_name,
                    "translated_name": translated_name,
                    "reason": reason,
                    "promotion_rule": rule,
                    "unique_type": DiscountType.PROMOTION,
                }
                line_discounts_to_create_inputs.append(line_discount_input)
            else:
                update_promotion_discount(
                    rule,
                    rule_info,
                    rule_discount_amount,
                    discount_to_update,
                    updated_fields,
                )
                line_discounts_to_update.append(discount_to_update)
        else:
            # Fallback for unlike mismatch between discount_amount and rules_info
            line_discounts_to_remove.extend(discounts_to_update)

    return (
        line_discounts_to_create_inputs,
        line_discounts_to_update,
        line_discounts_to_remove,
        updated_fields,
    )


def create_checkout_discount_objects_for_order_promotions(
    checkout_info: "CheckoutInfo",
    lines_info: list["CheckoutLineInfo"],
    *,
    save: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    # The base prices are required for order promotion discount qualification.
    _set_checkout_base_prices(checkout_info, lines_info)

    checkout = checkout_info.checkout

    # Discount from order rules is applied only when the voucher is not set
    if checkout.voucher_code:
        _clear_checkout_discount(checkout_info, lines_info, save)
        return

    (
        gift_promotion_applied,
        discount_object,
    ) = create_discount_objects_for_order_promotions(
        checkout,
        lines_info,
        checkout.base_subtotal,
        checkout_info.channel,
        checkout_info.get_country(),
        database_connection_name=database_connection_name,
    )
    if not gift_promotion_applied and not discount_object:
        _clear_checkout_discount(checkout_info, lines_info, save)
        return

    if discount_object:
        checkout_info.discounts = [discount_object]
        checkout = checkout_info.checkout
        checkout.discount_amount = discount_object.amount_value
        checkout.discount_name = discount_object.name
        checkout.translated_discount_name = discount_object.translated_name
        if save:
            checkout.save(
                update_fields=[
                    "discount_amount",
                    "discount_name",
                    "translated_discount_name",
                ]
            )


def _set_checkout_base_prices(checkout_info, lines_info):
    """Set base checkout prices that includes only catalogue discounts."""
    checkout = checkout_info.checkout
    subtotal = base_checkout_subtotal(
        lines_info, checkout_info.channel, checkout.currency, include_voucher=False
    )
    shipping_price = base_checkout_delivery_price(
        checkout_info, lines_info, include_voucher=False
    )
    total = subtotal + shipping_price
    is_update_needed = not (
        checkout.base_subtotal == subtotal and checkout.base_total == total
    )
    if is_update_needed:
        checkout.base_subtotal = subtotal
        checkout.base_total = total
        with allow_writer():
            checkout.save(update_fields=["base_total_amount", "base_subtotal_amount"])


def _clear_checkout_discount(
    checkout_info: "CheckoutInfo", lines_info: list["CheckoutLineInfo"], save: bool
):
    delete_gift_line(checkout_info.checkout, lines_info)
    if checkout_info.discounts:
        CheckoutDiscount.objects.filter(
            checkout=checkout_info.checkout,
            type=DiscountType.ORDER_PROMOTION,
        ).delete()
        checkout_info.discounts = [
            discount
            for discount in checkout_info.discounts
            if discount.type != DiscountType.ORDER_PROMOTION
        ]
    checkout = checkout_info.checkout
    if not checkout_info.voucher_code:
        is_update_needed = not (
            checkout.discount_amount == 0
            and checkout.discount_name is None
            and checkout.translated_discount_name is None
        )
        if is_update_needed:
            checkout.discount_amount = 0
            checkout.discount_name = None
            checkout.translated_discount_name = None

            if save and is_update_needed:
                checkout.save(
                    update_fields=[
                        "discount_amount",
                        "discount_name",
                        "translated_discount_name",
                    ]
                )


def has_checkout_order_promotion(checkout_info: "CheckoutInfo") -> bool:
    return next(
        (
            True
            for discount in checkout_info.discounts
            if discount.type == DiscountType.ORDER_PROMOTION
        ),
        False,
    )
