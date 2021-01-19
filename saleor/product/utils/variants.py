from typing import TYPE_CHECKING

from ...attribute import AttributeInputType, AttributeType

if TYPE_CHECKING:
    from ...attribute.models import AssignedVariantAttribute
    from ..models import ProductVariant


def generate_and_set_variant_name(variant: "ProductVariant", sku: str):
    """Generate ProductVariant's name based on its attributes."""
    attributes_display = []

    variant_selection_input_types = AttributeInputType.ALLOWED_IN_VARIANT_SELECTION
    variant_selection_attributes = variant.attributes.filter(
        assignment__attribute__input_type__in=variant_selection_input_types,
        assignment__attribute__type=AttributeType.PRODUCT_TYPE,
    )
    for (
        attribute_rel
    ) in variant_selection_attributes.iterator():  # type: AssignedVariantAttribute
        values_qs = attribute_rel.values.all()
        translated_values = [str(value.translated) for value in values_qs]
        attributes_display.append(", ".join(translated_values))

    name = " / ".join(sorted(attributes_display))
    if not name:
        name = sku

    variant.name = name
    variant.save(update_fields=["name"])


def get_variant_selection_attributes(attributes):
    """Return attributes that can be used in variant selection.

    Attribute must be product attribute and attribute input type must be
    in ALLOWED_IN_VARIANT_SELECTION list.
    """
    return [
        attribute
        for attribute in attributes
        if attribute.input_type in AttributeInputType.ALLOWED_IN_VARIANT_SELECTION
        and attribute.type == AttributeType.PRODUCT_TYPE
    ]
