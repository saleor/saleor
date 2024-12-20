import os
from decimal import Decimal

import graphene
from django.db.models import Sum

from ..checkout.logs import run_order_price_checks
from ..discount import DiscountType
from ..discount.utils.shared import discount_info_for_logs

DISABLE_EXTRA_LOGS = os.environ.get("DISABLE_EXTRA_LOGS", False)


def log_suspicious_order_in_draft_order_flow(order, order_lines_info, logger):
    if DISABLE_EXTRA_LOGS:
        return

    order_id = graphene.Node.to_global_id("Order", order.pk)

    # Check if order has 0 total
    try:
        if order.total_net_amount <= 0 or order.total_gross_amount <= 0:
            log_draft_order_complete_with_zero_total(order, order_lines_info, logger)
    except Exception as e:
        logger.warning("Error logging order (%s) with zero total: %s", order_id, e)

    # Run rest of the checks (shared between checkout and draft order flow)
    run_order_price_checks(order, order_lines_info, logger)


def log_draft_order_complete_with_zero_total(order, order_lines_info, logger):
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
