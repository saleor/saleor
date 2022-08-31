from typing import TYPE_CHECKING, Iterable, List, Optional, Tuple

from ...attribute import AttributeType

if TYPE_CHECKING:
    from ...attribute.models import AssignedVariantAttribute, Attribute
    from ..models import ProductVariant


def generate_and_set_variant_name(variant: "ProductVariant", sku: Optional[str]):
    """Generate ProductVariant's name based on its attributes."""
    attributes_display = []

    variant_selection_attributes = variant.attributes.filter(
        assignment__variant_selection=True,
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
        name = sku or variant.get_global_id()

    variant.name = name
    variant.save(update_fields=["name", "updated_at"])


def get_variant_selection_attributes(
    attributes: Iterable[Tuple["Attribute", bool]]
) -> List[Tuple["Attribute", bool]]:
    """Return attributes that can be used in variant selection.

    Attribute must be product attribute and attribute input type must be
    in ALLOWED_IN_VARIANT_SELECTION list.
    """
    return [
        (attribute, variant_selection)
        for attribute, variant_selection in attributes
        if variant_selection and attribute.type == AttributeType.PRODUCT_TYPE
    ]
