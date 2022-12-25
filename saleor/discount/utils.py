from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator
from decimal import ROUND_HALF_UP, Decimal
from functools import partial
from typing import TYPE_CHECKING, Optional, cast
from uuid import UUID

import graphene
from django.db import transaction
from django.db.models import Exists, F, OuterRef, QuerySet
from django.utils import timezone
from prices import Money, TaxedMoney, fixed_discount, percentage_discount

from ..channel.models import Channel
from ..core.taxes import zero_money
from ..core.utils.promo_code import InvalidPromoCode
from ..discount.models import VoucherCustomer
from ..product.models import Product, ProductVariant
from . import DiscountType, PromotionRuleInfo
from .models import (
    CheckoutLineDiscount,
    DiscountValueType,
    NotApplicable,
    Promotion,
    PromotionRule,
    Voucher,
    VoucherCode,
)

if TYPE_CHECKING:
    from ..account.models import User
    from ..checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ..discount.interface import VariantPromotionRuleInfo
    from ..order.models import Order
    from ..plugins.manager import PluginsManager
    from ..product.managers import ProductVariantQueryset
    from ..product.models import (
        ProductVariantChannelListing,
        VariantChannelListingPromotionRule,
    )

CatalogueInfo = defaultdict[str, set[int | str]]
CATALOGUE_FIELDS = ["categories", "collections", "products", "variants"]


def increase_voucher_usage(
    voucher: "Voucher",
    code: "VoucherCode",
    customer_email: str,
    increase_voucher_customer_usage: bool = True,
) -> None:
    if voucher.usage_limit:
        increase_voucher_code_usage_value(code)
    if voucher.apply_once_per_customer and increase_voucher_customer_usage:
        add_voucher_usage_by_customer(code, customer_email)
    if voucher.single_use:
        deactivate_voucher_code(code)


def increase_voucher_code_usage_value(code: "VoucherCode") -> None:
    """Increase voucher code uses by 1."""
    code.used = F("used") + 1
    code.save(update_fields=["used"])


def decrease_voucher_code_usage_value(code: "VoucherCode") -> None:
    """Decrease voucher code uses by 1."""
    code.used = F("used") - 1
    code.save(update_fields=["used"])


def deactivate_voucher_code(code: "VoucherCode") -> None:
    """Mark voucher code as used."""
    code.is_active = False
    code.save(update_fields=["is_active"])


def activate_voucher_code(code: "VoucherCode") -> None:
    """Mark voucher code as unused."""
    code.is_active = True
    code.save(update_fields=["is_active"])


def add_voucher_usage_by_customer(code: "VoucherCode", customer_email: str) -> None:
    _, created = VoucherCustomer.objects.get_or_create(
        voucher_code=code, customer_email=customer_email
    )
    if not created:
        raise NotApplicable("This offer is only valid once per customer.")


def remove_voucher_usage_by_customer(code: "VoucherCode", customer_email: str) -> None:
    voucher_customer = VoucherCustomer.objects.filter(
        voucher_code=code, customer_email=customer_email
    )
    if voucher_customer:
        voucher_customer.delete()


def release_voucher_code_usage(
    code: Optional["VoucherCode"],
    voucher: Optional["Voucher"],
    user_email: str | None,
):
    if not code:
        return
    if voucher and voucher.usage_limit:
        decrease_voucher_code_usage_value(code)
    if voucher and voucher.single_use:
        activate_voucher_code(code)
    if user_email:
        remove_voucher_usage_by_customer(code, user_email)


def prepare_promotion_discount_reason(promotion: "Promotion", sale_id: str):
    return f"{'Sale' if promotion.old_sale_id else 'Promotion'}: {sale_id}"


def get_sale_id(promotion: "Promotion"):
    return (
        graphene.Node.to_global_id("Sale", promotion.old_sale_id)
        if promotion.old_sale_id
        else graphene.Node.to_global_id("Promotion", promotion.id)
    )


def get_voucher_code_instance(
    voucher_code: str,
    channel_slug: str,
):
    """Return a voucher code instance if it's valid or raise an error."""
    if (
        Voucher.objects.active_in_channel(
            date=timezone.now(), channel_slug=channel_slug
        )
        .filter(
            Exists(
                VoucherCode.objects.filter(
                    code=voucher_code,
                    voucher_id=OuterRef("id"),
                    is_active=True,
                )
            )
        )
        .exists()
    ):
        code_instance = VoucherCode.objects.get(code=voucher_code)
    else:
        raise InvalidPromoCode()
    return code_instance


def calculate_discounted_price_for_rules(
    *, price: Money, rules: Iterable["PromotionRule"], currency: str
):
    """Calculate the discounted price for provided rules.

    The discounts from rules summed up and applied to the price.
    """
    total_discount = zero_money(currency)
    for rule in rules:
        discount = rule.get_discount(currency)
        total_discount += price - discount(price)

    return max(price - total_discount, zero_money(currency))


def calculate_discounted_price_for_promotions(
    *,
    price: Money,
    rules_info_per_variant: dict[int, list[PromotionRuleInfo]],
    channel: "Channel",
    variant_id: int,
) -> tuple[UUID, Money] | None:
    """Return minimum product's price of all prices with promotions applied."""
    applied_discount = None
    rules_info_for_variant = rules_info_per_variant.get(variant_id)
    if rules_info_for_variant:
        applied_discount = get_best_promotion_discount(
            price, rules_info_for_variant, channel
        )
    return applied_discount


def get_best_promotion_discount(
    price: Money,
    rules_info_for_variant: list[PromotionRuleInfo],
    channel: "Channel",
) -> tuple[UUID, Money] | None:
    """Return the rule with the discount amount for the best promotion.

    The data for the promotion that gives the best saving are returned in the following
    shape:
        (rule_id_1, discount_amount_1)
    """
    available_discounts = []
    for rule_id, discount in get_product_promotion_discounts(
        rules_info=rules_info_for_variant,
        channel=channel,
    ):
        available_discounts.append((rule_id, discount))

    applied_discount = None
    if available_discounts:
        applied_discount = max(
            [
                (rule_id, price - discount(price))
                for rule_id, discount in available_discounts
            ],
            key=lambda x: x[1].amount,  # sort over a max discount
        )

    return applied_discount


def get_product_promotion_discounts(
    *,
    rules_info: list[PromotionRuleInfo],
    channel: "Channel",
) -> Iterator[tuple[UUID, Callable]]:
    """Return rule id, discount value for all rules applicable for given channel."""
    for rule_info in rules_info:
        try:
            yield get_product_discount_on_promotion(rule_info, channel)
        except NotApplicable:
            pass


def get_product_discount_on_promotion(
    rule_info: PromotionRuleInfo,
    channel: "Channel",
) -> tuple[UUID, Callable]:
    """Return rule id, discount value if rule applied or raise NotApplicable."""
    if channel.id in rule_info.channel_ids:
        return rule_info.rule.id, rule_info.rule.get_discount(channel.currency_code)
    raise NotApplicable("Promotion rule not applicable for this product")


def validate_voucher_for_checkout(
    manager: "PluginsManager",
    voucher: "Voucher",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
):
    from ..checkout import base_calculations
    from ..checkout.utils import calculate_checkout_quantity

    quantity = calculate_checkout_quantity(lines)
    subtotal = base_calculations.base_checkout_subtotal(
        lines,
        checkout_info.channel,
        checkout_info.checkout.currency,
    )

    customer_email = cast(str, checkout_info.get_customer_email())
    validate_voucher(
        voucher,
        subtotal,
        quantity,
        customer_email,
        checkout_info.channel,
        checkout_info.user,
    )


def validate_voucher_in_order(order: "Order"):
    if not order.voucher:
        return

    subtotal = order.subtotal
    quantity = order.get_total_quantity()
    customer_email = order.get_customer_email()
    tax_configuration = order.channel.tax_configuration
    prices_entered_with_tax = tax_configuration.prices_entered_with_tax
    value = subtotal.gross if prices_entered_with_tax else subtotal.net

    validate_voucher(
        order.voucher, value, quantity, customer_email, order.channel, order.user
    )


def validate_voucher(
    voucher: "Voucher",
    total_price: TaxedMoney,
    quantity: int,
    customer_email: str,
    channel: Channel,
    customer: Optional["User"],
) -> None:
    voucher.validate_min_spent(total_price, channel)
    voucher.validate_min_checkout_items_quantity(quantity)
    if voucher.apply_once_per_customer:
        voucher.validate_once_per_customer(customer_email)
    if voucher.only_for_staff:
        voucher.validate_only_for_staff(customer)


def get_products_voucher_discount(
    voucher: "Voucher", prices: Iterable[Money], channel: Channel
) -> Money:
    """Calculate discount value for a voucher of product or category type."""
    if voucher.apply_once_per_order:
        return voucher.get_discount_amount_for(min(prices), channel)
    discounts = (voucher.get_discount_amount_for(price, channel) for price in prices)
    total_amount = sum(discounts, zero_money(channel.currency_code))
    return total_amount


def apply_discount_to_value(
    value: Decimal,
    value_type: str,
    currency: str,
    price_to_discount: Money | TaxedMoney,
):
    """Calculate the price based on the provided values."""
    if value_type == DiscountValueType.FIXED:
        discount_method = fixed_discount
        discount_kwargs = {"discount": Money(value, currency)}
    else:
        discount_method = percentage_discount
        discount_kwargs = {"percentage": value, "rounding": ROUND_HALF_UP}
    discount = partial(
        discount_method,
        **discount_kwargs,
    )
    return discount(price_to_discount)


def create_or_update_discount_objects_from_promotion_for_checkout(
    lines_info: Iterable["CheckoutLineInfo"],
):
    line_discounts_to_create = []
    line_discounts_to_update = []
    line_discount_ids_to_remove = []
    updated_fields: list[str] = []

    for line_info in lines_info:
        line = line_info.line

        # discount_amount based on the difference between discounted_price and price
        discount_amount = _get_discount_amount(line_info.channel_listing, line.quantity)

        # get the existing discounts for the line
        discounts_to_update = line_info.get_promotion_discounts()
        rule_id_to_discount = {
            discount.promotion_rule_id: discount for discount in discounts_to_update
        }

        # delete all existing discounts if the line is not discounted
        if not discount_amount:
            ids_to_remove = [discount.id for discount in discounts_to_update]
            CheckoutLineDiscount.objects.filter(id__in=ids_to_remove).delete()
            line_info.discounts = []
            continue

        # delete the discount objects that are not valid anymore
        line_discount_ids_to_remove.extend(
            _get_discounts_that_are_not_valid_anymore(
                line_info.rules_info,
                rule_id_to_discount,  # type: ignore[arg-type]
                line_info,
            )
        )

        for rule_info in line_info.rules_info:
            rule = rule_info.rule
            discount_to_update = rule_id_to_discount.get(rule.id)
            rule_discount_amount = _get_rule_discount_amount(
                rule_info.variant_listing_promotion_rule, line.quantity
            )
            discount_name = get_discount_name(rule, rule_info.promotion)
            translated_name = get_discount_translated_name(rule_info)
            if not discount_to_update:
                line_discount = CheckoutLineDiscount(
                    line=line,
                    type=DiscountType.PROMOTION,
                    value_type=rule.reward_value_type,
                    value=rule.reward_value,
                    amount_value=rule_discount_amount,
                    currency=line.currency,
                    name=discount_name,
                    translated_name=translated_name,
                    reason=None,
                    promotion_rule=rule,
                )
                line_discounts_to_create.append(line_discount)
                line_info.discounts.append(line_discount)
            else:
                _update_line_discount(
                    rule,
                    rule_info,
                    rule_discount_amount,
                    discount_to_update,
                    updated_fields,
                )

                line_discounts_to_update.append(discount_to_update)

    if line_discounts_to_create:
        CheckoutLineDiscount.objects.bulk_create(line_discounts_to_create)
    if line_discounts_to_update and updated_fields:
        CheckoutLineDiscount.objects.bulk_update(
            line_discounts_to_update, updated_fields
        )
    if line_discount_ids_to_remove:
        CheckoutLineDiscount.objects.filter(id__in=line_discount_ids_to_remove).delete()


def _get_discount_amount(
    variant_channel_listing: "ProductVariantChannelListing", line_quantity: int
) -> Decimal:
    price_amount = variant_channel_listing.price_amount
    discounted_price_amount = variant_channel_listing.discounted_price_amount

    if (
        price_amount is None
        or discounted_price_amount is None
        or price_amount == discounted_price_amount
    ):
        return Decimal("0.0")

    unit_discount = price_amount - discounted_price_amount
    return unit_discount * line_quantity


def _get_discounts_that_are_not_valid_anymore(
    rules_info: list["VariantPromotionRuleInfo"],
    rule_id_to_discount: dict[int, "CheckoutLineDiscount"],
    line_info: "CheckoutLineInfo",
):
    discount_ids = []
    rule_ids = {rule_info.rule.id for rule_info in rules_info}
    for rule_id, discount in rule_id_to_discount.items():
        if rule_id not in rule_ids:
            discount_ids.append(discount.id)
            line_info.discounts.remove(discount)
    return discount_ids


def _get_rule_discount_amount(
    variant_listing_promotion_rule: "VariantChannelListingPromotionRule",
    line_quantity: int,
) -> Decimal:
    discount_amount = variant_listing_promotion_rule.discount_amount
    return discount_amount * line_quantity


def get_discount_name(rule: "PromotionRule", promotion: "Promotion"):
    if promotion.name and rule.name:
        return f"{promotion.name}: {rule.name}"
    return rule.name or promotion.name


def get_discount_translated_name(rule_info: "VariantPromotionRuleInfo"):
    promotion_translation = rule_info.promotion_translation
    rule_translation = rule_info.rule_translation
    if promotion_translation and rule_translation:
        return f"{promotion_translation.name}: {rule_translation.name}"
    if rule_translation:
        return rule_translation.name
    if promotion_translation:
        return promotion_translation.name
    return None


def _update_line_discount(
    rule: "PromotionRule",
    rule_info: "VariantPromotionRuleInfo",
    rule_discount_amount: Decimal,
    discount_to_update: "CheckoutLineDiscount",
    updated_fields: list[str],
):
    if discount_to_update.value_type != rule.reward_value_type:
        discount_to_update.value_type = (
            rule.reward_value_type  # type: ignore[assignment]
        )
        updated_fields.append("value_type")
    if discount_to_update.value != rule.reward_value:
        discount_to_update.value = rule.reward_value  # type: ignore[assignment]
        updated_fields.append("value")
    if discount_to_update.amount_value != rule_discount_amount:
        discount_to_update.amount_value = rule_discount_amount
        updated_fields.append("amount_value")
    discount_name = get_discount_name(rule, rule_info.promotion)
    if discount_to_update.name != discount_name:
        discount_to_update.name = discount_name
        updated_fields.append("name")
    translated_name = get_discount_translated_name(rule_info)
    if discount_to_update.translated_name != translated_name:
        discount_to_update.translated_name = translated_name
        updated_fields.append("translated_name")


def get_variants_to_promotion_rules_map(
    variant_qs: "ProductVariantQueryset",
) -> dict[int, list[PromotionRuleInfo]]:
    """Return map of variant ids to the list of promotion rules that can be applied.

    The data is returned in the following shape:
    {
        variant_id_1: [PromotionRuleInfo_1, PromotionRuleInfo_2, PromotionRuleInfo_3],
        variant_id_2: [PromotionRuleInfo_1]
    }
    """
    rules_info_per_variant: dict[int, list[PromotionRuleInfo]] = defaultdict(list)

    promotions = Promotion.objects.active()
    PromotionRuleVariant = PromotionRule.variants.through
    promotion_rule_variants = PromotionRuleVariant.objects.filter(
        Exists(variant_qs.filter(id=OuterRef("productvariant_id")))
    )

    # fetch rules only for active promotions
    rules = PromotionRule.objects.filter(
        Exists(promotions.filter(id=OuterRef("promotion_id"))),
        Exists(promotion_rule_variants.filter(promotionrule_id=OuterRef("pk"))),
    ).prefetch_related("channels")
    rule_to_channel_ids_map = _get_rule_to_channel_ids_map(rules)
    rules_in_bulk = rules.in_bulk()

    for promotion_rule_variant in list(promotion_rule_variants.iterator()):
        rule_id = promotion_rule_variant.promotionrule_id
        rule = rules_in_bulk.get(rule_id)
        # there is no rule when it is a part of inactive promotion
        if not rule:
            continue
        variant_id = promotion_rule_variant.productvariant_id
        rules_info_per_variant[variant_id].append(
            PromotionRuleInfo(
                rule=rule,
                channel_ids=rule_to_channel_ids_map.get(rule_id, []),
            )
        )

    return rules_info_per_variant


def _get_rule_to_channel_ids_map(rules: QuerySet):
    rule_to_channel_ids_map = defaultdict(list)
    PromotionRuleChannel = PromotionRule.channels.through
    promotion_rule_channels = PromotionRuleChannel.objects.filter(
        Exists(rules.filter(id=OuterRef("promotionrule_id")))
    )
    for promotion_rule_channel in promotion_rule_channels:
        rule_id = promotion_rule_channel.promotionrule_id
        channel_id = promotion_rule_channel.channel_id
        rule_to_channel_ids_map[rule_id].append(channel_id)
    return rule_to_channel_ids_map


def get_current_products_for_rules(rules: "QuerySet[PromotionRule]"):
    """Get currently assigned products to promotions.

    Collect all products for variants that are assigned to promotion rules.
    """
    PromotionRuleVariant = PromotionRule.variants.through
    rule_variants = PromotionRuleVariant.objects.filter(
        Exists(rules.filter(pk=OuterRef("promotionrule_id")))
    )
    variants = ProductVariant.objects.filter(
        Exists(rule_variants.filter(productvariant_id=OuterRef("id")))
    )
    return Product.objects.filter(Exists(variants.filter(product_id=OuterRef("id"))))


def update_rule_variant_relation(
    rules: QuerySet[PromotionRule], new_rules_variants: list
):
    """Update PromotionRule - ProductVariant relation.

    Deletes relations, which are not valid anymore.
    Adds new relations, if they don't exist already.
    `new_rules_variants` is a list of PromotionRuleVariant objects.
    """
    with transaction.atomic():
        PromotionRuleVariant = PromotionRule.variants.through
        existing_rules_variants = PromotionRuleVariant.objects.filter(
            Exists(rules.filter(pk=OuterRef("promotionrule_id")))
        ).all()
        new_rule_variant_set = set(
            (rv.promotionrule_id, rv.productvariant_id) for rv in new_rules_variants
        )
        existing_rule_variant_set = set(
            (rv.promotionrule_id, rv.productvariant_id)
            for rv in existing_rules_variants
        )

        # Clear invalid variants assigned to promotion rules
        rule_variant_to_delete_ids = [
            rv.id
            for rv in existing_rules_variants
            if (rv.promotionrule_id, rv.productvariant_id) not in new_rule_variant_set
        ]
        PromotionRuleVariant.objects.filter(id__in=rule_variant_to_delete_ids).delete()

        # Assign new variants to promotion rules
        rules_variants_to_add = [
            rv
            for rv in new_rules_variants
            if (rv.promotionrule_id, rv.productvariant_id)
            not in existing_rule_variant_set
        ]
        PromotionRuleVariant.objects.bulk_create(
            rules_variants_to_add, ignore_conflicts=True
        )
