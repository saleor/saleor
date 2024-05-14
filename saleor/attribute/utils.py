from collections import defaultdict
from functools import reduce
from typing import Union

from django.db.models import Q

from ..page.models import Page
from ..product.models import Product, ProductVariant
from .models import (
    AssignedPageAttribute,
    AssignedPageAttributeValue,
    AssignedProductAttribute,
    AssignedProductAttributeValue,
    AssignedVariantAttribute,
    AssignedVariantAttributeValue,
    AttributePage,
    AttributeProduct,
    AttributeValue,
    AttributeVariant,
)

AttributeAssignmentType = Union[
    AssignedProductAttribute, AssignedVariantAttribute, AssignedPageAttribute
]
T_INSTANCE = Union[Product, ProductVariant, Page]


instance_to_function_variables_mapping = {
    "Product": (
        AttributeProduct,
        AssignedProductAttribute,
        AssignedProductAttributeValue,
        "product",
    ),
    "ProductVariant": (
        AttributeVariant,
        AssignedVariantAttribute,
        AssignedVariantAttributeValue,
        "variant",
    ),
    "Page": (AttributePage, AssignedPageAttribute, AssignedPageAttributeValue, "page"),
}


def associate_attribute_values_to_instance(
    instance: T_INSTANCE, attr_val_map: dict[int, list]
):
    """Assign given attribute values to a product, variant or page.

    Note: be aware any values already assigned or concurrently
    assigned will be overridden by this call.
    """

    # Ensure the values are actually form the given attribute
    validate_attribute_owns_values(attr_val_map)

    # Associate the attribute and the passed values
    _associate_attribute_to_instance(instance, attr_val_map)


def validate_attribute_owns_values(attr_val_map: dict[int, list]) -> None:
    if not attr_val_map:
        return
    values_map = defaultdict(set)
    slug_value_to_value_map = {}

    # we need to fetch the proper values which attribute ids and value slug matches
    lookup = reduce(
        lambda acc, val_map_item: acc
        | Q(
            attribute_id=val_map_item[0], slug__in=[val.slug for val in val_map_item[1]]
        ),
        attr_val_map.items(),
        Q(),
    )
    values = AttributeValue.objects.filter(lookup)

    for value in values:
        attr_id = value.attribute_id
        values_map[attr_id].add(value.slug)
        slug_value_to_value_map[attr_id, value.slug] = value

    for attribute_id, attr_values in attr_val_map.items():
        if values_map[attribute_id] != {v.slug for v in attr_values}:
            raise AssertionError("Some values are not from the provided attribute.")
        # Update the attr_val_map to use the created AttributeValue instances with
        # id set. This is needed as `ignore_conflicts=True` flag in `bulk_create
        # is used in `AttributeValueManager`
        attr_val_map[attribute_id] = [
            slug_value_to_value_map[attribute_id, v.slug] for v in attr_values
        ]


def _associate_attribute_to_instance(
    instance: T_INSTANCE, attr_val_map: dict[int, list]
):
    instance_type = instance.__class__.__name__
    variables = instance_to_function_variables_mapping.get(instance_type)

    if not variables:
        raise AssertionError(f"{instance_type} is unsupported")

    (
        instance_attribute_model,
        assignment_model,
        value_model,
        instance_field_name,
    ) = variables

    attribute_filter: dict[str, Union[int, list[int]]] = {
        "attribute_id__in": list(attr_val_map.keys()),
    }

    if isinstance(instance, Page):
        attribute_filter["page_type_id"] = instance.page_type_id
    elif isinstance(instance, ProductVariant):
        prod_type_id = instance.product.product_type_id
        attribute_filter["product_type_id"] = prod_type_id
    else:
        attribute_filter["product_type_id"] = instance.product_type_id

    instance_attrs_ids = instance_attribute_model.objects.filter(
        **attribute_filter
    ).values_list("pk", flat=True)

    assignments = _get_or_create_assignments(
        instance, instance_attrs_ids, assignment_model, instance_field_name
    )

    values_order_map = _overwrite_values(assignments, attr_val_map, value_model)
    _order_assigned_attr_values(
        values_order_map, assignments, attr_val_map, value_model
    )


def _get_or_create_assignments(
    instance, instance_attrs_ids, assignment_model, instance_field_name
):
    instance_field_kwarg = {instance_field_name: instance}
    assignments = list(
        assignment_model.objects.filter(
            assignment_id__in=instance_attrs_ids, **instance_field_kwarg
        )
    )

    assignments_to_create = []
    for id in instance_attrs_ids:
        if id not in [a.assignment_id for a in assignments]:
            assignments_to_create.append(id)

    if assignments_to_create:
        assignments += list(
            assignment_model.objects.bulk_create(
                [
                    assignment_model(
                        assignment_id=assignment_id, **instance_field_kwarg
                    )
                    for assignment_id in assignments_to_create
                ]
            )
        )
    return assignments


def _overwrite_values(assignments, attr_val_map, assignment_model) -> dict[int, list]:
    assignment_attr_map = {a.assignment.attribute_id: a for a in assignments}

    assignment_model.objects.filter(
        assignment_id__in=[a.pk for a in assignments],
    ).exclude(
        value_id__in=[v.pk for values in attr_val_map.values() for v in values]
    ).delete()

    values_order_map = defaultdict(list)
    assigned_attr_values_instances = []
    for attr_id, values in attr_val_map.items():
        assignment = assignment_attr_map[attr_id]

        for value in values:
            assigned_attr_values_instances.append(
                assignment_model(value=value, assignment_id=assignment.id)
            )
            values_order_map[assignment.id].append(value.id)

    assignment_model.objects.bulk_create(
        assigned_attr_values_instances, ignore_conflicts=True
    )
    return values_order_map


def _order_assigned_attr_values(
    values_order_map, assignments, attr_val_map, assigment_model
) -> None:
    assigned_attrs_values = assigment_model.objects.filter(
        assignment_id__in=(a.pk for a in assignments),
        value_id__in=(v.pk for values in attr_val_map.values() for v in values),
    )
    for value in assigned_attrs_values:
        value.sort_order = values_order_map[value.assignment_id].index(value.value_id)

    assigment_model.objects.bulk_update(assigned_attrs_values, ["sort_order"])
