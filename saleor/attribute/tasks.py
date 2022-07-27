from celery.utils.log import get_task_logger
from django.db.models import Exists, OuterRef, Q

from ..attribute.models import AttributeValue
from ..celeryconf import app
from ..product.models import Product, ProductVariant
from ..product.search import update_products_search_vector

task_logger = get_task_logger(__name__)


@app.task
def update_associated_products_search_vector(attribute_value_pk: int):
    task_logger.info("Updating associated products search_vector")
    instance = AttributeValue.objects.get(pk=attribute_value_pk)
    variants = ProductVariant.objects.filter(
        Exists(instance.variantassignments.filter(variant_id=OuterRef("id")))
    )
    products = Product.objects.filter(
        Q(Exists(instance.productassignments.filter(product_id=OuterRef("id"))))
        | Q(Exists(variants.filter(product_id=OuterRef("id"))))
    )
    update_products_search_vector(products)
