from collections import defaultdict
from typing import Dict, List

import graphene
from django.utils.text import slugify

from ...product import AttributeInputType, models
from .interfaces import ResolvedAttributeInput

attribute_input_type = List[ResolvedAttributeInput]
attribute_map_type = Dict[str, models.Attribute]


def validate_attribute_input(instance: models.Attribute, values: List[str]):
    if not values:
        if not instance.value_required:
            return
        raise ValueError(f"{instance.slug} expects a value but none were given")

    if instance.input_type != AttributeInputType.MULTISELECT and len(values) != 1:
        raise ValueError(f"A {instance.input_type} attribute must take only one value")


def _resolve_attributes_input(
    attribute_input: List[dict],
    attributes_map_by_slug: attribute_map_type,
    attributes_map_by_id: attribute_map_type,
) -> attribute_input_type:
    """Resolve a raw GraphQL input to proper attribute.

    Its job is to ensure a backward compatibility with passing attributes by slug.
    """

    resolved_input = []  # type: List[ResolvedAttributeInput]

    for attribute_input in attribute_input:
        if "slug" in attribute_input:
            attribute = attributes_map_by_slug.get(attribute_input["slug"])
        elif "id" in attribute_input:
            type_, attribute_id = graphene.Node.from_global_id(attribute_input["id"])
            if type_ != "Attribute":
                raise ValueError(f"Couldn't resolve to a node: {attribute_input['id']}")
            attribute = attributes_map_by_id.get(attribute_id)
        else:
            raise ValueError("The value ID or slug was not provided")

        if not attribute:
            raise ValueError(
                "The given attribute doesn't belong to given product type."
            )

        values = attribute_input.get("values")
        validate_attribute_input(attribute, values)

        resolved_input.append(ResolvedAttributeInput(instance=attribute, values=values))

    return resolved_input


def attributes_to_json(
    raw_input: List[dict], attributes_queryset
) -> Dict[str, List[str]]:
    """Transform attributes to the HStore representation.

    Attributes configuration per product is stored in a HStore field as
    a dict of IDs. This function transforms the list of `AttributeValueInput`
    objects to this format.
    """

    attributes_json = defaultdict(list)
    passed_slugs = set()

    attributes_map_by_slug = {}  # type: attribute_map_type
    attributes_map_by_id = {}  # type: attribute_map_type

    for attr in attributes_queryset:
        attributes_map_by_slug[attr.slug] = attr
        attributes_map_by_id[str(attr.id)] = attr

    resolved_input = _resolve_attributes_input(
        raw_input, attributes_map_by_slug, attributes_map_by_id
    )

    values_map = {}
    for attr in attributes_queryset:
        for value in attr.values.all():
            values_map[value.slug] = value.id

    for item in resolved_input:
        passed_slugs.add(item.instance.slug)

        for value in item.values:
            value_id = values_map.get(value)

            if value_id is None:
                # `value_id` was not found; create a new AttributeValue
                # instance from the provided `value`.
                obj = item.instance.values.get_or_create(
                    name=value, slug=slugify(value)
                )[0]
                value_id = obj.pk

            attributes_json[str(item.instance.pk)].append(str(value_id))

    # Check that all required attributes were passed
    for missing_slug in attributes_map_by_slug.keys() ^ passed_slugs:
        attribute = attributes_map_by_slug[missing_slug]  # type: models.Attribute
        validate_attribute_input(attribute, [])

    return attributes_json
