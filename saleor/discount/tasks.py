from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING, Dict

import graphene
import pytz
from celery.utils.log import get_task_logger
from django.db.models import Exists, F, OuterRef, Q, QuerySet

from ..celeryconf import app
from ..graphql.discount.utils import get_variants_for_predicate
from ..plugins.manager import get_plugins_manager
from ..product.models import Product, ProductVariant
from ..product.tasks import update_products_discounted_prices_for_promotion_task
from .models import Promotion, PromotionRule

if TYPE_CHECKING:
    from uuid import UUID

task_logger = get_task_logger(__name__)
# Batch of size 100 takes ~1 sec and consumes ~3mb at peak
PROMOTION_TOGGLE_BATCH_SIZE = 100


# DEPRECATED: To remove in 3.18
@app.task
def handle_sale_toggle():
    pass


@app.task
def handle_promotion_toggle():
    """Send the notification about promotion toggle and recalculate discounted prices.

    Send the notifications about starting or ending promotions and call recalculation
    of product discounted prices.
    """
    manager = get_plugins_manager()

    starting_promotions = get_starting_promotions(batch=True)
    ending_promotions = get_ending_promotions(batch=True)
    promotion_ids = [
        promotion.id for promotion in starting_promotions | ending_promotions
    ][:PROMOTION_TOGGLE_BATCH_SIZE]
    starting_promotions = [
        promotion for promotion in starting_promotions if promotion.id in promotion_ids
    ]
    ending_promotions = [
        promotion for promotion in ending_promotions if promotion.id in promotion_ids
    ]
    promotions = Promotion.objects.filter(id__in=promotion_ids).all()
    promotion_id_to_variants, product_ids = fetch_promotion_variants_and_product_ids(
        promotions
    )

    for starting_promo in starting_promotions:
        manager.promotion_started(starting_promo)

    for ending_promo in ending_promotions:
        manager.promotion_ended(ending_promo)

    # DEPRECATED: will be removed in Saleor 4.0.
    for promotion in promotions:
        variants = promotion_id_to_variants.get(promotion.id)
        catalogues = {
            "variants": [
                graphene.Node.to_global_id("ProductVariant", v.pk) for v in variants
            ]
            if variants
            else [],
            "products": [],
            "categories": [],
            "collections": [],
        }
        manager.sale_toggle(promotion, catalogues)

    if product_ids:
        # Recalculate discounts of affected products
        update_products_discounted_prices_for_promotion_task.delay(product_ids)

    starting_promotion_ids = ", ".join(
        [str(staring_promo.id) for staring_promo in starting_promotions]
    )
    ending_promotions_ids = ", ".join(
        [str(ending_promo.id) for ending_promo in ending_promotions]
    )

    # DEPRECATED: will be removed in Saleor 4.0.
    promotion_ids_str = ", ".join([str(promo.id) for promo in promotions])

    promotions.update(last_notification_scheduled_at=datetime.now(pytz.UTC))
    if starting_promotion_ids:
        task_logger.info(
            "The promotion_started webhook sent for Promotions with ids: %s",
            starting_promotion_ids,
        )
    if ending_promotions_ids:
        task_logger.info(
            "The promotion_ended webhook sent for Promotions with ids: %s",
            ending_promotions_ids,
        )

    # DEPRECATED: will be removed in Saleor 4.0.
    task_logger.info(
        "The sale_toggle webhook sent for sales with ids: %s", promotion_ids_str
    )


def get_starting_promotions(batch=False):
    """Return promotions for which the notify about starting should be sent.

    The notification should be sent for promotions for which the start date has passed
    and the notification date is null or the last notification was sent
    before the start date.
    """
    now = datetime.now(pytz.UTC)
    promotions = Promotion.objects.filter(
        (
            (
                Q(last_notification_scheduled_at__isnull=True)
                | Q(last_notification_scheduled_at__lt=F("start_date"))
            )
            & Q(start_date__lte=now)
        )
    )
    if batch:
        return promotions.all()[:PROMOTION_TOGGLE_BATCH_SIZE]
    return promotions


def get_ending_promotions(batch=False):
    """Return promotions for which the notify about ending should be sent.

    The notification should be sent for promotions for which the end date has passed
    and the notification date is null or the last notification was sent
    before the end date.
    """
    now = datetime.now(pytz.UTC)
    promotions = Promotion.objects.filter(
        (
            (
                Q(last_notification_scheduled_at__isnull=True)
                | Q(last_notification_scheduled_at__lt=F("end_date"))
            )
            & Q(end_date__lte=now)
        )
    )
    if batch:
        return promotions[:PROMOTION_TOGGLE_BATCH_SIZE]
    return promotions


def fetch_promotion_variants_and_product_ids(promotions: "QuerySet[Promotion]"):
    """Fetch products that are included in the given promotions."""
    promotion_id_to_variants: Dict[UUID, "QuerySet"] = defaultdict(
        lambda: ProductVariant.objects.none()
    )
    variants = ProductVariant.objects.none()
    rules = PromotionRule.objects.filter(
        Exists(promotions.filter(id=OuterRef("promotion_id")))
    )
    for rule in rules:
        rule_variants = get_variants_for_predicate(rule.catalogue_predicate)
        variants |= rule_variants
        promotion_id_to_variants[rule.promotion_id] |= rule_variants
    products = Product.objects.filter(
        Exists(variants.filter(product_id=OuterRef("id")))
    )
    return promotion_id_to_variants, list(products.values_list("id", flat=True))
