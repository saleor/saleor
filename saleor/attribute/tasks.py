from celery.utils.log import get_task_logger
from django.db.models import Exists, Max, OuterRef, Q

from ..attribute.models import AttributeValue
from ..celeryconf import app
from ..product.models import Product, ProductVariant
from .models import Attribute

task_logger = get_task_logger(__name__)


@app.task
def update_associated_products_search_vector(attribute_value_pk: int):
    try:
        instance = AttributeValue.objects.get(pk=attribute_value_pk)
    except AttributeValue.DoesNotExist:
        task_logger.warning(
            (
                "Could not perform search_vector update on associated products as "
                'AttributeValue with pk "%s" does not exists.'
            ),
            attribute_value_pk,
        )
        return

    variants = ProductVariant.objects.filter(
        Exists(instance.variantassignments.filter(variant_id=OuterRef("id")))
    )
    Product.objects.filter(
        Q(Exists(instance.productassignments.filter(product_id=OuterRef("id"))))
        | Q(Exists(variants.filter(product_id=OuterRef("id"))))
    ).update(search_index_dirty=True)


@app.task()
def setup_max_sort_order():
    for attribute in Attribute.objects.filter(max_sort_order=None).iterator():
        attribute.max_sort_order = attribute.values.aggregate(Max("sort_order")).get(
            "sort_order__max"
        )
        attribute.save(update_fields=["max_sort_order"])
