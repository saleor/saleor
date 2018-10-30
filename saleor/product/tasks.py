from celery import shared_task

from .models import ProductVariant
from .utils.attributes import get_name_from_attributes


def _update_variants_names(instance, saved_attributes):
    """After change in attribute value name, all product variant names
    should be updated. Products variant name created from attribute
    names of variants."""
    initial_attributes = set(instance.variant_attributes.all())
    attributes_changed = initial_attributes.intersection(saved_attributes)
    if not attributes_changed:
        return
    variants_to_be_updated = ProductVariant.objects.filter(
        product__in=instance.products.all(),
        product__product_type__variant_attributes__in=attributes_changed)
    variants_to_be_updated = variants_to_be_updated.prefetch_related(
        'product__product_type__variant_attributes__values').all()
    attributes = instance.variant_attributes.all()
    for variant in variants_to_be_updated:
        variant.name = get_name_from_attributes(variant, attributes)
        variant.save(update_fields=['name'])


@shared_task
def update_variants_names(instance, saved_attributes):
    return _update_variants_names(instance, saved_attributes)
