import logging
from collections.abc import Iterable
from uuid import UUID

from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from ..attribute.models import Attribute
from ..celeryconf import app
from ..core.exceptions import PreorderAllocationError
from ..discount.models import Promotion, PromotionRule
from ..discount.utils import get_current_products_for_rules
from ..plugins.manager import get_plugins_manager
from ..warehouse.management import deactivate_preorder_for_variant
from ..webhook.event_types import WebhookEventAsyncType
from ..webhook.utils import get_webhooks_for_event
from .models import Product, ProductType, ProductVariant
from .search import PRODUCTS_BATCH_SIZE, update_products_search_vector
from .utils.variant_prices import update_discounted_prices_for_promotion
from .utils.variants import (
    fetch_variants_for_promotion_rules,
    generate_and_set_variant_name,
)

logger = logging.getLogger(__name__)
task_logger = get_task_logger(__name__)

VARIANTS_UPDATE_BATCH = 500
# Results in update time ~0.2s
DISCOUNTED_PRODUCT_BATCH = 2000
# Results in update time ~1.5s
PROMOTION_RULE_BATCH_SIZE = 250


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

    After change in attribute value name, for all product variants using this
    attributes we need to update the names.
    """
    initial_attributes = set(instance.variant_attributes.all())
    attributes_changed = initial_attributes.intersection(saved_attributes)
    if not attributes_changed:
        return

    variants = ProductVariant.objects.filter(
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
        instance = ProductType.objects.get(pk=product_type_pk)
    except ObjectDoesNotExist:
        logging.warning(f"Cannot find product type with id: {product_type_pk}.")
        return
    saved_attributes = Attribute.objects.filter(pk__in=saved_attributes_ids)
    _update_variants_names(instance, saved_attributes)


@app.task
def update_products_discounted_prices_of_promotion_task(promotion_pk: UUID):
    from ..graphql.discount.utils import get_products_for_promotion

    try:
        promotion = Promotion.objects.get(pk=promotion_pk)
    except ObjectDoesNotExist:
        logging.warning(f"Cannot find promotion with id: {promotion_pk}.")
        return
    previous_products = get_current_products_for_rules(promotion.rules.all())
    products = get_products_for_promotion(promotion, update_rule_variants=True)
    products |= previous_products
    update_discounted_prices_task.delay(list(products.values_list("id", flat=True)))


@app.task
def update_products_discounted_prices_for_promotion_task(
    product_ids: Iterable[int],
    start_id: UUID | None = None,
    *,
    rule_ids: list[UUID] | None = None,
):
    """Update the product discounted prices for given product ids.

    Firstly the promotion rule variants are recalculated, then the products discounted
    prices are calculated.
    """
    promotions = Promotion.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).active()
    kwargs = {"id__gt": start_id} if start_id else {}
    if rule_ids:
        kwargs["id__in"] = rule_ids  # type: ignore[assignment]
    rules = (
        PromotionRule.objects.order_by("id")
        .using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(Exists(promotions.filter(id=OuterRef("promotion_id"))), **kwargs)
        .exclude(Q(reward_value__isnull=True) | Q(reward_value=0))[
            :PROMOTION_RULE_BATCH_SIZE
        ]
    )
    if ids := list(rules.values_list("pk", flat=True)):
        qs = PromotionRule.objects.filter(pk__in=ids).exclude(
            Q(reward_value__isnull=True) | Q(reward_value=0)
        )
        fetch_variants_for_promotion_rules(rules=qs)
        update_products_discounted_prices_for_promotion_task.delay(
            product_ids, ids[-1], rule_ids=rule_ids
        )
    else:
        # when all promotion rules variants are up to date, call discounted prices
        # recalculation for products
        update_discounted_prices_task.delay(product_ids)


@app.task
def update_discounted_prices_task(product_ids: Iterable[int]):
    """Update the product discounted prices for given product ids."""
    ids = sorted(product_ids)[:DISCOUNTED_PRODUCT_BATCH]
    qs = Product.objects.filter(pk__in=ids)
    if ids:
        update_discounted_prices_for_promotion(qs)
        remaining_ids = list(set(product_ids) - set(ids))
        update_discounted_prices_task.delay(remaining_ids)


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
    products = Product.objects.filter(search_index_dirty=True).order_by()[
        :PRODUCTS_BATCH_SIZE
    ]
    update_products_search_vector(products, use_batches=False)


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
