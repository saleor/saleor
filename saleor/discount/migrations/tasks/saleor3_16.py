from dataclasses import dataclass
from typing import Dict, List
from ....celeryconf import app

import graphene
from django.db.models import Exists, OuterRef
from ...models import (
    Promotion,
    PromotionRule,
    SaleChannelListing,
    SaleTranslation,
    Sale,
    PromotionTranslation,
    CheckoutLineDiscount,
    OrderLineDiscount,
)


# The batch of size 100 takes ~0.9 second and consumes ~30MB memory at peak
BATCH_SIZE = 100


@dataclass
class RuleInfo:
    rule: PromotionRule
    sale_id: int
    channel_id: int


@app.task
def migrate_sales_to_promotions_task():
    # TODO: to update - needs to create `VariantChannelListingPromotionRule` instances

    sales = Sale.objects.exclude(
        Exists(Promotion.objects.filter(old_sale_id=OuterRef("pk")))
    ).order_by("pk")
    sales_listing = SaleChannelListing.objects.order_by("sale_id").filter(
        Exists(sales.filter(id=OuterRef("sale_id")))
    )[:BATCH_SIZE]
    listing_ids = list(sales_listing.values_list("pk", flat=True))

    # we want to have channel all channel listings for given sale, so we need to get
    # last sale_id from listing batch and extend the batch to include all listings
    # for this sale
    if listing_ids:
        last_sale_id = list(sales_listing.values_list("sale_id", flat=True))[-1]
        last_sale_listing_ids = SaleChannelListing.objects.filter(
            sale_id=last_sale_id
        ).values_list("pk", flat=True)

        listing_ids = set(listing_ids) | set(last_sale_listing_ids)

        qs = SaleChannelListing.objects.filter(
            id__in=list(listing_ids)
        ).prefetch_related(
            "sale",
            "sale__collections",
            "sale__categories",
            "sale__products",
            "sale__variants",
        )

        migrate_sales(qs)
        migrate_sales_to_promotions_task.delay()

    migrate_sales_not_listed_in_any_channels_task.delay()


def migrate_sales(sale_listings):
    sales_batch_pks = {listing.sale_id for listing in sale_listings}

    saleid_promotion_map: Dict[int, Promotion] = {}
    rules_info: List[RuleInfo] = []

    migrate_sales_to_promotions(Sale, Promotion, sales_batch_pks, saleid_promotion_map)
    migrate_sale_listing_to_promotion_rules(
        RuleInfo,
        PromotionRule,
        sale_listings,
        saleid_promotion_map,
        rules_info,
    )
    migrate_translations(
        SaleTranslation, PromotionTranslation, sales_batch_pks, saleid_promotion_map
    )

    rule_by_channel_and_sale = get_rule_by_channel_sale(rules_info)
    migrate_checkout_line_discounts(
        CheckoutLineDiscount, sales_batch_pks, rule_by_channel_and_sale
    )
    migrate_order_line_discounts(
        OrderLineDiscount, sales_batch_pks, rule_by_channel_and_sale
    )


@app.task
def migrate_sales_not_listed_in_any_channels_task():
    # migrate sales not listed in any channel
    sales_listing = SaleChannelListing.objects.order_by("sale_id")
    sales_not_listed = Sale.objects.filter(
        ~Exists(sales_listing.filter(sale_id=OuterRef("pk"))),
        ~Exists(Promotion.objects.filter(old_sale_id=OuterRef("pk"))),
    ).order_by("pk")
    ids = list(sales_not_listed.values_list("pk", flat=True)[:BATCH_SIZE])
    if ids:
        migrate_sales_not_listed_in_any_channels(ids)
        migrate_sales_not_listed_in_any_channels_task.delay()


def migrate_sales_not_listed_in_any_channels(sales_batch_pks):
    saleid_promotion_map = {}
    migrate_sales_to_promotions(Sale, Promotion, sales_batch_pks, saleid_promotion_map)
    migrate_sales_to_promotion_rules(
        Sale, PromotionRule, sales_batch_pks, saleid_promotion_map
    )
    migrate_translations(
        SaleTranslation, PromotionTranslation, sales_batch_pks, saleid_promotion_map
    )


def migrate_sales_to_promotions(Sale, Promotion, sales_pks, saleid_promotion_map):
    if sales := Sale.objects.filter(pk__in=sales_pks).order_by("pk"):
        for sale in sales:
            saleid_promotion_map[sale.id] = convert_sale_into_promotion(Promotion, sale)
        Promotion.objects.bulk_create(saleid_promotion_map.values())


def convert_sale_into_promotion(Promotion, sale):
    return Promotion(
        name=sale.name,
        old_sale_id=sale.id,
        start_date=sale.start_date,
        end_date=sale.end_date,
        created_at=sale.created_at,
        updated_at=sale.updated_at,
        metadata=sale.metadata,
        private_metadata=sale.private_metadata,
        last_notification_scheduled_at=sale.notification_sent_datetime,
    )


def create_promotion_rule(
    PromotionRule, sale, promotion, discount_value=None, old_channel_listing_id=None
):
    return PromotionRule(
        promotion=promotion,
        catalogue_predicate=create_catalogue_predicate_from_sale(sale),
        reward_value_type=sale.type,
        reward_value=discount_value,
        old_channel_listing_id=old_channel_listing_id,
    )


def migrate_sale_listing_to_promotion_rules(
    RuleInfo,
    PromotionRule,
    sale_listings,
    saleid_promotion_map,
    rules_info,
):
    if sale_listings:
        for sale_listing in sale_listings:
            promotion = saleid_promotion_map[sale_listing.sale_id]
            rules_info.append(
                RuleInfo(
                    rule=create_promotion_rule(
                        PromotionRule,
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


def create_catalogue_predicate_from_sale(sale):
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
    if not predicate.get("OR"):
        predicate = {}

    return predicate


def migrate_sales_to_promotion_rules(
    Sale, PromotionRule, sales_pks, saleid_promotion_map
):
    if sales := Sale.objects.filter(pk__in=sales_pks).order_by("pk"):
        rules: List[PromotionRule] = []
        for sale in sales:
            promotion = saleid_promotion_map[sale.id]
            rules.append(create_promotion_rule(PromotionRule, sale, promotion))
        PromotionRule.objects.bulk_create(rules)


def migrate_translations(
    SaleTranslation, PromotionTranslation, sales_pks, saleid_promotion_map
):
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


def migrate_checkout_line_discounts(
    CheckoutLineDiscount, sales_pks, rule_by_channel_and_sale
):
    if checkout_line_discounts := CheckoutLineDiscount.objects.filter(
        sale_id__in=sales_pks
    ).select_related("line__checkout"):
        for checkout_line_discount in checkout_line_discounts:
            if checkout_line := checkout_line_discount.line:
                channel_id = checkout_line.checkout.channel_id
                sale_id = checkout_line_discount.sale_id
                lookup = f"{channel_id}_{sale_id}"
                checkout_line_discount.type = "promotion"
                if promotion_rule := rule_by_channel_and_sale.get(lookup):
                    checkout_line_discount.promotion_rule = promotion_rule

        CheckoutLineDiscount.objects.bulk_update(
            checkout_line_discounts, ["promotion_rule_id", "type"]
        )


def migrate_order_line_discounts(
    OrderLineDiscount, sales_pks, rule_by_channel_and_sale
):
    # TODO: to update - should be created based on `OrderLine.sale_id`
    if order_line_discounts := OrderLineDiscount.objects.filter(
        sale_id__in=sales_pks
    ).select_related("line__order"):
        for order_line_discount in order_line_discounts:
            if order_line := order_line_discount.line:
                channel_id = order_line.order.channel_id
                sale_id = order_line_discount.sale_id
                lookup = f"{channel_id}_{sale_id}"
                order_line_discount.type = "promotion"
                if promotion_rule := rule_by_channel_and_sale.get(lookup):
                    order_line_discount.promotion_rule = promotion_rule

        OrderLineDiscount.objects.bulk_update(
            order_line_discounts, ["promotion_rule_id", "type"]
        )


def get_rule_by_channel_sale(rules_info):
    return {
        f"{rule_info.channel_id}_{rule_info.sale_id}": rule_info.rule
        for rule_info in rules_info
    }
