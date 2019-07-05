from ..celeryconf import app
from ..discount.models import Sale
from .models import Attribute, ProductType, ProductVariant
from .utils.attributes import get_name_from_attributes
from .utils.variant_prices import (
    update_products_minimal_variant_prices,
    update_products_minimal_variant_prices_of_discount,
)


def _update_variants_names(instance, saved_attributes):
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
        "product__product_type__variant_attributes__values"
    ).all()
    attributes = instance.variant_attributes.prefetch_related("values__translations")
    for variant in variants_to_be_updated:
        variant.name = get_name_from_attributes(variant, attributes)
        variant.save(update_fields=["name"])


@app.task
def update_variants_names(product_type_pk, saved_attributes_ids):
    instance = ProductType.objects.get(pk=product_type_pk)
    saved_attributes = Attribute.objects.filter(pk__in=saved_attributes_ids)
    return _update_variants_names(instance, saved_attributes)


@app.task
def update_all_products_minimal_variant_prices_task():
    update_products_minimal_variant_prices()


@app.task
def update_products_minimal_variant_prices_of_discount_task(discount_pk):
    discount = Sale.objects.get(pk=discount_pk)
    update_products_minimal_variant_prices_of_discount(discount)
