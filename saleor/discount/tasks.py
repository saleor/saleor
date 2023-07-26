from datetime import datetime

import pytz
from celery.utils.log import get_task_logger
from django.db.models import Exists, F, OuterRef, Q, QuerySet

from ..celeryconf import app
from ..graphql.discount.utils import get_variants_for_predicate
from ..plugins.manager import get_plugins_manager
from ..product.models import Product, ProductVariant
from ..product.tasks import update_products_discounted_prices_for_promotion_task
from .models import Promotion, PromotionRule

task_logger = get_task_logger(__name__)


@app.task
def handle_promotion_toggle():
    """Send the notification about promotion toggle and recalculate discounted prices.

    Send the notifications about starting or ending promotions and call recalculation
    of product discounted prices.
    """
    manager = get_plugins_manager()

    staring_promotions = get_starting_promotions()
    ending_promotions = get_ending_promotions()

    if not staring_promotions or not ending_promotions:
        return

    promotions = staring_promotions | ending_promotions
    product_ids = fetch_promotion_product_ids(promotions)

    for staring_promo in staring_promotions:
        manager.promotion_started(staring_promo)

    for ending_promo in ending_promotions:
        manager.promotion_ended(ending_promo)

    if product_ids:
        # Recalculate discounts of affected products
        update_products_discounted_prices_for_promotion_task.delay(product_ids)

    starting_promotion_ids = ", ".join(
        [str(staring_promo.id) for staring_promo in staring_promotions]
    )
    ending_promotions_ids = ", ".join(
        [str(ending_promo.id) for ending_promo in ending_promotions]
    )

    promotions.update(last_notification_scheduled_at=datetime.now(pytz.UTC))

    task_logger.info(
        "The promotion_started webhook sent for Promotions with ids: %s",
        starting_promotion_ids,
    )
    task_logger.info(
        "The promotion_ended webhook sent for Promotions with ids: %s",
        ending_promotions_ids,
    )


def get_starting_promotions():
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
    return promotions


def get_ending_promotions():
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
    return promotions


def fetch_promotion_product_ids(promotions: "QuerySet[Promotion]"):
    """Fetch products that are included in the given promotions."""
    variants = ProductVariant.objects.none()
    rules = PromotionRule.objects.filter(
        Exists(promotions.filter(id=OuterRef("promotion_id")))
    )
    for rule in rules:
        variants |= get_variants_for_predicate(rule.catalogue_predicate)
    products = Product.objects.filter(
        Exists(variants.filter(product_id=OuterRef("id")))
    )
    return products.values_list("id", flat=True)
