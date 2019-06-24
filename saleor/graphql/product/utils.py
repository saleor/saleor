from collections import defaultdict
from typing import List

from django.utils.text import slugify

from ...product import AttributeInputType, models


def validate_attribute_input(instance: models.Attribute, values: List[str]):
    if instance.input_type != AttributeInputType.MULTISELECT and len(values) != 1:
        raise ValueError(f"A {instance.input_type} attribute must take only one value")


def attributes_to_json(attribute_value_input: List[dict], attributes_queryset):
    """Transform attributes to the HStore representation.

    Attributes configuration per product is stored in a HStore field as
    a dict of IDs. This function transforms the list of `AttributeValueInput`
    objects to this format.
    """
    attributes_map = {attr.slug: attr for attr in attributes_queryset}
    attributes_json = defaultdict(list)

    values_map = {}
    for attr in attributes_queryset:
        for value in attr.values.all():
            values_map[value.slug] = value.id

    for attribute_input in attribute_value_input:
        attr_slug = attribute_input.get("slug")
        if attr_slug not in attributes_map:
            raise ValueError(
                "Attribute %r doesn't belong to given product type." % (attr_slug,)
            )

        values = attribute_input.get("values")
        if not values:
            continue

        attribute = attributes_map[attr_slug]  # type: models.Attribute
        validate_attribute_input(attribute, values)

        for value in values:
            value_id = values_map.get(value)

            if value_id is None:
                # `value_id` was not found; create a new AttributeValue
                # instance from the provided `value`.
                obj = attribute.values.get_or_create(name=value, slug=slugify(value))[0]
                value_id = obj.pk

            attributes_json[str(attribute.pk)].append(str(value_id))

    return attributes_json
