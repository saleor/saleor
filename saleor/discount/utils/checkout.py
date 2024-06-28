from collections.abc import Iterable
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
    create_discount_objects_for_order_promotions,
    delete_gift_line,
    prepare_line_discount_objects_for_catalogue_promotions,
)
from .shared import update_line_info_cached_discounts

if TYPE_CHECKING:
    from ...checkout.fetch import CheckoutInfo, CheckoutLineInfo


def create_or_update_discount_objects_from_promotion_for_checkout(
    checkout_info: "CheckoutInfo",
    lines_info: Iterable["CheckoutLineInfo"],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    create_checkout_line_discount_objects_for_catalogue_promotions(lines_info)
    create_checkout_discount_objects_for_order_promotions(
        checkout_info, lines_info, database_connection_name=database_connection_name
    )


def create_checkout_line_discount_objects_for_catalogue_promotions(
    lines_info: Iterable["CheckoutLineInfo"],
):
    discount_data = prepare_line_discount_objects_for_catalogue_promotions(lines_info)
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
            checkout_id = lines_info[0].line.checkout_id  # type: ignore[index]
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


def create_checkout_discount_objects_for_order_promotions(
    checkout_info: "CheckoutInfo",
    lines_info: Iterable["CheckoutLineInfo"],
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
    checkout_info: "CheckoutInfo", lines_info: Iterable["CheckoutLineInfo"], save: bool
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
