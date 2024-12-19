import logging
from decimal import Decimal

import graphene
from django.db.models import Sum

from ..discount import DiscountType
from ..discount.utils.shared import discount_info_for_logs
from ..product.models import ProductVariantChannelListing

logger = logging.getLogger(__name__)


def log_suspicious_order(order, order_lines_info):
    order_id = graphene.Node.to_global_id("Order", order.pk)
    try:
        if order.total_net_amount <= 0 or order.total_gross_amount <= 0:
            log_draft_order_complete_with_zero_total(order, order_lines_info)
    except Exception as e:
        logger.warning("Error logging order (%s) with zero total: %s", order_id, e)

    try:
        if any(
            [
                (order_line_info.line.total_price_net_amount <= 0)
                or (order_line_info.line.total_price_gross_amount <= 0)
                for order_line_info in order_lines_info
            ]
        ):
            log_order_with_suspicious_line(order, order_lines_info)
    except Exception as e:
        logger.warning(
            "Error logging order (%s) with 0 line total price: %s", order_id, e
        )


def log_draft_order_complete_with_zero_total(
    order,
    order_lines_info,
):
    extra = {
        "orderId": graphene.Node.to_global_id("Order", order.id),
    }
    order_id = graphene.Node.to_global_id("Order", order.id)
    logger.warning("Draft Order with zero total completed: %s.", order_id, extra=extra)
    voucher_code = order.voucher_code
    gift_cards = order.gift_cards.all()
    order_discounts = order.discounts.all()
    manual_order_discount = [
        discount for discount in order_discounts if discount.type == DiscountType.MANUAL
    ]

    shipping_price_net = order.shipping_price_net_amount
    shipping_price_gross = order.shipping_price_gross_amount
    not_valid_msg = "Not valid 0 total amount for draft order completion: %s."
    not_valid = False
    # shipping voucher and manual discounts reduces the shipping price
    # so only gift cards can cover the shipping price
    if (shipping_price_net > 0 or shipping_price_gross > 0) and not gift_cards:
        not_valid_msg += " Shipping price is greater than 0."
        extra["shipping_price_net_amount"] = shipping_price_net
        extra["shipping_price_gross_amount"] = shipping_price_gross
        not_valid = True

    # only voucher and manual discount can reduce the shipping price
    # entire order voucher and order promotions are not applied on the shipping price
    if (
        order.is_shipping_required()
        and (shipping_price_net <= 0 or shipping_price_gross <= 0)
        and order.undiscounted_base_shipping_price_amount > 0
        and not voucher_code
        and not manual_order_discount
    ):
        not_valid_msg += " Shipping price is 0 for no reason."
        extra["shipping_price_net_amount"] = shipping_price_net
        extra["shipping_price_gross_amount"] = shipping_price_gross
        extra["discounts"] = discount_info_for_logs(order_discounts)
        not_valid = True

    invalid_lines_above_0 = []
    invalid_lines_0_price = []
    line_discounts = []
    # line price can be reduced by catalogue promotions, line manual discount,
    # line vouchers, order voucher,order promotions
    for line_info in order_lines_info:
        line = line_info.line
        line_total_price_net = line.total_price_net_amount
        line_total_price_gross = line.total_price_gross_amount
        # only gift cards can cover the line price without reducing it
        if (line_total_price_net > 0 or line_total_price_gross > 0) and not gift_cards:
            invalid_lines_above_0.append(line)
        elif (
            (line_total_price_net <= 0 or line_total_price_gross <= 0)
            and line.undiscounted_total_price_net_amount > 0
            and not voucher_code
            and not gift_cards
            and not order_discounts
            and not line.is_price_overridden
            and not line_info.line_discounts
        ):
            invalid_lines_0_price.append(line)

        if line_info.line_discounts:
            line_discounts.extend(line_info.line_discounts)

    if invalid_lines_above_0:
        not_valid_msg += " Lines with total price above 0."
        extra["line_ids"] = [
            graphene.Node.to_global_id("OrderLine", line.id)
            for line in invalid_lines_above_0
        ]
        not_valid = True

    if invalid_lines_0_price:
        not_valid_msg += " Lines with total price 0 for no reason."
        ids = [
            graphene.Node.to_global_id("OrderLine", line.id)
            for line in invalid_lines_0_price
        ]
        if "line_ids" in extra:
            extra["line_ids"].extend(ids)
        else:
            extra["line_ids"] = ids
        not_valid = True

    gift_card_balance = gift_cards.aggregate(Sum("initial_balance_amount"))[
        "initial_balance_amount__sum"
    ]
    # Order total from lines should have included all discounts;
    # line discounts: catalogue promotion, line vouchers
    # order discounts: entire order voucher, order promotion
    order_total_from_lines = sum(
        line_info.line.total_price_net_amount for line_info in order_lines_info
    )
    if gift_cards and gift_card_balance < order_total_from_lines:
        not_valid_msg += " Existing gift cards not covers whole order."
        not_valid = True

    if not gift_cards:
        order_discounts_sum = sum(
            [discount.amount_value for discount in order_discounts], Decimal(0)
        )
        line_discounts_sum = sum(
            [discount.amount_value for discount in line_discounts], Decimal(0)
        )
        if (
            order_discounts_sum + line_discounts_sum
            < order.undiscounted_total_net_amount
        ):
            not_valid_msg += " Discounts do not cover total price."
            not_valid = True
            extra["order_discounts"] = discount_info_for_logs(order_discounts)
            extra["line_discounts"] = discount_info_for_logs(line_discounts)

    if not_valid:
        logger.error(
            not_valid_msg,
            order_id,
            extra=extra,
        )


def log_order_with_suspicious_line(order, lines_info):
    order_id = graphene.Node.to_global_id("Order", order.id)

    variant_listings_data = ProductVariantChannelListing.objects.filter(
        variant_id__in=[line_info.line.variant_id for line_info in lines_info],
        channel_id=order.channel_id,
    ).values(
        "variant_id",
        "price_amount",
        "discounted_price_amount",
    )
    variant_listings = {
        variant["variant_id"]: (
            variant["price_amount"],
            variant["discounted_price_amount"],
        )
        for variant in variant_listings_data
    }
    extra = {
        "order_id": order_id,
        "orderId": order_id,
        "order": {
            "currency": order.currency,
            "status": order.status,
            "origin": order.origin,
            "checkout_id": order.checkout_token,
            "undiscounted_base_shipping_price_amount": order.undiscounted_base_shipping_price_amount,
            "base_shipping_price_amount": order.base_shipping_price_amount,
            "shipping_price_net_amount": order.shipping_price_net_amount,
            "shipping_price_gross_amount": order.shipping_price_gross_amount,
            "undiscounted_total_net_amount": order.undiscounted_total_net_amount,
            "total_net_amount": order.total_net_amount,
            "undiscounted_total_gross_amount": order.undiscounted_total_gross_amount,
            "total_gross_amount": order.total_gross_amount,
            "subtotal_net_amount": order.subtotal_net_amount,
            "subtotal_gross_amount": order.subtotal_gross_amount,
            "has_voucher_code": bool(order.voucher_code),
            "tax_exemption": order.tax_exemption,
            "tax_error": order.tax_error,
        },
        "discounts": discount_info_for_logs(order.discounts.all()),
        "lines": [
            {
                "id": graphene.Node.to_global_id("OrderLine", line_info.line.pk),
                "variant_id": graphene.Node.to_global_id(
                    "ProductVariant", line_info.line.variant_id
                ),
                "quantity": line_info.line.quantity,
                "is_gift_card": line_info.line.is_gift_card,
                "is_price_overridden": line_info.line.is_price_overridden,
                "undiscounted_base_unit_price_amount": line_info.line.undiscounted_base_unit_price_amount,
                "base_unit_price_amount": line_info.line.base_unit_price_amount,
                "undiscounted_unit_price_net_amount": line_info.line.undiscounted_unit_price_net_amount,
                "undiscounted_unit_price_gross_amount": line_info.line.undiscounted_unit_price_gross_amount,
                "unit_price_net_amount": line_info.line.unit_price_net_amount,
                "unit_price_gross_amount": line_info.line.unit_price_gross_amount,
                "undiscounted_total_price_net_amount": line_info.line.undiscounted_total_price_net_amount,
                "undiscounted_total_price_gross_amount": line_info.line.undiscounted_total_price_gross_amount,
                "total_price_net_amount": line_info.line.total_price_net_amount,
                "total_price_gross_amount": line_info.line.total_price_gross_amount,
                "has_voucher_code": bool(line_info.line.voucher_code),
                "variant_listing_price": (
                    variant_listings[line_info.line.variant_id][0]
                    if line_info.line.variant_id in variant_listings
                    else None
                ),
                "variant_listing_discounted_price": (
                    variant_listings[line_info.line.variant_id][1]
                    if line_info.line.variant_id in variant_listings
                    else None
                ),
                "unit_discount_amount": line_info.line.unit_discount_amount,
                "unit_discount_type": line_info.line.unit_discount_type,
                "unit_discount_reason": line_info.line.unit_discount_reason,
                "discounts": discount_info_for_logs(line_info.line_discounts)
                if line_info.line_discounts
                else None,
            }
            for line_info in lines_info
        ],
    }
    logger.warning(
        "Order with 0 line total price: %s.",
        order_id,
        extra=extra,
    )
