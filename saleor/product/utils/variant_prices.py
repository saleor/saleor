from collections import defaultdict
from typing import Dict, Iterable, List, Set, Tuple

from django.db.models import Exists, OuterRef, QuerySet
from django.db.models.query_utils import Q
from prices import Money

from ...channel.models import Channel
from ...discount import DiscountInfo
from ...discount.models import Promotion, PromotionRule, Sale
from ...discount.utils import calculate_discounted_price, fetch_active_discounts
from ..models import (
    Category,
    CollectionProduct,
    Product,
    ProductChannelListing,
    ProductVariant,
    ProductVariantChannelListing,
    VariantChannelListingPromotionRule,
)


def update_products_discounted_price(products: Iterable[Product], discounts=None):
    """Update Products and ProductVariants discounted prices.

    The discounted price is the minimal price of the product/variant based on active
    sales that are applied to a given product.
    If there is no applied sale, the discounted price for the product is equal to the
    cheapest variant price, in the case of the variant it's equal to the variant price.
    """
    if discounts is None:
        discounts = fetch_active_discounts()
    product_ids = [product.id for product in products]
    product_qs = Product.objects.filter(id__in=product_ids)
    collection_products = CollectionProduct.objects.filter(
        Exists(product_qs.filter(id=OuterRef("product_id")))
    )
    product_to_collection_ids_map = defaultdict(set)
    for collection_id, product_id in collection_products.values_list(
        "collection_id", "product_id"
    ).iterator():
        product_to_collection_ids_map[product_id].add(collection_id)

    product_to_variant_listings_per_channel_map = (
        _get_product_to_variant_channel_listings_per_channel_map(product_qs)
    )

    changed_products_listings_to_update = []
    changed_variants_listings_to_update = []
    changed_rule_listings_to_update: List[VariantChannelListingPromotionRule] = []
    rule_listings_to_create: List[VariantChannelListingPromotionRule] = []

    product_channel_listings = ProductChannelListing.objects.filter(
        Exists(product_qs.filter(id=OuterRef("product_id")))
    ).prefetch_related("product", "channel")
    for product_channel_listing in product_channel_listings.iterator():
        product_id = product_channel_listing.product_id
        channel_id = product_channel_listing.channel_id
        variant_listings = product_to_variant_listings_per_channel_map[product_id][
            channel_id
        ]
        if not variant_listings:
            continue
        collection_ids = product_to_collection_ids_map[product_id]
        (
            discounted_variants_price,
            variant_listings_to_update,
            listings_promotion_rule_to_update,
            listings_promotion_rule_to_create,
        ) = _get_discounted_variants_prices(
            variant_listings,
            product_channel_listing.product,
            collection_ids,
            discounts,
            product_channel_listing.channel,
        )

        product_discounted_price = min(discounted_variants_price)
        changed_variants_listings_to_update.extend(variant_listings_to_update)
        changed_rule_listings_to_update.extend(listings_promotion_rule_to_update)
        rule_listings_to_create.extend(listings_promotion_rule_to_create)

        # check if the product discounted_price has changed
        if product_channel_listing.discounted_price != product_discounted_price:
            product_channel_listing.discounted_price_amount = (
                product_discounted_price.amount
            )
            changed_products_listings_to_update.append(product_channel_listing)

    if changed_products_listings_to_update:
        ProductChannelListing.objects.bulk_update(
            changed_products_listings_to_update, ["discounted_price_amount"]
        )
    if changed_variants_listings_to_update:
        ProductVariantChannelListing.objects.bulk_update(
            changed_variants_listings_to_update, ["discounted_price_amount"]
        )
    if changed_rule_listings_to_update:
        VariantChannelListingPromotionRule.objects.bulk_update(
            changed_rule_listings_to_update, ["discount_amount"]
        )
    if rule_listings_to_create:
        VariantChannelListingPromotionRule.objects.bulk_create(rule_listings_to_create)


def _get_product_to_variant_channel_listings_per_channel_map(
    products: QuerySet[Product],
):
    variants = ProductVariant.objects.filter(
        Exists(products.filter(id=OuterRef("product_id")))
    )
    variant_channel_listings = ProductVariantChannelListing.objects.filter(
        Exists(variants.filter(id=OuterRef("variant_id"))), price_amount__isnull=False
    )
    variant_to_product_id = {
        variant_id: product_id
        for variant_id, product_id in variants.values_list(
            "id", "product_id"
        ).iterator()
    }

    price_data: Dict[int, Dict[int, List[Money]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for variant_channel_listing in variant_channel_listings.iterator():
        product_id = variant_to_product_id[variant_channel_listing.variant_id]
        price_data[product_id][variant_channel_listing.channel_id].append(
            variant_channel_listing
        )
    return price_data


def _get_discounted_variants_prices(
    variant_listings: List[ProductVariantChannelListing],
    product: Product,
    collection_ids: Set[int],
    discounts: List[DiscountInfo],
    channel: Channel,
) -> Tuple[
    Money,
    List[ProductVariantChannelListing],
    List[VariantChannelListingPromotionRule],
    List[VariantChannelListingPromotionRule],
]:
    listings_promotion_rule_to_update: List[VariantChannelListingPromotionRule] = []
    listings_promotion_rule_to_create: List[VariantChannelListingPromotionRule] = []
    variants_listings_to_update: List[ProductVariantChannelListing] = []
    discounted_variants_price: List[Money] = []
    for variant_listing in variant_listings:
        sale_id, discounted_variant_price = calculate_discounted_price(
            product=product,
            price=variant_listing.price,
            collection_ids=collection_ids,
            discounts=discounts,
            channel=channel,
            variant_id=variant_listing.variant_id,
        )
        if variant_listing.discounted_price != discounted_variant_price:
            variant_listing.discounted_price_amount = discounted_variant_price.amount
            variants_listings_to_update.append(variant_listing)
        discounted_variants_price.append(discounted_variant_price)
        discount_amount = (
            variant_listing.price_amount  # type: ignore
            - variant_listing.discounted_price_amount
        )
        if discount_amount:
            (
                rule_listing_to_update,
                rule_listing_to_create,
            ) = variant_listing_promotion_rule_update(
                sale_id, variant_listing, discount_amount
            )
            if rule_listing_to_update:
                listings_promotion_rule_to_update.append(rule_listing_to_update)
            if rule_listing_to_create:
                listings_promotion_rule_to_create.append(rule_listing_to_create)
    return (
        discounted_variants_price,
        variants_listings_to_update,
        listings_promotion_rule_to_update,
        listings_promotion_rule_to_create,
    )


def variant_listing_promotion_rule_update(sale_id, variant_listing, discount_amount):
    """Update or create VariantChannelListingPromotionRule for given sale.

    Return tuple, first element will be VariantChannelListingPromotionRule to update,
    second will be VariantChannelListingPromotionRule to create.

    Return (None, None) if Promotion does not exist yet. The proper listing promotion
    rule instances will be created when migrating.
    """
    promotion = Promotion.objects.filter(old_sale_id=sale_id)
    promotion_rules = PromotionRule.objects.filter(
        Exists(promotion.filter(id=OuterRef("promotion_id")))
    )
    # If the promotion does not exists it mean that the sale wasn't migrated yet.
    # The proper VariantChannelListingPromotionRule will be created during migration.
    if not promotion:
        return None, None
    listing_promotion_rule_to_update = (
        variant_listing.variantlistingpromotionrule.filter(
            Exists(promotion_rules.filter(id=OuterRef("promotion_rule_id")))
        ).first()
    )
    if listing_promotion_rule_to_update:
        if listing_promotion_rule_to_update.discount_amount != discount_amount:
            listing_promotion_rule_to_update.discount_amount = discount_amount
            return listing_promotion_rule_to_update, None
        return None, None

    # create VariantChannelListingPromotionRule
    PromotionRuleChannel = PromotionRule.channels.through
    rule_channels = PromotionRuleChannel.objects.filter(
        channel_id=variant_listing.channel_id
    )
    promotion_rule = promotion_rules.filter(
        Exists(rule_channels.filter(promotionrule_id=OuterRef("id")))
    ).first()
    new_listing_promotion_rule = VariantChannelListingPromotionRule(
        variant_channel_listing=variant_listing,
        promotion_rule=promotion_rule,
        discount_amount=discount_amount,
        currency=variant_listing.currency,
    )
    return None, new_listing_promotion_rule


def _products_in_batches(products_qs):
    """Slice a products queryset into batches."""
    start_pk = 0

    # Results in memory usage of ~40MB for 500 products
    BATCH_SIZE = 500

    first_batch = True

    while True:
        filter_args = {}
        if not first_batch:
            filter_args = {"pk__lt": start_pk}
        first_batch = False
        products = list(
            products_qs.order_by("-pk")
            .filter(**filter_args)
            .prefetch_related("channel_listings", "collections")[:BATCH_SIZE]
        )
        if not products:
            break
        yield products
        start_pk = products[-1].pk


def update_products_discounted_prices(products, discounts=None):
    if discounts is None:
        discounts = fetch_active_discounts()

    for product_batch in _products_in_batches(products):
        update_products_discounted_price(product_batch, discounts)


def update_products_discounted_prices_of_catalogues(
    product_ids=None, category_ids=None, collection_ids=None, variant_ids=None
):
    lookup = Q()
    if product_ids:
        lookup |= Q(pk__in=product_ids)
    if category_ids:
        categories = Category.objects.filter(id__in=category_ids)
        lookup |= Q(Exists(categories.filter(id=OuterRef("category_id"))))
    if collection_ids:
        collection_products = CollectionProduct.objects.filter(
            collection_id__in=collection_ids
        )
        lookup |= Q(Exists(collection_products.filter(product_id=OuterRef("id"))))
    if variant_ids:
        variants = ProductVariant.objects.filter(id__in=variant_ids)
        lookup |= Q(Exists(variants.filter(product_id=OuterRef("id"))))

    if lookup:
        products = Product.objects.filter(lookup)

        update_products_discounted_prices(products)


def update_products_discounted_prices_of_sale(sale: Sale):
    """Recalculate discounted prices of related sale products."""
    product_lookup = Q()
    product_lookup |= Q(Exists(sale.variants.filter(product_id=OuterRef("id"))))
    product_lookup |= Q(Exists(sale.categories.filter(id=OuterRef("category_id"))))
    collection_products = CollectionProduct.objects.filter(
        Exists(sale.collections.filter(id=OuterRef("collection_id")))
    )
    product_lookup |= Q(Exists(collection_products.filter(product_id=OuterRef("id"))))

    products = sale.products.all() | Product.objects.filter(product_lookup)

    update_products_discounted_prices(products)
