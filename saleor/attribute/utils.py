from typing import TYPE_CHECKING, Set, Union

from ..page.models import Page
from ..product.models import Product, ProductVariant
from .models import (
    AssignedPageAttribute,
    AssignedProductAttribute,
    AssignedVariantAttribute,
    Attribute,
    AttributeValue,
)

AttributeAssignmentType = Union[
    AssignedProductAttribute, AssignedVariantAttribute, AssignedPageAttribute
]


if TYPE_CHECKING:
    from .models import AttributeProduct, AttributeVariant, AttributePage


def _associate_attribute_to_instance(
    instance: Union[Product, ProductVariant, Page], attribute_pk: int
) -> AttributeAssignmentType:
    """Associate a given attribute to an instance."""
    assignment: AttributeAssignmentType
    if isinstance(instance, Product):
        attribute_rel: Union[
            "AttributeProduct", "AttributeVariant", "AttributePage"
        ] = instance.product_type.attributeproduct.get(attribute_id=attribute_pk)

        assignment, _ = AssignedProductAttribute.objects.get_or_create(
            product=instance, assignment=attribute_rel
        )
    elif isinstance(instance, ProductVariant):
        attribute_rel = instance.product.product_type.attributevariant.get(
            attribute_id=attribute_pk
        )

        assignment, _ = AssignedVariantAttribute.objects.get_or_create(
            variant=instance, assignment=attribute_rel
        )
    elif isinstance(instance, Page):
        attribute_rel = instance.page_type.attributepage.get(attribute_id=attribute_pk)
        assignment, _ = AssignedPageAttribute.objects.get_or_create(
            page=instance, assignment=attribute_rel
        )
    else:
        raise AssertionError(f"{instance.__class__.__name__} is unsupported")

    return assignment


def validate_attribute_owns_values(attribute: Attribute, value_ids: Set[int]) -> None:
    """Check given value IDs are belonging to the given attribute.

    :raise: AssertionError
    """
    attribute_actual_value_ids = set(attribute.values.values_list("pk", flat=True))
    found_associated_ids = attribute_actual_value_ids & value_ids
    if found_associated_ids != value_ids:
        raise AssertionError("Some values are not from the provided attribute.")


def associate_attribute_values_to_instance(
    instance: Union[Product, ProductVariant, Page],
    attribute: Attribute,
    *values: AttributeValue,
) -> AttributeAssignmentType:
    """Assign given attribute values to a product or variant.

    Note: be award this function invokes the ``set`` method on the instance's
    attribute association. Meaning any values already assigned or concurrently
    assigned will be overridden by this call.
    """
    values_ids = {value.pk for value in values}

    # Ensure the values are actually form the given attribute
    validate_attribute_owns_values(attribute, values_ids)

    # Associate the attribute and the passed values
    assignment = _associate_attribute_to_instance(instance, attribute.pk)
    assignment.values.set(values)
    return assignment
