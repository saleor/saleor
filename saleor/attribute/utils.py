from collections.abc import Iterable
from typing import Union

from django.db.models.expressions import Exists, OuterRef

from ..page.models import Page
from ..product.models import Product, ProductVariant
from .models import (
    AssignedPageAttributeValue,
    AssignedProductAttributeValue,
    AssignedVariantAttribute,
    AssignedVariantAttributeValue,
    Attribute,
    AttributeValue,
    AttributeVariant,
)

T_INSTANCE = Union[Product, ProductVariant, Page]


def associate_attribute_values_to_instance(
    instance: T_INSTANCE,
    attribute: Attribute,
    *values: AttributeValue,
) -> Union[None, AssignedVariantAttribute]:
    """Assign given attribute values to a product or variant.

    Note: be aware this function invokes the ``set`` method on the instance's
    attribute association. Meaning any values already assigned or concurrently
    assigned will be overridden by this call.
    """
    values_ids = {value.pk for value in values}

    # Ensure the values are actually form the given attribute
    validate_attribute_owns_values(attribute, values_ids)

    # Associate the attribute and the passed values
    return _associate_attribute_to_instance(instance, attribute, *values)


def validate_attribute_owns_values(attribute: Attribute, value_ids: set[int]) -> None:
    """Check if given value IDs belong to the given Attribute.

    :raise: AssertionError
    """
    attribute_actual_value_ids = set(
        AttributeValue.objects.filter(
            pk__in=value_ids, attribute=attribute
        ).values_list("pk", flat=True)
    )
    if attribute_actual_value_ids != value_ids:
        raise AssertionError("Some values are not from the provided attribute.")


def _associate_attribute_to_instance(
    instance: T_INSTANCE,
    attribute: Attribute,
    *values: AttributeValue,
) -> Union[None, AssignedVariantAttribute]:
    """Associate a given attribute to an instance.

    For a given instance assign an attribute to it and set values based on *values.

    Note: this will clean any value that already exist there.

    This function is under rebuilding while we move away from intermediate models
    for attribute relations

    See:
    https://github.com/saleor/saleor/issues/12881
    """
    if isinstance(instance, Page):
        # Clear all assignments that don't match the values we'd like to assign
        value_ids = [value.pk for value in values]
        values_qs = AttributeValue.objects.filter(attribute_id=attribute.pk)
        AssignedPageAttributeValue.objects.filter(
            Exists(values_qs.filter(id=OuterRef("value_id"))),
            page_id=instance.pk,
        ).exclude(value_id__in=value_ids).delete()

        # Create new assignments
        # Spend on db query to check values that are in the db so that we can use bulk_create
        # to set the new assignments
        # This code will be able to use bulk_create option ignore_conflicts once
        # unique_together is set for product + value on AssignedProductAttributeValue
        existing_page_values = AssignedPageAttributeValue.objects.filter(
            page=instance, value_id__in=value_ids
        ).values_list("value_id", flat=True)
        new_values = list(set(value_ids) - set(existing_page_values))

        AssignedPageAttributeValue.objects.bulk_create(
            AssignedPageAttributeValue(page=instance, value_id=value_id)
            for value_id in new_values
        )

        sort_assigned_attribute_values(instance, attribute, values)
        return None

    if isinstance(instance, Product):
        # Clear all assignments that don't match the values we'd like to assign
        value_ids = [value.pk for value in values]

        values_qs = AttributeValue.objects.filter(attribute_id=attribute.pk)
        AssignedProductAttributeValue.objects.filter(
            Exists(values_qs.filter(id=OuterRef("value_id"))),
            product_id=instance.pk,
        ).exclude(value_id__in=value_ids).delete()

        # Create new assignments
        # Spend on db query to check values that are in the db so that we can use bulk_create
        # to set the new assignments
        # This code will be able to use bulk_create option ignore_conflicts once
        # unique_together is set for product + value on AssignedProductAttributeValue
        existing_product_values = AssignedProductAttributeValue.objects.filter(
            product=instance, value_id__in=value_ids
        ).values_list("value_id", flat=True)
        new_values = list(set(value_ids) - set(existing_product_values))

        AssignedProductAttributeValue.objects.bulk_create(
            AssignedProductAttributeValue(product=instance, value_id=value_id)
            for value_id in new_values
        )

        sort_assigned_attribute_values(instance, attribute, values)
        return None

    if isinstance(instance, ProductVariant):
        assignment: AssignedVariantAttribute

        attribute_variant = AttributeVariant.objects.get(
            attribute_id=attribute.pk,
            product_type_id=instance.product.product_type_id,
        )

        assignment, _ = AssignedVariantAttribute.objects.get_or_create(
            variant=instance, assignment=attribute_variant
        )
        assignment.values.set(values)
        sort_assigned_attribute_values_using_assignment(instance, assignment, values)
        return assignment

    raise AssertionError(f"{instance.__class__.__name__} is unsupported")


def sort_assigned_attribute_values_using_assignment(
    instance: ProductVariant,
    assignment: AssignedVariantAttribute,
    values: Iterable[AttributeValue],
) -> None:
    """Sort assigned attribute values based on values list order."""
    instance_to_value_assignment_mapping = {
        "ProductVariant": ("variantvalueassignment", AssignedVariantAttributeValue),
    }
    assignment_lookup, assignment_model = instance_to_value_assignment_mapping[
        instance.__class__.__name__
    ]
    values_pks = [value.pk for value in values]

    values_assignment = list(
        getattr(assignment, assignment_lookup).select_related("value")
    )

    values_assignment.sort(key=lambda e: values_pks.index(e.value.pk))
    for index, value_assignment in enumerate(values_assignment):
        value_assignment.sort_order = index

    assignment_model._default_manager.bulk_update(values_assignment, ["sort_order"])


def sort_assigned_attribute_values(
    instance: Union[Page, Product],
    attribute: Attribute,
    values: Iterable[AttributeValue],
) -> None:
    values_pks = [value.pk for value in values]
    values_qs = AttributeValue.objects.filter(attribute_id=attribute.pk)

    if isinstance(instance, Page):
        assigned_page_values = list(
            AssignedPageAttributeValue.objects.filter(
                Exists(values_qs.filter(id=OuterRef("value_id"))),
                page_id=instance.pk,
            ).iterator()
        )
        assigned_page_values.sort(key=lambda e: values_pks.index(e.value_id))
        for index, page_value_assignment in enumerate(assigned_page_values):
            page_value_assignment.sort_order = index
        AssignedPageAttributeValue.objects.bulk_update(
            assigned_page_values,
            ["sort_order"],
        )
        return

    if isinstance(instance, Product):
        assigned_product_values = list(
            AssignedProductAttributeValue.objects.filter(
                Exists(values_qs.filter(id=OuterRef("value_id"))),
                product=instance.pk,
            ).iterator()
        )
        assigned_product_values.sort(key=lambda e: values_pks.index(e.value_id))
        for index, product_value_assignment in enumerate(assigned_product_values):
            product_value_assignment.sort_order = index
        AssignedProductAttributeValue.objects.bulk_update(
            assigned_product_values,
            ["sort_order"],
        )
        return
