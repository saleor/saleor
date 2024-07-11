from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.db.models import Exists, OuterRef
from prices import Money

from ...channel.models import Channel
from ...core.taxes import zero_money
from ...discount import PromotionRuleInfo
from ...discount.models import PromotionRule
from ...discount.utils.promotion import (
    calculate_discounted_price_for_promotions,
    get_variants_to_promotion_rules_map,
)
from ..managers import ProductsQueryset, ProductVariantQueryset
from ..models import (
    ProductChannelListing,
    ProductVariant,
    ProductVariantChannelListing,
    VariantChannelListingPromotionRule,
)


def update_discounted_prices_for_promotion(
    products: ProductsQueryset, only_dirty_products: bool = False
):
    """Update Products and ProductVariants discounted prices.

    The discounted price is the minimal price of the product/variant based on active
    promotions that are applied to a given product.
    If there is no applied promotion rule, the discounted price for the product
    is equal to the cheapest variant price, in the case of the variant it's equal
    to the variant price.

    When only_dirty_products set to True, the prices will be recalculated only for the
    listings marked as dirty.
    """
    variant_qs = ProductVariant.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).filter(Exists(products.filter(id=OuterRef("product_id"))))
    rules_info_per_variant = get_variants_to_promotion_rules_map(variant_qs)
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

    product_channel_listings = ProductChannelListing.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).filter(Exists(products.filter(id=OuterRef("product_id"))))
    if only_dirty_products:
        product_channel_listings.filter(discounted_price_dirty=True)

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
            rules_info_per_variant,
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
    changed_products_listings_to_update: list[ProductChannelListing],
    changed_variants_listings_to_update: list[ProductVariantChannelListing],
    changed_variant_listing_promotion_rule_to_create: list[
        VariantChannelListingPromotionRule
    ],
    changed_variant_listing_promotion_rule_to_update: list[
        VariantChannelListingPromotionRule
    ],
):
    if changed_products_listings_to_update:
        ProductChannelListing.objects.bulk_update(
            sorted(changed_products_listings_to_update, key=lambda listing: listing.id),
            ["discounted_price_amount"],
        )
    if changed_variants_listings_to_update:
        ProductVariantChannelListing.objects.bulk_update(
            sorted(changed_variants_listings_to_update, key=lambda listing: listing.id),
            ["discounted_price_amount"],
        )
    if changed_variant_listing_promotion_rule_to_create:
        _create_variant_listing_promotion_rule(
            changed_variant_listing_promotion_rule_to_create
        )
    if changed_variant_listing_promotion_rule_to_update:
        VariantChannelListingPromotionRule.objects.bulk_update(
            sorted(
                changed_variant_listing_promotion_rule_to_update,
                key=lambda listing: listing.id,
            ),
            ["discount_amount"],
        )


def _create_variant_listing_promotion_rule(variant_listing_promotion_rule_to_create):
    with transaction.atomic():
        rule_ids = [
            listing.promotion_rule_id
            for listing in variant_listing_promotion_rule_to_create
        ]
        listing_ids = [
            listing.variant_channel_listing_id
            for listing in variant_listing_promotion_rule_to_create
        ]
        # Lock PromotionRule and ProductVariantChannelListing before bulk_create
        rules = PromotionRule.objects.filter(id__in=rule_ids).select_for_update()
        variant_listings = ProductVariantChannelListing.objects.filter(
            id__in=listing_ids
        ).select_for_update()
        # Do not create VariantChannelListingPromotionRule for rules that were deleted.
        if len(rules) < len(rule_ids):
            variant_listing_promotion_rule_to_create = [
                listing
                for listing in variant_listing_promotion_rule_to_create
                if listing.promotion_rule_id in {rule.id for rule in rules}
            ]
        if len(variant_listings) < len(listing_ids):
            variant_listing_promotion_rule_to_create = [
                listing
                for listing in variant_listing_promotion_rule_to_create
                if listing.variant_channel_listing_id
                in {listing.id for listing in variant_listings}
            ]
        # After migrating to Django 4.0 we should use `update_conflicts` instead
        # of `ignore_conflicts`
        # https://docs.djangoproject.com/en/4.1/ref/models/querysets/#bulk-create
        VariantChannelListingPromotionRule.objects.bulk_create(
            variant_listing_promotion_rule_to_create, ignore_conflicts=True
        )


def _get_product_to_variant_channel_listings_per_channel_map(
    variants: ProductVariantQueryset,
):
    variant_channel_listings = ProductVariantChannelListing.objects.filter(
        Exists(variants.filter(id=OuterRef("variant_id"))), price_amount__isnull=False
    )
    variant_to_product_id = {
        variant_id: product_id
        for variant_id, product_id in variants.values_list(
            "id", "product_id"
        ).iterator()
    }

    price_data: dict[int, dict[int, list[Money]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for variant_channel_listing in variant_channel_listings.iterator():
        product_id = variant_to_product_id[variant_channel_listing.variant_id]
        price_data[product_id][variant_channel_listing.channel_id].append(
            variant_channel_listing
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
    variant_listing_rule_data: dict[
        int, dict[UUID, VariantChannelListingPromotionRule]
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


def _get_discounted_variants_prices_for_promotions(
    variant_listings: list[ProductVariantChannelListing],
    rules_info_per_variant: dict[int, list[PromotionRuleInfo]],
    channel: Channel,
    variant_listing_to_listing_rule_per_rule_map: dict,
) -> tuple[
    Money,
    list[ProductVariantChannelListing],
    list[VariantChannelListingPromotionRule],
    list[VariantChannelListingPromotionRule],
]:
    variants_listings_to_update: list[ProductVariantChannelListing] = []
    discounted_variants_price: list[Money] = []
    variant_listing_promotion_rule_to_create: list[
        VariantChannelListingPromotionRule
    ] = []
    variant_listing_promotion_rule_to_update: list[
        VariantChannelListingPromotionRule
    ] = []
    for variant_listing in variant_listings:
        applied_discount = calculate_discounted_price_for_promotions(
            price=variant_listing.price,
            rules_info_per_variant=rules_info_per_variant,
            channel=channel,
            variant_id=variant_listing.variant_id,
        )
        discounted_variant_price = variant_listing.price

        rule_id = None
        if applied_discount:
            rule_id, discount = applied_discount
            discounted_variant_price -= discount
            discounted_variant_price = max(
                discounted_variant_price, zero_money(discounted_variant_price.currency)
            )

            _handle_discount_rule_id(
                variant_listing,
                rule_id,
                variant_listing_to_listing_rule_per_rule_map,
                discount.amount,
                channel.currency_code,
                variant_listing_promotion_rule_to_update,
                variant_listing_promotion_rule_to_create,
            )

        if variant_listing.discounted_price != discounted_variant_price:
            variant_listing.discounted_price_amount = discounted_variant_price.amount
            variants_listings_to_update.append(variant_listing)

            # delete variant listing - promotion rules relations that are not valid
            # anymore
            VariantChannelListingPromotionRule.objects.filter(
                variant_channel_listing_id=variant_listing.id
            ).exclude(promotion_rule_id=rule_id).delete()

        discounted_variants_price.append(discounted_variant_price)

    return (
        discounted_variants_price,
        variants_listings_to_update,
        variant_listing_promotion_rule_to_create,
        variant_listing_promotion_rule_to_update,
    )


def _handle_discount_rule_id(
    variant_listing: ProductVariantChannelListing,
    rule_id: UUID,
    variant_listing_to_listing_rule_per_rule_map: dict,
    discount_amount: Decimal,
    currency: str,
    variant_listing_promotion_rule_to_update: list[VariantChannelListingPromotionRule],
    variant_listing_promotion_rule_to_create: list[VariantChannelListingPromotionRule],
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
