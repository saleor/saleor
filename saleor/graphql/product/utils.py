from django.utils.text import slugify

from ...product.models import (
    AttributeChoiceValue, ProductAttribute, ProductVariant)
from ...product.utils.attributes import get_name_from_attributes


def attributes_to_hstore(attribute_value_input, attributes_queryset):
    """Transform attributes to the HStore representation.

    Attributes configuration per product is stored in a HStore field as
    a dict of IDs. This function transforms the list of `AttributeValueInput`
    objects to this format.
    """
    attributes_map = {attr.slug: attr.id for attr in attributes_queryset}

    attributes_hstore = {}
    values_map = dict(
        AttributeChoiceValue.objects.values_list('slug', 'id'))

    for attribute in attribute_value_input:
        attr_slug = attribute.get('slug')
        if attr_slug not in attributes_map:
            raise ValueError(
                'Attribute %r doesn\'t belong to given product type.' % (
                    attr_slug,))

        value = attribute.get('value')
        if not value:
            continue

        attribute_id = attributes_map[attr_slug]
        value_id = values_map.get(value)

        if value_id is None:
            # `value_id` was not found; create a new AttributeChoiceValue
            # instance from the provided `value`.
            attr_instance = ProductAttribute.objects.get(slug=attr_slug)
            obj = attr_instance.values.get_or_create(
                name=value, slug=slugify(value))[0]
            value_id = obj.pk

        attributes_hstore[str(attribute_id)] = str(value_id)

    return attributes_hstore


def update_variants_names(instance, saved_attributes):
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
        variant.save()
