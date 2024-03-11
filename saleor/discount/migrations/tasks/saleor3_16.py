from dataclasses import dataclass
from typing import Dict, List
from ....celeryconf import app
from decimal import Decimal

import graphene
from django.db import transaction
from django.db.models import Exists, OuterRef
from ....order.models import OrderLine
from ....product.models import Product
from ....product.utils.variant_prices import update_products_discounted_price
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
from babel.numbers import get_currency_precision

# The batch of size 100 takes ~0.9 second and consumes ~30MB memory at peak
SALE_LISTING_BATCH_SIZE = 100

# Results in memory usage of ~40MB for 20K products
DISCOUNTED_PRICES_RECALCULATION_BATCH_SIZE = 100

# The batch of size 1000 takes ~0.2 seconds and consumes ~10MB memory at peak
PROMOTION_BATCH_SIZE = 1000

# The batch of size 1000 takes ~0.7 seconds and consumes ~18MB memory at peak
CHECKOUT_LINE_DISCOUNT_BATCH_SIZE = 500

# The batch of size 1000 takes ~0.5 seconds and consumes ~15MB memory at peak
ORDER_LINE_DISCOUNT_BATCH_SIZE = 500


@dataclass
class RuleInfo:
    rule: PromotionRule
    sale_id: int
    channel_id: int


@app.task
def remigrate_sales_to_promotions_task():
    # we need to recreate promotions as the error was introduced in 3.16.5
    # and promotion rules were not created for the promotions
    promotion_ids = list(
        Promotion.objects.all().values_list("id", flat=True)[:PROMOTION_BATCH_SIZE]
    )
    if promotion_ids:
        Promotion.objects.filter(id__in=promotion_ids).delete()
        remigrate_sales_to_promotions_task.delay()
    else:
        migrate_sales_to_promotions_task.delay()


@app.task
def migrate_sales_to_promotions_task():
    sales = Sale.objects.exclude(
        Exists(Promotion.objects.filter(old_sale_id=OuterRef("pk")))
    ).order_by("pk")
    sales_listing = SaleChannelListing.objects.order_by("sale_id").filter(
        Exists(sales.filter(id=OuterRef("sale_id")))
    )[:SALE_LISTING_BATCH_SIZE]
    sale_ids = list(sales_listing.values_list("sale_id", flat=True))

    if sale_ids:
        with transaction.atomic():
            # we need to double check if any of those listings already have promotion
            qs = (
                Sale.objects.filter(
                    id__in=sale_ids,
                )
                .exclude(Exists(Promotion.objects.filter(old_sale_id=OuterRef("pk"))))
                .order_by("pk")
            )

            # lock the batch of objects to avoid potential promotion creation in the
            # meantime by sale mutation
            _sales = list(qs.select_for_update(of=(["self"])))
            _sale_listings = list(
                SaleChannelListing.objects.filter(
                    Exists(qs.filter(id=OuterRef("sale_id")))
                ).select_for_update(of=(["self"]))
            )
            migrate_sales(qs)
        migrate_sales_to_promotions_task.delay()

    migrate_sales_not_listed_in_any_channels_task.delay()


def migrate_sales(sales):
    saleid_promotion_map: Dict[int, Promotion] = {}
    rules_info: List[RuleInfo] = []

    sale_ids = [sale.id for sale in sales]
    migrate_sales_to_promotions(sales, saleid_promotion_map)
    migrate_sale_listing_to_promotion_rules(
        sale_ids,
        saleid_promotion_map,
        rules_info,
    )
    migrate_translations(sale_ids, saleid_promotion_map)

    rule_by_channel_and_sale = get_rule_by_channel_sale(rules_info)
    migrate_checkout_line_discounts(sale_ids, rule_by_channel_and_sale)
    migrate_order_line_discounts(sale_ids, rule_by_channel_and_sale)


@app.task
def migrate_sales_not_listed_in_any_channels_task():
    # migrate sales not listed in any channel
    sales_listing = SaleChannelListing.objects.order_by("sale_id")
    sales_not_listed = Sale.objects.filter(
        ~Exists(sales_listing.filter(sale_id=OuterRef("pk"))),
        ~Exists(Promotion.objects.filter(old_sale_id=OuterRef("pk"))),
    ).order_by("pk")
    ids = list(sales_not_listed.values_list("pk", flat=True)[:SALE_LISTING_BATCH_SIZE])
    if ids:
        with transaction.atomic():
            # we need to double check if any of those listings already have promotion
            sales = Sale.objects.filter(
                ~Exists(Promotion.objects.filter(old_sale_id=OuterRef("pk"))),
                id__in=ids,
            )
            # lock the batch of objects to avoid potential promotion creation in the
            # meantime by sale mutation
            _sales = list(sales.select_for_update(of=(["self"])))
            _sale_listings = list(
                SaleChannelListing.objects.filter(
                    Exists(sales.filter(id=OuterRef("sale_id")))
                ).select_for_update(of=(["self"]))
            )
            migrate_sales_not_listed_in_any_channels(sales)
        migrate_sales_not_listed_in_any_channels_task.delay()
    else:
        # Call discounted price recalculation to create
        # VariantChannelListingPromotionRule instances
        update_discounted_prices_task.delay()


def migrate_sales_not_listed_in_any_channels(sales):
    saleid_promotion_map = {}
    sale_ids = [sale.id for sale in sales]
    migrate_sales_to_promotions(sales, saleid_promotion_map)
    migrate_sales_to_promotion_rules(sales, saleid_promotion_map)
    migrate_translations(sale_ids, saleid_promotion_map)


def migrate_sales_to_promotions(sales, saleid_promotion_map):
    for sale in sales:
        saleid_promotion_map[sale.id] = convert_sale_into_promotion(sale)
    Promotion.objects.bulk_create(saleid_promotion_map.values())


def convert_sale_into_promotion(sale):
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
    sale, promotion, discount_value=None, old_channel_listing_id=None
):
    return PromotionRule(
        promotion=promotion,
        catalogue_predicate=create_catalogue_predicate_from_sale(sale),
        reward_value_type=sale.type,
        reward_value=discount_value,
        old_channel_listing_id=old_channel_listing_id,
    )


def migrate_sale_listing_to_promotion_rules(
    sale_ids,
    saleid_promotion_map,
    rules_info,
):
    sale_listings = (
        SaleChannelListing.objects.order_by("sale_id")
        .filter(sale_id__in=sale_ids)
        .prefetch_related(
            "sale",
            "sale__collections",
            "sale__categories",
            "sale__products",
            "sale__variants",
        )
    )
    if not sale_listings:
        return

    for sale_listing in sale_listings:
        promotion = saleid_promotion_map[sale_listing.sale_id]
        rules_info.append(
            RuleInfo(
                rule=create_promotion_rule(
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


def migrate_sales_to_promotion_rules(sales, saleid_promotion_map):
    if not sales:
        return
    rules: List[PromotionRule] = []
    for sale in sales:
        promotion = saleid_promotion_map[sale.id]
        rules.append(create_promotion_rule(sale, promotion))
    PromotionRule.objects.bulk_create(rules)


def migrate_translations(sale_ids, saleid_promotion_map):
    if sale_translations := SaleTranslation.objects.filter(sale_id__in=sale_ids):
        promotion_translations = [
            PromotionTranslation(
                name=translation.name,
                language_code=translation.language_code,
                promotion=saleid_promotion_map[translation.sale_id],
            )
            for translation in sale_translations
        ]
        PromotionTranslation.objects.bulk_create(promotion_translations)


def migrate_checkout_line_discounts(sale_ids, rule_by_channel_and_sale):
    checkout_line_discounts = CheckoutLineDiscount.objects.filter(
        sale_id__in=sale_ids
    ).exclude(type="promotion")[:CHECKOUT_LINE_DISCOUNT_BATCH_SIZE]
    discount_line_ids = list(checkout_line_discounts.values_list("id", flat=True))
    if discount_line_ids:
        line_discounts = CheckoutLineDiscount.objects.filter(
            id__in=discount_line_ids
        ).select_related("line__checkout")
        discounts_to_update = []
        for checkout_line_discount in line_discounts:
            discounts_to_update.append(checkout_line_discount)
            checkout_line_discount.type = "promotion"
            if checkout_line := checkout_line_discount.line:
                channel_id = checkout_line.checkout.channel_id
                sale_id = checkout_line_discount.sale_id
                lookup = f"{channel_id}_{sale_id}"
                if promotion_rule := rule_by_channel_and_sale.get(lookup):
                    checkout_line_discount.promotion_rule = promotion_rule

        CheckoutLineDiscount.objects.bulk_update(
            discounts_to_update, ["promotion_rule_id", "type"]
        )
        migrate_checkout_line_discounts(sale_ids, rule_by_channel_and_sale)


def migrate_order_line_discounts(sale_ids, rule_by_channel_and_sale, last_id=None):
    global_pks = [graphene.Node.to_global_id("Sale", pk) for pk in sale_ids]
    lookup = {"sale_id__in": global_pks}
    if last_id:
        lookup["id__gt"] = last_id
    lines = OrderLine.objects.filter(**lookup).order_by("created_at", "id")[
        :ORDER_LINE_DISCOUNT_BATCH_SIZE
    ]
    discount_line_ids = list(lines.values_list("id", flat=True))
    if discount_line_ids:
        order_lines = OrderLine.objects.filter(
            id__in=discount_line_ids
        ).prefetch_related("order")
        order_line_discounts = []
        for order_line in order_lines:
            channel_id = order_line.order.channel_id
            sale_id = graphene.Node.from_global_id(order_line.sale_id)[1]
            lookup = f"{channel_id}_{sale_id}"
            if rule := rule_by_channel_and_sale.get(lookup):
                order_line_discounts.append(
                    OrderLineDiscount(
                        type="promotion",
                        value_type=rule.reward_value_type,
                        value=rule.reward_value,
                        amount_value=get_discount_amount_value(order_line),
                        currency=order_line.currency,
                        promotion_rule=rule,
                        line=order_line,
                    )
                )

        OrderLineDiscount.objects.bulk_create(order_line_discounts)
        migrate_order_line_discounts(
            sale_ids, rule_by_channel_and_sale, discount_line_ids[-1]
        )


def get_discount_amount_value(order_line):
    precision = get_currency_precision(order_line.currency)
    number_places = Decimal(10) ** -precision
    price = order_line.quantity * order_line.unit_discount_amount
    return price.quantize(number_places)


def get_rule_by_channel_sale(rules_info):
    return {
        f"{rule_info.channel_id}_{rule_info.sale_id}": rule_info.rule
        for rule_info in rules_info
    }


@app.task
def update_discounted_prices_task(
    start_pk: int = 0,
):
    products = list(
        Product.objects.filter(pk__gt=start_pk).order_by("pk")[
            :DISCOUNTED_PRICES_RECALCULATION_BATCH_SIZE
        ]
    )

    if products:
        update_products_discounted_price(products)
        update_discounted_prices_task.delay(
            start_pk=products[-1].pk,
        )
