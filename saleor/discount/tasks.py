from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING

import graphene
import pytz
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db.models import Exists, F, OuterRef, Q, QuerySet

from ..celeryconf import app
from ..graphql.discount.utils import get_variants_for_catalogue_predicate
from ..order import OrderStatus
from ..order.models import Order, OrderLine
from ..plugins.manager import get_plugins_manager
from ..product.models import (
    Product,
    ProductVariant,
    ProductVariantChannelListing,
    VariantChannelListingPromotionRule,
)
from ..product.utils.product import mark_products_in_channels_as_dirty_based_on_rules
from ..product.utils.variant_prices import update_discounted_prices_for_promotion
from ..webhook.event_types import WebhookEventAsyncType
from ..webhook.utils import get_webhooks_for_event
from . import DiscountType
from .models import (
    OrderDiscount,
    OrderLineDiscount,
    Promotion,
    PromotionRule,
    VoucherCode,
)
from .utils.promotion import mark_catalogue_promotion_rules_as_dirty

if TYPE_CHECKING:
    from uuid import UUID

# Results in update time ~0.1s
EXPIRED_RULES_BATCH_SIZE = 5000

task_logger = get_task_logger(__name__)
# Batch of size 100 takes ~1 sec and consumes ~3mb at peak
PROMOTION_TOGGLE_BATCH_SIZE = 100


@app.task
def handle_promotion_toggle():
    """Send the notification about promotion toggle and recalculate discounted prices.

    Send the notifications about starting or ending promotions and call recalculation
    of product discounted prices.
    """
    manager = get_plugins_manager(allow_replica=False)

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

    started_webhooks = get_webhooks_for_event(WebhookEventAsyncType.PROMOTION_STARTED)
    for starting_promo in starting_promotions:
        manager.promotion_started(starting_promo, webhooks=started_webhooks)

    ended_webhooks = get_webhooks_for_event(WebhookEventAsyncType.PROMOTION_ENDED)
    for ending_promo in ending_promotions:
        manager.promotion_ended(ending_promo, webhooks=ended_webhooks)

    toggle_webhooks = get_webhooks_for_event(WebhookEventAsyncType.SALE_TOGGLE)
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
        manager.sale_toggle(promotion, catalogues, webhooks=toggle_webhooks)

    if ending_promotions:
        clear_promotion_rule_variants_task.delay()

    mark_catalogue_promotion_rules_as_dirty(
        set(promotions.values_list("id", flat=True))
    )

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
            Q(last_notification_scheduled_at__isnull=True)
            | Q(last_notification_scheduled_at__lt=F("start_date"))
        )
        & Q(start_date__lte=now)
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
            Q(last_notification_scheduled_at__isnull=True)
            | Q(last_notification_scheduled_at__lt=F("end_date"))
        )
        & Q(end_date__lte=now)
    )
    if batch:
        return promotions[:PROMOTION_TOGGLE_BATCH_SIZE]
    return promotions


def fetch_promotion_variants_and_product_ids(promotions: "QuerySet[Promotion]"):
    """Fetch products that are included in the given promotions."""
    promotion_id_to_variants: dict[UUID, QuerySet] = defaultdict(
        lambda: ProductVariant.objects.none()
    )
    variants = ProductVariant.objects.none()
    rules = PromotionRule.objects.filter(
        Exists(promotions.filter(id=OuterRef("promotion_id")))
    )
    for rule in rules:
        rule_variants = get_variants_for_catalogue_predicate(rule.catalogue_predicate)
        variants |= rule_variants
        promotion_id_to_variants[rule.promotion_id] |= rule_variants
    products = Product.objects.filter(
        Exists(variants.filter(product_id=OuterRef("id")))
    )
    return promotion_id_to_variants, list(products.values_list("id", flat=True))


@app.task
def clear_promotion_rule_variants_task():
    """Clear all promotion rule variants."""
    promotions = Promotion.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).expired()
    rules = PromotionRule.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).filter(Exists(promotions.filter(id=OuterRef("promotion_id"))))
    PromotionRuleVariant = PromotionRule.variants.through
    rule_variants_id = list(
        PromotionRuleVariant.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(Exists(rules.filter(pk=OuterRef("promotionrule_id"))))[
            :EXPIRED_RULES_BATCH_SIZE
        ]
        .values_list("pk", flat=True)
    )
    if rule_variants_id:
        mark_products_in_channels_as_dirty_based_on_rules(rules, allow_replica=True)
        PromotionRuleVariant.objects.filter(pk__in=rule_variants_id).delete()
        clear_promotion_rule_variants_task.delay()


def decrease_voucher_code_usage_of_draft_orders(channel_id: int):
    codes = Order.objects.filter(
        channel_id=channel_id, status=OrderStatus.DRAFT, voucher_code__isnull=False
    ).values_list("voucher_code", flat=True)
    voucher_code_ids = VoucherCode.objects.filter(code__in=codes).values_list(
        "pk", flat=True
    )
    decrease_voucher_codes_usage_task.delay(list(voucher_code_ids))


@app.task
def decrease_voucher_codes_usage_task(voucher_code_ids):
    # Batch of size 1000 takes ~1sec and consumes ~20mb at peak
    BATCH_SIZE = 1000
    ids = voucher_code_ids[:BATCH_SIZE]
    if (
        voucher_codes := VoucherCode.objects.filter(pk__in=ids)
        .select_related("voucher")
        .only("voucher", "used", "is_active")
    ):
        for voucher_code in voucher_codes:
            if voucher_code.voucher.usage_limit and voucher_code.used > 0:
                voucher_code.used = F("used") - 1
            if voucher_code.voucher.single_use:
                voucher_code.is_active = True
        VoucherCode.objects.bulk_update(voucher_codes, ["used", "is_active"])
        if remaining_ids := list(set(voucher_code_ids) - set(ids)):
            decrease_voucher_codes_usage_task.delay(remaining_ids)


def disconnect_voucher_codes_from_draft_orders(channel_id: int):
    order_ids = Order.objects.filter(
        channel_id=channel_id, status=OrderStatus.DRAFT, voucher_code__isnull=False
    ).values_list("pk", flat=True)
    disconnect_voucher_codes_from_draft_orders_task.delay(list(order_ids))


@app.task
def disconnect_voucher_codes_from_draft_orders_task(order_ids):
    # Batch of size 1000 takes ~1sec and consumes ~20mb at peak
    BATCH_SIZE = 1000
    ids = order_ids[:BATCH_SIZE]
    if orders := Order.objects.filter(pk__in=ids).only(
        "voucher_code", "should_refresh_prices"
    ):
        for order in orders:
            order.voucher_code = None
            order.should_refresh_prices = True
        Order.objects.bulk_update(orders, ["voucher_code", "should_refresh_prices"])
        OrderDiscount.objects.filter(order_id__in=ids).filter(
            type=DiscountType.VOUCHER
        ).delete()
        OrderLineDiscount.objects.filter(
            Exists(OrderLine.objects.filter(order_id__in=order_ids))
        ).filter(type=DiscountType.VOUCHER).delete()
        if remaining_ids := list(set(order_ids) - set(ids)):
            disconnect_voucher_codes_from_draft_orders_task.delay(remaining_ids)


@app.task(
    name="saleor.discount.migrations.tasks.saleor3_17.update_discounted_prices_task"
)
def update_discounted_prices_task():
    """Recalculate discounted prices during sale to promotion migration."""
    # WARNING: this function is run during `0047_migrate_sales_to_promotions` migration,
    # so please be careful while updating.
    # This task can be deleted after we introduce a different process for calculating
    # discounted prices for promotions.

    # For 100 rules, with 1000 variants for each rule it takes around 15s
    BATCH_SIZE = 100
    variant_listing_qs = (
        ProductVariantChannelListing.objects.annotate(
            discount=F("price_amount") - F("discounted_price_amount")
        )
        .filter(discount__gt=0)
        .filter(
            ~Exists(
                VariantChannelListingPromotionRule.objects.filter(
                    variant_channel_listing_id=OuterRef("id")
                )
            )
        )
    )
    variant_qs = ProductVariant.objects.filter(
        Exists(variant_listing_qs.filter(variant_id=OuterRef("id")))
    )
    products_ids = Product.objects.filter(
        Exists(variant_qs.filter(product_id=OuterRef("id")))
    ).values_list("id", flat=True)[:BATCH_SIZE]
    if products_ids:
        products = Product.objects.filter(id__in=products_ids)
        update_discounted_prices_for_promotion(products)


@app.task(
    name="saleor.discount.migrations.tasks.saleor3_17.set_promotion_rule_variants"
)
def set_promotion_rule_variants_task(start_id=None):
    # WARNING: this function is run during `0067_fulfill_promotionrule_variants`
    # migration, be careful while updating.
    # This task can be deleted after we introduce a different process for calculating
    # discounted prices for promotions.

    # Results in update time ~0.4s and consumes ~20MB memory at peak
    from ..product.utils.variants import fetch_variants_for_promotion_rules

    PROMOTION_RULE_BATCH_SIZE = 250

    promotions = Promotion.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).active()
    kwargs = {"id__gt": start_id} if start_id else {}
    rules = (
        PromotionRule.objects.order_by("id")
        .using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(Exists(promotions.filter(id=OuterRef("promotion_id"))), **kwargs)[
            :PROMOTION_RULE_BATCH_SIZE
        ]
    )
    if ids := list(rules.values_list("pk", flat=True)):
        qs = PromotionRule.objects.filter(pk__in=ids)
        fetch_variants_for_promotion_rules(rules=qs)
        set_promotion_rule_variants_task.delay(ids[-1])
