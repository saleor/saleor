from collections import defaultdict, namedtuple
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional

import graphene
from django.core.exceptions import ValidationError
from django.db import DatabaseError, transaction
from django.db.utils import IntegrityError

from ...core.tracing import traced_atomic_transaction
from ...order import OrderStatus
from ...order import models as order_models
from ...warehouse.models import Stock
from ..core.enums import ProductErrorCode

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from ...product.models import ProductVariant

import logging

logger = logging.getLogger(__name__)


def get_used_attribute_values_for_variant(variant):
    """Create a dict of attributes values for variant.

    Sample result is:
    {
        "attribute_1_global_id": ["ValueAttr1_1"],
        "attribute_2_global_id": ["ValueAttr2_1"]
    }
    """
    attribute_values = defaultdict(list)
    for assigned_variant_attribute in variant.attributes.all():
        attribute = assigned_variant_attribute.attribute
        attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
        for attr_value in assigned_variant_attribute.values.all():
            attribute_values[attribute_id].append(attr_value.slug)
    return attribute_values


def get_used_variants_attribute_values(product):
    """Create list of attributes values for all existing `ProductVariants` for product.

    Sample result is:
    [
        {
            "attribute_1_global_id": ["ValueAttr1_1"],
            "attribute_2_global_id": ["ValueAttr2_1"]
        },
        ...
        {
            "attribute_1_global_id": ["ValueAttr1_2"],
            "attribute_2_global_id": ["ValueAttr2_2"]
        }
    ]
    """
    variants = (
        product.variants.prefetch_related("attributes__values")
        .prefetch_related("attributes__assignment")
        .all()
    )
    used_attribute_values = []
    for variant in variants:
        attribute_values = get_used_attribute_values_for_variant(variant)
        if attribute_values:
            used_attribute_values.append(attribute_values)
    return used_attribute_values


@traced_atomic_transaction()
def create_stocks(
    variant: "ProductVariant", stocks_data: List[Dict[str, str]], warehouses: "QuerySet"
):
    try:
        new_stocks = Stock.objects.bulk_create(
            [
                Stock(
                    product_variant=variant,
                    warehouse=warehouse,
                    quantity=stock_data["quantity"],
                )
                for stock_data, warehouse in zip(stocks_data, warehouses)
            ]
        )
    except IntegrityError:
        msg = "Stock for one of warehouses already exists for this product variant."
        raise ValidationError(msg)
    return new_stocks


DraftOrderLinesData = namedtuple(
    "DraftOrderLinesData", ["order_to_lines_mapping", "line_pks", "order_pks"]
)


def get_draft_order_lines_data_for_variants(
    variant_ids: Iterable[int],
):
    lines = order_models.OrderLine.objects.filter(
        variant__id__in=variant_ids, order__status=OrderStatus.DRAFT
    ).select_related("order")
    order_to_lines_mapping: Dict[
        order_models.Order, List[order_models.OrderLine]
    ] = defaultdict(list)
    line_pks = set()
    order_pks = set()
    for line in lines:
        order_to_lines_mapping[line.order].append(line)
        line_pks.add(line.pk)
        order_pks.add(line.order_id)

    return DraftOrderLinesData(order_to_lines_mapping, line_pks, order_pks)


def clean_variant_sku(sku: Optional[str]) -> Optional[str]:
    if sku:
        return sku.strip() or None
    return None


def update_ordered_media(ordered_media):
    errors = defaultdict(list)
    with transaction.atomic():
        for order, media in enumerate(ordered_media):
            media.sort_order = order
            try:
                media.save(update_fields=["sort_order"])
            except DatabaseError as e:
                msg = (
                    "Cannot update media for instance: %s. "
                    "Updating not existing object. "
                    "Details: %s.",
                    media,
                    str(e),
                )
                logger.warning(msg)
                errors["media"].append(
                    ValidationError(msg, code=ProductErrorCode.NOT_FOUND.value)
                )

    if errors:
        raise ValidationError(errors)
