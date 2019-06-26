from collections import defaultdict
from typing import List

from django.utils.text import slugify

from ...product import AttributeInputType, models


def validate_attribute_input(instance: models.Attribute, values: List[str]):
    if not values:
        if not instance.value_required:
            return
        raise ValueError(f"{instance.slug} expects a value but none were given")

    if instance.input_type != AttributeInputType.MULTISELECT and len(values) != 1:
        raise ValueError(f"A {instance.input_type} attribute must take only one value")


def attributes_to_json(attribute_value_input: List[dict], attributes_queryset):
    """Transform attributes to the HStore representation.

    Attributes configuration per product is stored in a HStore field as
    a dict of IDs. This function transforms the list of `AttributeValueInput`
    objects to this format.
    """
    attributes_map_by_slug = {}
    attributes_map_by_id = {}

    for attr in attributes_queryset:
        attributes_map_by_slug[attr.slug] = attr
        attributes_map_by_id[attr.id] = attr

    attributes_json = defaultdict(list)
    passed_slugs = set()

    values_map = {}
    for attr in attributes_queryset:
        for value in attr.values.all():
            values_map[value.slug] = value.id

    for attribute_input in attribute_value_input:
        if "slug" in attribute_input:
            attribute = attributes_map_by_slug.get(attribute_input["slug"])
        elif "id" in attribute_input:
            attribute = attributes_map_by_id.get(attribute_input["id"])
        else:
            raise ValueError("The value ID or slug was not provided")

        if not attribute:
            raise ValueError(
                "The given attribute doesn't belong to given product type."
            )

        passed_slugs.add(attribute.slug)

        values = attribute_input.get("values")
        validate_attribute_input(attribute, values)

        for value in values:
            value_id = values_map.get(value)

            if value_id is None:
                # `value_id` was not found; create a new AttributeValue
                # instance from the provided `value`.
                obj = attribute.values.get_or_create(name=value, slug=slugify(value))[0]
                value_id = obj.pk

            attributes_json[str(attribute.pk)].append(str(value_id))

    # Check that all required attributes were passed
    for missing_slug in attributes_map_by_slug.keys() ^ passed_slugs:
        attribute = attributes_map_by_slug[missing_slug]  # type: models.Attribute
        validate_attribute_input(attribute, [])

    return attributes_json
