from collections.abc import Iterable
from typing import TYPE_CHECKING

from django.db import transaction

from ...checkout.models import Checkout
from ..models import (
    CheckoutLineDiscount,
)
from .promotion import (
    create_checkout_discount_objects_for_order_promotions,
    prepare_line_discount_objects_for_catalogue_promotions,
)
from .shared import update_line_info_cached_discounts

if TYPE_CHECKING:
    from ...checkout.fetch import CheckoutInfo, CheckoutLineInfo


def create_or_update_discount_objects_from_promotion_for_checkout(
    checkout_info: "CheckoutInfo",
    lines_info: Iterable["CheckoutLineInfo"],
):
    create_checkout_line_discount_objects_for_catalogue_promotions(lines_info)
    create_checkout_discount_objects_for_order_promotions(checkout_info, lines_info)


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
    with transaction.atomic():
        # Protect against potential thread race. CheckoutLine object can have only
        # single catalogue discount applied.
        checkout_id = lines_info[0].line.checkout_id  # type: ignore[index]
        _checkout_lock = list(
            Checkout.objects.filter(pk=checkout_id).select_for_update(of=(["self"]))
        )

        if discount_ids_to_remove := [discount.id for discount in discount_to_remove]:
            CheckoutLineDiscount.objects.filter(id__in=discount_ids_to_remove).delete()

        if discounts_to_create_inputs:
            new_line_discounts = [
                CheckoutLineDiscount(**input) for input in discounts_to_create_inputs
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
