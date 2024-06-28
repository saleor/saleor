import datetime
from collections import defaultdict, namedtuple
from collections.abc import Iterable, Iterator
from decimal import Decimal
from typing import TYPE_CHECKING, Callable, Optional, Union, overload
from uuid import UUID

import graphene
import pytz
from django.conf import settings
from django.db import transaction
from django.db.models import Exists, OuterRef, QuerySet
from prices import Money

from ...channel.models import Channel
from ...checkout.fetch import CheckoutLineInfo
from ...checkout.models import Checkout, CheckoutLine
from ...core.db.connection import allow_writer
from ...core.exceptions import InsufficientStock
from ...core.taxes import zero_money
from ...order.fetch import EditableOrderLineInfo
from ...order.models import Order
from ...product.models import (
    Product,
    ProductChannelListing,
    ProductVariant,
    ProductVariantChannelListing,
)
from ...warehouse.availability import check_stock_quantity_bulk
from .. import (
    DiscountType,
    PromotionRuleInfo,
    PromotionType,
    RewardType,
    RewardValueType,
)
from ..interface import VariantPromotionRuleInfo, get_rule_translations
from ..models import (
    CheckoutDiscount,
    CheckoutLineDiscount,
    NotApplicable,
    OrderDiscount,
    OrderLineDiscount,
    Promotion,
    PromotionRule,
)
from .shared import update_line_discount

if TYPE_CHECKING:
    from ...checkout.fetch import CheckoutLineInfo
    from ...order.fetch import EditableOrderLineInfo
    from ...order.models import OrderLine
    from ...product.managers import ProductVariantQueryset


CatalogueInfo = defaultdict[str, set[Union[int, str]]]
CATALOGUE_FIELDS = ["categories", "collections", "products", "variants"]


def prepare_promotion_discount_reason(promotion: "Promotion", sale_id: str):
    return f"{'Sale' if promotion.old_sale_id else 'Promotion'}: {sale_id}"


def get_sale_id(promotion: "Promotion"):
    return (
        graphene.Node.to_global_id("Sale", promotion.old_sale_id)
        if promotion.old_sale_id
        else graphene.Node.to_global_id("Promotion", promotion.id)
    )


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


@overload
def prepare_line_discount_objects_for_catalogue_promotions(
    lines_info: Iterable["CheckoutLineInfo"],
) -> tuple[
    list[dict], list["CheckoutLineDiscount"], list["CheckoutLineDiscount"], list[str]
]: ...


@overload
def prepare_line_discount_objects_for_catalogue_promotions(
    lines_info: Iterable["EditableOrderLineInfo"],
) -> tuple[
    list[dict], list["OrderLineDiscount"], list["OrderLineDiscount"], list[str]
]: ...


def prepare_line_discount_objects_for_catalogue_promotions(lines_info):
    line_discounts_to_create_inputs: list[dict] = []
    line_discounts_to_update: list[Union[CheckoutLineDiscount, OrderLineDiscount]] = []
    line_discounts_to_remove: list[Union[CheckoutLineDiscount, OrderLineDiscount]] = []
    updated_fields: list[str] = []

    if not lines_info:
        return

    for line_info in lines_info:
        line = line_info.line

        # get the existing catalogue discount for the line
        discount_to_update = None
        if discounts_to_update := line_info.get_catalogue_discounts():
            discount_to_update = discounts_to_update[0]
            # Line should never have multiple catalogue discounts associated. Before
            # introducing unique_type on discount models, there was such a possibility.
            line_discounts_to_remove.extend(discounts_to_update[1:])

        # manual line discount do not stack with other discounts
        if [
            discount
            for discount in line_info.discounts
            if discount.type == DiscountType.MANUAL
        ]:
            line_discounts_to_remove.extend(discounts_to_update)
            continue

        # check if the line price is discounted by catalogue promotion
        discounted_line = _is_discounted_line_by_catalogue_promotion(
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


def _is_discounted_line_by_catalogue_promotion(
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
    update_line_discount(
        rule,
        None,
        discount_name,
        translated_name,
        reason,
        rule_discount_amount,
        value,
        value_type,
        DiscountType.PROMOTION,
        discount_to_update,
        updated_fields,
    )


def get_best_rule(
    rules: Iterable["PromotionRule"],
    channel: "Channel",
    country: str,
    subtotal: Money,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
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
            gift_rules, channel, country, database_connection_name
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


def _get_best_gift_reward(
    rules: Iterable["PromotionRule"],
    channel: "Channel",
    country: str,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> tuple[Optional[PromotionRule], Optional[ProductVariantChannelListing]]:
    rule_ids = [rule.id for rule in rules]
    PromotionRuleGift = PromotionRule.gifts.through
    rule_gifts = PromotionRuleGift.objects.using(database_connection_name).filter(
        promotionrule_id__in=rule_ids
    )
    variants = ProductVariant.objects.using(database_connection_name).filter(
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
            database_connection_name=database_connection_name,
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
        available_variant_ids,
        channel,
        database_connection_name=database_connection_name,
    )
    if not available_variant_ids:
        return None, None

    # check variant channel availability
    available_variant_listings = ProductVariantChannelListing.objects.using(
        database_connection_name
    ).filter(
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
    available_variant_ids: set[int],
    channel: "Channel",
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    today = datetime.datetime.now(pytz.UTC)
    variants = ProductVariant.objects.using(database_connection_name).filter(
        id__in=available_variant_ids
    )
    product_listings = ProductChannelListing.objects.using(
        database_connection_name
    ).filter(
        Exists(variants.filter(product_id=OuterRef("product_id"))),
        available_for_purchase_at__lte=today,
        channel_id=channel.id,
    )
    available_variant_ids = variants.filter(
        Exists(product_listings.filter(product_id=OuterRef("product_id")))
    ).values_list("id", flat=True)
    return set(available_variant_ids)


@allow_writer()
def delete_gift_line(
    order_or_checkout: Union[Checkout, Order],
    lines_info: Iterable[Union["CheckoutLineInfo", "EditableOrderLineInfo"]],
):
    if gift_line_infos := [line for line in lines_info if line.line.is_gift]:
        order_or_checkout.lines.filter(is_gift=True).delete()  # type: ignore[misc]
        for gift_line_info in gift_line_infos:
            lines_info.remove(gift_line_info)  # type: ignore[attr-defined]


def create_gift_line(order_or_checkout: Union[Checkout, Order], variant_id: int):
    defaults = _get_defaults_for_gift_line(order_or_checkout, variant_id)
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
    order_or_checkout: Union[Checkout, Order], variant_id: int
):
    if isinstance(order_or_checkout, Checkout):
        return {
            "variant_id": variant_id,
            "quantity": 1,
            "currency": order_or_checkout.currency,
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

    promotions = Promotion.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).active()
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
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    from ...graphql.discount.utils import PredicateObjectType, filter_qs_by_predicate

    with allow_writer():
        # TODO: channel should be loaded using dataloader
        currency = instance.channel.currency_code

    applicable_rules = []
    promotions = Promotion.objects.active()
    rules = (
        PromotionRule.objects.using(database_connection_name)
        .filter(Exists(promotions.filter(id=OuterRef("promotion_id"))))
        .exclude(order_predicate={})
        .prefetch_related("channels")
    )
    rule_to_channel_ids_map = _get_rule_to_channel_ids_map(rules)

    channel_id = instance.channel_id
    qs = instance._meta.model.objects.using(database_connection_name).filter(  # type: ignore[attr-defined] # noqa: E501
        pk=instance.pk
    )
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


def create_discount_objects_for_order_promotions(
    order_or_checkout: Union[Checkout, Order],
    lines_info: Union[Iterable["EditableOrderLineInfo"], Iterable["CheckoutLineInfo"]],
    subtotal: Money,
    channel: "Channel",
    country: str,
    *,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    """Create discount object for order promotions.

    If the best promotion is gift promotion, new gift line is created.
    """
    gift_promotion_applied = False
    discount_object = None
    rules = fetch_promotion_rules_for_checkout_or_order(
        order_or_checkout, database_connection_name
    )
    rule_data = get_best_rule(
        rules=rules,
        channel=channel,
        country=country,
        subtotal=subtotal,
        database_connection_name=database_connection_name,
    )
    if not rule_data:
        return gift_promotion_applied, discount_object

    best_rule, best_discount_amount, gift_listing = rule_data
    promotion = best_rule.promotion
    currency = channel.currency_code
    translation_language_code = order_or_checkout.language_code
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
        _handle_gift_reward(
            order_or_checkout,
            lines_info,
            gift_listing,
            channel,
            discount_object_defaults,
            rule_info,
        )
        gift_promotion_applied = True
    else:
        discount_object = _handle_order_promotion(
            order_or_checkout,
            lines_info,
            discount_object_defaults,
            rule_info,
        )
    return gift_promotion_applied, discount_object


@allow_writer()
def _handle_order_promotion(
    order_or_checkout: Union[Order, Checkout],
    lines_info: Union[Iterable["EditableOrderLineInfo"], Iterable["CheckoutLineInfo"]],
    discount_object_defaults: dict,
    rule_info: VariantPromotionRuleInfo,
):
    discount_object, created = order_or_checkout.discounts.get_or_create(
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

    delete_gift_line(order_or_checkout, lines_info)
    return discount_object


@allow_writer()
def _handle_gift_reward(
    order_or_checkout: Union[Order, Checkout],
    lines_info: Union[Iterable["EditableOrderLineInfo"], Iterable["CheckoutLineInfo"]],
    gift_listing: ProductVariantChannelListing,
    channel: "Channel",
    discount_object_defaults: dict,
    rule_info: VariantPromotionRuleInfo,
):
    discount_model = (
        CheckoutLineDiscount
        if isinstance(order_or_checkout, Checkout)
        else OrderLineDiscount
    )
    with transaction.atomic():
        line, line_created = create_gift_line(
            order_or_checkout, gift_listing.variant_id
        )
        (
            line_discount,
            discount_created,
        ) = discount_model.objects.get_or_create(  # type: ignore[attr-defined]
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
            "product_type": variant.product.product_type,
            "collections": [],
            "channel_listing": gift_listing,
            "discounts": [line_discount],
            "rules_info": [rule_info],
            "channel": channel,
            "voucher": None,
            "voucher_code": None,
        }
        if isinstance(order_or_checkout, Checkout):
            gift_line_info = CheckoutLineInfo(**init_values)
        else:
            gift_line_info = EditableOrderLineInfo(**init_values)  # type: ignore
        lines_info.append(gift_line_info)  # type: ignore
    else:
        line_info = next(
            line_info for line_info in lines_info if line_info.line.pk == line.id
        )
        line_info.line = line
        line_info.discounts = [line_discount]


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
