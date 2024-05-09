from collections import defaultdict
from functools import reduce
from typing import Union

from django.db.models import Exists, OuterRef, Q

from ..page.models import Page
from ..product.models import Product, ProductVariant
from .models import (
    AssignedPageAttributeValue,
    AssignedProductAttributeValue,
    AssignedVariantAttribute,
    AssignedVariantAttributeValue,
    AttributePage,
    AttributeProduct,
    AttributeValue,
    AttributeVariant,
)

T_INSTANCE = Union[Product, ProductVariant, Page]


instance_to_function_variables_mapping = {
    "Product": (
        AttributeProduct,
        AssignedProductAttributeValue,
        "product",
    ),
    "ProductVariant": (
        AttributeVariant,
        AssignedVariantAttributeValue,
        "variant",
    ),
    "Page": (AttributePage, AssignedPageAttributeValue, "page"),
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
        value_model,
        instance_field_name,
    ) = variables

    assignments = []
    if isinstance(instance, ProductVariant):
        prod_type_id = instance.product.product_type_id
        attribute_filter: dict[str, Union[int, list[int]]] = {
            "attribute_id__in": list(attr_val_map.keys()),
            "product_type_id": prod_type_id,
        }
        instance_attrs_ids = instance_attribute_model.objects.filter(  # type: ignore
            **attribute_filter
        ).values_list("pk", flat=True)

        assignments = _get_or_create_assignments(
            instance, instance_attrs_ids, AssignedVariantAttribute, instance_field_name
        )

    values_order_map = _overwrite_values(
        instance,
        assignments,
        attr_val_map,
        value_model,
        None if instance_field_name == "variant" else instance_field_name,
    )

    if isinstance(instance, ProductVariant):
        _order_variant_assigned_attr_values(
            values_order_map, assignments, attr_val_map, AssignedVariantAttributeValue
        )
    else:
        _order_assigned_attr_values(
            values_order_map, attr_val_map, value_model, instance_field_name, instance
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


def _overwrite_values(
    instance, assignments, attr_val_map, value_assignment_model, instance_field_name
) -> dict[int, list]:
    instance_field_kwarg = (
        {instance_field_name: instance} if instance_field_name else {}
    )

    value_ids = [v.id for values in attr_val_map.values() for v in values]
    new_value_ids = value_ids
    assignment_attr_map = {a.assignment.attribute_id: a for a in assignments}
    if isinstance(instance, ProductVariant):
        value_assignment_model.objects.filter(
            assignment_id__in=[a.pk for a in assignments],
        ).exclude(value_id__in=value_ids).delete()
    else:
        values_qs = AttributeValue.objects.filter(
            attribute_id__in=list(attr_val_map.keys())
        )
        value_ids = [v.pk for values in attr_val_map.values() for v in values]
        assigned_values = value_assignment_model.objects.filter(
            Exists(values_qs.filter(id=OuterRef("value_id"))), **instance_field_kwarg
        )

        # Clear all assignments that don't match the values we'd like to assign
        assigned_values.exclude(value_id__in=value_ids).delete()

        new_value_ids = list(
            set(value_ids) - set(assigned_values.values_list("value_id", flat=True))
        )

    # Create new assignments
    # Spend on db query to check values that are in the db so that we can use bulk_create
    # to set the new assignments
    # This code will be able to use bulk_create option ignore_conflicts once
    # unique_together is set for product + value on AssignedProductAttributeValue
    values_order_map = defaultdict(list)
    assigned_attr_values_instances = []
    for attr_id, values in attr_val_map.items():
        assignment = assignment_attr_map.get(attr_id)

        for value in values:
            if value.id not in new_value_ids:
                values_order_map[attr_id].append(value.id)
                continue

            params = {"value": value, **instance_field_kwarg}
            if assignment:
                params["assignment_id"] = assignment.id
            assigned_attr_values_instances.append(value_assignment_model(**params))
            if assignment:
                values_order_map[assignment.id].append(value.id)
            else:
                values_order_map[attr_id].append(value.id)

    value_assignment_model.objects.bulk_create(
        assigned_attr_values_instances, ignore_conflicts=True
    )
    return values_order_map


def _order_assigned_attr_values(
    values_order_map, attr_val_map, assignment_model, instance_field_name, instance
) -> None:
    instance_field_kwarg = (
        {instance_field_name: instance} if instance_field_name else {}
    )

    value_id_to_attribute_id = {
        v.id: attr_id for attr_id, values in attr_val_map.items() for v in values
    }
    attribute_ids = list(attr_val_map.keys())

    values_qs = AttributeValue.objects.filter(attribute_id__in=attribute_ids)
    assigned_values = list(
        assignment_model.objects.filter(
            Exists(values_qs.filter(id=OuterRef("value_id"))),
            **instance_field_kwarg,
        ).iterator()
    )
    for value in assigned_values:
        attribute_id = value_id_to_attribute_id[value.value_id]
        value.sort_order = values_order_map[attribute_id].index(value.value_id)

    assignment_model.objects.bulk_update(assigned_values, ["sort_order"])

    return


def _order_variant_assigned_attr_values(
    values_order_map, assignments, attr_val_map, assignment_model
) -> None:
    assigned_attrs_values = assignment_model.objects.filter(
        assignment_id__in=(a.pk for a in assignments),
        value_id__in=(v.pk for values in attr_val_map.values() for v in values),
    )
    for value in assigned_attrs_values:
        value.sort_order = values_order_map[value.assignment_id].index(value.value_id)

    assignment_model.objects.bulk_update(assigned_attrs_values, ["sort_order"])
