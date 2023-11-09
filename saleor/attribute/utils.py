from collections.abc import Iterable
from typing import TYPE_CHECKING, Union

from django.db.models.expressions import Exists, OuterRef

from ..page.models import Page
from ..product.models import Product, ProductVariant
from .models import (
    AssignedPageAttributeValue,
    AssignedProductAttribute,
    AssignedProductAttributeValue,
    AssignedVariantAttribute,
    AssignedVariantAttributeValue,
    Attribute,
    AttributeValue,
)

AttributeAssignmentType = Union[AssignedVariantAttribute, AssignedProductAttribute]
T_INSTANCE = Union[Product, ProductVariant, Page]

if TYPE_CHECKING:
    from .models import AttributePage, AttributeProduct, AttributeVariant


def disassociate_attributes_from_instance(
    instance: T_INSTANCE,
    *attributes: Attribute,
) -> None:
    """Remove attribute assigned to an instance.

    This has to remove a FK to Attribute from Page instance and
    remove all value assignments related to that same product and attribute.
    """
    values = AttributeValue.objects.filter(
        attribute_id__in=[attr.id for attr in attributes]
    )
    AssignedPageAttributeValue.objects.filter(
        Exists(values.filter(id=OuterRef("value_id"))),
        page_id=instance.pk,
    ).delete()


def associate_attribute_values_to_instance(
    instance: T_INSTANCE,
    attribute: Attribute,
    *values: AttributeValue,
) -> Union[None, AttributeAssignmentType]:
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
    """Check given value IDs are belonging to the given attribute.

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
) -> Union[None, AttributeAssignmentType]:
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
        values_qs = AttributeValue.objects.filter(attribute_id=attribute.pk)
        AssignedPageAttributeValue.objects.filter(
            Exists(values_qs.filter(id=OuterRef("value_id"))),
            page_id=instance.pk,
        ).exclude(value__in=values).delete()

        # Create new assignments
        for value in values:
            AssignedPageAttributeValue.objects.get_or_create(page=instance, value=value)

        sort_assigned_attribute_values(instance, attribute, values)
        return None

    assignment: AttributeAssignmentType

    if isinstance(instance, Product):
        attribute_rel: Union[
            "AttributeProduct", "AttributeVariant", "AttributePage"
        ] = instance.product_type.attributeproduct.get(attribute_id=attribute.pk)

        assignment, _ = AssignedProductAttribute.objects.get_or_create(
            product=instance, assignment=attribute_rel
        )
        assignment.values.set(values)

        sort_assigned_attribute_values_using_assignment(instance, assignment, values)

        # While migrating to a new structure we need to make sure we also
        # copy the assigned product to AssignedProductAttributeValue
        # where it will live after issue #12881 will be implemented
        AssignedProductAttributeValue.objects.filter(
            assignment_id=assignment.pk
        ).update(product_id=instance.pk)

        return assignment

    if isinstance(instance, ProductVariant):
        attribute_variant = instance.product.product_type.attributevariant.get(
            attribute_id=attribute.pk
        )

        assignment, _ = AssignedVariantAttribute.objects.get_or_create(
            variant=instance, assignment=attribute_variant
        )
        assignment.values.set(values)

        sort_assigned_attribute_values_using_assignment(instance, assignment, values)
        return assignment

    raise AssertionError(f"{instance.__class__.__name__} is unsupported")


def sort_assigned_attribute_values_using_assignment(
    instance: T_INSTANCE,
    assignment: AttributeAssignmentType,
    values: Iterable[AttributeValue],
) -> None:
    """Sort assigned attribute values based on values list order."""
    instance_to_value_assignment_mapping = {
        "ProductVariant": ("variantvalueassignment", AssignedVariantAttributeValue),
        "Product": ("productvalueassignment", AssignedProductAttributeValue),
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
    instance: Page,
    attribute: Attribute,
    values: Iterable[AttributeValue],
) -> None:
    values_pks = [value.pk for value in values]

    values_qs = AttributeValue.objects.filter(attribute_id=attribute.pk)
    values_assignment = list(
        instance.attributevalues.filter(
            Exists(values_qs.filter(id=OuterRef("value_id"))),
        )
    )
    values_assignment.sort(key=lambda e: values_pks.index(e.value_id))
    for index, value_assignment in enumerate(values_assignment):
        value_assignment.sort_order = index

    AssignedPageAttributeValue.objects.bulk_update(values_assignment, ["sort_order"])
