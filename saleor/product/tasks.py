import json
import logging
from typing import Iterable, List, Optional

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from ..attribute.models import Attribute
from ..celeryconf import app
from ..discount.models import Sale
from ..warehouse.management import deactivate_preorder_for_variant
from .models import Product, ProductType, ProductVariant
from .utils.variant_prices import (
    update_product_discounted_price,
    update_products_discounted_prices,
    update_products_discounted_prices_of_catalogues,
    update_products_discounted_prices_of_discount,
)
from .utils.variants import generate_and_set_variant_name

logger = logging.getLogger(__name__)


def _update_variants_names(instance: ProductType, saved_attributes: Iterable):
    """Product variant names are created from names of assigned attributes.

    After change in attribute value name, for all product variants using this
    attributes we need to update the names.
    """
    initial_attributes = set(instance.variant_attributes.all())
    attributes_changed = initial_attributes.intersection(saved_attributes)
    if not attributes_changed:
        return
    variants_to_be_updated = ProductVariant.objects.filter(
        product__in=instance.products.all(),
        product__product_type__variant_attributes__in=attributes_changed,
    )
    variants_to_be_updated = variants_to_be_updated.prefetch_related(
        "attributes__values__translations"
    ).all()
    for variant in variants_to_be_updated:
        generate_and_set_variant_name(variant, variant.sku)


@app.task
def update_variants_names(product_type_pk: int, saved_attributes_ids: List[int]):
    try:
        instance = ProductType.objects.get(pk=product_type_pk)
    except ObjectDoesNotExist:
        logging.warning(f"Cannot find product type with id: {product_type_pk}.")
        return
    saved_attributes = Attribute.objects.filter(pk__in=saved_attributes_ids)
    _update_variants_names(instance, saved_attributes)


@app.task
def update_product_discounted_price_task(product_pk: int):
    try:
        product = Product.objects.get(pk=product_pk)
    except ObjectDoesNotExist:
        logging.warning(f"Cannot find product with id: {product_pk}.")
        return
    update_product_discounted_price(product)


@app.task
def update_products_discounted_prices_of_catalogues_task(
    product_ids: Optional[List[int]] = None,
    category_ids: Optional[List[int]] = None,
    collection_ids: Optional[List[int]] = None,
):
    update_products_discounted_prices_of_catalogues(
        product_ids, category_ids, collection_ids
    )


@app.task
def update_products_discounted_prices_of_discount_task(discount_pk: int):
    try:
        discount = Sale.objects.get(pk=discount_pk)
    except ObjectDoesNotExist:
        logging.warning(f"Cannot find discount with id: {discount_pk}.")
        return
    update_products_discounted_prices_of_discount(discount)


@app.task
def update_products_discounted_prices_task(product_ids: List[int]):
    products = Product.objects.filter(pk__in=product_ids)
    update_products_discounted_prices(products)


def schedule_deactivate_preorder_for_variant_task(product_variant: ProductVariant):
    """Schedule a task that will trigger preorder deactivation at preorder end date."""
    if not product_variant.is_preorder or product_variant.preorder_end_date is None:
        return
    end_time = product_variant.preorder_end_date.timetz()
    end_date = product_variant.preorder_end_date.date()
    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute=str(end_time.minute),
        hour=str(end_time.hour),
        day_of_week="*",
        day_of_month=str(end_date.day),
        month_of_year=str(end_date.month),
        timezone=product_variant.preorder_end_date.tzinfo,
    )
    PeriodicTask.objects.create(
        crontab=schedule,
        name=_get_deactivate_preorder_for_variant_task_name(product_variant.pk),
        task="saleor.product.tasks.deactivate_preorder_for_variant_task",
        args=json.dumps([product_variant.pk]),
    )


def deactivate_preorder_for_variant_task(product_variant_id: int):
    try:
        product_variant = ProductVariant.objects.get(pk=product_variant_id)
    except ProductVariant.DoesNotExist:
        delete_deactivate_preorder_for_variant_task(product_variant_id)
        return

    if (
        product_variant.preorder_end_date is not None
        and timezone.now().date() == product_variant.preorder_end_date.date()
    ):
        deactivate_preorder_for_variant(product_variant)

    delete_deactivate_preorder_for_variant_task(product_variant_id)


def delete_deactivate_preorder_for_variant_task(product_variant_id: int):
    """Remove previously scheduled task for product variant preorder deactivation."""
    periodic_task = (
        PeriodicTask.objects.filter(
            name=_get_deactivate_preorder_for_variant_task_name(product_variant_id)
        )
        .select_related("crontab")
        .first()
    )
    if not periodic_task:
        return

    crontab = periodic_task.crontab
    if crontab.periodictask_set.count() == 1:
        crontab.delete()
    else:
        periodic_task.delete()


def _get_deactivate_preorder_for_variant_task_name(product_variant_id: int) -> str:
    return f"deactivate-preorder-{product_variant_id}"
