import logging
from typing import Iterable, List, Optional
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
from ..product.models import Category, CollectionProduct
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
def update_variants_names(product_type_pk: int, saved_attributes_ids: List[int]):
    try:
        instance = ProductType.objects.get(pk=product_type_pk)
    except ObjectDoesNotExist:
        logging.warning(f"Cannot find product type with id: {product_type_pk}.")
        return
    saved_attributes = Attribute.objects.filter(pk__in=saved_attributes_ids)
    _update_variants_names(instance, saved_attributes)


# DEPRECATED: To remove in 3.18
@app.task
def update_product_discounted_price_task(product_pk: int):
    products = Product.objects.filter(pk=product_pk)
    if not products:
        logging.warning(f"Cannot find product with id: {product_pk}.")
        return
    update_discounted_prices_for_promotion(products)


# DEPRECATED: To remove in 3.18
@app.task
def update_products_discounted_prices_of_catalogues_task(
    product_ids: Optional[List[int]] = None,
    category_ids: Optional[List[int]] = None,
    collection_ids: Optional[List[int]] = None,
    variant_ids: Optional[List[int]] = None,
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
    update_discounted_prices_for_promotion(products)


# DEPRECATED: To remove in 3.18
@app.task
def update_products_discounted_prices_of_sale_task(discount_pk: int):
    try:
        promotion = Promotion.objects.get(old_sale_id=discount_pk)
    except ObjectDoesNotExist:
        logging.warning(f"Cannot find discount with id: {discount_pk}.")
        return
    update_products_discounted_prices_of_promotion_task(promotion.id)


# DEPRECATED: To remove in 3.18
@app.task
def update_products_discounted_prices_task(product_ids: List[int]):
    products = Product.objects.filter(pk__in=product_ids)
    update_discounted_prices_for_promotion(products)


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
    product_ids: Iterable[int], start_id: Optional[UUID] = None
):
    """Update the product discounted prices for given product ids.

    Firstly the promotion rule variants are recalculated, then the products discounted
    prices are calculated.
    """
    promotions = Promotion.objects.active()
    kwargs = {"id__gt": start_id} if start_id else {}
    rules = PromotionRule.objects.order_by("id").filter(
        Exists(promotions.filter(id=OuterRef("promotion_id"))), **kwargs
    )[:PROMOTION_RULE_BATCH_SIZE]
    if ids := list(rules.values_list("pk", flat=True)):
        qs = PromotionRule.objects.filter(pk__in=ids)
        fetch_variants_for_promotion_rules(rules=qs)
        update_products_discounted_prices_for_promotion_task.delay(product_ids, ids[-1])
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
    manager = get_plugins_manager()
    products = list(
        Product.objects.filter(id__in=product_ids).prefetched_for_webhook(
            single_object=False
        )
    )
    webhooks = get_webhooks_for_event(WebhookEventAsyncType.PRODUCT_UPDATED)
    for product in products:
        manager.product_updated(product, webhooks=webhooks)
