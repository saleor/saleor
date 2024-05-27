import logging
from collections import defaultdict
from collections.abc import Iterable
from typing import Optional
from uuid import UUID

from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Exists, OuterRef, Q, QuerySet
from django.utils import timezone

from ..attribute.models import Attribute
from ..celeryconf import app
from ..core.exceptions import PreorderAllocationError
from ..discount import PromotionType
from ..discount.models import Promotion, PromotionRule
from ..plugins.manager import get_plugins_manager
from ..warehouse.management import deactivate_preorder_for_variant
from ..webhook.event_types import WebhookEventAsyncType
from ..webhook.utils import get_webhooks_for_event
from .models import Product, ProductChannelListing, ProductType, ProductVariant
from .search import update_products_search_vector
from .utils.product import mark_products_in_channels_as_dirty
from .utils.variant_prices import update_discounted_prices_for_promotion
from .utils.variants import (
    fetch_variants_for_promotion_rules,
    generate_and_set_variant_name,
)

logger = logging.getLogger(__name__)
task_logger = get_task_logger(__name__)

PRODUCTS_BATCH_SIZE = 300

VARIANTS_UPDATE_BATCH = 500
# Results in update time ~0.2s
DISCOUNTED_PRODUCT_BATCH = 2000
# Results in update time ~2s when 600 channels exist
PROMOTION_RULE_BATCH_SIZE = 100


def _variants_in_batches(variants_qs):
    """Slice a variants queryset into batches."""
    start_pk = 0

    while True:
        variants = list(
            variants_qs.order_by("pk").filter(pk__gt=start_pk)[:VARIANTS_UPDATE_BATCH]
        )
        if not variants:
            break
        yield variants
        start_pk = variants[-1].pk


def _update_variants_names(instance: ProductType, saved_attributes: Iterable):
    """Product variant names are created from names of assigned attributes.

    After change in attribute value name, we update the names for all product variants
    that lack names and use these attributes.
    """
    initial_attributes = set(instance.variant_attributes.all())
    attributes_changed = initial_attributes.intersection(saved_attributes)
    if not attributes_changed:
        return

    variants = ProductVariant.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).filter(
        name="",
        product__in=instance.products.all(),
        product__product_type__variant_attributes__in=attributes_changed,
    )

    for variants_batch in _variants_in_batches(variants):
        variants_to_update = [
            generate_and_set_variant_name(variant, variant.sku, save=False)
            for variant in variants_batch
        ]
        ProductVariant.objects.bulk_update(variants_to_update, ["name", "updated_at"])


@app.task
def update_variants_names(product_type_pk: int, saved_attributes_ids: list[int]):
    try:
        instance = ProductType.objects.using(
            settings.DATABASE_CONNECTION_REPLICA_NAME
        ).get(pk=product_type_pk)
    except ObjectDoesNotExist:
        logging.warning(f"Cannot find product type with id: {product_type_pk}.")
        return
    saved_attributes = Attribute.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).filter(pk__in=saved_attributes_ids)
    _update_variants_names(instance, saved_attributes)


@app.task
def update_products_discounted_prices_of_promotion_task(promotion_pk: UUID):
    # FIXME: Should be removed in Saleor 3.21

    # In case of triggering this task by old server worker, mark promotion
    # as dirty. The reclacultion will happen in the background
    PromotionRule.objects.filter(promotion_id=promotion_pk).update(variants_dirty=True)


def _get_channel_to_products_map(rule_to_variant_list):
    variant_ids = set(
        [rule_to_variant.productvariant_id for rule_to_variant in rule_to_variant_list]
    )
    variant_id_with_product_id_qs = (
        ProductVariant.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(id__in=variant_ids)
        .values_list("id", "product_id")
    )
    variant_id_to_product_id_map = {}
    for variant_id, product_id in variant_id_with_product_id_qs:
        variant_id_to_product_id_map[variant_id] = product_id

    rule_ids = set(
        [rule_to_variant.promotionrule_id for rule_to_variant in rule_to_variant_list]
    )
    PromotionChannel = PromotionRule.channels.through
    promotion_channel_qs = (
        PromotionChannel.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(promotionrule_id__in=rule_ids)
        .values_list("promotionrule_id", "channel_id")
    )

    rule_to_channels_map = defaultdict(set)
    for promotionrule_id, channel_id in promotion_channel_qs.iterator():
        rule_to_channels_map[promotionrule_id].add(channel_id)
    channel_to_products_map = defaultdict(set)
    for rule_to_variant in rule_to_variant_list:
        channel_ids = rule_to_channels_map[rule_to_variant.promotionrule_id]
        for channel_id in channel_ids:
            product_id = variant_id_to_product_id_map[rule_to_variant.productvariant_id]
            channel_to_products_map[channel_id].add(product_id)

    return channel_to_products_map


def _get_existing_rule_variant_list(rules: QuerySet[PromotionRule]):
    PromotionRuleVariant = PromotionRule.variants.through
    existing_rules_variants = (
        PromotionRuleVariant.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(Exists(rules.filter(pk=OuterRef("promotionrule_id"))))
        .all()
        .values_list(
            "promotionrule_id",
            "productvariant_id",
        )
    )
    return [
        PromotionRuleVariant(promotionrule_id=rule_id, productvariant_id=variant_id)
        for rule_id, variant_id in existing_rules_variants
    ]


@app.task
def update_variant_relations_for_active_promotion_rules_task():
    promotions = (
        Promotion.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .active()
        .filter(type=PromotionType.CATALOGUE)
    )

    rules = (
        PromotionRule.objects.order_by("id")
        .using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(
            Exists(promotions.filter(id=OuterRef("promotion_id"))), variants_dirty=True
        )
        .exclude(
            Q(reward_value__isnull=True) | Q(reward_value=0) | Q(catalogue_predicate={})
        )[:PROMOTION_RULE_BATCH_SIZE]
    )
    if ids := list(rules.values_list("pk", flat=True)):
        # fetch rules to get a qs without slicing
        rules = PromotionRule.objects.using(
            settings.DATABASE_CONNECTION_REPLICA_NAME
        ).filter(pk__in=ids)

        # Fetch existing variant relations to also mark products which are no longer
        # in the promotion as dirty
        existing_variant_relation = _get_existing_rule_variant_list(rules)

        new_rule_to_variant_list = fetch_variants_for_promotion_rules(
            rules=rules,
            database_connection_name=settings.DATABASE_CONNECTION_REPLICA_NAME,
        )
        channel_to_product_map = _get_channel_to_products_map(
            existing_variant_relation + new_rule_to_variant_list
        )
        with transaction.atomic():
            promotion_rule_ids = list(
                PromotionRule.objects.select_for_update(of=("self",))
                .filter(pk__in=ids, variants_dirty=True)
                .order_by("pk")
                .values_list("id", flat=True)
            )
            PromotionRule.objects.filter(pk__in=promotion_rule_ids).update(
                variants_dirty=False
            )

        mark_products_in_channels_as_dirty(channel_to_product_map, allow_replica=True)
        update_variant_relations_for_active_promotion_rules_task.delay()


@app.task
def update_products_discounted_prices_for_promotion_task(
    product_ids: Iterable[int],
    start_id: Optional[UUID] = None,
    *,
    rule_ids: Optional[list[UUID]] = None,
):
    # FIXME: Should be removed in Saleor 3.21

    # In case of triggered the task by old server worker, mark all active promotions as
    # dirty. This will make the same re-calculation as the old task.
    PromotionRule.objects.filter(variants_dirty=False).update(variants_dirty=True)


@app.task
def recalculate_discounted_price_for_products_task():
    """Recalculate discounted price for products."""
    listings = (
        ProductChannelListing.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(discounted_price_dirty=True)
        .order_by("id")[:DISCOUNTED_PRODUCT_BATCH]
    )
    listing_details = listings.values_list(
        "id",
        "product_id",
    )
    products_ids = set([product_id for _, product_id in listing_details])
    listing_ids = set([listing_id for listing_id, _ in listing_details])
    if products_ids:
        products = Product.objects.using(
            settings.DATABASE_CONNECTION_REPLICA_NAME
        ).filter(id__in=products_ids)
        update_discounted_prices_for_promotion(products, only_dirty_products=True)
        with transaction.atomic():
            channel_listings_ids = list(
                ProductChannelListing.objects.select_for_update(of=("self",))
                .filter(id__in=listing_ids, discounted_price_dirty=True)
                .order_by("pk")
                .values_list("id", flat=True)
            )
            ProductChannelListing.objects.filter(id__in=channel_listings_ids).update(
                discounted_price_dirty=False
            )
        recalculate_discounted_price_for_products_task.delay()


@app.task
def update_discounted_prices_task(product_ids: Iterable[int]):
    # FIXME: Should be removed in Saleor 3.21

    # in case triggering the task by old server worker, we will just mark the products
    # as dirty. The recalculation will happen in the background.
    ProductChannelListing.objects.filter(product_id__in=product_ids).update(
        discounted_price_dirty=True
    )


@app.task
def deactivate_preorder_for_variants_task():
    variants_to_clean = _get_preorder_variants_to_clean()

    for variant in variants_to_clean:
        try:
            deactivate_preorder_for_variant(variant)
        except PreorderAllocationError as e:
            task_logger.warning(str(e))


def _get_preorder_variants_to_clean():
    return ProductVariant.objects.filter(
        is_preorder=True, preorder_end_date__lt=timezone.now()
    )


@app.task(
    queue=settings.UPDATE_SEARCH_VECTOR_INDEX_QUEUE_NAME,
    expires=settings.BEAT_UPDATE_SEARCH_EXPIRE_AFTER_SEC,
)
def update_products_search_vector_task():
    products = (
        Product.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(search_index_dirty=True)
        .order_by("updated_at")[:PRODUCTS_BATCH_SIZE]
        .values_list("id", flat=True)
    )
    update_products_search_vector(products)


@app.task(queue=settings.COLLECTION_PRODUCT_UPDATED_QUEUE_NAME)
def collection_product_updated_task(product_ids):
    manager = get_plugins_manager(allow_replica=True)
    products = list(
        Product.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(id__in=product_ids)
        .prefetched_for_webhook(single_object=False)
    )
    replica_products_count = len(products)
    if replica_products_count != len(product_ids):
        products = list(
            Product.objects.filter(id__in=product_ids).prefetched_for_webhook(
                single_object=False
            )
        )
        if len(products) != replica_products_count:
            logger.warning(
                "collection_product_updated_task fetched %s products from replica, "
                "but %s from writer.",
                replica_products_count,
                len(products),
            )
    webhooks = get_webhooks_for_event(WebhookEventAsyncType.PRODUCT_UPDATED)
    for product in products:
        manager.product_updated(product, webhooks=webhooks)
