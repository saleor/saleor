from collections import defaultdict

from django.conf import settings
from django.db import transaction
from django.db.models import Exists, OuterRef, QuerySet

from ...discount.models import PromotionRule
from ...product.models import ProductChannelListing
from ..models import ProductVariant


def get_channel_to_products_map_from_rules(
    rules: "QuerySet[PromotionRule]", allow_replica=False
) -> dict[int, set[int]]:
    """Build map of channel ids to product ids based on promotion rules relations.

    The function returns the dictionary of channel_id to product_ids. Channels are
    aggregated from the input promotion rules. Returned product ids are ID of the
    product which has a variant assigned to the promotion rule.
    """
    PromotionRuleVariant = PromotionRule.variants.through
    promotion_rule_qs = PromotionRuleVariant.objects.all()
    product_variant_qs = ProductVariant.objects.all()
    PromotionRuleChannel = PromotionRule.channels.through
    promotion_rule_channel_qs = PromotionRuleChannel.objects.all()
    rules_qs = rules
    if allow_replica:
        rules_qs = rules.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        product_variant_qs = product_variant_qs.using(
            settings.DATABASE_CONNECTION_REPLICA_NAME
        )
        promotion_rule_qs = promotion_rule_qs.using(
            settings.DATABASE_CONNECTION_REPLICA_NAME
        )
        promotion_rule_channel_qs = promotion_rule_channel_qs.using(
            settings.DATABASE_CONNECTION_REPLICA_NAME
        )
    rule_variants = promotion_rule_qs.filter(
        Exists(rules_qs.filter(pk=OuterRef("promotionrule_id")))
    )

    variant_to_product_qs = product_variant_qs.filter(
        Exists(rule_variants.filter(productvariant_id=OuterRef("id")))
    ).values_list("id", "product_id")
    variant_to_product_map = {}
    for variant_id, product_id in variant_to_product_qs:
        variant_to_product_map[variant_id] = product_id

    rule_channels = promotion_rule_channel_qs.filter(
        Exists(rules_qs.filter(pk=OuterRef("promotionrule_id")))
    ).values_list("promotionrule_id", "channel_id")
    rule_to_channels_map = defaultdict(set)
    for rule_id, channel_id in rule_channels:
        rule_to_channels_map[rule_id].add(channel_id)

    channel_to_products_map = defaultdict(set)
    for rule_variant in rule_variants:
        channel_ids = rule_to_channels_map[rule_variant.promotionrule_id]
        for channel_id in channel_ids:
            product_id = variant_to_product_map[rule_variant.productvariant_id]
            channel_to_products_map[channel_id].add(product_id)
    return channel_to_products_map


def mark_products_in_channels_as_dirty_based_on_rules(
    rules: "QuerySet[PromotionRule]", allow_replica=False
):
    """Mark products as dirty to recalculate prices.

    Takes the promotion rules as input and marks the discounted_price_dirty flag as
    True for all product channel listings related to input rules.
    """
    channel_to_product_ids = get_channel_to_products_map_from_rules(
        rules, allow_replica=allow_replica
    )
    if channel_to_product_ids:
        mark_products_in_channels_as_dirty(
            channel_to_product_ids, allow_replica=allow_replica
        )


def mark_products_in_channels_as_dirty(
    channel_to_product_ids: dict[int, set[int]], allow_replica=False
):
    """Mark products as dirty to recalculate prices.

    Takes the dictionary of channel_id to product_ids as input and marks the
    discounted_price_dirty flag as True for all product channel listings related to
    input channels and products.
    The input structure looks like below:
    {
        channel_id1: {product_id1, product_id2, ...},
        channel_id2: {product_id3, product_id4, ...},
        ...
    }

    The structure can be built by function `get_channel_to_products_map_from_rules`
    """

    if not channel_to_product_ids:
        return
    channels = list(channel_to_product_ids.keys())
    product_ids = {
        product_id
        for product_ids in channel_to_product_ids.values()
        for product_id in product_ids
    }
    listing_ids_to_update = []
    product_channel_listings_qs = ProductChannelListing.objects.all()
    if allow_replica:
        product_channel_listings_qs = product_channel_listings_qs.using(
            settings.DATABASE_CONNECTION_REPLICA_NAME
        )

    product_channel_listings = product_channel_listings_qs.filter(
        product_id__in=product_ids, channel_id__in=channels
    ).values_list("id", "product_id", "channel_id")

    for id, product_id, channel_id in product_channel_listings.iterator():
        product_ids = channel_to_product_ids.get(channel_id, set())
        if product_id in product_ids:
            listing_ids_to_update.append(id)

    if listing_ids_to_update:
        with transaction.atomic():
            channel_listing_ids = list(
                ProductChannelListing.objects.select_for_update(of=("self",))
                .filter(id__in=listing_ids_to_update, discounted_price_dirty=False)
                .order_by("pk")
                .values_list("id", flat=True)
            )
            ProductChannelListing.objects.filter(id__in=channel_listing_ids).update(
                discounted_price_dirty=True
            )
