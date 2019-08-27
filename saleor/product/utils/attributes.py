from typing import Union

from ..models import (
    AssignedProductAttribute,
    AssignedVariantAttribute,
    Attribute,
    AttributeValue,
    Product,
    ProductVariant,
)

T_ASSIGNMENT_REL = Union[AssignedProductAttribute, AssignedVariantAttribute]


def generate_name_for_variant(variant: ProductVariant) -> str:
    """Generate ProductVariant's name based on its attributes."""
    attributes_display = []

    for attribute_rel in variant.attributes.all():  # type: AssignedVariantAttribute
        values_qs = attribute_rel.values.all()  # FIXME: this should be sorted
        translated_values = [str(value.translated) for value in values_qs]
        attributes_display.append(", ".join(translated_values))

    return " / ".join(attributes_display)


def _associate_attribute_to_instance(
    instance: Union[Product, ProductVariant], attribute_pk: Attribute
) -> T_ASSIGNMENT_REL:
    """Associate a given attribute to an instance."""
    if isinstance(instance, Product):
        attribute_rel = instance.product_type.attributeproduct.get(
            attribute_id=attribute_pk
        )

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


def associate_attribute_values_to_instance(
    instance: Union[Product, ProductVariant],
    attribute: Attribute,
    *values: AttributeValue,
) -> T_ASSIGNMENT_REL:
    """Assign given attribute values to a product or variant.

    Note: be award this function invokes the ``set`` method on the instance's
    attribute association. Meaning any values already assigned or concurrently
    assigned will be overridden by this call.
    """
    assignment = _associate_attribute_to_instance(instance, attribute.pk)
    assignment.values.set(values)
    return assignment
