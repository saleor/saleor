import datetime
from collections import defaultdict, namedtuple
from collections.abc import Iterable, Iterator
from decimal import ROUND_HALF_UP, Decimal
from functools import partial
from itertools import chain
from typing import TYPE_CHECKING, Callable, Optional, Union, cast, overload
from uuid import UUID

import graphene
import pytz
from django.conf import settings
from django.db import transaction
from django.db.models import Exists, F, OuterRef, QuerySet
from django.utils import timezone
from prices import Money, TaxedMoney, fixed_discount, percentage_discount

from ..channel.models import Channel
from ..checkout.base_calculations import (
    base_checkout_delivery_price,
    base_checkout_subtotal,
)
from ..checkout.models import Checkout, CheckoutLine
from ..core.exceptions import InsufficientStock
from ..core.prices import quantize_price
from ..core.taxes import zero_money
from ..core.utils.promo_code import InvalidPromoCode
from ..graphql.core.utils import to_global_id_or_none
from ..order.models import Order
from ..product.models import (
    Product,
    ProductChannelListing,
    ProductVariant,
    ProductVariantChannelListing,
)
from . import (
    DiscountType,
    PromotionRuleInfo,
    PromotionType,
    RewardType,
    RewardValueType,
    VoucherType,
)
from .interface import VariantPromotionRuleInfo, get_rule_translations
from .models import (
    CheckoutDiscount,
    CheckoutLineDiscount,
    DiscountValueType,
    NotApplicable,
    OrderDiscount,
    OrderLineDiscount,
    Promotion,
    PromotionRule,
    Voucher,
    VoucherCode,
    VoucherCustomer,
)

if TYPE_CHECKING:
    from ..account.models import User
    from ..checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ..core.pricing.interface import LineInfo
    from ..discount.models import Voucher
    from ..order.fetch import EditableOrderLineInfo
    from ..order.models import OrderLine
    from ..plugins.manager import PluginsManager
    from ..product.managers import ProductVariantQueryset
    from .interface import VoucherInfo

CatalogueInfo = defaultdict[str, set[Union[int, str]]]
CATALOGUE_FIELDS = ["categories", "collections", "products", "variants"]


def is_order_level_voucher(voucher: Optional[Voucher]):
    return bool(
        voucher
        and voucher.type == VoucherType.ENTIRE_ORDER
        and not voucher.apply_once_per_order
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


def is_shipping_voucher(voucher: Optional[Voucher]):
    return bool(voucher and voucher.type == VoucherType.SHIPPING)


def is_order_level_discount(discount: OrderDiscount) -> bool:
    return discount.type in [
        DiscountType.MANUAL,
        DiscountType.ORDER_PROMOTION,
    ] or is_order_level_voucher(discount.voucher)


def increase_voucher_usage(
    voucher: "Voucher",
    code: "VoucherCode",
    customer_email: Optional[str],
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


def add_voucher_usage_by_customer(
    code: "VoucherCode", customer_email: Optional[str]
) -> None:
    if not customer_email:
        raise NotApplicable("Unable to apply voucher as customer details are missing.")

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
    user_email: Optional[str],
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


def get_active_voucher_code(voucher, channel_slug):
    """Return an active VoucherCode instance.

    This method along with `Voucher.code` should be removed in Saleor 4.0.
    """

    voucher_queryset = Voucher.objects.active_in_channel(timezone.now(), channel_slug)
    if not voucher_queryset.filter(pk=voucher.pk).exists():
        raise InvalidPromoCode()
    voucher_code = VoucherCode.objects.filter(voucher=voucher, is_active=True).first()
    if not voucher_code:
        raise InvalidPromoCode()
    return voucher_code


def apply_voucher_to_line(
    voucher_info: "VoucherInfo",
    lines_info: Iterable["LineInfo"],
):
    """Attach voucher to valid checkout or order lines info.

    Apply a voucher to checkout/order line info when the voucher has the type
    SPECIFIC_PRODUCTS or is applied only to the cheapest item.
    """
    voucher = voucher_info.voucher
    discounted_lines_by_voucher: list[LineInfo] = []
    lines_included_in_discount = lines_info
    if voucher.type == VoucherType.SPECIFIC_PRODUCT:
        discounted_lines_by_voucher.extend(
            get_discounted_lines(lines_info, voucher_info)
        )
        lines_included_in_discount = discounted_lines_by_voucher
    if voucher.apply_once_per_order:
        if cheapest_line := _get_the_cheapest_line(lines_included_in_discount):
            discounted_lines_by_voucher = [cheapest_line]
    for line_info in lines_info:
        if line_info in discounted_lines_by_voucher:
            line_info.voucher = voucher
            line_info.voucher_code = voucher_info.voucher_code


def get_discounted_lines(
    lines: Iterable["LineInfo"], voucher_info: "VoucherInfo"
) -> Iterable["LineInfo"]:
    discounted_lines = []
    if (
        voucher_info.product_pks
        or voucher_info.collection_pks
        or voucher_info.category_pks
        or voucher_info.variant_pks
    ):
        for line_info in lines:
            if line_info.line.is_gift:
                continue
            line_variant = line_info.variant
            line_product = line_info.product
            if not line_variant or not line_product:
                continue
            line_category = line_product.category
            line_collections = set(
                [collection.pk for collection in line_info.collections if collection]
            )
            if line_info.variant and (
                line_variant.pk in voucher_info.variant_pks
                or line_product.pk in voucher_info.product_pks
                or line_category
                and line_category.pk in voucher_info.category_pks
                or line_collections.intersection(voucher_info.collection_pks)
            ):
                discounted_lines.append(line_info)
    else:
        # If there's no discounted products, collections or categories,
        # it means that all products are discounted
        discounted_lines.extend(lines)
    return discounted_lines


def _get_the_cheapest_line(
    lines_info: Optional[Iterable["LineInfo"]],
) -> Optional["LineInfo"]:
    if not lines_info:
        return None
    return min(lines_info, key=lambda line_info: line_info.variant_discounted_price)


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
) -> Optional[tuple[UUID, Money]]:
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
) -> Optional[tuple[UUID, Money]]:
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
    total_price: Money,
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
    value_type: Optional[str],
    currency: str,
    price_to_discount: Union[Money, TaxedMoney],
):
    """Calculate the price based on the provided values."""
    if value_type == DiscountValueType.PERCENTAGE:
        discount_method = percentage_discount
        discount_kwargs = {"percentage": value, "rounding": ROUND_HALF_UP}
    else:
        discount_method = fixed_discount
        discount_kwargs = {"discount": Money(value, currency)}
    discount = partial(
        discount_method,
        **discount_kwargs,
    )
    return discount(price_to_discount)


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

    _update_line_info_cached_discounts(
        lines_info, new_line_discounts, discounts_to_update, discount_ids_to_remove
    )


@overload
def prepare_line_discount_objects_for_catalogue_promotions(
    lines_info: Iterable["CheckoutLineInfo"],
) -> tuple[
    list[dict], list["CheckoutLineDiscount"], list["CheckoutLineDiscount"], list[str]
]:
    ...


@overload
def prepare_line_discount_objects_for_catalogue_promotions(
    lines_info: Iterable["EditableOrderLineInfo"],
) -> tuple[list[dict], list["OrderLineDiscount"], list["OrderLineDiscount"], list[str]]:
    ...


def prepare_line_discount_objects_for_catalogue_promotions(lines_info):
    line_discounts_to_create_inputs: list[dict] = []
    line_discounts_to_update: list[Union[CheckoutLineDiscount, OrderLineDiscount]] = []
    line_discounts_to_remove: list[Union[CheckoutLineDiscount, OrderLineDiscount]] = []
    updated_fields: list[str] = []

    if not lines_info:
        return
    from ..checkout.fetch import CheckoutLineInfo

    for line_info in lines_info:
        line = line_info.line

        # if channel_listing is not present, we can't close the checkout. User needs to
        # remove the line for the checkout first. Until that moment, we return the same
        # price as we did when listing was present - including line discount.
        if isinstance(line_info, CheckoutLineInfo) and not line_info.channel_listing:
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
        discounted_line = _is_discounted_line(line_info.channel_listing)

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
            reason = _get_discount_reason(rule)
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
                _update_promotion_discount(
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


def _is_discounted_line(
    variant_channel_listing: "ProductVariantChannelListing",
) -> bool:
    """Return True when the price is discounted by catalogue promotion."""
    price_amount = variant_channel_listing.price_amount
    discounted_price_amount = variant_channel_listing.discounted_price_amount

    if (
        price_amount is None
        or discounted_price_amount is None
        or price_amount == discounted_price_amount
    ):
        return False

    return True


def _get_rule_discount_amount(
    line: Union["CheckoutLine", "OrderLine"],
    rule_info: "VariantPromotionRuleInfo",
    channel: "Channel",
) -> Decimal:
    """Calculate the discount amount for catalogue promotion rule.

    When the line has overridden price, the discount is applied on the
    new overridden base price.
    """
    variant_listing_promotion_rule = rule_info.variant_listing_promotion_rule
    if not variant_listing_promotion_rule:
        return Decimal("0.0")

    if isinstance(line, CheckoutLine):
        price_override = (
            Money(line.price_override, channel.currency_code)
            if line.price_override is not None
            else None
        )
    else:
        price_override = (
            line.undiscounted_base_unit_price if line.is_price_overridden else None
        )

    if price_override is not None:
        # calculate discount amount on overridden price
        discount = rule_info.rule.get_discount(channel.currency_code)
        discounted_price = discount(price_override)
        discount_amount = (price_override - discounted_price).amount
    else:
        discount_amount = variant_listing_promotion_rule.discount_amount
    return discount_amount * line.quantity


def get_discount_name(rule: "PromotionRule", promotion: "Promotion"):
    if promotion.name and rule.name:
        return f"{promotion.name}: {rule.name}"
    return rule.name or promotion.name


def _get_discount_reason(rule: PromotionRule):
    promotion = rule.promotion
    if promotion.old_sale_id:
        return f"Sale: {graphene.Node.to_global_id('Sale', promotion.old_sale_id)}"
    return f"Promotion: {graphene.Node.to_global_id('Promotion', promotion.id)}"


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


def _update_promotion_discount(
    rule: "PromotionRule",
    rule_info: "VariantPromotionRuleInfo",
    rule_discount_amount: Decimal,
    discount_to_update: Union[
        "CheckoutLineDiscount", "CheckoutDiscount", "OrderLineDiscount", "OrderDiscount"
    ],
    updated_fields: list[str],
):
    discount_name = get_discount_name(rule, rule_info.promotion)
    translated_name = get_discount_translated_name(rule_info)
    reason = prepare_promotion_discount_reason(
        rule_info.promotion, get_sale_id(rule_info.promotion)
    )
    # gift rule has empty reward_value_type
    value_type = rule.reward_value_type or RewardValueType.FIXED
    # gift rule has empty reward_value
    value = rule.reward_value or rule_discount_amount
    _update_discount(
        rule=rule,
        voucher=None,
        discount_name=discount_name,
        translated_name=translated_name,
        discount_reason=reason,
        discount_amount=rule_discount_amount,
        value=value,
        value_type=value_type,
        unique_type=DiscountType.PROMOTION,
        discount_to_update=discount_to_update,
        updated_fields=updated_fields,
        voucher_code=None,
    )


def _update_discount(
    rule: Optional["PromotionRule"],
    voucher: Optional["Voucher"],
    discount_name: str,
    translated_name: str,
    discount_reason: str,
    discount_amount: Decimal,
    value: Decimal,
    value_type: str,
    unique_type: str,
    discount_to_update: Union[
        "CheckoutLineDiscount", "CheckoutDiscount", "OrderLineDiscount", "OrderDiscount"
    ],
    updated_fields: list[str],
    voucher_code: Optional[str],
):
    if voucher and discount_to_update.voucher_id != voucher.id:
        discount_to_update.voucher_id = voucher.id
        updated_fields.append("voucher_id")
    if rule and discount_to_update.promotion_rule_id != rule.id:
        discount_to_update.promotion_rule_id = rule.id
        updated_fields.append("promotion_rule_id")
    if discount_to_update.value_type != value_type:
        discount_to_update.value_type = value_type
        updated_fields.append("value_type")
    if discount_to_update.value != value:
        discount_to_update.value = value
        updated_fields.append("value")
    if discount_to_update.amount_value != discount_amount:
        discount_to_update.amount_value = discount_amount
        updated_fields.append("amount_value")
    if discount_to_update.name != discount_name:
        discount_to_update.name = discount_name
        updated_fields.append("name")
    if discount_to_update.translated_name != translated_name:
        discount_to_update.translated_name = translated_name
        updated_fields.append("translated_name")
    if discount_to_update.reason != discount_reason:
        discount_to_update.reason = discount_reason
        updated_fields.append("reason")
    if hasattr(discount_to_update, "unique_type"):
        if discount_to_update.unique_type is None:
            discount_to_update.unique_type = unique_type
            updated_fields.append("unique_type")
    if voucher_code and discount_to_update.voucher_code != voucher_code:
        discount_to_update.voucher_code = voucher_code
        updated_fields.append("voucher_code")


def _update_line_info_cached_discounts(
    lines_info, new_line_discounts, updated_discounts, line_discount_ids_to_remove
):
    if not any([new_line_discounts, updated_discounts, line_discount_ids_to_remove]):
        return

    line_id_line_discounts_map = defaultdict(list)
    for line_discount in new_line_discounts:
        line_id_line_discounts_map[line_discount.line_id].append(line_discount)

    for line_info in lines_info:
        line_info.discounts = [
            discount
            for discount in line_info.discounts
            if discount.id not in line_discount_ids_to_remove
        ]
        if discount := line_id_line_discounts_map.get(line_info.line.id):
            line_info.discounts.extend(discount)


def create_checkout_discount_objects_for_order_promotions(
    checkout_info: "CheckoutInfo",
    lines_info: Iterable["CheckoutLineInfo"],
    *,
    save: bool = False,
):
    # The base prices are required for order promotion discount qualification.
    _set_checkout_base_prices(checkout_info, lines_info)

    checkout = checkout_info.checkout

    # Discount from order rules is applied only when the voucher is not set
    if checkout.voucher_code:
        _clear_checkout_discount(checkout_info, lines_info, save)
        return

    channel = checkout_info.channel
    rules = fetch_promotion_rules_for_checkout_or_order(checkout)
    rule_data = get_best_rule(
        rules=rules,
        channel=channel,
        country=checkout_info.get_country(),
        subtotal=checkout.base_subtotal,
    )
    if not rule_data:
        _clear_checkout_discount(checkout_info, lines_info, save)
        return

    best_rule, best_discount_amount, gift_listing = rule_data
    promotion = best_rule.promotion
    currency = channel.currency_code
    translation_language_code = checkout.language_code
    promotion_translation, rule_translation = get_rule_translations(
        promotion, best_rule, translation_language_code
    )
    rule_info = VariantPromotionRuleInfo(
        rule=best_rule,
        variant_listing_promotion_rule=None,
        promotion=promotion,
        promotion_translation=promotion_translation,
        rule_translation=rule_translation,
    )
    # gift rule has empty reward_value and reward_value_type
    value_type = best_rule.reward_value_type or RewardValueType.FIXED
    amount_value = gift_listing.price_amount if gift_listing else best_discount_amount
    value = best_rule.reward_value or amount_value
    discount_object_defaults = {
        "promotion_rule": best_rule,
        "value_type": value_type,
        "value": value,
        "amount_value": amount_value,
        "currency": currency,
        "name": get_discount_name(best_rule, promotion),
        "translated_name": get_discount_translated_name(rule_info),
        "reason": prepare_promotion_discount_reason(promotion, get_sale_id(promotion)),
    }
    if gift_listing:
        _handle_gift_reward_for_checkout(
            checkout_info,
            lines_info,
            gift_listing,
            discount_object_defaults,
            rule_info,
            save,
        )
    else:
        _handle_order_promotion_for_checkout(
            checkout_info,
            lines_info,
            discount_object_defaults,
            rule_info,
            save,
        )


def get_best_rule(
    rules: Iterable["PromotionRule"],
    channel: "Channel",
    country: str,
    subtotal: Money,
):
    RuleDiscount = namedtuple(
        "RuleDiscount", ["rule", "discount_amount", "gift_listing"]
    )
    currency_code = channel.currency_code
    rule_discounts: list[RuleDiscount] = []
    gift_rules = [rule for rule in rules if rule.reward_type == RewardType.GIFT]
    for rule in rules:
        if rule in gift_rules:
            continue
        discount = rule.get_discount(currency_code)
        price = zero_money(currency_code)
        if rule.reward_type == RewardType.SUBTOTAL_DISCOUNT:
            price = subtotal
        discount_amount = (price - discount(price)).amount
        rule_discounts.append(RuleDiscount(rule, discount_amount, None))

    if gift_rules:
        best_gift_rule, gift_listing = _get_best_gift_reward(
            gift_rules,
            channel,
            country,
        )
        if best_gift_rule and gift_listing:
            rule_discounts.append(
                RuleDiscount(
                    best_gift_rule, gift_listing.discounted_price_amount, gift_listing
                )
            )

    if not rule_discounts:
        return

    best_rule, best_discount_amount, gift_listing = max(
        rule_discounts, key=lambda x: x.discount_amount
    )
    return best_rule, best_discount_amount, gift_listing


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


def _get_best_gift_reward(
    rules: Iterable["PromotionRule"],
    channel: "Channel",
    country: str,
) -> tuple[Optional[PromotionRule], Optional[ProductVariantChannelListing]]:
    from ..warehouse.availability import check_stock_quantity_bulk

    rule_ids = [rule.id for rule in rules]
    PromotionRuleGift = PromotionRule.gifts.through
    rule_gifts = PromotionRuleGift.objects.filter(promotionrule_id__in=rule_ids)
    variants = ProductVariant.objects.filter(
        Exists(
            rule_gifts.values("productvariant_id").filter(
                productvariant_id=OuterRef("id")
            )
        )
    )
    variant_ids_with_insufficient_stock = set()
    if not variants:
        return None, None

    try:
        check_stock_quantity_bulk(
            variants,
            country,
            [1] * variants.count(),
            channel.slug,
            None,
        )
    except InsufficientStock as error:
        variant_ids_with_insufficient_stock = {
            item.variant.pk for item in error.items if item.variant
        }

    available_variant_ids = (
        set(variants.values_list("id", flat=True)) - variant_ids_with_insufficient_stock
    )

    if not available_variant_ids:
        return None, None

    # check if variant is available for purchase
    available_variant_ids = _get_available_for_purchase_variant_ids(
        available_variant_ids, channel
    )
    if not available_variant_ids:
        return None, None

    # check variant channel availability
    available_variant_listings = ProductVariantChannelListing.objects.filter(
        variant_id__in=available_variant_ids,
        channel_id=channel.id,
        price_amount__isnull=False,
    )
    if not available_variant_listings:
        return None, None

    listing = max(
        list(available_variant_listings),
        # sort over a top price
        key=lambda x: x.discounted_price_amount,
    )
    rule_gift = rule_gifts.filter(productvariant_id=listing.variant_id).first()
    rule = rule_gift.promotionrule if rule_gift else None
    return rule, listing


def _get_available_for_purchase_variant_ids(
    available_variant_ids: set[int], channel: "Channel"
):
    today = datetime.datetime.now(pytz.UTC)
    variants = ProductVariant.objects.filter(id__in=available_variant_ids)
    product_listings = ProductChannelListing.objects.filter(
        Exists(variants.filter(product_id=OuterRef("product_id"))),
        available_for_purchase_at__lte=today,
        channel_id=channel.id,
    )
    available_variant_ids = variants.filter(
        Exists(product_listings.filter(product_id=OuterRef("product_id")))
    ).values_list("id", flat=True)
    return set(available_variant_ids)


def _handle_order_promotion_for_checkout(
    checkout_info: "CheckoutInfo",
    lines_info: Iterable["CheckoutLineInfo"],
    discount_object_defaults: dict,
    rule_info: VariantPromotionRuleInfo,
    save: bool = False,
):
    checkout = checkout_info.checkout
    discount_object, created = checkout.discounts.get_or_create(
        type=DiscountType.ORDER_PROMOTION,
        defaults=discount_object_defaults,
    )
    discount_amount = discount_object_defaults["amount_value"]

    if not created:
        fields_to_update: list[str] = []
        _update_promotion_discount(
            discount_object_defaults["promotion_rule"],
            rule_info,
            discount_amount,
            discount_object,
            fields_to_update,
        )
        if fields_to_update:
            discount_object.save(update_fields=fields_to_update)

    checkout_info.discounts = [discount_object]
    checkout = checkout_info.checkout
    checkout.discount_amount = discount_amount
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

    delete_gift_line(checkout, lines_info)


def delete_gift_line(
    order_or_checkout: Union[Checkout, Order],
    lines_info: Iterable[Union["CheckoutLineInfo", "EditableOrderLineInfo"]],
):
    if gift_line_infos := [line for line in lines_info if line.line.is_gift]:
        order_or_checkout.lines.filter(is_gift=True).delete()  # type: ignore[misc]
        for gift_line_info in gift_line_infos:
            lines_info.remove(gift_line_info)  # type: ignore[attr-defined]


def _handle_gift_reward_for_checkout(
    checkout_info: "CheckoutInfo",
    lines_info: Iterable["CheckoutLineInfo"],
    gift_listing: ProductVariantChannelListing,
    discount_object_defaults: dict,
    rule_info: VariantPromotionRuleInfo,
    save: bool = False,
):
    from ..checkout.fetch import CheckoutLineInfo

    with transaction.atomic():
        line, line_created = create_gift_line(checkout_info.checkout, gift_listing)
        (
            line_discount,
            discount_created,
        ) = CheckoutLineDiscount.objects.get_or_create(
            type=DiscountType.ORDER_PROMOTION,
            line=line,
            defaults=discount_object_defaults,
        )

    if not discount_created:
        fields_to_update = []
        if line_discount.line_id != line.id:
            line_discount.line = line
            fields_to_update.append("line_id")
        _update_promotion_discount(
            discount_object_defaults["promotion_rule"],
            rule_info,
            discount_object_defaults["amount_value"],
            line_discount,
            fields_to_update,
        )
        if fields_to_update:
            line_discount.save(update_fields=fields_to_update)

    checkout_info.discounts = []
    checkout_info.checkout.discount_amount = Decimal("0")
    if save:
        checkout_info.checkout.save(update_fields=["discount_amount"])

    if line_created:
        variant = gift_listing.variant
        init_values = {
            "line": line,
            "variant": variant,
            "channel_listing": gift_listing,
            "discounts": [line_discount],
            "rules_info": [rule_info],
            "channel": checkout_info.channel,
            "product": variant.product,
            "product_type": variant.product.product_type,
            "collections": [],
            "voucher": None,
            "voucher_code": None,
        }

        gift_line_info = CheckoutLineInfo(**init_values)
        lines_info.append(gift_line_info)  # type: ignore[attr-defined]
    else:
        line_info = next(
            line_info for line_info in lines_info if line_info.line.pk == line.id
        )
        line_info.line = line
        line_info.discounts = [line_discount]


def create_gift_line(
    order_or_checkout: Union[Checkout, Order],
    gift_listing: "ProductVariantChannelListing",
):
    defaults = _get_defaults_for_gift_line(order_or_checkout, gift_listing)
    line, created = order_or_checkout.lines.get_or_create(
        is_gift=True, defaults=defaults
    )
    if not created:
        fields_to_update = []
        for field, value in defaults.items():
            if getattr(line, field) != value:
                setattr(line, field, value)
                fields_to_update.append(field)
        if fields_to_update:
            line.save(update_fields=fields_to_update)

    return line, created


def _get_defaults_for_gift_line(
    order_or_checkout: Union[Checkout, Order],
    gift_listing: "ProductVariantChannelListing",
):
    variant_id = gift_listing.variant_id
    if isinstance(order_or_checkout, Checkout):
        return {
            "variant_id": variant_id,
            "quantity": 1,
            "currency": order_or_checkout.currency,
            "undiscounted_unit_price_amount": gift_listing.price_amount,
        }
    else:
        variant = (
            ProductVariant.objects.filter(id=variant_id)
            .select_related("product")
            .only("sku", "product__name")
            .first()
        )
        return {
            "variant_id": variant_id,
            "product_name": variant.product.name if variant else "",
            "product_sku": variant.sku if variant else "",
            "quantity": 1,
            "currency": order_or_checkout.currency,
            "unit_price_net_amount": Decimal(0),
            "unit_price_gross_amount": Decimal(0),
            "total_price_net_amount": Decimal(0),
            "total_price_gross_amount": Decimal(0),
            "is_shipping_required": True,
            "is_gift_card": False,
        }


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
    promotion_rule_variants = PromotionRuleVariant.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).filter(Exists(variant_qs.filter(id=OuterRef("productvariant_id"))))

    # fetch rules only for active promotions
    rules = PromotionRule.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).filter(
        Exists(promotions.filter(id=OuterRef("promotion_id"))),
        Exists(promotion_rule_variants.filter(promotionrule_id=OuterRef("pk"))),
    )
    rule_to_channel_ids_map = _get_rule_to_channel_ids_map(rules)
    rules_in_bulk = rules.in_bulk()

    for promotion_rule_variant in promotion_rule_variants.iterator():
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


def fetch_promotion_rules_for_checkout_or_order(
    instance: Union["Checkout", "Order"],
):
    from ..graphql.discount.utils import PredicateObjectType, filter_qs_by_predicate

    applicable_rules = []
    promotions = Promotion.objects.active()
    rules = (
        PromotionRule.objects.filter(
            Exists(promotions.filter(id=OuterRef("promotion_id")))
        )
        .exclude(order_predicate={})
        .prefetch_related("channels")
    )
    rule_to_channel_ids_map = _get_rule_to_channel_ids_map(rules)

    channel_id = instance.channel_id
    currency = instance.channel.currency_code
    qs = instance._meta.model.objects.filter(pk=instance.pk)  # type: ignore[attr-defined] # noqa: E501

    for rule in rules.iterator():
        rule_channel_ids = rule_to_channel_ids_map.get(rule.id, [])
        if channel_id not in rule_channel_ids:
            continue
        predicate_type = (
            PredicateObjectType.CHECKOUT
            if isinstance(instance, Checkout)
            else PredicateObjectType.ORDER
        )
        objects = filter_qs_by_predicate(
            rule.order_predicate,
            qs,
            predicate_type,
            currency,
        )
        if objects.exists():
            applicable_rules.append(rule)

    return applicable_rules


def _get_rule_to_channel_ids_map(rules: QuerySet):
    rule_to_channel_ids_map = defaultdict(list)
    PromotionRuleChannel = PromotionRule.channels.through
    promotion_rule_channels = PromotionRuleChannel.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).filter(Exists(rules.filter(id=OuterRef("promotionrule_id"))))
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


def _create_new_rules(rules_to_add, variants_lock, rules_lock):
    # base on what locks returned, filter out rules and variants that weren't locked
    rules_to_add_batch = [
        rv
        for rv in rules_to_add
        if rv.promotionrule_id in rules_lock and rv.productvariant_id in variants_lock
    ]

    return PromotionRule.variants.through.objects.bulk_create(
        rules_to_add_batch, ignore_conflicts=True
    )


def update_rule_variant_relation(
    rules: QuerySet[PromotionRule], new_rules_variants: list
):
    """Update PromotionRule - ProductVariant relation.

    Deletes relations, which are not valid anymore.
    Adds new relations, if they don't exist already.
    `new_rules_variants` is a list of PromotionRuleVariant objects.

    It is important to lock the variants and rules before deleting and adding new
    relations to avoid integrity errors. It is also important to lock the rules and
    variants in the same order to avoid deadlocks.
    """
    PromotionRuleVariant = PromotionRule.variants.through
    existing_rules_variants = PromotionRuleVariant.objects.filter(
        Exists(rules.filter(pk=OuterRef("promotionrule_id")))
    ).all()
    new_rule_variant_set = set(
        (rv.promotionrule_id, rv.productvariant_id) for rv in new_rules_variants
    )
    existing_rule_variant_set = set(
        (rv.promotionrule_id, rv.productvariant_id) for rv in existing_rules_variants
    )
    # Assign new variants to promotion rules
    rules_variants_to_add = [
        rv
        for rv in new_rules_variants
        if (rv.promotionrule_id, rv.productvariant_id) not in existing_rule_variant_set
    ]

    # Clear invalid variants assigned to promotion rules
    rule_variant_to_delete_ids = [
        rv
        for rv in existing_rules_variants
        if (rv.promotionrule_id, rv.productvariant_id) not in new_rule_variant_set
    ]
    with transaction.atomic():
        variants_lock = tuple(
            ProductVariant.objects.order_by("pk")
            .select_for_update(of=("self",))
            .filter(
                id__in={
                    rv.productvariant_id
                    for rv in chain(rule_variant_to_delete_ids, rules_variants_to_add)
                }
            )
            .values_list("id", flat=True)
        )
        rules_lock = tuple(
            PromotionRule.objects.order_by("pk")
            .select_for_update(of=("self",))
            .filter(
                id__in={
                    rv.promotionrule_id
                    for rv in chain(rule_variant_to_delete_ids, rules_variants_to_add)
                }
            )
            .values_list("pk", flat=True)
        )
        PromotionRuleVariant.objects.order_by("pk").select_for_update(
            of=("self",)
        ).filter(id__in={rv.id for rv in rule_variant_to_delete_ids}).delete()

        return _create_new_rules(rules_variants_to_add, variants_lock, rules_lock)


def create_or_update_discount_objects_for_order(
    order: "Order", lines_info: Iterable["EditableOrderLineInfo"]
):
    create_or_update_discount_objects_from_promotion_for_order(order, lines_info)
    create_or_update_line_discount_objects_for_manual_discounts(lines_info)
    create_or_update_discount_objects_from_voucher(order, lines_info)
    _copy_unit_discount_data_to_order_line(lines_info)


def create_or_update_discount_objects_from_promotion_for_order(
    order: "Order",
    lines_info: Iterable["EditableOrderLineInfo"],
):
    create_order_line_discount_objects_for_catalogue_promotions(lines_info)
    # base unit price must reflect all actual catalogue discounts
    _update_base_unit_price_amount_for_catalogue_promotion(lines_info)
    create_order_discount_objects_for_order_promotions(order, lines_info)


def create_order_line_discount_objects_for_catalogue_promotions(
    lines_info: Iterable["EditableOrderLineInfo"],
):
    discount_data = prepare_line_discount_objects_for_catalogue_promotions(lines_info)
    create_order_line_discount_objects(lines_info, discount_data)


def create_order_line_discount_objects(
    lines_info: Iterable["EditableOrderLineInfo"],
    discount_data: tuple[
        list[dict],
        list["OrderLineDiscount"],
        list["OrderLineDiscount"],
        list[str],
    ],
):
    if not discount_data or not lines_info:
        return

    (
        discounts_to_create_inputs,
        discounts_to_update,
        discount_to_remove,
        updated_fields,
    ) = discount_data

    new_line_discounts: list[OrderLineDiscount] = []
    with transaction.atomic():
        # Protect against potential thread race. OrderLine object can have only
        # single catalogue discount applied.
        order_id = lines_info[0].line.order_id  # type: ignore[index]
        _order_lock = list(
            Order.objects.filter(id=order_id).select_for_update(of=(["self"]))
        )

        if discount_ids_to_remove := [discount.id for discount in discount_to_remove]:
            OrderLineDiscount.objects.filter(id__in=discount_ids_to_remove).delete()

        if discounts_to_create_inputs:
            new_line_discounts = [
                OrderLineDiscount(**input) for input in discounts_to_create_inputs
            ]
            OrderLineDiscount.objects.bulk_create(
                new_line_discounts, ignore_conflicts=True
            )

        if discounts_to_update and updated_fields:
            OrderLineDiscount.objects.bulk_update(discounts_to_update, updated_fields)

    _update_line_info_cached_discounts(
        lines_info, new_line_discounts, discounts_to_update, discount_ids_to_remove
    )
    affected_line_ids = [
        discount_line.line_id
        for discount_line in (new_line_discounts + discounts_to_update)
    ]
    affected_line_ids.extend(discount_ids_to_remove)
    modified_lines_info = [
        line_info for line_info in lines_info if line_info.line.id in affected_line_ids
    ]
    return modified_lines_info


def _copy_unit_discount_data_to_order_line(
    lines_info: Iterable["EditableOrderLineInfo"],
):
    for line_info in lines_info:
        if discounts := line_info.discounts:
            line = line_info.line
            discount_amount = sum([discount.amount_value for discount in discounts])
            unit_discount_amount = discount_amount / line.quantity
            discount_reason = "; ".join(
                [discount.reason for discount in discounts if discount.reason]
            )
            discount_type = (
                discounts[0].value_type
                if len(discounts) == 1
                else DiscountValueType.FIXED
            )
            discount_value = (
                discounts[0].value if len(discounts) == 1 else unit_discount_amount
            )

            line.unit_discount_amount = unit_discount_amount
            line.unit_discount_reason = discount_reason
            line.unit_discount_type = discount_type
            line.unit_discount_value = discount_value


def _update_base_unit_price_amount_for_catalogue_promotion(
    lines_info: Iterable["EditableOrderLineInfo"],
):
    for line_info in lines_info:
        line = line_info.line
        base_unit_price = line.undiscounted_base_unit_price_amount
        for discount in line_info.get_catalogue_discounts():
            unit_discount = discount.amount_value / line.quantity
            base_unit_price -= unit_discount
        line.base_unit_price_amount = max(base_unit_price, Decimal(0))


def create_order_discount_objects_for_order_promotions(
    order: "Order",
    lines_info: Iterable["EditableOrderLineInfo"],
):
    from ..order.utils import get_order_country

    # If voucher is set or manual discount applied, then skip order promotions
    if order.voucher_code or order.discounts.filter(type=DiscountType.MANUAL):
        _clear_order_discount(order, lines_info)
        return

    # The base prices are required for order promotion discount qualification.
    _set_order_base_prices(order, lines_info)

    channel = order.channel
    rules = fetch_promotion_rules_for_checkout_or_order(order)
    rule_data = get_best_rule(
        rules=rules,
        channel=channel,
        country=get_order_country(order),
        subtotal=order.subtotal.net,
    )
    if not rule_data:
        _clear_order_discount(order, lines_info)
        return

    best_rule, best_discount_amount, gift_listing = rule_data
    promotion = best_rule.promotion
    currency = channel.currency_code
    translation_language_code = order.language_code
    promotion_translation, rule_translation = get_rule_translations(
        promotion, best_rule, translation_language_code
    )
    rule_info = VariantPromotionRuleInfo(
        rule=best_rule,
        variant_listing_promotion_rule=None,
        promotion=best_rule.promotion,
        promotion_translation=promotion_translation,
        rule_translation=rule_translation,
    )
    # gift rule has empty reward_value and reward_value_type
    value_type = best_rule.reward_value_type or RewardValueType.FIXED
    amount_value = gift_listing.price_amount if gift_listing else best_discount_amount
    value = best_rule.reward_value or amount_value
    discount_object_defaults = {
        "promotion_rule": best_rule,
        "value_type": value_type,
        "value": value,
        "amount_value": amount_value,
        "currency": currency,
        "name": get_discount_name(best_rule, promotion),
        "translated_name": get_discount_translated_name(rule_info),
        "reason": prepare_promotion_discount_reason(promotion, get_sale_id(promotion)),
    }
    if gift_listing:
        _handle_gift_reward_for_order(
            order,
            lines_info,
            gift_listing,
            discount_object_defaults,
            rule_info,
        )
    else:
        _handle_order_promotion_for_order(
            order,
            lines_info,
            discount_object_defaults,
            rule_info,
        )


def _clear_order_discount(
    order_or_checkout: Union[Checkout, Order],
    lines_info: Iterable["EditableOrderLineInfo"],
):
    with transaction.atomic():
        delete_gift_line(order_or_checkout, lines_info)
        order_or_checkout.discounts.filter(type=DiscountType.ORDER_PROMOTION).delete()


def _set_order_base_prices(order: Order, lines_info: Iterable["EditableOrderLineInfo"]):
    """Set base order prices that includes only catalogue discounts."""
    from ..order.base_calculations import base_order_subtotal

    lines = [line_info.line for line_info in lines_info]
    subtotal = base_order_subtotal(order, lines)
    shipping_price = order.base_shipping_price
    total = subtotal + shipping_price

    update_fields = []
    if order.subtotal != TaxedMoney(net=subtotal, gross=subtotal):
        order.subtotal = TaxedMoney(net=subtotal, gross=subtotal)
        update_fields.extend(["subtotal_net_amount", "subtotal_gross_amount"])
    if order.total != TaxedMoney(net=total, gross=total):
        order.total = TaxedMoney(net=total, gross=total)
        update_fields.extend(["total_net_amount", "total_gross_amount"])

    if update_fields:
        order.save(update_fields=update_fields)


def _handle_order_promotion_for_order(
    order: Order,
    lines_info: Iterable["EditableOrderLineInfo"],
    discount_object_defaults: dict,
    rule_info: VariantPromotionRuleInfo,
):
    discount_object, created = order.discounts.get_or_create(
        type=DiscountType.ORDER_PROMOTION,
        defaults=discount_object_defaults,
    )
    discount_amount = discount_object_defaults["amount_value"]

    if not created:
        fields_to_update: list[str] = []
        _update_promotion_discount(
            discount_object_defaults["promotion_rule"],
            rule_info,
            discount_amount,
            discount_object,
            fields_to_update,
        )
        if fields_to_update:
            discount_object.save(update_fields=fields_to_update)

    delete_gift_line(order, lines_info)


def _handle_gift_reward_for_order(
    order: Order,
    lines_info: Iterable["EditableOrderLineInfo"],
    gift_listing: ProductVariantChannelListing,
    discount_object_defaults: dict,
    rule_info: VariantPromotionRuleInfo,
):
    from ..order.fetch import EditableOrderLineInfo

    with transaction.atomic():
        line, line_created = create_gift_line(order, gift_listing)
        (
            line_discount,
            discount_created,
        ) = OrderLineDiscount.objects.get_or_create(
            type=DiscountType.ORDER_PROMOTION,
            line=line,
            defaults=discount_object_defaults,
        )

    if not discount_created:
        fields_to_update = []
        if line_discount.line_id != line.id:
            line_discount.line = line
            fields_to_update.append("line_id")
        _update_promotion_discount(
            discount_object_defaults["promotion_rule"],
            rule_info,
            discount_object_defaults["amount_value"],
            line_discount,
            fields_to_update,
        )
        if fields_to_update:
            line_discount.save(update_fields=fields_to_update)

    if line_created:
        variant = gift_listing.variant
        init_values = {
            "line": line,
            "variant": variant,
            "product": variant.product,
            "collections": list(variant.product.collections.all()),
            "channel_listing": gift_listing,
            "discounts": [line_discount],
            "rules_info": [rule_info],
            "channel": order.channel_id,
            "voucher": None,
            "voucher_code": None,
        }
        gift_line_info = EditableOrderLineInfo(**init_values)
        lines_info.append(gift_line_info)  # type: ignore[attr-defined]
    else:
        line_info = next(
            line_info for line_info in lines_info if line_info.line.pk == line.id
        )
        line_info.line = line
        line_info.discounts = [line_discount]


def create_or_update_line_discount_objects_for_manual_discounts(lines_info):
    discount_to_update: list[OrderLineDiscount] = []
    for line_info in lines_info:
        manual_discount = line_info.get_manual_line_discount()
        if not manual_discount:
            continue
        line = line_info.line
        base_unit_price = line.undiscounted_base_unit_price
        reduced_unit_price = apply_discount_to_value(
            manual_discount.value,
            manual_discount.value_type,
            line.currency,
            base_unit_price,
        )
        reduced_unit_price = max(reduced_unit_price, zero_money(line.currency))
        line.base_unit_price_amount = reduced_unit_price.amount

        discount_unit_amount = (base_unit_price - reduced_unit_price).amount
        discount_amount = discount_unit_amount * line.quantity
        if manual_discount.amount_value != discount_amount:
            manual_discount.amount_value = discount_amount
            discount_to_update.append(manual_discount)

    if discount_to_update:
        OrderLineDiscount.objects.bulk_update(discount_to_update, ["amount_value"])


def create_or_update_discount_objects_from_voucher(order, lines_info):
    create_or_update_discount_object_from_order_level_voucher(order)
    create_or_update_line_discount_objects_from_voucher(lines_info)


def create_or_update_discount_object_from_order_level_voucher(order):
    """Create or update discount object for ENTIRE_ORDER and SHIPPING voucher."""
    voucher = order.voucher
    if not order.voucher_id or (
        is_order_level_voucher(voucher)
        and order.discounts.filter(type=DiscountType.MANUAL)
    ):
        order.discounts.filter(type=DiscountType.VOUCHER).delete()
        return

    if not is_order_level_voucher(voucher) and not is_shipping_voucher(voucher):
        return

    voucher_channel_listing = voucher.channel_listings.filter(
        channel=order.channel
    ).first()
    if not voucher_channel_listing:
        return

    discount_amount = zero_money(order.currency)
    if is_order_level_voucher(voucher):
        discount_amount = voucher.get_discount_amount_for(
            order.subtotal.net, order.channel
        )
    if is_shipping_voucher(voucher):
        discount_amount = voucher.get_discount_amount_for(
            order.undiscounted_base_shipping_price, order.channel
        )
        # Shipping voucher is tricky: it is associated with an order, but it
        # decreases base price, similar to line level discounts
        order.base_shipping_price = max(
            order.undiscounted_base_shipping_price - discount_amount,
            zero_money(order.currency),
        )

    discount_reason = f"Voucher code: {order.voucher_code}"
    discount_name = voucher.name or ""

    discount_object_defaults = {
        "voucher": voucher,
        "value_type": voucher.discount_value_type,
        "value": voucher_channel_listing.discount_value,
        "amount_value": discount_amount.amount,
        "currency": order.currency,
        "reason": discount_reason,
        "name": discount_name,
        "type": DiscountType.VOUCHER,
        "voucher_code": order.voucher_code,
        # TODO (SHOPX-914): set translated voucher name
        "translated_name": "",
    }

    discount_object, created = order.discounts.get_or_create(
        type=DiscountType.VOUCHER,
        defaults=discount_object_defaults,
    )
    if not created:
        updated_fields: list[str] = []
        _update_discount(
            rule=None,
            voucher=voucher,
            discount_name=discount_name,
            # TODO (SHOPX-914): set translated voucher name
            translated_name="",
            discount_reason=discount_reason,
            discount_amount=discount_amount.amount,
            value=voucher_channel_listing.discount_value,
            value_type=voucher.discount_value_type,
            unique_type=DiscountType.VOUCHER,
            discount_to_update=discount_object,
            updated_fields=updated_fields,
            voucher_code=order.voucher_code,
        )
        if updated_fields:
            discount_object.save(update_fields=updated_fields)


def create_or_update_line_discount_objects_from_voucher(lines_info):
    """Create or update line discount object for voucher applied on lines.

    The LineDiscount object is created for each line with voucher applied.
    Only `SPECIFIC_PRODUCT` and `apply_once_per_order` voucher types are applied.

    """
    discount_data = prepare_line_discount_objects_for_voucher(lines_info)
    modified_lines_info = create_order_line_discount_objects(lines_info, discount_data)
    # base unit price must reflect all actual line voucher discounts
    if modified_lines_info:
        _reduce_base_unit_price_for_voucher_discount(modified_lines_info)


# TODO (SHOPX-912): share the method with checkout
def prepare_line_discount_objects_for_voucher(
    lines_info: Iterable["EditableOrderLineInfo"],
):
    line_discounts_to_create_inputs: list[dict] = []
    line_discounts_to_update: list[OrderLineDiscount] = []
    line_discounts_to_remove: list[OrderLineDiscount] = []
    updated_fields: list[str] = []

    if not lines_info:
        return

    for line_info in lines_info:
        line = line_info.line
        total_price = line.base_unit_price * line.quantity
        discount_amount = calculate_line_discount_amount_from_voucher(
            line_info, total_price
        )
        # only one voucher can be applied
        discount_to_update = None
        if discounts_to_update := line_info.get_voucher_discounts():
            discount_to_update = discounts_to_update[0]

        # manual line discount do not stack with other line discounts
        manual_line_discount = line_info.get_manual_line_discount()

        if not discount_amount or line.is_gift or manual_line_discount:
            if discount_to_update:
                line_discounts_to_remove.append(discount_to_update)
            continue

        discount_amount = discount_amount.amount
        code = line_info.voucher_code
        discount_reason = f"Voucher code: {code}"
        voucher = cast(Voucher, line_info.voucher)
        discount_name = f"{voucher.name}"
        if discount_to_update:
            _update_discount(
                rule=None,
                voucher=voucher,
                discount_name=discount_name,
                # TODO (SHOPX-914): set translated voucher name
                translated_name="",
                discount_reason=discount_reason,
                discount_amount=discount_amount,
                value=discount_amount,
                value_type=voucher.discount_value_type,
                unique_type=DiscountType.VOUCHER,
                discount_to_update=discount_to_update,
                updated_fields=updated_fields,
                voucher_code=code,
            )
            line_discounts_to_update.append(discount_to_update)
        else:
            line_discount_input = {
                "line": line,
                "type": DiscountType.VOUCHER,
                # TODO (SHOPX-914): should be taken from voucher value_type and value
                "value_type": DiscountValueType.FIXED,
                "value": discount_amount,
                "amount_value": discount_amount,
                "currency": line.currency,
                "name": discount_name,
                "translated_name": None,
                "reason": discount_reason,
                "voucher": line_info.voucher,
                "unique_type": DiscountType.VOUCHER,
                "voucher_code": code,
            }
            line_discounts_to_create_inputs.append(line_discount_input)

    return (
        line_discounts_to_create_inputs,
        line_discounts_to_update,
        line_discounts_to_remove,
        updated_fields,
    )


def calculate_line_discount_amount_from_voucher(
    line_info: "LineInfo", total_price: Money
) -> Money:
    """Calculate discount amount for voucher applied on line.

    Included vouchers: `SPECIFIC_PRODUCT` and `apply_once_per_order`.

    Args:
        line_info: Order/Checkout line data.
        total_price: Total price of the line, should be already reduced by
    catalogue discounts if any applied.

    """
    if not line_info.voucher:
        return zero_money(total_price.currency)

    channel = line_info.channel
    quantity = line_info.line.quantity
    if not line_info.voucher.apply_once_per_order:
        if line_info.voucher.discount_value_type == DiscountValueType.PERCENTAGE:
            voucher_discount_amount = line_info.voucher.get_discount_amount_for(
                total_price, channel=channel
            )
            discount_amount = min(voucher_discount_amount, total_price)
        else:
            unit_price = total_price / quantity
            voucher_unit_discount_amount = line_info.voucher.get_discount_amount_for(
                unit_price, channel=channel
            )
            discount_amount = min(
                voucher_unit_discount_amount * quantity,
                total_price,
            )
    else:
        unit_price = total_price / quantity
        voucher_unit_discount_amount = line_info.voucher.get_discount_amount_for(
            unit_price, channel=channel
        )
        discount_amount = min(voucher_unit_discount_amount, unit_price)
    return discount_amount


def _reduce_base_unit_price_for_voucher_discount(
    lines_info: Iterable["EditableOrderLineInfo"],
):
    for line_info in lines_info:
        line = line_info.line
        base_unit_price = line.base_unit_price_amount
        for discount in line_info.get_voucher_discounts():
            base_unit_price -= discount.amount_value / line.quantity
        line.base_unit_price_amount = max(base_unit_price, Decimal(0))


def get_active_catalogue_promotion_rules(
    allow_replica: bool = False,
) -> "QuerySet[PromotionRule]":
    promotions = Promotion.objects.active().filter(type=PromotionType.CATALOGUE)
    if allow_replica:
        promotions = promotions.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
    rules = (
        PromotionRule.objects.order_by("id")
        .filter(
            Exists(promotions.filter(id=OuterRef("promotion_id"))),
        )
        .exclude(catalogue_predicate={})
    )
    if allow_replica:
        rules = rules.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
    return rules


def mark_active_catalogue_promotion_rules_as_dirty(channel_ids: Iterable[int]):
    """Force promotion rule to recalculate.

    The rules which are marked as dirty, will be recalculated in background.
    Products related to these rules will be recalculated as well.
    """

    if not channel_ids:
        return

    rules = get_active_catalogue_promotion_rules()
    PromotionRuleChannel = PromotionRule.channels.through
    promotion_rules = PromotionRuleChannel.objects.filter(channel_id__in=channel_ids)
    rule_ids = rules.filter(
        Exists(promotion_rules.filter(promotionrule_id=OuterRef("id")))
    ).values_list("id", flat=True)

    with transaction.atomic():
        rule_ids_to_update = list(
            PromotionRule.objects.select_for_update(of=("self",))
            .filter(id__in=rule_ids, variants_dirty=False)
            .order_by("pk")
            .values_list("id", flat=True)
        )
        PromotionRule.objects.filter(id__in=rule_ids_to_update).update(
            variants_dirty=True
        )


def mark_catalogue_promotion_rules_as_dirty(promotion_pks: Iterable[UUID]):
    """Mark rules for promotions as dirty.

    The rules which are marked as dirty, will be recalculated in background.
    Products related to these rules will be recalculated as well.
    """
    if not promotion_pks:
        return
    with transaction.atomic():
        rule_ids_to_update = list(
            PromotionRule.objects.select_for_update(of=(["self"]))
            .filter(promotion_id__in=promotion_pks, variants_dirty=False)
            .order_by("pk")
            .values_list("id", flat=True)
        )
        PromotionRule.objects.filter(id__in=rule_ids_to_update).update(
            variants_dirty=True
        )


def split_manual_discount(
    discount: OrderDiscount, subtotal: Money, shipping_price: Money
) -> tuple[Money, Money]:
    """Discounts sent to tax app must be split into subtotal and shipping portion."""
    currency = subtotal.currency
    subtotal_discount, shipping_discount = zero_money(currency), zero_money(currency)
    total = subtotal + shipping_price
    if total.amount > 0:
        discounted_total = apply_discount_to_value(
            value=discount.value,
            value_type=discount.value_type,
            currency=currency,
            price_to_discount=total,
        )
        total_discount = total - discounted_total
        subtotal_discount = subtotal / total * total_discount
        shipping_discount = total_discount - subtotal_discount

    return quantize_price(subtotal_discount, currency), quantize_price(
        shipping_discount, currency
    )


def discount_info_for_logs(discounts):
    return [
        {
            "id": to_global_id_or_none(discount),
            "type": discount.type,
            "value_type": discount.value_type,
            "value": discount.value,
            "amount_value": discount.amount_value,
            "reason": discount.reason,
            "promotion_rule": {
                "id": to_global_id_or_none(discount.promotion_rule),
                "promotion_id": graphene.Node.to_global_id(
                    "Promotion", discount.promotion_rule.promotion_id
                ),
                "catalogue_predicate": discount.promotion_rule.catalogue_predicate,
                "order_predicate": discount.promotion_rule.order_predicate,
                "reward_value_type": discount.promotion_rule.reward_value_type,
                "reward_value": discount.promotion_rule.reward_value,
                "reward_type": discount.promotion_rule.reward_type,
                "variants_dirty": discount.promotion_rule.variants_dirty,
            }
            if discount.promotion_rule
            else None,
            "voucher": {
                "id": to_global_id_or_none(discount.voucher),
                "type": discount.voucher.type,
                "discount_value_type": discount.voucher.discount_value_type,
                "apply_once_per_order": discount.voucher.apply_once_per_order,
            }
            if discount.voucher
            else None,
        }
        for discount in discounts
    ]
