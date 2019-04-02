from django.utils.text import slugify

from ...product.models import Attribute, AttributeValue


def attributes_to_hstore(attribute_value_input, attributes_queryset):
    """Transform attributes to the HStore representation.

    Attributes configuration per product is stored in a HStore field as
    a dict of IDs. This function transforms the list of `AttributeValueInput`
    objects to this format.
    """
    attributes_map = {attr.slug: attr.id for attr in attributes_queryset}

    attributes_hstore = {}
    values_map = dict(
        AttributeValue.objects.values_list('slug', 'id'))

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
            # `value_id` was not found; create a new AttributeValue
            # instance from the provided `value`.
            attr_instance = Attribute.objects.get(slug=attr_slug)
            obj = attr_instance.values.get_or_create(
                name=value, slug=slugify(value))[0]
            value_id = obj.pk

        attributes_hstore[str(attribute_id)] = str(value_id)

    return attributes_hstore
