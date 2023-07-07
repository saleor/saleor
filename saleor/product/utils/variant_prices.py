from collections import defaultdict
from decimal import Decimal
from typing import Dict, Iterable, List, Optional, Set, Tuple

from django.db.models import Exists, OuterRef
from django.db.models.query_utils import Q
from prices import Money

from ...channel.models import Channel
from ...core.taxes import zero_money
from ...discount import DiscountInfo, PromotionRuleInfo
from ...discount.models import Sale
from ...discount.utils import (
    calculate_discounted_price,
    calculate_discounted_price_for_promotions,
    fetch_active_discounts,
    fetch_active_promotion_rules,
)
from ..models import (
    Category,
    CollectionProduct,
    Product,
    ProductChannelListing,
    ProductsQueryset,
    ProductVariant,
    ProductVariantChannelListing,
    ProductVariantQueryset,
    VariantChannelListingPromotionRule,
)


def update_discounted_prices_for_promotion(
    products: ProductsQueryset, rules_info: Optional[List[PromotionRuleInfo]] = None
):
    """Update Products and ProductVariants discounted prices.

    The discounted price is the minimal price of the product/variant based on active
    promotions that are applied to a given product.
    If there is no applied promotion rule, the discounted price for the product
    is equal to the cheapest variant price, in the case of the variant it's equal
    to the variant price.
    """
    variant_qs = ProductVariant.objects.filter(
        Exists(products.filter(id=OuterRef("product_id")))
    )
    if rules_info is None:
        rules_info_per_promotion_id = fetch_active_promotion_rules(variant_qs)
    product_to_variant_listings_per_channel_map = (
        _get_product_to_variant_channel_listings_per_channel_map(variant_qs)
    )
    variant_listing_to_listing_rule_per_rule_map = (
        _get_variant_listings_to_listing_rule_per_rule_id_map(variant_qs)
    )

    changed_products_listings_to_update = []
    changed_variants_listings_to_update = []

    changed_variant_listing_promotion_rule_to_create = []
    changed_variant_listing_promotion_rule_to_update = []

    product_channel_listings = ProductChannelListing.objects.filter(
        Exists(products.filter(id=OuterRef("product_id")))
    )
    for product_channel_listing in product_channel_listings:
        product_id = product_channel_listing.product_id
        channel_id = product_channel_listing.channel_id
        variant_listings = product_to_variant_listings_per_channel_map[product_id][
            channel_id
        ]
        if not variant_listings:
            continue
        (
            discounted_variants_price,
            variant_listings_to_update,
            variant_listing_promotion_rule_to_create,
            variant_listing_promotion_rule_to_update,
        ) = _get_discounted_variants_prices_for_promotions(
            variant_listings,
            rules_info_per_promotion_id,
            product_channel_listing.channel,
            variant_listing_to_listing_rule_per_rule_map,
        )

        product_discounted_price = min(discounted_variants_price)
        changed_variants_listings_to_update.extend(variant_listings_to_update)
        changed_variant_listing_promotion_rule_to_create.extend(
            variant_listing_promotion_rule_to_create
        )
        changed_variant_listing_promotion_rule_to_update.extend(
            variant_listing_promotion_rule_to_update
        )

        # check if the product discounted_price has changed
        if product_channel_listing.discounted_price != product_discounted_price:
            product_channel_listing.discounted_price_amount = (
                product_discounted_price.amount
            )
            changed_products_listings_to_update.append(product_channel_listing)

    _update_or_create_listings(
        changed_products_listings_to_update,
        changed_variants_listings_to_update,
        changed_variant_listing_promotion_rule_to_create,
        changed_variant_listing_promotion_rule_to_update,
    )


def _update_or_create_listings(
    changed_products_listings_to_update: List[ProductChannelListing],
    changed_variants_listings_to_update: List[ProductVariantChannelListing],
    changed_variant_listing_promotion_rule_to_create: List[
        VariantChannelListingPromotionRule
    ],
    changed_variant_listing_promotion_rule_to_update: List[
        VariantChannelListingPromotionRule
    ],
):
    if changed_products_listings_to_update:
        ProductChannelListing.objects.bulk_update(
            changed_products_listings_to_update, ["discounted_price_amount"]
        )
    if changed_variants_listings_to_update:
        ProductVariantChannelListing.objects.bulk_update(
            changed_variants_listings_to_update, ["discounted_price_amount"]
        )
    if changed_variant_listing_promotion_rule_to_create:
        VariantChannelListingPromotionRule.objects.bulk_create(
            changed_variant_listing_promotion_rule_to_create
        )
    if changed_variant_listing_promotion_rule_to_update:
        VariantChannelListingPromotionRule.objects.bulk_update(
            changed_variant_listing_promotion_rule_to_update, ["discount_amount"]
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
    ):
        product_to_collection_ids_map[product_id].add(collection_id)

    variant_qs = ProductVariant.objects.filter(
        Exists(product_qs.filter(id=OuterRef("product_id")))
    )
    product_to_variant_listings_per_channel_map = (
        _get_product_to_variant_channel_listings_per_channel_map(variant_qs)
    )

    changed_products_listings_to_update = []
    changed_variants_listings_to_update = []
    product_channel_listings = ProductChannelListing.objects.filter(
        Exists(product_qs.filter(id=OuterRef("product_id")))
    )
    for product_channel_listing in product_channel_listings:
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
        ) = _get_discounted_variants_prices(
            variant_listings,
            product_channel_listing.product,
            collection_ids,
            discounts,
            product_channel_listing.channel,
        )

        product_discounted_price = min(discounted_variants_price)
        changed_variants_listings_to_update.extend(variant_listings_to_update)

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


def _get_product_to_variant_channel_listings_per_channel_map(
    variants: ProductVariantQueryset,
):
    variant_channel_listings = ProductVariantChannelListing.objects.filter(
        Exists(variants.filter(id=OuterRef("variant_id"))), price_amount__isnull=False
    )
    variant_to_product_id = {
        variant_id: product_id
        for variant_id, product_id in variants.values_list("id", "product_id")
    }

    price_data: Dict[int, Dict[int, List[Money]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for variant_channel_listings in variant_channel_listings:
        product_id = variant_to_product_id[variant_channel_listings.variant_id]
        price_data[product_id][variant_channel_listings.channel_id].append(
            variant_channel_listings
        )
    return price_data


def _get_variant_listings_to_listing_rule_per_rule_id_map(
    variants: ProductVariantQueryset,
):
    """Return map for fetching VariantChannelListingPromotionRule per listing per rule.

    The map is in the format:
    {
        variant_channel_listing_id: {
            rule_id: variant_channel_listing_promotion_rule
        }
    }
    """
    variant_listing_rule_data: Dict[
        int, Dict[int, VariantChannelListingPromotionRule]
    ] = defaultdict(dict)
    variant_channel_listings = ProductVariantChannelListing.objects.filter(
        Exists(variants.filter(id=OuterRef("variant_id"))), price_amount__isnull=False
    )
    variant_listing_promotion_rules = VariantChannelListingPromotionRule.objects.filter(
        Exists(
            variant_channel_listings.filter(id=OuterRef("variant_channel_listing_id"))
        )
    )
    for variant_listing_promotion_rule in variant_listing_promotion_rules:
        listing_id = variant_listing_promotion_rule.variant_channel_listing_id
        rule_id = variant_listing_promotion_rule.promotion_rule_id
        variant_listing_rule_data[listing_id][rule_id] = variant_listing_promotion_rule

    return variant_listing_rule_data


def _get_variants_for_product_ids(product_ids: Iterable[int]):
    products = Product.objects.filter(id__in=product_ids)
    return ProductVariant.objects.filter(
        Exists(products.filter(id=OuterRef("product_id")))
    )


def _get_discounted_variants_prices(
    variant_listings: List[ProductVariantChannelListing],
    product: Product,
    collection_ids: Set[int],
    discounts: List[DiscountInfo],
    channel: Channel,
) -> Tuple[Money, List[ProductVariantChannelListing]]:
    variants_listings_to_update: List[ProductVariantChannelListing] = []
    discounted_variants_price: List[Money] = []
    for variant_listing in variant_listings:
        discounted_variant_price = calculate_discounted_price(
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
    return discounted_variants_price, variants_listings_to_update


def _get_discounted_variants_prices_for_promotions(
    variant_listings: List[ProductVariantChannelListing],
    rules_info_per_promotion_id: Dict[int, List[PromotionRuleInfo]],
    channel: Channel,
    variant_listing_to_listing_rule_per_rule_map: dict,
) -> Tuple[
    Money,
    List[ProductVariantChannelListing],
    List[VariantChannelListingPromotionRule],
    List[VariantChannelListingPromotionRule],
]:
    variants_listings_to_update: List[ProductVariantChannelListing] = []
    discounted_variants_price: List[Money] = []
    variant_listing_promotion_rule_to_create: List[
        VariantChannelListingPromotionRule
    ] = []
    variant_listing_promotion_rule_to_update: List[
        VariantChannelListingPromotionRule
    ] = []
    for variant_listing in variant_listings:
        applied_discounts = calculate_discounted_price_for_promotions(
            price=variant_listing.price,
            rules_info_per_promotion_id=rules_info_per_promotion_id,
            channel=channel,
            variant_id=variant_listing.variant_id,
        )
        rule_ids = []
        discounted_variant_price = variant_listing.price
        for rule_id, discount in applied_discounts:
            if discounted_variant_price.amount < discount.amount:
                discount = discounted_variant_price
                discounted_variant_price = zero_money(discounted_variant_price.currency)
            else:
                discounted_variant_price -= discount
            _handle_discount_rule_id(
                variant_listing,
                rule_id,
                variant_listing_to_listing_rule_per_rule_map,
                discount.amount,
                channel.currency_code,
                variant_listing_promotion_rule_to_update,
                variant_listing_promotion_rule_to_create,
            )
            rule_ids.append(rule_id)
            if discounted_variant_price.amount == 0:
                break

        if variant_listing.discounted_price != discounted_variant_price:
            variant_listing.discounted_price_amount = discounted_variant_price.amount
            variants_listings_to_update.append(variant_listing)

            # delete variant listing - promotion rules relationd that are not valid
            # anymore
            VariantChannelListingPromotionRule.objects.filter(
                variant_channel_listing_id=variant_listing.id
            ).exclude(promotion_rule_id__in=rule_ids).delete()

        discounted_variants_price.append(discounted_variant_price)

    return (
        discounted_variants_price,
        variants_listings_to_update,
        variant_listing_promotion_rule_to_create,
        variant_listing_promotion_rule_to_update,
    )


def _handle_discount_rule_id(
    variant_listing: ProductVariantChannelListing,
    rule_id: int,
    variant_listing_to_listing_rule_per_rule_map: dict,
    discount_amount: Decimal,
    currency: str,
    variant_listing_promotion_rule_to_update: List[VariantChannelListingPromotionRule],
    variant_listing_promotion_rule_to_create: List[VariantChannelListingPromotionRule],
):
    listing_promotion_rule = variant_listing_to_listing_rule_per_rule_map[
        variant_listing.id
    ].get(rule_id)
    if listing_promotion_rule:
        listing_promotion_rule.discount_amount = discount_amount
        variant_listing_promotion_rule_to_update.append(listing_promotion_rule)
    else:
        variant_listing_promotion_rule_to_create.append(
            VariantChannelListingPromotionRule(
                variant_channel_listing=variant_listing,
                promotion_rule_id=rule_id,
                discount_amount=discount_amount,
                currency=currency,
            )
        )


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
        update_products_discounted_price(product_batch)


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
        lookup |= Q(Exists(ProductVariant.objects.filter(product_id=OuterRef("id"))))

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
