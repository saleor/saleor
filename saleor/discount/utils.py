import datetime
from collections import defaultdict, namedtuple
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from functools import partial
from typing import (
    TYPE_CHECKING,
    Callable,
    Generic,
    Optional,
    TypeVar,
    Union,
    cast,
)
from uuid import UUID

import graphene
import pytz
from django.db import transaction
from django.db.models import Exists, F, OuterRef, QuerySet, prefetch_related_objects
from django.utils import timezone
from prices import Money, TaxedMoney, fixed_discount, percentage_discount

from ..channel.models import Channel
from ..checkout.base_calculations import (
    base_checkout_delivery_price,
    base_checkout_subtotal,
)
from ..checkout.fetch import CheckoutInfo, CheckoutLineInfo
from ..checkout.models import Checkout, CheckoutLine
from ..core.exceptions import InsufficientStock
from ..core.taxes import zero_money
from ..core.utils.promo_code import InvalidPromoCode
from ..order.fetch import DraftOrderLineInfo
from ..order.models import Order, OrderLine
from ..product.models import (
    Product,
    ProductChannelListing,
    ProductVariant,
    ProductVariantChannelListing,
)
from . import DiscountType, PromotionRuleInfo, RewardType, RewardValueType
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
    from ..graphql.discount.utils import PredicateObjectType
    from ..plugins.manager import PluginsManager
    from ..product.managers import ProductVariantQueryset
    from ..product.models import (
        VariantChannelListingPromotionRule,
    )

CatalogueInfo = defaultdict[str, set[Union[int, str]]]
CATALOGUE_FIELDS = ["categories", "collections", "products", "variants"]
T_Model = TypeVar("T_Model", bound=type[Union[Checkout, Order]])
T_LineModel = TypeVar("T_LineModel", bound=type[Union[CheckoutLine, OrderLine]])
T_DiscountModel = TypeVar(
    "T_DiscountModel", bound=type[Union[CheckoutDiscount, OrderDiscount]]
)
T_LineDiscountModel = TypeVar(
    "T_LineDiscountModel", bound=type[Union[CheckoutLineDiscount, OrderLineDiscount]]
)
T_LineInfo = TypeVar(
    "T_LineInfo", bound=type[Union[CheckoutLineInfo, DraftOrderLineInfo]]
)


@dataclass
class CheckoutOrOrderHelper(
    Generic[T_Model, T_LineModel, T_DiscountModel, T_LineDiscountModel, T_LineInfo]
):
    predicate_type: "PredicateObjectType"
    model: T_Model
    line_model: T_LineModel
    discount_model: T_DiscountModel
    discount_line_model: T_LineDiscountModel
    line_info: T_LineInfo


def get_checkout_or_order_models(
    instance: Union[Checkout, Order],
) -> CheckoutOrOrderHelper:
    from ..graphql.discount.utils import PredicateObjectType

    if isinstance(instance, (Checkout, CheckoutInfo, CheckoutLine, CheckoutLineInfo)):
        return CheckoutOrOrderHelper(
            predicate_type=PredicateObjectType.CHECKOUT,
            model=Checkout,
            line_model=CheckoutLine,
            discount_model=CheckoutDiscount,
            discount_line_model=CheckoutLineDiscount,
            line_info=CheckoutLineInfo,
        )
    else:
        return CheckoutOrOrderHelper(
            predicate_type=PredicateObjectType.ORDER,
            model=Order,
            line_model=OrderLine,
            discount_model=OrderDiscount,
            discount_line_model=OrderLineDiscount,
            line_info=DraftOrderLineInfo,
        )


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
    value_type: str,
    currency: str,
    price_to_discount: Union[Money, TaxedMoney],
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
    checkout_info: "CheckoutInfo",
    lines_info: Iterable["CheckoutLineInfo"],
):
    create_discount_objects_for_catalogue_promotions(lines_info)
    create_checkout_discount_objects_for_order_promotions(checkout_info, lines_info)


def create_or_update_discount_objects_from_promotion_for_order(
    order: "Order",
    lines_info: Iterable["DraftOrderLineInfo"],
):
    # TODO zedzior sprawdz checkoutowe flow czy nie trzbea poodswiezac prefetchy
    create_discount_objects_for_catalogue_promotions(lines_info)
    _update_order_line_prefetched_discounts(lines_info)
    _update_order_line_base_unit_prices(lines_info)

    create_order_discount_objects_for_order_promotions(order, lines_info)
    # if order promotion is type of gift, discount is associated with line, not order
    _update_order_line_prefetched_discounts(lines_info)


def _update_order_line_prefetched_discounts(lines_info: Iterable[DraftOrderLineInfo]):
    modified_lines_info = [
        line_info for line_info in lines_info if line_info.should_refresh_discounts
    ]
    for line_info in modified_lines_info:
        line_info.line._prefetched_objects_cache.pop(  # type: ignore[attr-defined] # noqa: E501
            "discounts", None
        )
    modified_lines = [line_info.line for line_info in modified_lines_info]
    prefetch_related_objects(modified_lines, "discounts__promotion_rule__promotion")
    for line_info in modified_lines_info:
        line_info.discounts = list(line_info.line.discounts.all())


def _update_order_line_base_unit_prices(lines_info: Iterable[DraftOrderLineInfo]):
    modified_lines = [
        line_info.line for line_info in lines_info if line_info.should_refresh_discounts
    ]
    for line in modified_lines:
        base_unit_price = line.undiscounted_base_unit_price_amount
        for discount in line.discounts.all():
            unit_discount = discount.amount_value / line.quantity
            base_unit_price -= unit_discount
        line.base_unit_price_amount = max(base_unit_price, Decimal(0))
    OrderLine.objects.bulk_update(modified_lines, ["base_unit_price_amount"])


def create_discount_objects_for_catalogue_promotions(
    lines_info: Union[Iterable["CheckoutLineInfo"], Iterable["DraftOrderLineInfo"]],
):
    line_discounts_to_create = []
    line_discounts_to_update = []
    line_discount_ids_to_remove = []
    updated_fields: list[str] = []

    if not lines_info:
        return

    models = get_checkout_or_order_models(lines_info[0])  # type: ignore[index]

    for line_info in lines_info:
        line = line_info.line

        # discount_amount based on the difference between discounted_price and price
        discount_amount = _get_discount_amount(line_info.channel_listing, line.quantity)

        # get the existing discounts for the line
        discounts_to_update = line_info.get_catalogue_discounts()
        rule_id_to_discount = {
            discount.promotion_rule_id: discount for discount in discounts_to_update
        }

        # delete all existing discounts if the line is not discounted, or it is a gift
        if not discount_amount or line.is_gift:
            ids_to_remove = [discount.id for discount in discounts_to_update]
            if ids_to_remove:
                line_discount_ids_to_remove.extend(ids_to_remove)
                line_info.discounts = [  # type: ignore[assignment]
                    discount
                    for discount in line_info.discounts
                    if discount.id not in ids_to_remove
                ]
                _invalidate_order_line_discounts(line_info)
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
            reason = _get_discount_reason(rule)
            if not discount_to_update:
                line_discount = models.discount_line_model(
                    line=line,
                    type=DiscountType.PROMOTION,
                    value_type=rule.reward_value_type,
                    value=rule.reward_value,
                    amount_value=rule_discount_amount,
                    currency=line.currency,
                    name=discount_name,
                    translated_name=translated_name,
                    reason=reason,
                    promotion_rule=rule,
                )
                line_discounts_to_create.append(line_discount)
                line_info.discounts.append(line_discount)
            else:
                _update_discount(
                    rule,
                    rule_info,
                    rule_discount_amount,
                    discount_to_update,
                    updated_fields,
                )
                line_discounts_to_update.append(discount_to_update)
            _invalidate_order_line_discounts(line_info)

    if line_discounts_to_create:
        models.discount_line_model.objects.bulk_create(line_discounts_to_create)
    if line_discounts_to_update and updated_fields:
        models.discount_line_model.objects.bulk_update(
            line_discounts_to_update, updated_fields
        )
    if line_discount_ids_to_remove:
        models.discount_line_model.objects.filter(
            id__in=line_discount_ids_to_remove
        ).delete()


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
    rule_id_to_discount: dict[int, Union["CheckoutLineDiscount", "OrderLineDiscount"]],
    line_info: Union["CheckoutLineInfo", "DraftOrderLineInfo"],
):
    discount_ids = []
    rule_ids = {rule_info.rule.id for rule_info in rules_info}
    for rule_id, discount in rule_id_to_discount.items():
        if rule_id not in rule_ids:
            discount_ids.append(discount.id)
            line_info.discounts.remove(discount)  # type: ignore[arg-type]  # got "Union[CheckoutLineDiscount, OrderLineDiscount]"; expected "CheckoutLineDiscount"
            _invalidate_order_line_discounts(line_info)
    return discount_ids


def _get_rule_discount_amount(
    variant_listing_promotion_rule: Optional["VariantChannelListingPromotionRule"],
    line_quantity: int,
) -> Decimal:
    if not variant_listing_promotion_rule:
        return Decimal("0.0")
    discount_amount = variant_listing_promotion_rule.discount_amount
    return discount_amount * line_quantity


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


def _update_discount(
    rule: "PromotionRule",
    rule_info: "VariantPromotionRuleInfo",
    rule_discount_amount: Decimal,
    discount_to_update: Union[
        "CheckoutLineDiscount", "CheckoutDiscount", "OrderLineDiscount", "OrderDiscount"
    ],
    updated_fields: list[str],
):
    if discount_to_update.promotion_rule_id != rule.id:
        discount_to_update.promotion_rule_id = rule.id
        updated_fields.append("promotion_rule_id")
    # gift rule has empty reward_value_type
    value_type = rule.reward_value_type or RewardValueType.FIXED
    if discount_to_update.value_type != value_type:
        discount_to_update.value_type = value_type
        updated_fields.append("value_type")
    # gift rule has empty reward_value
    value = rule.reward_value or rule_discount_amount
    if discount_to_update.value != value:
        discount_to_update.value = value
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
    reason = prepare_promotion_discount_reason(
        rule_info.promotion, get_sale_id(rule_info.promotion)
    )
    if discount_to_update.reason != reason:
        discount_to_update.reason = reason
        updated_fields.append("reason")


def _invalidate_order_line_discounts(
    line_info: Union["CheckoutLineInfo", "DraftOrderLineInfo"],
):
    if isinstance(line_info, DraftOrderLineInfo):
        line_info.should_refresh_discounts = True


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
        return lines_info

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
        return lines_info

    best_rule, best_discount_amount, gift_listing = rule_data

    _create_or_update_order_discount(
        checkout,
        lines_info,
        best_rule,
        best_discount_amount,
        gift_listing,
        channel.currency_code,
        best_rule.promotion,
        checkout_info,
        save,
    )


def create_order_discount_objects_for_order_promotions(
    order: "Order",
    lines_info: Iterable["DraftOrderLineInfo"],
):
    from ..order.base_calculations import base_order_subtotal

    # The base prices are required for order promotion discount qualification.
    _set_order_base_prices(order, lines_info)

    # Discount from order rules is applied only when the voucher is not set
    if order.voucher_code:
        _clear_order_discount(order, lines_info)
        return lines_info

    lines = [line_info.line for line_info in lines_info]
    subtotal = base_order_subtotal(order, lines)
    channel = order.channel
    rules = fetch_promotion_rules_for_checkout_or_order(order)
    rule_data = get_best_rule(
        rules=rules,
        channel=channel,
        country=order.get_country(),
        subtotal=subtotal,
    )
    if not rule_data:
        _clear_order_discount(order, lines_info)
        return lines_info

    best_rule, best_discount_amount, gift_listing = rule_data

    _create_or_update_order_discount(
        order,
        lines_info,
        best_rule,
        best_discount_amount,
        gift_listing,
        channel.currency_code,
        best_rule.promotion,
    )


def get_best_rule(
    rules: Iterable["PromotionRule"], channel: "Channel", country: str, subtotal: Money
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
            gift_rules, channel, country
        )
        if best_gift_rule and gift_listing:
            rule_discounts.append(
                RuleDiscount(
                    best_gift_rule, gift_listing.discounted_price_amount, gift_listing
                )
            )

    if not rule_discounts:
        return None

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
    checkout.base_subtotal = subtotal
    checkout.base_total = total
    checkout.save(update_fields=["base_total_amount", "base_subtotal_amount"])


def _set_order_base_prices(order: Order, lines_info: Iterable[DraftOrderLineInfo]):
    """Set base order prices that includes only catalogue discounts."""
    from ..order.base_calculations import base_order_subtotal

    lines = [line_info.line for line_info in lines_info]
    subtotal = base_order_subtotal(order, lines)
    shipping_price = order.base_shipping_price
    total = subtotal + shipping_price
    order.subtotal = TaxedMoney(net=subtotal, gross=subtotal)
    order.total = TaxedMoney(net=total, gross=total)
    order.save(
        update_fields=[
            "subtotal_net_amount",
            "subtotal_gross_amount",
            "total_net_amount",
            "total_gross_amount",
        ]
    )


def _clear_checkout_discount(
    checkout_info: "CheckoutInfo", lines_info: Iterable["CheckoutLineInfo"], save: bool
):
    delete_gift_line(checkout_info.checkout, lines_info)
    CheckoutDiscount.objects.filter(
        checkout=checkout_info.checkout,
        type=DiscountType.ORDER_PROMOTION,
    ).delete()
    checkout_info.discounts = [
        discount
        for discount in checkout_info.discounts
        if discount.type != DiscountType.ORDER_PROMOTION
    ]
    if not checkout_info.voucher_code:
        checkout_info.checkout.discount_amount = 0
        checkout_info.checkout.discount_name = None
        checkout_info.checkout.translated_discount_name = None

        if save:
            checkout_info.checkout.save(
                update_fields=[
                    "discount_amount",
                    "discount_name",
                    "translated_discount_name",
                ]
            )


def _clear_order_discount(
    order_or_checkout: Union[Checkout, Order],
    lines_info: Iterable[DraftOrderLineInfo],
):
    delete_gift_line(order_or_checkout, lines_info)
    order_or_checkout.discounts.filter(type=DiscountType.ORDER_PROMOTION).delete()


def _get_best_gift_reward(
    rules: Iterable["PromotionRule"], channel: "Channel", country: str
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


def _create_or_update_order_discount(
    order_or_checkout: Union[Checkout, Order],
    lines_info: Union[Iterable[CheckoutLineInfo], Iterable[DraftOrderLineInfo]],
    best_rule: "PromotionRule",
    best_discount_amount: Decimal,
    gift_listing: Optional[ProductVariantChannelListing],
    currency_code: str,
    promotion: "Promotion",
    checkout_info: Optional["CheckoutInfo"] = None,
    save: bool = False,
):
    translation_language_code = order_or_checkout.language_code
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
        "currency": currency_code,
        "name": get_discount_name(best_rule, promotion),
        "translated_name": get_discount_translated_name(rule_info),
        "reason": prepare_promotion_discount_reason(promotion, get_sale_id(promotion)),
    }
    if gift_listing:
        _handle_gift_reward(
            order_or_checkout,
            lines_info,
            gift_listing,
            discount_object_defaults,
            rule_info,
            checkout_info,
            save,
        )
    else:
        _handle_order_promotion(
            order_or_checkout,
            lines_info,
            discount_object_defaults,
            rule_info,
            checkout_info,
            save,
        )


def _handle_order_promotion(
    order_or_checkout: Union[Checkout, Order],
    lines_info: Iterable[Union[CheckoutLineInfo, DraftOrderLineInfo]],
    discount_object_defaults: dict,
    rule_info: VariantPromotionRuleInfo,
    checkout_info: Optional[CheckoutInfo] = None,
    save: bool = False,
):
    discount_object, created = order_or_checkout.discounts.get_or_create(
        type=DiscountType.ORDER_PROMOTION,
        defaults=discount_object_defaults,
    )
    discount_amount = discount_object_defaults["amount_value"]

    if not created:
        fields_to_update: list[str] = []
        _update_discount(
            discount_object_defaults["promotion_rule"],
            rule_info,
            discount_amount,
            discount_object,
            fields_to_update,
        )
        if fields_to_update:
            discount_object.save(update_fields=fields_to_update)

    if checkout_info:
        discount_object = cast(CheckoutDiscount, discount_object)
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

    delete_gift_line(order_or_checkout, lines_info)


def delete_gift_line(
    order_or_checkout: Union[Checkout, Order],
    lines_info: Iterable[Union["CheckoutLineInfo", "DraftOrderLineInfo"]],
):
    if gift_line_infos := [line for line in lines_info if line.line.is_gift]:
        order_or_checkout.lines.filter(is_gift=True).delete()  # type: ignore[misc]
        for gift_line_info in gift_line_infos:
            lines_info.remove(gift_line_info)  # type: ignore[attr-defined]


def _handle_gift_reward(
    order_or_checkout: Union[Checkout, Order],
    lines_info: Iterable[Union[CheckoutLineInfo, DraftOrderLineInfo]],
    gift_listing: ProductVariantChannelListing,
    discount_object_defaults: dict,
    rule_info: VariantPromotionRuleInfo,
    checkout_info: Optional[CheckoutInfo] = None,
    save: bool = False,
):
    models = get_checkout_or_order_models(order_or_checkout)
    with transaction.atomic():
        line, line_created = create_gift_line(
            order_or_checkout, gift_listing.variant_id
        )
        (
            line_discount,
            discount_created,
        ) = models.discount_line_model.objects.get_or_create(
            type=DiscountType.ORDER_PROMOTION,
            line=line,
            defaults=discount_object_defaults,
        )

    if not discount_created:
        fields_to_update = []
        if line_discount.line_id != line.id:
            line_discount.line = line
            fields_to_update.append("line_id")
        _update_discount(
            discount_object_defaults["promotion_rule"],
            rule_info,
            discount_object_defaults["amount_value"],
            line_discount,
            fields_to_update,
        )
        if fields_to_update:
            line_discount.save(update_fields=fields_to_update)

    if checkout_info:
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
            "channel": order_or_checkout.channel,
        }
        if checkout_info:
            init_values |= {
                "product": variant.product,
                "product_type": variant.product.product_type,
                "collections": [],
            }
        gift_line_info = models.line_info(**init_values)
        lines_info.append(gift_line_info)  # type: ignore[attr-defined]
    else:
        line_info = next(
            line_info for line_info in lines_info if line_info.line.pk == line.id
        )
        line_info.line = line
        line_info.discounts = [line_discount]


def _get_defaults_for_line(order_or_checkout: Union[Checkout, Order], variant_id: int):
    if isinstance(order_or_checkout, Checkout):
        return {
            "variant_id": variant_id,
            "quantity": 1,
            "currency": order_or_checkout.currency,
        }
    else:
        return {
            "variant_id": variant_id,
            "quantity": 1,
            "currency": order_or_checkout.currency,
            "unit_price_net_amount": 0,
            "unit_price_gross_amount": 0,
            "total_price_net_amount": 0,
            "total_price_gross_amount": 0,
            "is_shipping_required": True,
            "is_gift_card": False,
        }


def create_gift_line(order_or_checkout: Union[Checkout, Order], variant_id: int):
    defaults = _get_defaults_for_line(order_or_checkout, variant_id)
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


def fetch_promotion_rules_for_checkout_or_order(instance: Union["Checkout", "Order"]):
    from ..graphql.discount.utils import filter_qs_by_predicate

    models = get_checkout_or_order_models(instance)
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
    qs = models.model.objects.filter(pk=instance.pk)
    for rule in rules.iterator():
        rule_channel_ids = rule_to_channel_ids_map.get(rule.id, [])
        if channel_id not in rule_channel_ids:
            continue
        objects = filter_qs_by_predicate(
            rule.order_predicate,
            qs,
            models.predicate_type,
            currency,
        )
        if objects.exists():
            applicable_rules.append(rule)

    return applicable_rules


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
