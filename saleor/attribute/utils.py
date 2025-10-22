from collections import defaultdict

from django.conf import settings
from django.db.models import Exists, OuterRef, Q

from ..page.models import Page
from ..product.models import Product, ProductVariant
from .models import (
    AssignedPageAttributeValue,
    AssignedProductAttributeValue,
    AssignedVariantAttributeValue,
    AttributeValue,
)

T_INSTANCE = Product | ProductVariant | Page


instance_to_function_variables_mapping = {
    "Product": (
        AssignedProductAttributeValue,
        "product",
    ),
    "ProductVariant": (
        AssignedVariantAttributeValue,
        "variant",
    ),
    "Page": (AssignedPageAttributeValue, "page"),
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

    # prepare a lookup with all attributes and their values to get them from the db
    lookup = Q()
    for attribute_id, values in attr_val_map.items():
        value_slugs = [value.slug for value in values]
        lookup |= Q(attribute_id=attribute_id, slug__in=value_slugs)

    values = AttributeValue.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).filter(lookup)

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

    value_model, instance_field_name = variables
    values_order_map = _overwrite_values(
        instance, attr_val_map, value_model, instance_field_name
    )

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
    instance, attr_val_map, value_assignment_model, instance_field_name
) -> dict[int, list]:
    instance_field_kwarg = (
        {instance_field_name: instance} if instance_field_name else {}
    )

    value_ids = [v.id for values in attr_val_map.values() for v in values]
    new_value_ids = value_ids

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
        for value in values:
            if value.id not in new_value_ids:
                values_order_map[attr_id].append(value.id)
                continue

            params = {"value": value, **instance_field_kwarg}
            assigned_attr_values_instances.append(value_assignment_model(**params))
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
        ).iterator(chunk_size=1000)
    )
    for value in assigned_values:
        attribute_id = value_id_to_attribute_id[value.value_id]
        value.sort_order = values_order_map[attribute_id].index(value.value_id)

    assignment_model.objects.bulk_update(assigned_values, ["sort_order"])

    return
