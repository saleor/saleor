from typing import TYPE_CHECKING

from ...attribute import AttributeInputType, AttributeType

if TYPE_CHECKING:
    from ...attribute.models import AssignedVariantAttribute
    from ..models import ProductVariant


def generate_name_for_variant(variant: "ProductVariant") -> str:
    """Generate ProductVariant's name based on its attributes."""
    attributes_display = []

    for attribute_rel in variant.attributes.all():  # type: AssignedVariantAttribute
        values_qs = attribute_rel.values.all()  # FIXME: this should be sorted
        translated_values = [str(value.translated) for value in values_qs]
        attributes_display.append(", ".join(translated_values))

    return " / ".join(attributes_display)


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
