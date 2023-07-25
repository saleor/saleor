from dataclasses import dataclass
from typing import Dict, List

import graphene
from django.db.models import Exists, OuterRef

from .models import (
    CheckoutLineDiscount,
    OrderLineDiscount,
    Promotion,
    PromotionRule,
    PromotionTranslation,
    Sale,
    SaleChannelListing,
    SaleTranslation,
)

# The batch of size 100 takes ~0.9 second and consumes ~30MB memory at peak
BATCH_SIZE = 100


@dataclass
class RuleInfo:
    rule: PromotionRule
    sale_id: int
    channel_id: int


def convert_sales_to_promotions():
    sales_listing = SaleChannelListing.objects.order_by("sale_id")
    for sale_listing_batch_pks in _channel_listing_in_batches(sales_listing):
        sales_listing_batch = (
            SaleChannelListing.objects.filter(pk__in=sale_listing_batch_pks)
            .order_by("sale_id")
            .prefetch_related(
                "sale",
                "sale__collections",
                "sale__categories",
                "sale__products",
                "sale__variants",
            )
        )
        sales_batch_pks = {listing.sale_id for listing in sales_listing_batch}

        saleid_promotion_map: Dict[int, Promotion] = {}
        rules_info: List[RuleInfo] = []

        _migrate_sales_to_promotions(sales_batch_pks, saleid_promotion_map)
        _migrate_sale_listing_to_promotion_rules(
            sales_listing_batch,
            saleid_promotion_map,
            rules_info,
        )
        _migrate_translations(sales_batch_pks, saleid_promotion_map)

        rule_by_channel_and_sale = _get_rule_by_channel_sale(rules_info)
        _migrate_checkout_line_discounts(sales_batch_pks, rule_by_channel_and_sale)
        _migrate_order_line_discounts(sales_batch_pks, rule_by_channel_and_sale)

    # migrate sales not listed in any channel
    sales_not_listed = Sale.objects.filter(
        ~Exists(sales_listing.filter(sale_id=OuterRef("pk")))
    ).order_by("pk")
    for sales_batch_pks in _queryset_in_batches(sales_not_listed):
        saleid_promotion_map = {}
        _migrate_sales_to_promotions(sales_batch_pks, saleid_promotion_map)
        _migrate_sales_to_promotion_rules(sales_batch_pks, saleid_promotion_map)
        _migrate_translations(sales_batch_pks, saleid_promotion_map)


def _migrate_sales_to_promotions(sales_pks, saleid_promotion_map):
    if sales := Sale.objects.filter(pk__in=sales_pks).order_by("pk"):
        for sale in sales:
            saleid_promotion_map[sale.id] = _convert_sale_into_promotion(sale)
        Promotion.objects.bulk_create(saleid_promotion_map.values())


def _convert_sale_into_promotion(sale):
    return Promotion(
        name=sale.name,
        old_sale_id=sale.id,
        start_date=sale.start_date,
        end_date=sale.end_date,
        created_at=sale.created_at,
        updated_at=sale.updated_at,
        metadata=sale.metadata,
        private_metadata=sale.private_metadata,
    )


def _migrate_sale_listing_to_promotion_rules(
    sale_listings,
    saleid_promotion_map,
    rules_info,
):
    if sale_listings:
        for sale_listing in sale_listings:
            promotion = saleid_promotion_map[sale_listing.sale_id]
            rules_info.append(
                RuleInfo(
                    rule=_create_promotion_rule(
                        sale_listing.sale,
                        promotion,
                        sale_listing.discount_value,
                        sale_listing.id,
                    ),
                    sale_id=sale_listing.sale_id,
                    channel_id=sale_listing.channel_id,
                )
            )

        promotion_rules = [rules_info.rule for rules_info in rules_info]
        PromotionRule.objects.bulk_create(promotion_rules)

        PromotionRuleChannel = PromotionRule.channels.through
        rules_channels = [
            PromotionRuleChannel(
                promotionrule_id=rule_info.rule.id, channel_id=rule_info.channel_id
            )
            for rule_info in rules_info
        ]
        PromotionRuleChannel.objects.bulk_create(rules_channels)


def _create_promotion_rule(
    sale, promotion, discount_value=None, old_channel_listing_id=None
):
    return PromotionRule(
        name="",
        promotion=promotion,
        catalogue_predicate=_create_catalogue_predicate_from_sale(sale),
        reward_value_type=sale.type,
        reward_value=discount_value,
        old_channel_listing_id=old_channel_listing_id,
    )


def _create_catalogue_predicate_from_sale(sale):
    collection_ids = [
        graphene.Node.to_global_id("Collection", pk)
        for pk in sale.collections.values_list("pk", flat=True)
    ]
    category_ids = [
        graphene.Node.to_global_id("Category", pk)
        for pk in sale.categories.values_list("pk", flat=True)
    ]
    product_ids = [
        graphene.Node.to_global_id("Product", pk)
        for pk in sale.products.values_list("pk", flat=True)
    ]
    variant_ids = [
        graphene.Node.to_global_id("ProductVariant", pk)
        for pk in sale.variants.values_list("pk", flat=True)
    ]
    return create_catalogue_predicate(
        collection_ids, category_ids, product_ids, variant_ids
    )


def create_catalogue_predicate(collection_ids, category_ids, product_ids, variant_ids):
    predicate: Dict[str, List] = {"OR": []}
    if collection_ids:
        predicate["OR"].append({"collectionPredicate": {"ids": collection_ids}})
    if category_ids:
        predicate["OR"].append({"categoryPredicate": {"ids": category_ids}})
    if product_ids:
        predicate["OR"].append({"productPredicate": {"ids": product_ids}})
    if variant_ids:
        predicate["OR"].append({"variantPredicate": {"ids": variant_ids}})

    return predicate


def _migrate_sales_to_promotion_rules(sales_pks, saleid_promotion_map):
    if sales := Sale.objects.filter(pk__in=sales_pks).order_by("pk"):
        rules: List[PromotionRule] = []
        for sale in sales:
            promotion = saleid_promotion_map[sale.id]
            rules.append(_create_promotion_rule(sale, promotion))
        PromotionRule.objects.bulk_create(rules)


def _migrate_translations(sales_pks, saleid_promotion_map):
    if sale_translations := SaleTranslation.objects.filter(sale_id__in=sales_pks):
        promotion_translations = [
            PromotionTranslation(
                name=translation.name,
                language_code=translation.language_code,
                promotion=saleid_promotion_map[translation.sale_id],
            )
            for translation in sale_translations
        ]
        PromotionTranslation.objects.bulk_create(promotion_translations)


def _migrate_checkout_line_discounts(sales_pks, rule_by_channel_and_sale):
    if checkout_line_discounts := CheckoutLineDiscount.objects.filter(
        sale_id__in=sales_pks
    ).select_related("line__checkout"):
        for checkout_line_discount in checkout_line_discounts:
            if checkout_line := checkout_line_discount.line:
                channel_id = checkout_line.checkout.channel_id
                sale_id = checkout_line_discount.sale_id
                lookup = f"{channel_id}_{sale_id}"
                if promotion_rule := rule_by_channel_and_sale.get(lookup):
                    checkout_line_discount.promotion_rule = promotion_rule

        CheckoutLineDiscount.objects.bulk_update(
            checkout_line_discounts, ["promotion_rule_id"]
        )


def _migrate_order_line_discounts(sales_pks, rule_by_channel_and_sale):
    if order_line_discounts := OrderLineDiscount.objects.filter(
        sale_id__in=sales_pks
    ).select_related("line__order"):
        for order_line_discount in order_line_discounts:
            if order_line := order_line_discount.line:
                channel_id = order_line.order.channel_id
                sale_id = order_line_discount.sale_id
                lookup = f"{channel_id}_{sale_id}"
                if promotion_rule := rule_by_channel_and_sale.get(lookup):
                    order_line_discount.promotion_rule = promotion_rule

        OrderLineDiscount.objects.bulk_update(
            order_line_discounts, ["promotion_rule_id"]
        )


def _get_rule_by_channel_sale(rules_info):
    return {
        f"{rule_info.channel_id}_{rule_info.sale_id}": rule_info.rule
        for rule_info in rules_info
    }


def _channel_listing_in_batches(qs):
    first_sale_id = 0
    while True:
        batch_1 = qs.values("sale_id").filter(sale_id__gt=first_sale_id)[:BATCH_SIZE]
        if len(batch_1) == 0:
            break
        last_sale_id = batch_1[len(batch_1) - 1]["sale_id"]

        # `batch_2` extends initial `batch_1` to include all records from
        # `SaleChannelListing` which refer to `last_sale_id`
        batch_2 = qs.values("pk", "sale_id").filter(
            sale_id__gt=first_sale_id, sale_id__lte=last_sale_id
        )
        pks = [v["pk"] for v in batch_2]
        if not pks:
            break
        yield pks
        first_sale_id = batch_2[len(batch_2) - 1]["sale_id"]


def _queryset_in_batches(queryset):
    start_pk = 0
    while True:
        qs = queryset.values("pk").filter(pk__gt=start_pk)[:BATCH_SIZE]
        pks = [v["pk"] for v in qs]
        if not pks:
            break
        yield pks
        start_pk = pks[-1]
