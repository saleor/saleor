from typing import TYPE_CHECKING, Optional, Set, Union

from ..models import (
    AssignedProductAttribute,
    AssignedVariantAttribute,
    Attribute,
    AttributeValue,
    Product,
    ProductVariant,
)

AttributeAssignmentType = Union[AssignedProductAttribute, AssignedVariantAttribute]


if TYPE_CHECKING:
    # flake8: noqa
    from ..models import AttributeProduct, AttributeVariant


def generate_name_for_variant(variant: ProductVariant) -> str:
    """Generate ProductVariant's name based on its attributes."""
    attributes_display = []

    for attribute_rel in variant.attributes.all():  # type: AssignedVariantAttribute
        values_qs = attribute_rel.values.all()  # FIXME: this should be sorted
        translated_values = [str(value.translated) for value in values_qs]
        attributes_display.append(", ".join(translated_values))

    return " / ".join(attributes_display)


def _associate_attribute_to_instance(
    instance: Union[Product, ProductVariant], attribute_pk: int
) -> AttributeAssignmentType:
    """Associate a given attribute to an instance."""
    assignment: Union["AssignedProductAttribute", "AssignedVariantAttribute"]
    if isinstance(instance, Product):
        attribute_rel: Union[
            "AttributeProduct", "AttributeVariant"
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
    instance: Union[Product, ProductVariant],
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
